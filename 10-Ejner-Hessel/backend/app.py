"""Min Hessel – kundeportal for Ejner Hessel. Flask API (logiklag).

Kravgrundlag: ../kravspecifikation.md
Kør:  pip install -r requirements.txt  &&  python app.py  →  http://localhost:5110

Kravspecifikationen nævner React og Node/Express. For at alle prototyper på holdet har samme
struktur, er denne prototype lavet med Flask og HTML/CSS/JavaScript – men samme tre-lags
arkitektur, SQLite, HTTP og JSON.
"""
import os
from datetime import date

from flask import jsonify, request

from core import ApiError, create_app, get_or_404, register_crud, require, run
from database import init_db, query_all, query_one

PORT = int(os.environ.get("PORT", 5110))
app = create_app(__name__, "Min Hessel")

# ---------------------------------------------------------------- Forretningsregler
SLOTS = ["07:30", "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "12:00", "12:30", "13:00",
         "13:30", "14:00", "14:30", "15:00"]
REPAIR_STEPS = ["MODTAGET", "DIAGNOSE", "VENTER_PÅ_DELE", "I_GANG", "KLAR_TIL_AFHENTNING", "AFHENTET"]


def validate_booking(data, existing):
    """Booking: dato i fremtiden, gyldigt tidspunkt, værkstedet servicerer mærket og tiden er ledig."""
    if data.get("status", "BEKRÆFTET") != "BEKRÆFTET":
        return
    try:
        booking_date = date.fromisoformat(data["date"])
    except ValueError:
        raise ApiError("Datoen skal have formatet ÅÅÅÅ-MM-DD")
    if booking_date <= date.today():
        raise ApiError("Vælg en dato fra i morgen og frem.")
    if booking_date.weekday() >= 5:
        raise ApiError("Værkstederne har lukket i weekenden – vælg en hverdag.")
    if data["time"] not in SLOTS:
        raise ApiError(f"Vælg et af værkstedets tidspunkter: {', '.join(SLOTS)}")
    car = get_or_404("car", data["car_id"], "Bil")
    workshop = get_or_404("workshop", data["workshop_id"], "Værksted")
    if car["brand"] not in workshop["brands"].split(","):
        raise ApiError(f"{workshop['name']} servicerer ikke {car['brand']}. Vælg et andet værksted.")
    clash = query_one("""SELECT id FROM booking WHERE workshop_id = ? AND date = ? AND time = ?
                         AND status = 'BEKRÆFTET' AND id != ?""",
                      (data["workshop_id"], data["date"], data["time"], existing["id"] if existing else 0))
    if clash:
        raise ApiError(f"Tiden {data['date']} kl. {data['time']} er optaget. Vælg en anden tid.", 409)


def validate_repair(data, existing):
    if data.get("status", "MODTAGET") not in REPAIR_STEPS:
        raise ApiError("Ukendt reparationsstatus")


# ---------------------------------------------------------------- CRUD
register_crud(app, "customers", "customer", fields=["name", "email", "phone", "address"], required=["name", "email"])
register_crud(app, "workshops", "workshop", fields=["name", "address", "brands"], required=["name", "address", "brands"])
register_crud(app, "cars", "car",
              fields=["customer_id", "brand", "model", "registration", "vin", "year", "fuel", "mileage_km",
                      "ownership", "next_service_date"],
              required=["customer_id", "brand", "model", "registration"])
register_crud(app, "service-history", "service_history",
              fields=["car_id", "date", "type", "workshop_id", "mileage_km", "price", "description"],
              required=["car_id", "date", "type"], order_by="date DESC")
register_crud(app, "bookings", "booking",
              fields=["car_id", "workshop_id", "date", "time", "service_type", "notes", "status"],
              update_fields=["workshop_id", "date", "time", "service_type", "notes", "status"],
              required=["car_id", "workshop_id", "date", "time", "service_type"],
              order_by="date, time", validate=validate_booking)
register_crud(app, "repairs", "repair",
              fields=["car_id", "description", "status", "estimated_ready", "message"],
              required=["car_id", "description"], validate=validate_repair)
