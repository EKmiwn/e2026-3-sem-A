"""Amitylux – experience finder and inquiry journey. Flask API (logic layer).

Kravgrundlag: ../Kravspecifikation.md
Kør:  pip install -r requirements.txt  &&  python app.py  →  http://localhost:5103
"""
import os
from datetime import date

from flask import jsonify, request

from core import ApiError, create_app, get_or_404, json_body, now, register_crud, require, run
from database import init_db, query_all, query_one, transaction

PORT = int(os.environ.get("PORT", 5103))
app = create_app(__name__, "Amitylux Experience Finder")

# ---------------------------------------------------------------- Business rules
SHORT_NOTICE_DAYS = 14
BUDGET_RANK = {"low": 1, "medium": 2, "high": 3, "premium": 4}
TYPE_NAMES = {"public": "Public small-group tour", "private": "Private tour", "customised": "Customised experience"}


def as_list(value):
    if isinstance(value, list):
        return [v for v in value if v]
    return [v.strip() for v in (value or "").split(",") if v.strip()]


def enrich_experience(e):
    e["languages"] = as_list(e["languages"])
    e["interests"] = as_list(e["interests"])
    e["value_points"] = [v for v in (e["value_points"] or "").split(";") if v]
    e["price_label"] = f"€{e['price_per_person']:g} per person" if e["price_per_person"] else "Price on request"
    e["type_name"] = TYPE_NAMES[e["type_code"]]
    return e


def score_product_types(p):
    """F-03: Scores public/private/customised from the customer's answers.
    Every point comes with a reason that refers to the customer's own answer (NF-04 transparency)."""
    scores = {code: {"score": 0, "reasons": []} for code in TYPE_NAMES}

    def add(code, points, reason):
        scores[code]["score"] += points
        scores[code]["reasons"].append(reason)

    budget = p.get("budget")
    group_type = p.get("group_type")
    group_size = int(p.get("group_size") or 2)
    pace = p.get("pace")
    interests = as_list(p.get("interests"))
    addons = as_list(p.get("addons"))
    language = p.get("language") or "English"

    if budget == "low":
        add("public", 3, "Your budget fits a shared small-group tour with a fixed price per person.")
    elif budget == "medium":
        add("public", 1, "A medium budget covers our small-group tours comfortably.")
        add("private", 1, "A medium budget can cover a private guide when shared across your group.")
    elif budget == "high":
        add("private", 2, "Your budget allows a private guide just for your party.")
        add("customised", 1, "Your budget leaves room for a few tailor-made elements.")
    elif budget == "premium":
        add("private", 2, "Your budget allows a private guide just for your party.")
        add("customised", 3, "Your premium budget opens for a fully tailor-made experience with special access.")

    if group_type == "solo":
        add("public", 2, "Travelling solo, you get company and a lower price in a small group.")
    elif group_type in ("couple", "family"):
        add("private", 2, f"As a {group_type}, a private tour lets you set the pace and focus together.")
    elif group_type == "friends" and group_size >= 5:
        add("private", 1, "A group of friends your size often prefers its own guide.")

    if group_size > 8:
        add("customised", 2, f"With {group_size} people, a customised set-up handles logistics and splitting the group.")
    elif 3 <= group_size <= 8:
        add("private", 1, f"{group_size} people fits perfectly in one private tour.")
    elif group_size <= 2:
        add("public", 1, "A party of 1–2 joins a small group easily.")

    if pace == "fixed":
        add("public", 1, "You are happy with a fixed schedule, which is how public tours run.")
    elif pace == "relaxed":
        add("private", 1, "You prefer a relaxed pace – a private guide adapts on the day.")
    elif pace == "flexible":
        add("customised", 2, "You want full flexibility, which a customised programme gives you.")
        add("private", 1, "You want flexibility in date and start time.")

    if len(interests) >= 3:
        add("customised", 2, f"You combine {len(interests)} interests ({', '.join(interests)}) – best put together by a planner.")
    if len(addons) >= 2:
        add("customised", 2, f"You chose {len(addons)} add-ons, which we coordinate for you in one programme.")
    if language not in ("English", "Danish"):
        add("private", 1, f"Public tours run in English – a private guide can speak {language}.")

    ranked = sorted(scores.items(), key=lambda kv: kv[1]["score"], reverse=True)
    return [{"type_code": code, "type_name": TYPE_NAMES[code], **data} for code, data in ranked]


def capacity_warning(destination, date_from):
    """F-12: Warn about short notice and high season."""
    if not date_from:
        return None
    try:
        start = date.fromisoformat(date_from)
    except ValueError:
        raise ApiError("date_from must be in the format YYYY-MM-DD")
    messages = []
    days = (start - date.today()).days
    if days < SHORT_NOTICE_DAYS:
        messages.append(f"Your trip starts in {max(days, 0)} days. With short notice our best guides may be booked.")
    if str(start.month) in destination["high_season_months"].split(","):
        messages.append(f"{start.strftime('%B')} is high season in {destination['name']}.")
    if not messages:
        return None
    return {"messages": messages,
            "suggestion": "Consider flexible dates, a morning start or one of the alternatives below – "
                          "we will confirm real availability personally."}


