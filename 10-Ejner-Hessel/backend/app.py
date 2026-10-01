"""Min Hessel – kundeportal for Ejner Hessel. Flask API (logiklag).

Kravgrundlag: ../kravspecifikation.md og ændringerne i ../kravspecifikation-2.md (version 2)
Kør:  pip install -r requirements.txt  &&  python app.py  →  http://localhost:5110

Kravspecifikationen nævner React og Node/Express. For at alle prototyper på holdet har samme
struktur, er denne prototype lavet med Flask og HTML/CSS/JavaScript – men samme tre-lags
arkitektur, SQLite, HTTP og JSON.
"""
import html
import os
from datetime import date
from urllib.parse import quote

from flask import Response, jsonify, request

from core import ApiError, create_app, get_or_404, json_body, register_crud, require, run
from database import init_db, query_all, query_one, transaction

PORT = int(os.environ.get("PORT", 5110))
app = create_app(__name__, "Min Hessel")

# ---------------------------------------------------------------- Forretningsregler
SLOTS = ["07:30", "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "12:00", "12:30", "13:00",
         "13:30", "14:00", "14:30", "15:00"]
REPAIR_STEPS = ["MODTAGET", "DIAGNOSE", "VENTER_PÅ_DELE", "I_GANG", "KLAR_TIL_AFHENTNING", "AFHENTET"]
REPAIR_TEXT = {"MODTAGET": "Bilen er modtaget", "DIAGNOSE": "Fejlfinding i gang", "VENTER_PÅ_DELE": "Venter på reservedele",
               "I_GANG": "Reparation i gang", "KLAR_TIL_AFHENTNING": "Klar til afhentning", "AFHENTET": "Afhentet"}

# Forbrug og klima: enhed, pris pr. enhed og CO₂ pr. enhed (antagelser – kan justeres her)
FUEL = {
    "Benzin": {"unit": "liter", "price": 13.5, "co2_kg": 2.37},
    "Mild hybrid": {"unit": "liter", "price": 13.5, "co2_kg": 2.37},
    "Hybrid": {"unit": "liter", "price": 13.5, "co2_kg": 2.37},
    "Plug-in hybrid": {"unit": "liter", "price": 13.5, "co2_kg": 2.37},
    "Diesel": {"unit": "liter", "price": 12.5, "co2_kg": 2.64},
    "El": {"unit": "kWh", "price": 2.5, "co2_kg": 0.10},      # dansk elmix ca. 100 g CO₂/kWh
}


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
              fields=["customer_id", "brand", "model", "registration", "vin", "year", "fuel", "gearbox", "body_type", "color",
                      "image_url", "mileage_km", "ownership", "next_service_date", "next_inspection_date", "warranty_until",
                      "battery_kwh", "range_km", "leasing_company", "leasing_end", "leasing_km_per_year", "leasing_monthly"],
              required=["customer_id", "brand", "model", "registration", "fuel"])
register_crud(app, "service-history", "service_history",
              fields=["car_id", "date", "type", "workshop_id", "mileage_km", "price", "description"],
              required=["car_id", "date", "type"], order_by="date DESC")
register_crud(app, "bookings", "booking",
              fields=["car_id", "workshop_id", "date", "time", "service_type", "notes", "status"],
              update_fields=["workshop_id", "date", "time", "service_type", "notes", "status"],
              required=["car_id", "workshop_id", "date", "time", "service_type"],
              order_by="date, time", validate=validate_booking)
