"""StockUP – Strandvejsristeriet. Flask API (logiklag).

Kravgrundlag: ../README.md
Kør:  pip install -r requirements.txt  &&  python app.py  →  http://localhost:5101
"""
import math
import os

from flask import jsonify

from core import ApiError, create_app, get_or_404, json_body, now, register_crud, require, run
from database import init_db, query_all, query_one, transaction

PORT = int(os.environ.get("PORT", 5101))
app = create_app(__name__, "StockUP")

# ---------------------------------------------------------------- Forretningsregler
SACK_KG = 80        # en sæk modtages altid med 80 kg – registreres uden vejning
ROAST_KG = 25       # en ristning bruger altid 25 kg
SHRINK = 0.16       # ristesvind, bruges kun til at foreslå et poseantal


def sack_status(remaining_kg):
    if remaining_kg <= 0:
        return "TOM"
    if remaining_kg < ROAST_KG:
        return "REST"
    return "I_BRUG" if remaining_kg < SACK_KG else "PAA_LAGER"


def suggested_bags(bag_size_g):
    return math.floor(ROAST_KG * (1 - SHRINK) * 1000 / bag_size_g)


def max_bags(bag_size_g):
    return math.floor(ROAST_KG * 1000 / bag_size_g)


def log_movement(db, movement_type, entity_type, entity_id, quantity, unit, note):
    db.execute(
        "INSERT INTO movement (occurred_at, movement_type, entity_type, entity_id, quantity, unit, note)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (now(), movement_type, entity_type, entity_id, quantity, unit, note),
    )


# ---------------------------------------------------------------- CRUD
register_crud(app, "green-coffees", "green_coffee",
              fields=["name", "origin", "supplier", "cost_per_kg", "min_sacks"],
              required=["name"])

register_crud(app, "sacks", "sack",
              fields=["green_coffee_id", "lot_number", "received_date"],
              required=["green_coffee_id", "lot_number"],
              defaults={"initial_kg": SACK_KG, "remaining_kg": SACK_KG, "status": "PAA_LAGER"})

register_crud(app, "products", "product",
              fields=["sku", "name", "bag_size_g", "green_coffee_id", "min_bags", "price"],
              required=["sku", "name"])

register_crud(app, "roasts", "roast", fields=["sack_id", "product_id"], read_only=True, order_by="id DESC")
register_crud(app, "sales", "sale", fields=["product_id", "channel"], read_only=True, order_by="id DESC")
register_crud(app, "movements", "movement", fields=["entity_type", "movement_type"], read_only=True,
              order_by="id DESC")


# ---------------------------------------------------------------- Sække
SACK_SQL = """
    SELECT s.*, g.name AS coffee_name, g.origin,
           CAST(s.remaining_kg / ? AS INTEGER) AS roasts_left
    FROM sack s JOIN green_coffee g ON g.id = s.green_coffee_id
"""


@app.get("/api/sacks/roastable")
def roastable_sacks():
    """Sække med mindst 25 kg tilbage."""
    return jsonify(query_all(SACK_SQL + " WHERE s.remaining_kg >= ? ORDER BY s.received_date",
                             (ROAST_KG, ROAST_KG)))


@app.post("/api/sacks/<int:sack_id>/close")
def close_sack(sack_id):
    """Afslut restmængde under 25 kg – sækken tømmes og bliver TOM."""
    sack = get_or_404("sack", sack_id, "Sæk")
    if sack["remaining_kg"] >= ROAST_KG:
        raise ApiError(f"Sæk {sack['lot_number']} har {sack['remaining_kg']:g} kg og kan stadig ristes.")
    with transaction() as db:
        db.execute("UPDATE sack SET remaining_kg = 0, status = 'TOM' WHERE id = ?", (sack_id,))
        log_movement(db, "REST_AFSLUTTET", "sack", sack_id, -sack["remaining_kg"], "kg",
                     f"Rest afsluttet på {sack['lot_number']}")
    return jsonify(get_or_404("sack", sack_id))