def matching_experiences(destination_id, type_code=None, prefs=None):
    rows = [enrich_experience(e) for e in query_all(
        "SELECT * FROM experience WHERE destination_id = ? ORDER BY rating DESC", (destination_id,))]
    prefs = prefs or {}
    if type_code:
        rows = [e for e in rows if e["type_code"] == type_code]
    interests = set(as_list(prefs.get("interests")))
    if interests:
        rows.sort(key=lambda e: len(interests & set(e["interests"])), reverse=True)
    return rows


# ---------------------------------------------------------------- CRUD
register_crud(app, "destinations", "destination",
              fields=["name", "country", "description", "high_season_months"], required=["name", "country"])
register_crud(app, "product-types", "product_type",
              fields=["code", "name", "group_form", "flexibility", "personalisation", "price_principle",
                      "booking_form", "included", "not_included"], required=["code", "name"])
register_crud(app, "experiences", "experience",
              fields=["destination_id", "type_code", "title", "description", "price_per_person", "price_level",
                      "languages", "interests", "min_group", "max_group", "duration_hours", "included",
                      "not_included", "value_points", "guide_name", "guide_expertise", "rating", "review_count",
                      "review_quote", "sustainable_label", "off_the_beaten_track"],
              required=["destination_id", "type_code", "title", "price_level", "languages", "interests"])
register_crud(app, "addons", "addon", fields=["code", "name", "description", "price_hint", "interest"],
              required=["code", "name"])
register_crud(app, "inquiries", "inquiry", fields=["status", "destination_id"], read_only=True, order_by="id DESC")
register_crud(app, "help-requests", "help_request", fields=["name", "contact", "step", "context", "status"],
              required=["name", "contact"], defaults={"created_at": now}, order_by="id DESC")


# ---------------------------------------------------------------- Filtering (F-04)
@app.get("/api/experiences/search")
def search_experiences():
    """Filters: destination_id, type, price_level (max), language, group_size, interest."""
    args = request.args
    rows = [enrich_experience(e) for e in query_all("SELECT * FROM experience ORDER BY rating DESC")]
    if args.get("destination_id"):
        rows = [e for e in rows if e["destination_id"] == int(args["destination_id"])]
    if args.get("type"):
        rows = [e for e in rows if e["type_code"] == args["type"]]
    if args.get("price_level"):
        rows = [e for e in rows if BUDGET_RANK[e["price_level"]] <= BUDGET_RANK[args["price_level"]]]
    if args.get("language"):
        rows = [e for e in rows if args["language"] in e["languages"]]
    if args.get("group_size"):
        size = int(args["group_size"])
        rows = [e for e in rows if e["min_group"] <= size <= e["max_group"]]
    if args.get("interest"):
        rows = [e for e in rows if args["interest"] in e["interests"]]
    return jsonify(active_filters={k: v for k, v in args.items() if v}, results=rows)


# ---------------------------------------------------------------- Recommendation (F-03, F-06, F-12, F-13, F-14)
@app.post("/api/recommendations")
def recommend():
    """Recommendation: primary type + up to two alternatives, each with reasons (F-03)."""
    prefs = json_body()
    require(prefs, "destination_id")
    destination = get_or_404("destination", prefs["destination_id"], "Destination")
    ranked = score_product_types(prefs)
    primary, alternatives = ranked[0], ranked[1:3]

    for option in ranked:
        option["experiences"] = matching_experiences(destination["id"], option["type_code"], prefs)[:2]

    interests = set(as_list(prefs.get("interests")))
    off_peak = next((e for e in matching_experiences(destination["id"], prefs=prefs)
                     if e["off_the_beaten_track"] and interests & set(e["interests"])), None)

    chosen_addons = set(as_list(prefs.get("addons")))
    suggestions = [a for a in query_all("SELECT * FROM addon")
                   if a["code"] not in chosen_addons and (a["interest"] in interests or
                   (a["code"] == "transport" and prefs.get("group_type") == "family"))][:2]
    other_destination = query_one("SELECT id, name, country, description FROM destination WHERE id != ? LIMIT 1",
                                  (destination["id"],))
    contextual = [{"kind": "addon", **a} for a in suggestions]
    if other_destination:
        contextual.append({"kind": "destination", **other_destination})

    return jsonify(
        based_on=prefs,
        destination=destination,
        primary=primary,
        alternatives=alternatives,
        capacity_warning=capacity_warning(destination, prefs.get("date_from")),
        less_crowded_alternative=off_peak and {
            **off_peak,
            "reason": "Fewer crowds and a more local feel" + (
                f" – and sustainable transport ({off_peak['sustainable_label'].lower()})"
                if off_peak["sustainable_label"] else ""),
        },
        contextual_suggestions=contextual[:3],
    )


