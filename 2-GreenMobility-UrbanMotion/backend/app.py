"""GreenMobility – reservation af hotspotparkering. Flask API (logiklag).

Kravgrundlag: ../Kravspecifikation.MD
Kør:  pip install -r requirements.txt  &&  python app.py  →  http://localhost:5102
"""
import os
from datetime import datetime, timedelta

from flask import jsonify, request

from core import ApiError, create_app, get_or_404, json_body, now, register_crud, require, run
from database import init_db, query_all, query_one, transaction

PORT = int(os.environ.get("PORT", 5102))
app = create_app(__name__, "GreenMobility Hotspot")

# ---------------------------------------------------------------- Forretningsregler
HOLD_MINUTES = 20   # foreløbig regel – skal vurderes gennem brugertest


def log_event(db, event, message, spot_id=None, reservation_id=None):
    db.execute("INSERT INTO event_log (occurred_at, event, spot_id, reservation_id, message) VALUES (?, ?, ?, ?, ?)",
               (now(), event, spot_id, reservation_id, message))


def expire_overdue():
    """Manglende ankomst: aktive reservationer ved/efter fristen udløber og pladsen frigives."""
    overdue = query_all("SELECT * FROM reservation WHERE status = 'AKTIV' AND arrival_deadline <= ?", (now(),))
    if not overdue:
        return
    with transaction() as db:
        for r in overdue:
            db.execute("UPDATE reservation SET status = 'UDLOEBET', closed_at = ? WHERE id = ?", (now(), r["id"]))
            db.execute("UPDATE spot SET status = 'LEDIG' WHERE id = ? AND status = 'RESERVERET'", (r["spot_id"],))
            log_event(db, "ReservationUdløbet", f"{r['reservation_no']} udløb – pladsen er frigivet",
                      r["spot_id"], r["id"])


@app.before_request
def run_expiry():
    if request.path.startswith("/api"):
        expire_overdue()


RESERVATION_SQL = """
    SELECT r.*, c.name AS customer_name, s.label AS spot_label, s.status AS spot_status,
           h.id AS hotspot_id, h.name AS hotspot_name, h.address AS hotspot_address
    FROM reservation r
    JOIN customer c ON c.id = r.customer_id
    JOIN spot s ON s.id = r.spot_id
    JOIN hotspot h ON h.id = s.hotspot_id
"""


def get_reservation(reservation_id):
    r = query_one(RESERVATION_SQL + " WHERE r.id = ?", (reservation_id,))
    if r is None:
        raise ApiError(f"Reservation {reservation_id} findes ikke", 404)
    return r


def require_active(r, action):
    if r["status"] != "AKTIV":
        status = {"UDLOEBET": "udløbet", "ANNULLERET": "annulleret", "BENYTTET": "allerede benyttet"}[r["status"]]
        raise ApiError(f"Reservation {r['reservation_no']} er {status} og kan ikke {action}.")


# ---------------------------------------------------------------- CRUD
register_crud(app, "customers", "customer", fields=["name", "email", "car_plate"], required=["name", "email"])
register_crud(app, "hotspots", "hotspot", fields=["name", "address", "area"], required=["name", "address"])
def validate_spot(data, existing):
    """Administratoren må kun spærre/åbne pladser. Reservation og ankomst styres af reglerne ovenfor."""
    if existing and data["status"] != existing["status"]:
        if existing["status"] in ("RESERVERET", "OPTAGET") or data["status"] not in ("LEDIG", "SPAERRET"):
            raise ApiError("Kun ledige pladser kan spærres, og kun spærrede pladser kan åbnes igen.")


register_crud(app, "spots", "spot", fields=["hotspot_id", "label", "status"], required=["hotspot_id", "label"],
              update_fields=["label", "status"], order_by="hotspot_id, label", validate=validate_spot)
register_crud(app, "events", "event_log", fields=["event"], read_only=True, order_by="id DESC")


# ---------------------------------------------------------------- Hotspots
@app.get("/api/hotspots/overview")
def hotspot_overview():
    """Hotspots med antal ledige, reserverede, optagede og spærrede pladser."""
    return jsonify(query_all("""
        SELECT h.*,
               COUNT(s.id) AS total,
               SUM(s.status = 'LEDIG') AS free,
               SUM(s.status = 'RESERVERET') AS reserved,
               SUM(s.status = 'OPTAGET') AS occupied,
               SUM(s.status = 'SPAERRET') AS blocked
        FROM hotspot h LEFT JOIN spot s ON s.hotspot_id = h.id
        GROUP BY h.id ORDER BY h.name
    """))


# ---------------------------------------------------------------- Reservationer (kunde)
@app.get("/api/reservations")
def list_reservations():
    """Reservationer – filtrér på kunde med ?customer_id=1"""
    customer_id = request.args.get("customer_id")
    if customer_id:
        return jsonify(query_all(RESERVATION_SQL + " WHERE r.customer_id = ? ORDER BY r.id DESC", (customer_id,)))
    return jsonify(query_all(RESERVATION_SQL + " ORDER BY r.id DESC"))


@app.get("/api/reservations/<int:reservation_id>")
def show_reservation(reservation_id):
    """Én reservation med hotspot og plads."""
    return jsonify(get_reservation(reservation_id))