# ---------------------------------------------------------------- Ristning og salg
@app.post("/api/roasts")
def register_roast():
    """Registrér ristning: trækker 25 kg fra sækken og lægger poser til varen."""
    data = json_body()
    require(data, "sack_id", "product_id")
    sack = get_or_404("sack", data["sack_id"], "Sæk")
    product = get_or_404("product", data["product_id"], "Vare")

    if sack["remaining_kg"] < ROAST_KG:
        raise ApiError(f"Sæk {sack['lot_number']} har {sack['remaining_kg']:g} kg tilbage "
                       f"og kan ikke dække en ristning på {ROAST_KG} kg.")
    if product["green_coffee_id"] and product["green_coffee_id"] != sack["green_coffee_id"]:
        raise ApiError(f"{product['name']} kan kun ristes fra sin egen råkaffetype.")

    bags = int(data.get("bags_produced") or suggested_bags(product["bag_size_g"]))
    if not 0 < bags <= max_bags(product["bag_size_g"]):
        raise ApiError(f"{bags} poser er urealistisk for {ROAST_KG} kg "
                       f"(maks. {max_bags(product['bag_size_g'])} á {product['bag_size_g']} g).")

    remaining = sack["remaining_kg"] - ROAST_KG
    with transaction() as db:
        db.execute("UPDATE sack SET remaining_kg = ?, status = ? WHERE id = ?",
                   (remaining, sack_status(remaining), sack["id"]))
        db.execute("UPDATE product SET stock_bags = stock_bags + ? WHERE id = ?", (bags, product["id"]))
        cur = db.execute(
            "INSERT INTO roast (sack_id, product_id, kg_used, bags_produced, performed_by, roasted_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (sack["id"], product["id"], ROAST_KG, bags, data.get("performed_by"), now()))
        log_movement(db, "RISTNING", "sack", sack["id"], -ROAST_KG, "kg",
                     f"Sæk {sack['lot_number']} → {product['name']}")
        log_movement(db, "RISTNING", "product", product["id"], bags, "poser",
                     f"Ristning fra {sack['lot_number']}")

    return jsonify(
        roast=get_or_404("roast", cur.lastrowid),
        sack=query_one(SACK_SQL + " WHERE s.id = ?", (ROAST_KG, sack["id"])),
        product=get_or_404("product", product["id"]),
        suggested_bags=suggested_bags(product["bag_size_g"]),
    ), 201


@app.delete("/api/roasts/<int:roast_id>")
def undo_roast(roast_id):
    """Fortryd ristning – kun hvis poserne ikke allerede er solgt."""
    roast = get_or_404("roast", roast_id, "Ristning")
    product = get_or_404("product", roast["product_id"])
    if product["stock_bags"] < roast["bags_produced"]:
        raise ApiError("Ristningen kan ikke fortrydes, fordi poserne allerede er solgt.")
    sack = get_or_404("sack", roast["sack_id"])
    remaining = sack["remaining_kg"] + roast["kg_used"]
    with transaction() as db:
        db.execute("UPDATE sack SET remaining_kg = ?, status = ? WHERE id = ?",
                   (remaining, sack_status(remaining), sack["id"]))
        db.execute("UPDATE product SET stock_bags = stock_bags - ? WHERE id = ?",
                   (roast["bags_produced"], product["id"]))
        db.execute("DELETE FROM roast WHERE id = ?", (roast_id,))
        log_movement(db, "KORREKTION", "sack", sack["id"], roast["kg_used"], "kg", f"Ristning {roast_id} fortrudt")
        log_movement(db, "KORREKTION", "product", product["id"], -roast["bags_produced"], "poser",
                     f"Ristning {roast_id} fortrudt")
    return "", 204


@app.post("/api/sales")
def register_sale():
    """Registrér salg af poser."""
    data = json_body()
    require(data, "product_id", "bags")
    product = get_or_404("product", data["product_id"], "Vare")
    bags = int(data["bags"])
    if bags <= 0:
        raise ApiError("Antal poser skal være større end 0.")
    if bags > product["stock_bags"]:
        raise ApiError(f"Der er kun {product['stock_bags']} poser {product['name']} på lager.")
    channel = data.get("channel", "BUTIK")
    with transaction() as db:
        db.execute("UPDATE product SET stock_bags = stock_bags - ? WHERE id = ?", (bags, product["id"]))
        cur = db.execute("INSERT INTO sale (product_id, bags, channel, sold_at) VALUES (?, ?, ?, ?)",
                         (product["id"], bags, channel, now()))
        log_movement(db, "SALG", "product", product["id"], -bags, "poser", f"Salg via {channel}")
    return jsonify(sale=get_or_404("sale", cur.lastrowid), product=get_or_404("product", product["id"])), 201


# ---------------------------------------------------------------- Dashboard
@app.get("/api/dashboard")
def dashboard():
    """Nøgletal, sække, varer og seneste bevægelser i ét kald."""
    sacks = query_all(SACK_SQL + " WHERE s.status != 'TOM' ORDER BY s.received_date", (ROAST_KG,))
    products = query_all("""
        SELECT p.*, g.name AS coffee_name,
               COALESCE((SELECT SUM(bags) FROM sale
                         WHERE product_id = p.id AND sold_at >= date('now', '-30 days')), 0) / 30.0
               AS sales_per_day
        FROM product p LEFT JOIN green_coffee g ON g.id = p.green_coffee_id
        ORDER BY p.name
    """)
    for p in products:
        p["sales_per_day"] = round(p["sales_per_day"], 1)
        p["coverage_days"] = round(p["stock_bags"] / p["sales_per_day"]) if p["sales_per_day"] else None
        p["status"] = "LAV" if p["stock_bags"] < p["min_bags"] else "OK"
        p["suggested_bags"] = suggested_bags(p["bag_size_g"])

    return jsonify(
        kpis={
            "sacks_in_stock": len(sacks),
            "green_kg": sum(s["remaining_kg"] for s in sacks),
            "roasts_possible": sum(s["roasts_left"] for s in sacks),
            "bags_in_stock": sum(p["stock_bags"] for p in products),
            "products_low": sum(p["status"] == "LAV" for p in products),
        },
        rules={"sack_kg": SACK_KG, "roast_kg": ROAST_KG, "shrink": SHRINK},
        sacks=sacks,
        products=products,
        movements=query_all("SELECT * FROM movement ORDER BY id DESC LIMIT 15"),
    )


if __name__ == "__main__":
    init_db()
    run(app, PORT)