# ---------------------------------------------------------------- Inquiry and brief (F-08, F-15)
def build_brief(inquiry):
    destination = get_or_404("destination", inquiry["destination_id"])
    experience = inquiry["experience_id"] and query_one("SELECT title FROM experience WHERE id = ?",
                                                        (inquiry["experience_id"],))
    uncertainties = []
    if not inquiry["date_from"]:
        uncertainties.append("No dates given")
    if not inquiry["budget"]:
        uncertainties.append("No budget given")
    warning = capacity_warning(destination, inquiry["date_from"])
    if warning:
        uncertainties.extend(warning["messages"])
    if (inquiry["group_size"] or 0) > 12:
        uncertainties.append("Large group – may need several guides")

    return {
        "reference": inquiry["reference"],
        "received": inquiry["created_at"],
        "status": inquiry["status"],
        "customer": {"name": inquiry["contact_name"], "email": inquiry["contact_email"],
                     "phone": inquiry["contact_phone"]},
        "trip": {"destination": destination["name"], "date_from": inquiry["date_from"],
                 "date_to": inquiry["date_to"], "group_type": inquiry["group_type"],
                 "group_size": inquiry["group_size"]},
        "preferences": {"interests": as_list(inquiry["interests"]), "language": inquiry["language"],
                        "pace": inquiry["pace"], "budget": inquiry["budget"]},
        "guide_wishes": {"language": inquiry["guide_language"], "focus": inquiry["guide_focus"],
                         "style": inquiry["guide_style"], "note": "Wishes – not guaranteed"},
        "add_ons": as_list(inquiry["addons"]),
        "selected_experience": experience["title"] if experience else None,
        "recommended_type": TYPE_NAMES.get(inquiry["recommended_type"]),
        "free_text": inquiry["notes"],
        "uncertainties": uncertainties,
        "next_action": "Planner contacts the customer within 24 hours with a first proposal"
                       if not uncertainties else "Planner calls the customer to clarify the uncertainties above",
    }


@app.post("/api/inquiries")
def create_inquiry():
    """Send a structured request – returns a receipt and the staff brief (F-08)."""
    data = json_body()
    require(data, "contact_name", "contact_email", "destination_id")
    get_or_404("destination", data["destination_id"], "Destination")
    if "@" not in data["contact_email"]:
        raise ApiError("Please enter a valid e-mail address")
    columns = ["contact_name", "contact_email", "contact_phone", "destination_id", "experience_id", "date_from",
               "date_to", "group_type", "group_size", "interests", "language", "pace", "budget", "addons",
               "guide_language", "guide_focus", "guide_style", "notes", "recommended_type"]
    values = [",".join(as_list(data.get(c))) if c in ("interests", "addons") else data.get(c) for c in columns]
    with transaction() as db:
        next_no = db.execute("SELECT COALESCE(MAX(id), 0) + 1001 FROM inquiry").fetchone()[0]
        cur = db.execute(
            f"INSERT INTO inquiry (reference, created_at, {', '.join(columns)})"
            f" VALUES (?, ?, {', '.join('?' for _ in columns)})",
            (f"AMX-{next_no}", now(), *values))
    inquiry = get_or_404("inquiry", cur.lastrowid)
    return jsonify(
        receipt={
            "reference": inquiry["reference"],
            "message": f"Thank you, {inquiry['contact_name']}! Your request has been sent to our local team.",
            "next_steps": ["A personal planner reviews your request",
                           "You receive a proposal by e-mail within 24 hours",
                           "Nothing is booked or paid until you confirm"],
        },
        brief=build_brief(inquiry),
    ), 201


@app.get("/api/inquiries/<int:inquiry_id>/brief")
def inquiry_brief(inquiry_id):
    """Standardised brief for staff (F-15)."""
    return jsonify(build_brief(get_or_404("inquiry", inquiry_id, "Inquiry")))


@app.put("/api/inquiries/<int:inquiry_id>")
def update_inquiry_status(inquiry_id):
    """Update the status of an inquiry."""
    get_or_404("inquiry", inquiry_id, "Inquiry")
    data = json_body()
    require(data, "status")
    with transaction() as db:
        db.execute("UPDATE inquiry SET status = ? WHERE id = ?", (data["status"], inquiry_id))
    return jsonify(get_or_404("inquiry", inquiry_id))


@app.delete("/api/inquiries/<int:inquiry_id>")
def delete_inquiry(inquiry_id):
    """Delete an inquiry."""
    get_or_404("inquiry", inquiry_id, "Inquiry")
    with transaction() as db:
        db.execute("DELETE FROM inquiry WHERE id = ?", (inquiry_id,))
    return "", 204


if __name__ == "__main__":
    init_db()
    run(app, PORT)