@app.post("/api/reservations")
def create_reservation():
    """Reservér en ledig plads ved et hotspot i 20 minutter."""
    data = json_body()
    require(data, "customer_id", "hotspot_id")
    customer = get_or_404("customer", data["customer_id"], "Kunde")
    hotspot = get_or_404("hotspot", data["hotspot_id"], "Hotspot")

    active = query_one("SELECT reservation_no FROM reservation WHERE customer_id = ? AND status = 'AKTIV'",
                       (customer["id"],))
    if active:
        raise ApiError(f"Du har allerede en aktiv reservation ({active['reservation_no']}). "
                       "Se eller annullér den, før du reserverer igen.", 409)

    spot = query_one("SELECT * FROM spot WHERE hotspot_id = ? AND status = 'LEDIG' ORDER BY label LIMIT 1",
                     (hotspot["id"],))
    if spot is None:
        raise ApiError(f"Der er ingen ledige pladser ved {hotspot['name']}. Vælg et andet hotspot.", 409)

    created = datetime.now().replace(microsecond=0)
    deadline = created + timedelta(minutes=HOLD_MINUTES)
    with transaction() as db:
        next_no = db.execute("SELECT COALESCE(MAX(id), 0) + 1001 FROM reservation").fetchone()[0]
        cur = db.execute(
            "INSERT INTO reservation (reservation_no, customer_id, spot_id, created_at, arrival_deadline)"
            " VALUES (?, ?, ?, ?, ?)",
            (f"R-{next_no}", customer["id"], spot["id"], str(created), str(deadline)))
        db.execute("UPDATE spot SET status = 'RESERVERET' WHERE id = ?", (spot["id"],))
        log_event(db, "ReservationOprettet", f"R-{next_no}: {customer['name']} har reserveret {spot['label']}",
                  spot["id"], cur.lastrowid)
    return jsonify(get_reservation(cur.lastrowid)), 201


@app.post("/api/reservations/<int:reservation_id>/cancel")
def cancel_reservation(reservation_id):
    """Annullér en aktiv reservation og frigiv pladsen."""
    r = get_reservation(reservation_id)
    require_active(r, "annulleres")
    with transaction() as db:
        db.execute("UPDATE reservation SET status = 'ANNULLERET', closed_at = ? WHERE id = ?", (now(), r["id"]))
        db.execute("UPDATE spot SET status = 'LEDIG' WHERE id = ?", (r["spot_id"],))
        log_event(db, "ReservationAnnulleret", f"{r['reservation_no']} annulleret – pladsen er frigivet",
                  r["spot_id"], r["id"])
    return jsonify(get_reservation(reservation_id))


@app.post("/api/reservations/<int:reservation_id>/arrive")
def register_arrival(reservation_id):
    """Registrér ankomst: reservationen benyttes, og pladsen bliver optaget."""
    r = get_reservation(reservation_id)
    require_active(r, "benyttes")
    with transaction() as db:
        db.execute("UPDATE reservation SET status = 'BENYTTET', arrived_at = ?, closed_at = ? WHERE id = ?",
                   (now(), now(), r["id"]))
        db.execute("UPDATE spot SET status = 'OPTAGET' WHERE id = ?", (r["spot_id"],))
        log_event(db, "AnkomstRegistreret", f"{r['reservation_no']}: bilen er parkeret på {r['spot_label']}",
                  r["spot_id"], r["id"])
    return jsonify(get_reservation(reservation_id))


# ---------------------------------------------------------------- Administrator
@app.post("/api/admin/spots/<int:spot_id>/depart")
def simulate_departure(spot_id):
    """En bil kører fra pladsen – først nu bliver pladsen ledig igen."""
    spot = get_or_404("spot", spot_id, "Plads")
    if spot["status"] != "OPTAGET":
        raise ApiError(f"Plads {spot['label']} er ikke optaget.")
    with transaction() as db:
        db.execute("UPDATE spot SET status = 'LEDIG' WHERE id = ?", (spot_id,))
        log_event(db, "AfgangRegistreret", f"Bil kørt fra {spot['label']}", spot_id)
    return jsonify(get_or_404("spot", spot_id))


@app.post("/api/admin/spots/<int:spot_id>/occupy")
def simulate_arrival_without_reservation(spot_id):
    """Simulér at en bil uden reservation parkerer."""
    spot = get_or_404("spot", spot_id, "Plads")
    if spot["status"] != "LEDIG":
        raise ApiError(f"Plads {spot['label']} er ikke ledig.")
    with transaction() as db:
        db.execute("UPDATE spot SET status = 'OPTAGET' WHERE id = ?", (spot_id,))
        log_event(db, "BilParkeret", f"Bil uden reservation parkeret på {spot['label']}", spot_id)
    return jsonify(get_or_404("spot", spot_id))


@app.post("/api/admin/reservations/<int:reservation_id>/expire")
def simulate_deadline_passed(reservation_id):
    """Simulerer at ankomstfristen er overskredet (i stedet for at vente 20 minutter)."""
    r = get_reservation(reservation_id)
    require_active(r, "udløbe")
    with transaction() as db:
        db.execute("UPDATE reservation SET arrival_deadline = ? WHERE id = ?", (now(), reservation_id))
    expire_overdue()
    return jsonify(get_reservation(reservation_id))


@app.get("/api/admin/spots")
def admin_spots():
    """Alle pladser med status og eventuel aktiv reservation."""
    return jsonify(query_all("""
        SELECT s.*, h.name AS hotspot_name,
               (SELECT reservation_no FROM reservation WHERE spot_id = s.id AND status = 'AKTIV') AS active_reservation
        FROM spot s JOIN hotspot h ON h.id = s.hotspot_id
        ORDER BY h.name, s.label
    """))


if __name__ == "__main__":
    init_db()
    run(app, PORT)