register_crud(app, "documents", "document",
              fields=["customer_id", "car_id", "title", "category", "date", "description"],
              required=["customer_id", "title", "category", "date"], order_by="date DESC")


# ---------------------------------------------------------------- Kundens overblik
def enrich_car(car):
    car["next_booking"] = query_one("""SELECT b.*, w.name AS workshop_name FROM booking b
                                       JOIN workshop w ON w.id = b.workshop_id
                                       WHERE b.car_id = ? AND b.status = 'BEKRÆFTET' AND b.date >= date('now')
                                       ORDER BY b.date, b.time LIMIT 1""", (car["id"],))
    car["active_repair"] = query_one("""SELECT * FROM repair WHERE car_id = ? AND status != 'AFHENTET'
                                        ORDER BY id DESC LIMIT 1""", (car["id"],))
    if car["active_repair"]:
        car["active_repair"]["step"] = REPAIR_STEPS.index(car["active_repair"]["status"]) + 1
        car["active_repair"]["steps"] = len(REPAIR_STEPS) - 1
    car["service_due_soon"] = bool(car["next_service_date"]) and \
        (date.fromisoformat(car["next_service_date"]) - date.today()).days <= 30
    return car


@app.get("/api/customers/<int:customer_id>/overview")
def customer_overview(customer_id):
    """Kundens biler med næste booking og reparationsstatus, bookinger, dokumenter og notifikationer."""
    customer = get_or_404("customer", customer_id, "Kunde")
    cars = [enrich_car(c) for c in query_all("SELECT * FROM car WHERE customer_id = ? ORDER BY brand", (customer_id,))]
    documents = query_all("SELECT * FROM document WHERE customer_id = ? ORDER BY date DESC", (customer_id,))
    bookings = query_all("""SELECT b.*, c.brand, c.model, c.registration, w.name AS workshop_name
                            FROM booking b JOIN car c ON c.id = b.car_id JOIN workshop w ON w.id = b.workshop_id
                            WHERE c.customer_id = ? ORDER BY b.date DESC, b.time""", (customer_id,))
    return jsonify(customer=customer, cars=cars, bookings=bookings, documents=documents,
                   notifications=[f"{c['brand']} {c['model']}: service inden {c['next_service_date']}"
                                  for c in cars if c["service_due_soon"] and not c["next_booking"]]
                   + [f"{c['brand']} {c['model']}: {c['active_repair']['message']}"
                      for c in cars if c["active_repair"] and c["active_repair"]["message"]])


@app.get("/api/cars/<int:car_id>/details")
def car_details(car_id):
    """Biloplysninger, servicehistorik, reparationer og dokumenter for én bil."""
    car = enrich_car(get_or_404("car", car_id, "Bil"))
    return jsonify(
        car=car,
        service_history=query_all("""SELECT s.*, w.name AS workshop_name FROM service_history s
                                     LEFT JOIN workshop w ON w.id = s.workshop_id
                                     WHERE s.car_id = ? ORDER BY s.date DESC""", (car_id,)),
        repairs=query_all("SELECT * FROM repair WHERE car_id = ? ORDER BY id DESC", (car_id,)),
        documents=query_all("SELECT * FROM document WHERE car_id = ? ORDER BY date DESC", (car_id,)),
    )


@app.get("/api/available-times")
def available_times():
    """Ledige tider på et værksted en given dato: ?workshop_id=1&date=2026-10-12"""
    require(request.args, "workshop_id", "date")
    taken = {r["time"] for r in query_all(
        "SELECT time FROM booking WHERE workshop_id = ? AND date = ? AND status = 'BEKRÆFTET'",
        (request.args["workshop_id"], request.args["date"]))}
    return jsonify([{"time": t, "available": t not in taken} for t in SLOTS])


@app.get("/api/repair-steps")
def repair_steps():
    """Trinene i en reparation, i rækkefølge."""
    return jsonify(REPAIR_STEPS)


if __name__ == "__main__":
    init_db()
    run(app, PORT)
