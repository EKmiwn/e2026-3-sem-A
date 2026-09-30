"""Amitylux Experience Compass – few, explainable experience suggestions. Flask API.

Kravgrundlag: ../kravspecifikation-2.md (K1–K12) · Idé 1 i ../prototype-ideer.md
Matchreglerne ligger i compass.py (ingen Flask/SQLite), her er kun HTTP og data.
Kør:  pip install -r requirements.txt  &&  python app.py  →  http://localhost:5103
"""
import json
import os

from flask import jsonify

import compass
from core import ApiError, create_app, get_or_404, json_body, now, register_crud, require, run
from database import init_db, query_all, query_one, transaction

PORT = int(os.environ.get("PORT", 5103))
app = create_app(__name__, "Amitylux Experience Compass")

K5_FIELDS = ["title", "description", "location", "experience_type", "duration_hours", "min_group", "max_group",
             "transport_modes", "included", "not_included", "price_unit"]


def value_claims():
    return {c["code"]: c for c in query_all("SELECT * FROM value_claim ORDER BY id")}


def catalogue_problems(e, claims):
    """K5, K7, K9: hvad mangler, før en katalogrække må bruges som grundlag for et forslag?"""
    problems = [f"missing {f}" for f in K5_FIELDS if e[f] in (None, "")]
    if e["price_unit"] != "request" and e["price_from"] is None:
        problems.append("missing price_from")
    problems += [f"undocumented claim '{c}'" for c in compass.as_list(e["value_points"], ";") if c not in claims]
    if e["catalogue_status"] != "approved":
        problems.append("not approved")
    return problems


def approved_catalogue():
    """K9: kun godkendte og komplette katalogrækker bruges nogensinde som grundlag for forslag."""
    claims = value_claims()
    return [e for e in query_all("SELECT * FROM experience ORDER BY id") if not catalogue_problems(e, claims)]


def checked_prefs(prefs):
    errors = compass.validate(prefs)
    if errors:
        raise ApiError("Please check your answers: " + "; ".join(errors.values()))
    return get_or_404("destination", prefs["destination_id"], "Destination")


def run_compass(prefs):
    destination = checked_prefs(prefs)
    result = compass.suggest(approved_catalogue(), destination, prefs)
    claims = value_claims()
    for s in result["suggestions"]:
        # K7: kun dokumenterede værdipåstande, med kilden ved siden af
        s["amitylux_value"] = [claims[c] for c in s["experience"]["value_points"] if c in claims]
    result["destination"] = destination
    return result


# ---------------------------------------------------------------- CRUD
register_crud(app, "destinations", "destination",
              fields=["name", "country", "description", "high_season_months"], required=["name", "country"])
register_crud(app, "product-types", "product_type",
              fields=["code", "name", "short", "group_form", "flexibility", "personalisation", "booking_form",
                      "price_principle", "best_for"], required=["code", "name"])
register_crud(app, "value-claims", "value_claim", fields=["code", "label", "text", "evidence"],
              required=["code", "label", "text", "evidence"])
register_crud(app, "experiences", "experience",
              fields=["destination_id", "type_code", *K5_FIELDS[:4], "duration_hours", "min_group", "max_group",
                      "languages", "interests", "pace", "practical", "transport_modes", "mobility_note", "included",
                      "not_included", "price_from", "price_unit", "value_points", "local_alternative", "local_note",
                      "rating", "review_count", "review_quote", "review_source", "needs_confirmation",
                      "catalogue_status", "approved_by", "approved_at"],
              required=["destination_id", "type_code", "title", "description", "location", "experience_type",
                        "duration_hours", "languages", "interests", "pace", "included", "not_included", "price_unit"],
              defaults={"catalogue_status": "draft"})
register_crud(app, "addons", "addon", fields=["code", "name", "description", "price_hint"],
              required=["code", "name", "price_hint"])
register_crud(app, "inquiries", "inquiry", fields=["status", "destination_id", "wanted_type"], read_only=True,
              order_by="id DESC")
register_crud(app, "help-requests", "help_request", fields=["status", "step"], read_only=True, order_by="id DESC")


