"""GreenMobility – reservation af hotspotparkering. Flask API (logiklag).

Kravgrundlag: ../Kravspecifikation.MD
Kør:  pip install -r requirements.txt  &&  python app.py  →  http://localhost:5102
      Kundeside: /            Administrator: /admin.html
"""
import math
import os
import re
from datetime import datetime, timedelta

from flask import jsonify, request

from core import ApiError, create_app, get_or_404, json_body, now, register_crud, require, run
from database import get_db, init_db, query_all, query_one, transaction

PORT = int(os.environ.get("PORT", 5102))
app = create_app(__name__, "GreenMobility Hotspot")

# ---------------------------------------------------------------- Forretningsregler
HOLD_MINUTES = 20        # foreløbig regel – skal vurderes gennem brugertest
RESERVATION_FEE_KR = 0   # pris for at reservere
CANCEL_FEE_KR = 0        # pris for at annullere
NO_SHOW_FEE_KR = 0       # pris hvis reservationen udløber uden ankomst

SUPPORT_PHONE = "+45 12 34 56 78"   # fiktivt nummer
SUPPORT_HOURS = {                    # ugedag (0 = mandag) → (åbner, lukker)
    0: (8, 20), 1: (8, 20), 2: (8, 20), 3: (8, 20), 4: (8, 20), 5: (10, 18), 6: (10, 18),
}
SUPPORT_HOURS_TEXT = "Man–fre kl. 8–20 · Lør–søn kl. 10–18"


def kr(amount):
    return "Gratis" if amount == 0 else f"{amount} kr."


def support_open(at=None):
    at = at or datetime.now()
    opens, closes = SUPPORT_HOURS[at.weekday()]
    return opens <= at.hour < closes


def log_event(db, event, message, spot_id=None, reservation_id=None):
    db.execute("INSERT INTO event_log (occurred_at, event, spot_id, reservation_id, message) VALUES (?, ?, ?, ?, ?)",
               (now(), event, spot_id, reservation_id, message))


def begin_write(db):
    """Tager skrivelåsen på databasen med det samme (BEGIN IMMEDIATE).

    Så kan to samtidige requests – også fra forskellige gunicorn-processer – ikke begge
    læse den samme plads som ledig, før en af dem har nået at reservere den."""
    if db.in_transaction:
        db.commit()
    db.execute("BEGIN IMMEDIATE")


def expire_overdue():
    """Manglende ankomst: aktive reservationer ved/efter fristen udløber og pladsen frigives."""
    overdue = query_all("SELECT * FROM reservation WHERE status = 'AKTIV' AND arrival_deadline <= ?", (now(),))
    if not overdue:
        return
    with transaction() as db:
        for r in overdue:
            changed = db.execute("UPDATE reservation SET status = 'UDLOEBET', closed_at = ? WHERE id = ? AND status = 'AKTIV'",
                                 (now(), r["id"])).rowcount
            if not changed:   # en anden request nåede det først
                continue
            db.execute("UPDATE spot SET status = 'LEDIG' WHERE id = ? AND status = 'RESERVERET'", (r["spot_id"],))
            log_event(db, "ReservationUdløbet", f"{r['reservation_no']} udløb – pladsen er frigivet",
                      r["spot_id"], r["id"])


@app.before_request
def run_expiry():
    if request.path.startswith("/api"):
        expire_overdue()


