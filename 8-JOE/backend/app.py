"""Joe & The Juice – pantsystem for genanvendelige kopper. Flask API (logiklag).

Kravgrundlag: ../Kravspecifikation.md
Kør:  pip install -r requirements.txt  &&  python app.py  →  http://localhost:5108
"""
import os
import secrets

from flask import jsonify

from core import ApiError, create_app, get_or_404, json_body, now, register_crud, require, run
from database import init_db, query_all, query_one, transaction

PORT = int(os.environ.get("PORT", 5108))
app = create_app(__name__, "JOE Pantsystem")


# ---------------------------------------------------------------- Centrale indstillinger (kan justeres uden ny kode)
def setting(key):
    row = query_one("SELECT value FROM setting WHERE key = ?", (key,))
    if row is None:
        raise ApiError(f"Indstillingen {key} mangler", 500)
    return row["value"]


def new_cup_code():
    """Unik, svær at gætte kop-kode (i virkeligheden trykt som QR eller indstøbt RFID)."""
    return f"JOE-{secrets.token_hex(4).upper()}"


def log_transaction(db, type_, store_id, cup_id=None, customer_id=None, amount=0, points=0, note=None):
    db.execute("""INSERT INTO deposit_transaction (cup_id, customer_id, store_id, type, amount, points, created_at, note)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
               (cup_id, customer_id, store_id, type_, amount, points, now(), note))


# ---------------------------------------------------------------- CRUD
register_crud(app, "settings", "setting", fields=["key", "value", "description"], required=["key", "value"],
              update_fields=["value", "description"])
register_crud(app, "stores", "store", fields=["name", "city", "location_type"], required=["name", "city"])
register_crud(app, "customers", "customer", fields=["name", "email"], required=["name", "email"])
register_crud(app, "drinks", "drink", fields=["name", "price"], required=["name", "price"])
register_crud(app, "cups", "cup", fields=["status", "order_id", "code"], read_only=True, order_by="id DESC")


# ---------------------------------------------------------------- Køb: pant opkræves og kop udleveres (FR-01, FR-02)
@app.post("/api/orders")
def create_order():
    """Salg med pant-kop: opkræver pant og udleverer en kop med unik kode."""
    data = json_body()
    require(data, "store_id", "drink_id")
    store = get_or_404("store", data["store_id"], "Butik")
    drink = get_or_404("drink", data["drink_id"], "Drik")
    customer = data.get("customer_id") and get_or_404("customer", data["customer_id"], "Kunde")
    deposit = setting("deposit_amount")
    code = new_cup_code()

    with transaction() as db:
        next_no = db.execute("SELECT COALESCE(MAX(id), 0) + 100001 FROM sale_order").fetchone()[0]
        receipt_no = f"K-{next_no}"
        order_id = db.execute(
            """INSERT INTO sale_order (receipt_no, store_id, customer_id, drink_id, price, deposit, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (receipt_no, store["id"], customer["id"] if customer else None, drink["id"], drink["price"], deposit,
             now())).lastrowid
        cup_id = db.execute("INSERT INTO cup (code, order_id, issued_at) VALUES (?, ?, ?)",
                            (code, order_id, now())).lastrowid
        log_transaction(db, "PANT_BETALT", store["id"], cup_id, customer["id"] if customer else None, deposit,
                        note=receipt_no + ("" if customer else " – kunde uden app"))

    return jsonify(receipt={
        "receipt_no": receipt_no, "store": store["name"], "drink": drink["name"],
        "price": drink["price"], "deposit": deposit, "total": drink["price"] + deposit,
        "cup_code": code, "customer": customer["name"] if customer else None,
        "message": f"Heraf {deposit:g} kr. i pant – aflevér koppen i en hvilken som helst JOE-butik "
                   f"og få {deposit * setting('points_per_krone'):g} point i appen.",
    }), 201


# ---------------------------------------------------------------- Retur: scan kop-kode og kreditér point (FR-03 – FR-07, FR-10)
@app.post("/api/returns")
def return_cup():
    """Retur: scan kop-koden og kreditér point. Samme kop kan kun indløses én gang."""
    data = json_body()
    require(data, "cup_code", "store_id")
    store = get_or_404("store", data["store_id"], "Butik")
    code = data["cup_code"].strip().upper()
    cup = query_one("""SELECT c.*, o.customer_id, o.deposit, o.receipt_no FROM cup c
                       JOIN sale_order o ON o.id = c.order_id WHERE c.code = ?""", (code,))

    def reject(message, status=400):
        with transaction() as db:
            log_transaction(db, "RETUR_AFVIST", store["id"], cup["id"] if cup else None, note=f"{code}: {message}")
        raise ApiError(message, status)

    if cup is None:
        reject(f"Kop-koden {code} findes ikke. Kontrollér koden eller scan igen.", 404)
    if cup["status"] == "RETURNERET":
        reject(f"Koppen {code} er allerede returneret {cup['returned_at']} – pant kan kun indløses én gang.", 409)

    # Kunden findes via ordren, via den app-konto der scanner, eller via kvitteringsnummeret (FR-10)
    customer_id = cup["customer_id"] or data.get("customer_id")
    if not customer_id and data.get("receipt_no") and data["receipt_no"].strip().upper() != cup["receipt_no"]:
        reject("Kvitteringsnummeret passer ikke til koppen.")
    if not customer_id:
        reject("Koppen er ikke knyttet til en app-konto. Log ind i appen og scan koppen for at få dine point.")
    customer = get_or_404("customer", customer_id, "Kunde")

    points = int(cup["deposit"] * setting("points_per_krone"))
    with transaction() as db:
        db.execute("UPDATE cup SET status = 'RETURNERET', returned_at = ?, returned_store_id = ? WHERE id = ?",
                   (now(), store["id"], cup["id"]))
        db.execute("UPDATE customer SET points = points + ? WHERE id = ?", (points, customer["id"]))
        log_transaction(db, "RETUR_GODKENDT", store["id"], cup["id"], customer["id"], cup["deposit"], points,
                        note=None if cup["customer_id"] else "Kop koblet til konto ved retur")
    return jsonify(approved=True, cup_code=code, customer=customer["name"], points_added=points,
                   new_balance=customer["points"] + points,
                   message=f"Tak! {points} point er lagt på {customer['name']}s konto."), 201


@app.post("/api/customers/<int:customer_id>/redeem")
def redeem_points(customer_id):
    """Point kan kun bruges digitalt i appen – fx som rabat på næste køb."""
    customer = get_or_404("customer", customer_id, "Kunde")
    data = json_body()
    require(data, "points", "store_id")
    points = int(data["points"])
    if not 0 < points <= customer["points"]:
        raise ApiError(f"Du har {customer['points']} point og kan ikke indløse {points}.")
    value = round(points * setting("points_value_kr"), 2)
    with transaction() as db:
        db.execute("UPDATE customer SET points = points - ? WHERE id = ?", (points, customer_id))
        log_transaction(db, "POINT_INDLØST", data["store_id"], customer_id=customer_id, points=-points,
                        note=f"Rabat {value:g} kr.")
    return jsonify(points_used=points, discount_kr=value, new_balance=customer["points"] - points)


# ---------------------------------------------------------------- App: pointsaldo og historik (FR-06)
@app.get("/api/customers/<int:customer_id>/wallet")
def wallet(customer_id):
    """Kundens app: pointsaldo, kopper at aflevere og historik."""
    customer = get_or_404("customer", customer_id, "Kunde")
    cups = query_all("""SELECT c.code, c.issued_at, o.deposit, s.name AS store_name
                        FROM cup c JOIN sale_order o ON o.id = c.order_id JOIN store s ON s.id = o.store_id
                        WHERE o.customer_id = ? AND c.status = 'UDLEVERET' ORDER BY c.issued_at DESC""",
                     (customer_id,))
    history = query_all("""SELECT t.*, s.name AS store_name, c.code AS cup_code
                           FROM deposit_transaction t JOIN store s ON s.id = t.store_id
                           LEFT JOIN cup c ON c.id = t.cup_id
                           WHERE t.customer_id = ? ORDER BY t.id DESC""", (customer_id,))
    returned = sum(1 for t in history if t["type"] == "RETUR_GODKENDT")
    return jsonify(customer=customer, points_value_kr=round(customer["points"] * setting("points_value_kr"), 2),
                   cups_to_return=cups, history=history,
                   impact={"cups_returned": returned, "badge": "🌱 Kop-helt" if returned >= 3 else None})


# ---------------------------------------------------------------- Bæredygtighedsrapport (FR-09)
@app.get("/api/sustainability")
def sustainability():
    """Bæredygtighedsrapport: udleverede og returnerede kopper, returrate og pr. butik."""
    per_store = query_all("""
        SELECT s.id, s.name, s.location_type,
               (SELECT COUNT(*) FROM cup c JOIN sale_order o ON o.id = c.order_id WHERE o.store_id = s.id) AS issued,
               (SELECT COUNT(*) FROM cup c WHERE c.returned_store_id = s.id) AS returned_here,
               (SELECT COUNT(*) FROM deposit_transaction t WHERE t.store_id = s.id AND t.type = 'RETUR_AFVIST') AS rejected
        FROM store s ORDER BY s.name""")
    totals = query_one("""SELECT COUNT(*) AS issued, SUM(status = 'RETURNERET') AS returned,
                                 SUM(status = 'UDLEVERET') AS outstanding FROM cup""")
    money = query_one("""SELECT COALESCE(SUM(CASE WHEN type = 'PANT_BETALT' THEN amount END), 0) AS deposits_paid,
                                COALESCE(SUM(CASE WHEN type = 'RETUR_GODKENDT' THEN amount END), 0) AS deposits_returned,
                                COALESCE(SUM(CASE WHEN type = 'RETUR_GODKENDT' THEN points END), 0) AS points_credited
                         FROM deposit_transaction""")
    no_app = query_one("""SELECT COUNT(*) AS n FROM cup c JOIN sale_order o ON o.id = c.order_id
                          WHERE o.customer_id IS NULL""")["n"]
    return jsonify(
        cups_issued=totals["issued"], cups_returned=totals["returned"] or 0, cups_outstanding=totals["outstanding"] or 0,
        return_rate_pct=round(100 * (totals["returned"] or 0) / totals["issued"]) if totals["issued"] else 0,
        cups_sold_without_app=no_app, **money, per_store=per_store,
    )


@app.get("/api/transactions")
def transactions():
    """Log over pant-transaktioner."""
    return jsonify(query_all("""SELECT t.*, s.name AS store_name, c.code AS cup_code, cu.name AS customer_name
                                FROM deposit_transaction t JOIN store s ON s.id = t.store_id
                                LEFT JOIN cup c ON c.id = t.cup_id LEFT JOIN customer cu ON cu.id = t.customer_id
                                ORDER BY t.id DESC LIMIT 100"""))


if __name__ == "__main__":
    init_db()
    run(app, PORT)