# ---------------------------------------------------------------- K1 Svarmuligheder
@app.get("/api/options")
def get_options():
    """Answer options for the preference flow (K1) – the same lists the engine validates against."""
    return jsonify(compass.options())


# ---------------------------------------------------------------- K2, K3, K6, K7, K9 Kompasset
@app.post("/api/compass")
def compass_suggestions():
    """Up to three explained suggestions. Send {"preferences": {...}, "previous": {...}} to see what changed (K3)."""
    body = json_body()
    prefs = body.get("preferences", body)
    result = run_compass(prefs)
    if body.get("previous"):
        previous = compass.suggest(approved_catalogue(), checked_prefs(body["previous"]), body["previous"])
        result["changes"] = compass.compare(previous, result)
    return jsonify(result)


@app.get("/api/catalogue")
def catalogue():
    """The approved catalogue in the same card structure as the suggestions (K5, K11)."""
    return jsonify([compass.describe(e) for e in approved_catalogue()])


@app.get("/api/catalogue/audit")
def catalogue_audit():
    """K9: for Amitylux – every row is checked for approval, missing K5 fields and undocumented value claims."""
    claims = value_claims()
    return jsonify([{"id": e["id"], "title": e["title"], "destination_id": e["destination_id"],
                     "type_name": compass.TYPE_NAMES[e["type_code"]], "catalogue_status": e["catalogue_status"],
                     "approved_by": e["approved_by"], "approved_at": e["approved_at"],
                     "problems": catalogue_problems(e, claims),
                     "requires_confirmation": compass.as_list(e["needs_confirmation"], ";"),
                     "used_in_suggestions": not catalogue_problems(e, claims)}
                    for e in query_all("SELECT * FROM experience ORDER BY destination_id, id")])


# ---------------------------------------------------------------- K8 Struktureret overlevering
INQUIRY_COLUMNS = ["wanted_type", "contact_name", "contact_email", "contact_phone", "destination_id", "travel_date",
                   "group_type", "group_size", "interests", "pace", "language", "practical", "experience_ids",
                   "addons", "customer_unsure", "notes"]
LIST_COLUMNS = ("interests", "practical", "experience_ids", "addons")


def build_brief(inquiry):
    """Samme brief bruges i kundens forhåndsvisning og i medarbejdervisningen."""
    destination = get_or_404("destination", inquiry["destination_id"], "Destination")
    ids = [int(i) for i in compass.as_list(inquiry["experience_ids"])]
    chosen = [query_one("SELECT * FROM experience WHERE id = ?", (i,)) for i in ids]
    chosen = [e for e in chosen if e]
    addons = {a["code"]: a for a in query_all("SELECT * FROM addon")}

    uncertainties = []
    for e in chosen:
        uncertainties += [f"{e['title']}: {c}" for c in compass.as_list(e["needs_confirmation"], ";")]
        if inquiry["language"] and inquiry["language"] not in compass.as_list(e["languages"]):
            uncertainties.append(f"{e['title']}: guide in {inquiry['language']}")
    uncertainties += compass.date_notes(destination, inquiry["travel_date"])
    if not inquiry["travel_date"]:
        uncertainties.append("No travel date given")
    if (inquiry["group_size"] or 0) > 12:
        uncertainties.append("Large group – may need several guides")
    if inquiry["customer_unsure"]:
        uncertainties.append(f"Customer is unsure: {inquiry['customer_unsure']}")

    return {
        "reference": inquiry.get("reference", "(not sent yet)"),
        "received": inquiry.get("created_at"),
        "status": inquiry.get("status", "DRAFT"),
        "wanted_type": compass.TYPE_NAMES[inquiry["wanted_type"]],
        "customer": {"name": inquiry["contact_name"], "email": inquiry["contact_email"],
                     "phone": inquiry["contact_phone"]},
        "trip": {"destination": destination["name"], "travel_date": inquiry["travel_date"],
                 "group": f"{inquiry['group_size']} · {compass.GROUP_TYPES.get(inquiry['group_type'], '–')}"},
        "preferences": {
            "interests": [compass.INTERESTS.get(i, i) for i in compass.as_list(inquiry["interests"])],
            "pace": compass.PACES.get(inquiry["pace"]), "language": inquiry["language"],
            "practical": [compass.PRACTICAL.get(p, p) for p in compass.as_list(inquiry["practical"])]},
        "selected": {
            "experiences": [f"{e['title']} ({compass.TYPE_NAMES[e['type_code']]}, {compass.price_label(e)})"
                            for e in chosen],
            "add_ons": [addons[c]["name"] for c in compass.as_list(inquiry["addons"]) if c in addons]},
        "notes": inquiry["notes"],
        "uncertainties": uncertainties,
        "next_action": "Planner checks the items marked 'requires confirmation' and sends a first proposal within 24 hours"
                       if uncertainties else "Planner sends a first proposal within 24 hours",
    }