RESERVATION_SQL = """
    SELECT r.*, c.name AS customer_name, s.label AS spot_label, s.status AS spot_status,
           h.id AS hotspot_id, h.name AS hotspot_name, h.address AS hotspot_address,
           h.directions AS hotspot_directions
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


def active_reservation_for(customer_id):
    return query_one(RESERVATION_SQL + " WHERE r.customer_id = ? AND r.status = 'AKTIV'", (customer_id,))


def require_active(r, action):
    if r["status"] != "AKTIV":
        status = {"UDLOEBET": "udløbet", "ANNULLERET": "annulleret", "BENYTTET": "allerede benyttet"}[r["status"]]
        raise ApiError(f"Reservation {r['reservation_no']} er {status} og kan ikke {action}.")


# ---------------------------------------------------------------- CRUD
register_crud(app, "customers", "customer", fields=["name", "email", "car_plate"], required=["name", "email"])
register_crud(app, "hotspots", "hotspot", fields=["name", "address", "area", "lat", "lng", "directions"],
              required=["name", "address"], order_by="name")
register_crud(app, "staff", "staff", fields=["name", "role", "online"], required=["name", "role"], order_by="name")


def validate_spot(data, existing):
    """Administratoren må kun spærre/åbne pladser. Reservation og ankomst styres af reglerne ovenfor."""
    if existing and data["status"] != existing["status"]:
        if existing["status"] in ("RESERVERET", "OPTAGET") or data["status"] not in ("LEDIG", "SPAERRET"):
            raise ApiError("Kun ledige pladser kan spærres, og kun spærrede pladser kan åbnes igen.")


register_crud(app, "spots", "spot", fields=["hotspot_id", "label", "status"], required=["hotspot_id", "label"],
              update_fields=["label", "status"], order_by="hotspot_id, label", validate=validate_spot)
register_crud(app, "events", "event_log", fields=["event"], read_only=True, order_by="id DESC")


# ---------------------------------------------------------------- Info: regler, gebyrer, privatliv, kontakt
@app.get("/api/info")
def info():
    """Regler og vilkår, gebyrer, privatlivspolitik og kontaktoplysninger – ét sted, så teksterne altid passer med reglerne."""
    return jsonify(
        hold_minutes=HOLD_MINUTES,
        fees={"reservation": kr(RESERVATION_FEE_KR), "cancel": kr(CANCEL_FEE_KR), "no_show": kr(NO_SHOW_FEE_KR)},
        rules=[
            {"title": "Hvor længe gælder en reservation?",
             "text": f"Pladsen holdes til dig i {HOLD_MINUTES} minutter fra du reserverer. Du kan have én aktiv reservation ad gangen."},
            {"title": "Sådan annullerer du",
             "text": f"Tryk »Annullér« på din reservation. Pladsen bliver straks ledig for andre. Pris: {kr(CANCEL_FEE_KR).lower()}."},
            {"title": "Hvis du kommer for sent",
             "text": f"Når de {HOLD_MINUTES} minutter er gået, udløber reservationen automatisk, og pladsen gives videre. "
                     f"Gebyr ved udløb: {kr(NO_SHOW_FEE_KR).lower()}. Du kan reservere igen, hvis der er ledige pladser."},
            {"title": "Når du er fremme",
             "text": "Parkér på det pladsnummer, du har fået, og tryk »Jeg er ankommet«. Så står pladsen som optaget."},
            {"title": "Gebyrer",
             "text": f"Reservation: {kr(RESERVATION_FEE_KR).lower()}. Annullering: {kr(CANCEL_FEE_KR).lower()}. "
                     f"Udløb uden ankomst: {kr(NO_SHOW_FEE_KR).lower()}. Almindelig kørselspris betales som normalt i GreenMobility-appen."},
        ],
        privacy=[
            {"title": "Det gemmer vi",
             "text": "Dit navn, din e-mail og bilens nummerplade. Dine reservationer (sted, plads og tidspunkter) "
                     "og dine henvendelser til kundeservice."},
            {"title": "Din lokation",
             "text": "Hvis du tillader det, bruges din position kun på din telefon til at sortere hotspots efter afstand. "
                     "Den sendes ikke til os og gemmes ikke."},
            {"title": "AI-chatten",
             "text": "Det, du skriver til AI-assistenten, bruges kun til at finde et svar og gemmes ikke. "
                     "Chat med en medarbejder gemmes, så vi kan hjælpe dig videre."},
            {"title": "Hvad bruges det til?",
             "text": "Til at holde pladsen til dig, vise din reservation, løse problemer med pladser og forbedre tjenesten. "
                     "Vi sælger ikke dine oplysninger."},
            {"title": "Dine rettigheder",
             "text": "Du kan altid få indsigt i, rette eller få slettet dine oplysninger ved at kontakte kundeservice."},
        ],
        support={"phone": SUPPORT_PHONE, "hours": SUPPORT_HOURS_TEXT, "open_now": support_open()},
        staff=query_all("SELECT * FROM staff ORDER BY name"),
    )


# ---------------------------------------------------------------- Hotspots
OVERVIEW_SQL = """
    SELECT h.*,
           COUNT(s.id) AS total,
           COALESCE(SUM(s.status = 'LEDIG'), 0) AS free,
           COALESCE(SUM(s.status = 'RESERVERET'), 0) AS reserved,
           COALESCE(SUM(s.status = 'OPTAGET'), 0) AS occupied,
           COALESCE(SUM(s.status = 'SPAERRET'), 0) AS blocked,
           (SELECT COUNT(*) FROM reservation r JOIN spot s2 ON s2.id = r.spot_id
             WHERE s2.hotspot_id = h.id AND r.status = 'AKTIV') AS active_reservations
    FROM hotspot h LEFT JOIN spot s ON s.hotspot_id = h.id