register_crud(app, "repairs", "repair",
              fields=["car_id", "workshop_id", "description", "status", "estimated_ready", "message"],
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
    car["service_due_soon"] = due_within(car["next_service_date"], 30)
    car["inspection_due_soon"] = due_within(car["next_inspection_date"], 60)
    car["warranty_active"] = bool(car["warranty_until"]) and date.fromisoformat(car["warranty_until"]) >= date.today()
    car["leasing_months_left"] = None
    if car["leasing_end"]:
        end = date.fromisoformat(car["leasing_end"])
        car["leasing_months_left"] = max(0, (end.year - date.today().year) * 12 + end.month - date.today().month)
    return car


def due_within(value, days):
    return bool(value) and (date.fromisoformat(value) - date.today()).days <= days


@app.get("/api/customers/<int:customer_id>/overview")
def customer_overview(customer_id):
    """Kundens biler med næste booking og reparationsstatus, bookinger, dokumenter og notifikationer."""
    customer = get_or_404("customer", customer_id, "Kunde")
    cars = [enrich_car(c) for c in query_all("SELECT * FROM car WHERE customer_id = ? ORDER BY brand", (customer_id,))]
    documents = query_all("SELECT * FROM document WHERE customer_id = ? ORDER BY date DESC", (customer_id,))
    bookings = query_all("""SELECT b.*, c.brand, c.model, c.registration, w.name AS workshop_name
                            FROM booking b JOIN car c ON c.id = b.car_id JOIN workshop w ON w.id = b.workshop_id
                            WHERE c.customer_id = ? ORDER BY b.date DESC, b.time""", (customer_id,))
    def dk(value):
        return date.fromisoformat(value).strftime("%d.%m.%Y")

    return jsonify(customer=customer, cars=cars, bookings=bookings, documents=documents,
                   notifications=[f"{c['brand']} {c['model']}: service inden {dk(c['next_service_date'])}"
                                  for c in cars if c["service_due_soon"] and not c["next_booking"]]
                   + [f"{c['brand']} {c['model']}: syn senest {dk(c['next_inspection_date'])}"
                      for c in cars if c["inspection_due_soon"]]
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


# ---------------------------------------------------------------- Reparationsstatus (kundefane)
@app.get("/api/customers/<int:customer_id>/repairs")
def customer_repairs(customer_id):
    """Kundens reparationer med status, forventet færdigtidspunkt og alle beskeder fra værkstedet samlet."""
    get_or_404("customer", customer_id, "Kunde")
    repairs = query_all("""SELECT r.*, c.brand, c.model, c.registration, c.body_type, c.color, c.image_url,
                                  w.name AS workshop_name, w.address AS workshop_address
                           FROM repair r JOIN car c ON c.id = r.car_id LEFT JOIN workshop w ON w.id = r.workshop_id
                           WHERE c.customer_id = ? ORDER BY r.status = 'AFHENTET', r.updated_at DESC""", (customer_id,))
    for r in repairs:
        r["step"] = REPAIR_STEPS.index(r["status"]) + 1
        r["steps"] = len(REPAIR_STEPS) - 1
        r["status_text"] = REPAIR_TEXT[r["status"]]
        r["updates"] = query_all("SELECT * FROM repair_update WHERE repair_id = ? ORDER BY created_at DESC, id DESC", (r["id"],))
    return jsonify(repairs)


# ---------------------------------------------------------------- Dokumenter: åbn og download
@app.get("/api/documents/<int:document_id>/file")
def document_file(document_id):
    """Dokumentet som en printvenlig side. ?download=1 gemmer filen i stedet for at åbne den."""
    doc = get_or_404("document", document_id, "Dokument")
    customer = get_or_404("customer", doc["customer_id"])
    car = query_one("SELECT * FROM car WHERE id = ?", (doc["car_id"],)) if doc["car_id"] else None
    e = html.escape
    body = f"""<!DOCTYPE html><html lang="da"><head><meta charset="utf-8"><title>{e(doc['title'])}</title>
<style>body{{font-family:system-ui,sans-serif;max-width:720px;margin:40px auto;padding:0 16px;color:#1d2320}}
h1{{color:#003b5c}}dt{{color:#64706a}}dd{{margin:0 0 10px}}.logo{{font-weight:800;letter-spacing:.12em;color:#003b5c}}</style></head>
<body><div class="logo">EJNER HESSEL</div><h1>{e(doc['title'])}</h1><dl>
<dt>Kategori</dt><dd>{e(doc['category'])}</dd>
<dt>Dato</dt><dd>{date.fromisoformat(doc['date']).strftime('%d.%m.%Y')}</dd>
<dt>Kunde</dt><dd>{e(customer['name'])}, {e(customer['address'] or '')}</dd>
<dt>Bil</dt><dd>{e(f"{car['brand']} {car['model']} ({car['registration']})") if car else 'Gælder alle biler'}</dd>
<dt>Beskrivelse</dt><dd>{e(doc['description'] or '–')}</dd></dl>
<p><small>Prototype – dokumentet er genereret ud fra testdata.</small></p></body></html>"""
    filename = f"{doc['title']}.html".replace(" ", "_").replace("/", "-")
    disposition = "attachment" if request.args.get("download") == "1" else "inline"
    return Response(body, mimetype="text/html", headers={
        "Content-Disposition": f"{disposition}; filename*=UTF-8''{quote(filename)}"})


# ---------------------------------------------------------------- Forbrug og klima
def consumption_data(car):
    fuel = FUEL[car["fuel"]]
    logs = query_all("SELECT * FROM consumption_log WHERE car_id = ? ORDER BY month", (car["id"],))
    for log in logs:
        log["per_100"] = round(log["amount"] / log["km"] * 100, 1)
        log["cost"] = round(log["amount"] * fuel["price"])
        log["co2_kg"] = round(log["amount"] * fuel["co2_kg"], 1)
    recent = logs[-3:]
    km_recent = sum(l["km"] for l in recent)
    current = round(sum(l["amount"] for l in recent) / km_recent * 100, 1) if km_recent else None
    yearly_km = round(sum(l["km"] for l in logs) / len(logs) * 12) if logs else 0
    goal = query_one("SELECT * FROM consumption_goal WHERE car_id = ?", (car["id"],))
    savings = None
    if goal and current:
        units = max(0.0, (current - goal["target_per_100"]) / 100 * yearly_km)
        savings = {"target_per_100": goal["target_per_100"], "units_per_year": round(units),
                   "kr_per_year": round(units * fuel["price"]), "co2_kg_per_year": round(units * fuel["co2_kg"]),
                   "reached": current <= goal["target_per_100"]}
    return {"car": {k: car[k] for k in ("id", "brand", "model", "registration", "fuel")},
            "unit": fuel["unit"], "unit_per_100": f"{fuel['unit']}/100 km", "price_per_unit": fuel["price"],
            "co2_kg_per_unit": fuel["co2_kg"], "logs": logs, "current_per_100": current, "yearly_km": yearly_km,
            "yearly_cost": round(current / 100 * yearly_km * fuel["price"]) if current else None,
            "yearly_co2_kg": round(current / 100 * yearly_km * fuel["co2_kg"]) if current else None,
            "goal": goal, "savings": savings,
            "tips": ["Hold dæktrykket korrekt – det kan spare op til 3 %",
                     "Kør roligt og hold en jævn fart – undgå hårde accelerationer",
                     "Fjern tagboks og unødig vægt",
                     "Forvarm elbilen, mens den lader" if car["fuel"] in ("El", "Plug-in hybrid") else "Sluk motoren ved holdt over et minut"]}


@app.get("/api/cars/<int:car_id>/consumption")
def consumption(car_id):
    """Bilens forbrug pr. måned, nuværende forbrug pr. 100 km, mål og beregnet besparelse i kroner og CO₂."""
    return jsonify(consumption_data(get_or_404("car", car_id, "Bil")))


@app.post("/api/cars/<int:car_id>/consumption")
def add_consumption(car_id):
    """Registrér en måneds kørsel og forbrug (opdaterer måneden, hvis den findes)."""
    car = get_or_404("car", car_id, "Bil")
    data = json_body()
    require(data, "month", "km", "amount")
    if int(data["km"]) <= 0 or float(data["amount"]) <= 0:
        raise ApiError("Kilometer og forbrug skal være større end 0")
    with transaction() as db:
        db.execute("""INSERT INTO consumption_log (car_id, month, km, amount) VALUES (?, ?, ?, ?)
                      ON CONFLICT (car_id, month) DO UPDATE SET km = excluded.km, amount = excluded.amount""",
                   (car_id, data["month"][:7], int(data["km"]), float(data["amount"])))
    return jsonify(consumption_data(car)), 201


@app.put("/api/cars/<int:car_id>/goal")
def set_goal(car_id):
    """Sæt et mål for forbruget pr. 100 km. Svaret viser besparelsen i kroner og CO₂ pr. år."""
    car = get_or_404("car", car_id, "Bil")
    data = json_body()
    require(data, "target_per_100")
    if float(data["target_per_100"]) <= 0:
        raise ApiError("Målet skal være større end 0")
    with transaction() as db:
        db.execute("""INSERT INTO consumption_goal (car_id, target_per_100) VALUES (?, ?)
                      ON CONFLICT (car_id) DO UPDATE SET target_per_100 = excluded.target_per_100,
                                                         created_at = datetime('now', 'localtime')""",
                   (car_id, float(data["target_per_100"])))
    return jsonify(consumption_data(car))


if __name__ == "__main__":
    init_db()
    run(app, PORT)