def inquiry_values(data, preview=False):
    """preview=True: kontaktoplysninger må mangle, mens kunden stadig udfylder formularen."""
    require(data, "destination_id", "wanted_type", *(() if preview else ("contact_name", "contact_email")))
    if not preview and "@" not in data["contact_email"]:
        raise ApiError("Please enter a valid e-mail address")
    if data["wanted_type"] not in compass.TYPE_NAMES:
        raise ApiError("wanted_type must be public, private or customised")
    get_or_404("destination", data["destination_id"], "Destination")
    return {c: ",".join(map(str, compass.as_list(data.get(c)))) if c in LIST_COLUMNS else data.get(c)
            for c in INQUIRY_COLUMNS}


@app.post("/api/inquiries/preview")
def preview_inquiry():
    """K8: exactly what will be sent – nothing is saved."""
    return jsonify(build_brief(inquiry_values(json_body(), preview=True)))


@app.post("/api/inquiries")
def create_inquiry():
    """K8: save the structured request and return a receipt plus the staff brief."""
    values = inquiry_values(json_body())
    with transaction() as db:
        next_no = db.execute("SELECT COALESCE(MAX(id), 0) + 1001 FROM inquiry").fetchone()[0]
        cur = db.execute(
            f"INSERT INTO inquiry (reference, created_at, {', '.join(values)}) "
            f"VALUES (?, ?, {', '.join('?' for _ in values)})",
            (f"AMX-{next_no}", now(), *values.values()))
    inquiry = get_or_404("inquiry", cur.lastrowid)
    return jsonify(
        receipt={
            "reference": inquiry["reference"],
            "message": f"Thank you, {inquiry['contact_name']}! Your request is with our local team.",
            "next_steps": ["A personal planner reads your request – you will not be asked the same questions again",
                           "We check everything marked 'requires confirmation'",
                           "You receive a proposal by e-mail within 24 hours",
                           "Nothing is booked or paid until you confirm"],
        },
        brief=build_brief(inquiry),
    ), 201


@app.get("/api/inquiries/<int:inquiry_id>/brief")
def inquiry_brief(inquiry_id):
    """Staff brief for one inquiry (K8)."""
    return jsonify(build_brief(get_or_404("inquiry", inquiry_id, "Inquiry")))


@app.put("/api/inquiries/<int:inquiry_id>")
def update_inquiry_status(inquiry_id):
    """Update the status of an inquiry."""
    get_or_404("inquiry", inquiry_id, "Inquiry")
    data = json_body()
    require(data, "status")
    if data["status"] not in ("NEW", "IN_PROGRESS", "ANSWERED", "CLOSED"):
        raise ApiError("Unknown status")
    with transaction() as db:
        db.execute("UPDATE inquiry SET status = ? WHERE id = ?", (data["status"], inquiry_id))
    return jsonify(get_or_404("inquiry", inquiry_id))


@app.post("/api/help-requests")
def create_help_request():
    """K8: 'Talk to a person' from any step. The answers so far are attached, so nothing has to be repeated."""
    data = json_body()
    require(data, "name", "contact")
    with transaction() as db:
        cur = db.execute(
            "INSERT INTO help_request (created_at, name, contact, step, context, answers) VALUES (?, ?, ?, ?, ?, ?)",
            (now(), data["name"], data["contact"], data.get("step"), data.get("context"),
             json.dumps(data.get("answers") or {}, ensure_ascii=False)))
    return jsonify(get_or_404("help_request", cur.lastrowid)), 201


if __name__ == "__main__":
    init_db()
    run(app, PORT)