"""


def with_check(row):
    """Tal der stemmer: ledige + reserverede + optagede + spærrede = i alt,
    og antallet af reserverede pladser = antallet af aktive reservationer."""
    parts = row["free"] + row["reserved"] + row["occupied"] + row["blocked"]
    row["consistent"] = parts == row["total"] and row["reserved"] == row["active_reservations"]
    return row


def distance_km(a, b):
    if None in (a["lat"], a["lng"], b["lat"], b["lng"]):
        return None
    dlat, dlng = math.radians(b["lat"] - a["lat"]), math.radians(b["lng"] - a["lng"])
    x = math.sin(dlat / 2) ** 2 + math.cos(math.radians(a["lat"])) * math.cos(math.radians(b["lat"])) * math.sin(dlng / 2) ** 2
    return round(6371 * 2 * math.asin(math.sqrt(x)), 1)


@app.get("/api/hotspots/overview")
def hotspot_overview():
    """Hotspots med antal ledige, reserverede, optagede og spærrede pladser. Søg med ?q=nørreport"""
    q = request.args.get("q", "").strip()
    where = " WHERE h.name LIKE ? OR h.address LIKE ? OR h.area LIKE ?" if q else ""
    params = (f"%{q}%",) * 3 if q else ()
    return jsonify([with_check(row) for row in query_all(OVERVIEW_SQL + where + " GROUP BY h.id ORDER BY h.name", params)])


def alternatives_for(hotspot_id, limit=3):
    origin = get_or_404("hotspot", hotspot_id, "Hotspot")
    rows = query_all(OVERVIEW_SQL + " WHERE h.id != ? GROUP BY h.id HAVING free > 0", (hotspot_id,))
    for row in rows:
        row["distance_km"] = distance_km(origin, row)
    rows.sort(key=lambda row: (row["distance_km"] is None, row["distance_km"] or 0))
    return rows[:limit]


@app.get("/api/hotspots/<int:hotspot_id>/alternatives")
def hotspot_alternatives(hotspot_id):
    """De nærmeste andre hotspots med ledige pladser (bruges når et hotspot er fuldt)."""
    return jsonify(alternatives_for(hotspot_id))


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
    """Reservér en ledig plads ved et hotspot i 20 minutter. Pladsen låses atomisk, så den ikke kan dobbeltbookes."""
    data = json_body()
    require(data, "customer_id", "hotspot_id")
    customer = get_or_404("customer", data["customer_id"], "Kunde")
    hotspot = get_or_404("hotspot", data["hotspot_id"], "Hotspot")

    created = datetime.now().replace(microsecond=0)
    deadline = created + timedelta(minutes=HOLD_MINUTES)
    with transaction() as db:
        begin_write(db)
        active = db.execute("SELECT reservation_no FROM reservation WHERE customer_id = ? AND status = 'AKTIV'",
                            (customer["id"],)).fetchone()
        if active:
            raise ApiError(f"Du har allerede en aktiv reservation ({active['reservation_no']}). "
                           "Annullér den, før du reserverer igen.", 409)
        spot = db.execute("SELECT * FROM spot WHERE hotspot_id = ? AND status = 'LEDIG' ORDER BY label LIMIT 1",
                          (hotspot["id"],)).fetchone()
        if spot is None:
            raise ApiError(f"{hotspot['name']} er fuldt lige nu. Se de nærmeste alternativer.", 409)
        db.execute("UPDATE spot SET status = 'RESERVERET' WHERE id = ? AND status = 'LEDIG'", (spot["id"],))
        next_no = db.execute("SELECT COALESCE(MAX(id), 0) + 1001 FROM reservation").fetchone()[0]
        cur = db.execute(
            "INSERT INTO reservation (reservation_no, customer_id, spot_id, created_at, arrival_deadline)"
            " VALUES (?, ?, ?, ?, ?)",
            (f"R-{next_no}", customer["id"], spot["id"], str(created), str(deadline)))
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
        db.execute("UPDATE spot SET status = 'LEDIG' WHERE id = ? AND status = 'RESERVERET'", (r["spot_id"],))
        log_event(db, "ReservationAnnulleret", f"{r['reservation_no']} annulleret – pladsen er frigivet",
                  r["spot_id"], r["id"])
    return jsonify(get_reservation(reservation_id))


@app.post("/api/reservations/<int:reservation_id>/arrive")
def register_arrival(reservation_id):
    """Registrér ankomst: reservationen benyttes, og pladsen skifter fra reserveret til optaget."""
    r = get_reservation(reservation_id)
    require_active(r, "benyttes")
    with transaction() as db:
        db.execute("UPDATE reservation SET status = 'BENYTTET', arrived_at = ?, closed_at = ? WHERE id = ?",
                   (now(), now(), r["id"]))
        db.execute("UPDATE spot SET status = 'OPTAGET' WHERE id = ?", (r["spot_id"],))
        log_event(db, "AnkomstRegistreret", f"{r['reservation_no']}: bilen er parkeret på {r['spot_label']}",
                  r["spot_id"], r["id"])
    return jsonify(get_reservation(reservation_id))


# ---------------------------------------------------------------- Meld et problem
def open_case(db, customer_id, case_type, first_message, reservation_id=None, staff_id=None, sender="KUNDE"):
    created = now()
    next_no = db.execute("SELECT COALESCE(MAX(id), 0) + 501 FROM support_case").fetchone()[0]
    case_id = db.execute(
        "INSERT INTO support_case (case_no, customer_id, reservation_id, staff_id, type, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (f"H-{next_no}", customer_id, reservation_id, staff_id, case_type, created)).lastrowid
    db.execute("INSERT INTO support_message (case_id, sender, text, sent_at) VALUES (?, ?, ?, ?)",
               (case_id, sender, first_message, created))
    return case_id


@app.post("/api/reservations/<int:reservation_id>/report")
def report_problem(reservation_id):
    """Meld et problem med pladsen: {"type": "PLADS_OPTAGET" | "KAN_IKKE_FINDE"}.

    PLADS_OPTAGET:  kunden flyttes til en anden ledig plads ved samme hotspot. Er der ingen,
                    annulleres reservationen gratis, og de nærmeste alternativer vises.
    KAN_IKKE_FINDE: kunden får vejvisning, og en medarbejder får en henvendelse.
    """
    data = json_body()
    kind = data.get("type")
    if kind not in ("PLADS_OPTAGET", "KAN_IKKE_FINDE"):
        raise ApiError("type skal være PLADS_OPTAGET eller KAN_IKKE_FINDE")
    r = get_reservation(reservation_id)
    require_active(r, "bruges til at melde et problem")

    if kind == "KAN_IKKE_FINDE":
        with transaction() as db:
            case_id = open_case(db, r["customer_id"], kind,
                                f"Kan ikke finde plads {r['spot_label']} ved {r['hotspot_name']}.", r["id"])
            log_event(db, "ProblemMeldt", f"{r['reservation_no']}: kunden kan ikke finde {r['spot_label']}",
                      r["spot_id"], r["id"])
        return jsonify(outcome="HELP", case_id=case_id, reservation=get_reservation(reservation_id),
                       message=f"Plads {r['spot_label']}: {r['hotspot_directions'] or 'Kig efter de grønne GreenMobility-skilte.'} "
                               "En medarbejder har fået besked og skriver til dig i chatten.")

    with transaction() as db:
        begin_write(db)
        # En fremmed bil holder på pladsen – den markeres optaget
        db.execute("UPDATE spot SET status = 'OPTAGET' WHERE id = ?", (r["spot_id"],))
        new_spot = db.execute("SELECT * FROM spot WHERE hotspot_id = ? AND status = 'LEDIG' ORDER BY label LIMIT 1",
                              (r["hotspot_id"],)).fetchone()
        if new_spot:
            db.execute("UPDATE spot SET status = 'RESERVERET' WHERE id = ?", (new_spot["id"],))
            db.execute("UPDATE reservation SET spot_id = ? WHERE id = ?", (new_spot["id"], r["id"]))
            text = f"Plads {r['spot_label']} var optaget. Du har fået plads {new_spot['label']} i stedet."
            outcome = "MOVED"
        else:
            db.execute("UPDATE reservation SET status = 'ANNULLERET', closed_at = ? WHERE id = ?", (now(), r["id"]))
            text = (f"Plads {r['spot_label']} var optaget, og der er ingen andre ledige pladser ved {r['hotspot_name']}. "
                    "Din reservation er annulleret uden gebyr.")
            outcome = "CANCELLED"
        case_id = open_case(db, r["customer_id"], kind, f"Plads {r['spot_label']} ved {r['hotspot_name']} er optaget af en anden bil.",
                            r["id"])
        db.execute("INSERT INTO support_message (case_id, sender, text, sent_at) VALUES (?, 'SYSTEM', ?, ?)",
                   (case_id, text, now()))
        db.execute("UPDATE support_case SET status = 'LUKKET' WHERE id = ?", (case_id,))   # løst automatisk
        log_event(db, "ProblemMeldt", f"{r['reservation_no']}: {text}", r["spot_id"], r["id"])
    return jsonify(outcome=outcome, case_id=case_id, message=text, reservation=get_reservation(reservation_id),
                   alternatives=alternatives_for(r["hotspot_id"]) if outcome == "CANCELLED" else [])


# ---------------------------------------------------------------- Kontakt en medarbejder
CASE_SQL = """
    SELECT sc.*, c.name AS customer_name, st.name AS staff_name, r.reservation_no
    FROM support_case sc
    JOIN customer c ON c.id = sc.customer_id
    LEFT JOIN staff st ON st.id = sc.staff_id
    LEFT JOIN reservation r ON r.id = sc.reservation_id
"""


def get_case(case_id):
    case = query_one(CASE_SQL + " WHERE sc.id = ?", (case_id,))
    if case is None:
        raise ApiError(f"Henvendelse {case_id} findes ikke", 404)
    case["messages"] = query_all("SELECT * FROM support_message WHERE case_id = ? ORDER BY id", (case_id,))
    return case


@app.get("/api/support")
def list_cases():
    """Henvendelser – filtrér på kunde med ?customer_id=1"""
    customer_id = request.args.get("customer_id")
    where, params = (" WHERE sc.customer_id = ?", (customer_id,)) if customer_id else ("", ())
    cases = query_all(CASE_SQL + where + " ORDER BY sc.status, sc.id DESC", params)
    for case in cases:
        case["messages"] = query_all("SELECT * FROM support_message WHERE case_id = ? ORDER BY id", (case["id"],))
    return jsonify(cases)


@app.get("/api/support/<int:case_id>")
def show_case(case_id):
    return jsonify(get_case(case_id))


@app.post("/api/support")
def create_case():
    """Start en chat med en medarbejder: {"customer_id": 1, "text": "…", "staff_id": 2 (valgfri)}"""
    data = json_body()
    require(data, "customer_id", "text")
    get_or_404("customer", data["customer_id"], "Kunde")
    staff_id = data.get("staff_id")
    if staff_id:
        get_or_404("staff", staff_id, "Medarbejder")
    else:   # første ledige medarbejder
        free = query_one("SELECT id FROM staff WHERE online = 1 ORDER BY (SELECT COUNT(*) FROM support_case "
                         "WHERE staff_id = staff.id AND status = 'AABEN'), id LIMIT 1")
        staff_id = free["id"] if free else None
    active = active_reservation_for(data["customer_id"])
    with transaction() as db:
        case_id = open_case(db, data["customer_id"], "KONTAKT", data["text"].strip(),
                            active["id"] if active else None, staff_id)
        if not support_open():
            db.execute("INSERT INTO support_message (case_id, sender, text, sent_at) VALUES (?, 'SYSTEM', ?, ?)",
                       (case_id, f"Kundeservice har lukket nu ({SUPPORT_HOURS_TEXT}). Vi svarer, så snart vi åbner.", now()))
    return jsonify(get_case(case_id)), 201


@app.post("/api/support/<int:case_id>/messages")
def add_message(case_id):
    """Skriv i en henvendelse: {"sender": "KUNDE" | "MEDARBEJDER", "text": "…", "staff_id": 1 (medarbejder)}"""
    data = json_body()
    require(data, "sender", "text")
    if data["sender"] not in ("KUNDE", "MEDARBEJDER"):
        raise ApiError("sender skal være KUNDE eller MEDARBEJDER")
    case = get_case(case_id)
    if case["status"] == "LUKKET":
        raise ApiError(f"Henvendelse {case['case_no']} er lukket. Start en ny chat.")
    with transaction() as db:
        db.execute("INSERT INTO support_message (case_id, sender, text, sent_at) VALUES (?, ?, ?, ?)",
                   (case_id, data["sender"], data["text"].strip(), now()))
        if data["sender"] == "MEDARBEJDER" and data.get("staff_id") and not case["staff_id"]:
            db.execute("UPDATE support_case SET staff_id = ? WHERE id = ?", (data["staff_id"], case_id))
    return jsonify(get_case(case_id)), 201


@app.post("/api/support/<int:case_id>/close")
def close_case(case_id):
    get_case(case_id)
    with transaction() as db:
        db.execute("UPDATE support_case SET status = 'LUKKET' WHERE id = ?", (case_id,))
    return jsonify(get_case(case_id))


# ---------------------------------------------------------------- AI-assistent (regelbaseret demo)
ASSISTANT_TOPICS = [
    # (emne, nøgleord, svar). {hold}, {fee} osv. udfyldes fra reglerne ovenfor.
    ("book", ["reservér", "reserver", "book", "bestil", "hvordan får jeg"],
     "Find et hotspot på listen (du kan søge øverst), og tryk »Reservér«. Du får et pladsnummer, "
     "og pladsen holdes i {hold} minutter. Det koster {fee_res}."),
    ("cancel", ["annull", "afbestil", "fortryd", "aflys", "slet reserv"],
     "Tryk »Annullér« på din reservation øverst på forsiden. Pladsen bliver straks ledig igen. Det koster {fee_cancel}."),
    ("late", ["sent", "forsink", "nå det", "udløb", "frist", "hvor lang", "hvor længe", "minutter", "timer"],
     "Pladsen holdes i {hold} minutter. Kommer du for sent, udløber reservationen automatisk, og pladsen gives videre. "
     "Gebyr ved udløb: {fee_noshow}. Du kan reservere igen, hvis der er ledige pladser."),
    ("fee", ["gebyr", "pris", "koste", "betal", "penge", "kroner", "kr."],
     "Reservation: {fee_res}. Annullering: {fee_cancel}. Udløb uden ankomst: {fee_noshow}. "
     "Selve turen betales som normalt i GreenMobility-appen."),
    ("arrive", ["ankom", "fremme", "parkeret", "holder på pladsen", "er her"],
     "Parkér på dit pladsnummer, og tryk »Jeg er ankommet« på din reservation. Så står pladsen som optaget."),
    ("occupied", ["optaget", "holder en bil", "står en bil", "anden bil", "nogen holder"],
     "Tryk »Problem med pladsen?« på din reservation og vælg »Min plads er optaget«. "
     "Så giver vi dig en anden ledig plads, hvis der er en."),
    ("find", ["finde", "find", "hvor er", "skilt", "kan ikke se"],
     "Tryk »Problem med pladsen?« og vælg »Jeg kan ikke finde pladsen«. Du får en vejvisning, og en medarbejder får besked."),
    ("full", ["fuld", "ingen ledige", "ingen plads", "alternativ", "andet sted"],
     "Er et hotspot fuldt, viser appen de nærmeste hotspots med ledige pladser. Tryk »Se alternativer« på det fulde hotspot."),
    ("app", ["app", "fejl", "virker ikke", "hænger", "crash", "loader", "indlæs", "log ind", "login", "opdater"],
     "Prøv at genindlæse siden og tjek, at du har internet. Hjælper det ikke, så skriv til en medarbejder – "
     "fortæl gerne, hvad du trykkede på, og hvad der skete."),
    ("privacy", ["data", "privat", "gdpr", "lokation", "position", "gemmer"],
     "Vi gemmer navn, e-mail, nummerplade, dine reservationer og henvendelser. Din position bruges kun på telefonen "
     "og gemmes ikke. Se »Privatliv« i menuen."),
    ("parking", ["parker", "hotspot", "lade", "oplad"],
     "Hotspots er faste GreenMobility-pladser. Du kan reservere en plads, før du kører derhen, så du er sikker på at kunne parkere."),
    ("human", ["medarbejder", "menneske", "person", "ring", "telefon", "snakke med", "tale med"],
     "Du kan skrive eller ringe til en medarbejder. Tryk »Kontakt medarbejder« herunder."),
    ("hello", ["hej", "goddag", "hallo"],
     "Hej! Jeg er GreenMobilitys AI-assistent. Spørg mig om booking, parkering eller problemer med appen."),
    ("thanks", ["tak"], "Selv tak! Skriv endelig, hvis der er mere."),
]


def normalize(text):
    return re.sub(r"\s+", " ", text.lower()).strip()


@app.post("/api/assistant")
def assistant():
    """AI-hjælp: {"text": "Hvordan annullerer jeg?", "customer_id": 1}. Regelbaseret demo – ingen sprogmodel, intet gemmes."""
    data = json_body()
    require(data, "text")
    text = normalize(data["text"])
    values = {"hold": HOLD_MINUTES, "fee_res": kr(RESERVATION_FEE_KR).lower(),
              "fee_cancel": kr(CANCEL_FEE_KR).lower(), "fee_noshow": kr(NO_SHOW_FEE_KR).lower()}

    # Nøgleord skal stå i starten af et ord, så fx "tak" ikke rammer "kontakt"
    scored = [(sum(bool(re.search(r"(?<!\w)" + re.escape(word), text)) for word in words), topic, answer)
              for topic, words, answer in ASSISTANT_TOPICS]
    score, topic, answer = max(scored, key=lambda item: item[0])
    if score == 0:
        return jsonify(topic="unknown", handoff=True,
                       answer="Det kan jeg desværre ikke svare sikkert på. Vil du tale med en medarbejder?")

    answer = answer.format(**values)
    active = active_reservation_for(data["customer_id"]) if data.get("customer_id") else None
    if active and topic in ("late", "cancel", "arrive", "occupied", "find"):
        answer += (f" Din reservation {active['reservation_no']} er plads {active['spot_label']} ved "
                   f"{active['hotspot_name']} og udløber kl. {active['arrival_deadline'][11:16]}.")
    return jsonify(topic=topic, answer=answer, handoff=topic in ("human", "app"))


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
