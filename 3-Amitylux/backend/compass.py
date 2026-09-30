"""LOGIKLAG – oplevelseskompasset for Amitylux (K1–K3, K6, K9, K12).

Ren Python uden Flask og SQLite, så matchreglerne kan testes alene.
Motoren er regelbaseret og deterministisk: samme præferencer og samme katalog giver samme forslag.
"AI" er simuleret – motoren sorterer, matcher og forklarer, men opfinder aldrig fakta (K9).

    catalogue = [experience-rækker fra databasen, kun catalogue_status = 'approved']
    prefs     = {"destination_id", "group_type", "group_size", "interests", "pace", "language",
                 "practical", "travel_date"}
"""
from datetime import date

MAX_SUGGESTIONS = 3            # K2
MIN_MATCHED_PREFERENCES = 2    # K3
SHORT_NOTICE_DAYS = 14

# ---------------------------------------------------------------- Svarmuligheder (K1) – én kilde for UI og validering
GROUP_TYPES = {"solo": "Solo", "couple": "Couple", "family": "Family", "friends": "Friends"}
INTERESTS = {"history": "History", "art": "Art", "food": "Food", "architecture": "Architecture",
             "design": "Design", "nature": "Nature & outdoors", "local life": "Local life"}
PACES = {"relaxed": "Relaxed", "moderate": "Moderate", "active": "Active"}
LANGUAGES = ["English", "Danish", "German", "Spanish", "French", "Italian"]
PRACTICAL = {"step_free": "Step-free route", "kid_friendly": "Suitable for children",
             "short_walks": "Short walking distances", "indoor_option": "Indoor option in bad weather"}
TRANSPORT = {"walk": "On foot", "bike": "Bike", "public_transport": "Public transport", "car": "Private car",
             "boat": "Boat"}
TYPE_NAMES = {"public": "Public small-group", "private": "Private", "customised": "Customised"}
PACE_ORDER = ["relaxed", "moderate", "active"]

SLOTS = {
    "classic": ("Classic", "The well-known highlight, done the Amitylux way."),
    "local": ("Local", "A more local choice, outside the busiest tourist areas."),
    "balanced": ("Balanced", "A different format – compare what you get."),
}

# Kan ikke opfyldes af en oplevelse, der mangler den → udelukkes i stedet for at blive nedprioriteret
HARD_PRACTICAL = {"step_free"}


def as_list(value, sep=","):
    if isinstance(value, list):
        return [v for v in value if v]
    return [v.strip() for v in (value or "").split(sep) if v.strip()]


def options():
    return {"group_types": GROUP_TYPES, "interests": INTERESTS, "paces": PACES, "languages": LANGUAGES,
            "practical": PRACTICAL, "transport": TRANSPORT, "types": TYPE_NAMES,
            "max_suggestions": MAX_SUGGESTIONS}


# ---------------------------------------------------------------- K1 Validering
def validate(prefs):
    """Returnerer {felt: fejlbesked}. Tom dict = gyldige præferencer."""
    errors = {}
    if not prefs.get("destination_id"):
        errors["destination_id"] = "Choose a destination"
    if prefs.get("group_type") not in GROUP_TYPES:
        errors["group_type"] = "Choose who is travelling"
    try:
        size = int(prefs.get("group_size"))
        if not 1 <= size <= 40:
            raise ValueError
    except (TypeError, ValueError):
        errors["group_size"] = "Group size must be between 1 and 40"
    interests = as_list(prefs.get("interests"))
    if not interests:
        errors["interests"] = "Choose at least one interest"
    elif any(i not in INTERESTS for i in interests):
        errors["interests"] = "Unknown interest"
    if prefs.get("pace") not in PACES:
        errors["pace"] = "Choose a pace"
    if prefs.get("language") not in LANGUAGES:
        errors["language"] = "Choose a language"
    if any(p not in PRACTICAL for p in as_list(prefs.get("practical"))):
        errors["practical"] = "Unknown practical consideration"
    if prefs.get("travel_date"):
        try:
            date.fromisoformat(prefs["travel_date"])
        except ValueError:
            errors["travel_date"] = "Date must be YYYY-MM-DD"
    return errors


def normalise(prefs):
    return {
        "destination_id": int(prefs["destination_id"]),
        "group_type": prefs["group_type"],
        "group_size": int(prefs["group_size"]),
        "interests": sorted(as_list(prefs.get("interests")), key=list(INTERESTS).index),
        "pace": prefs["pace"],
        "language": prefs["language"],
        "practical": sorted(as_list(prefs.get("practical")), key=list(PRACTICAL).index),
        "travel_date": prefs.get("travel_date") or None,
    }


# ---------------------------------------------------------------- K5, K12 Præsentation af en katalogrække
def price_label(e):
    if e["price_unit"] == "request" or e["price_from"] is None:
        return "Price on request"
    if e["price_unit"] == "group":
        return f"€{e['price_from']:g} per group (up to {e['max_group']})"
    return f"€{e['price_from']:g} per person"


def describe(e):
    """Alle K5-felter i én ensartet struktur – samme kort for alle destinationer (K11)."""
    return {
        "id": e["id"],
        "title": e["title"],
        "description": e["description"],
        "destination_id": e["destination_id"],
        "location": e["location"],
        "experience_type": e["experience_type"],
        "type_code": e["type_code"],
        "type_name": TYPE_NAMES[e["type_code"]],
        "duration_hours": e["duration_hours"],
        "group": f"{e['min_group']}–{e['max_group']} people",
        "languages": as_list(e["languages"]),
        "interests": as_list(e["interests"]),
        "pace": e["pace"],
        "practical": [PRACTICAL[p] for p in as_list(e["practical"]) if p in PRACTICAL],
        "transport": [TRANSPORT[t] for t in as_list(e["transport_modes"]) if t in TRANSPORT],
        "mobility_note": e["mobility_note"],
        "included": e["included"],
        "not_included": e["not_included"],
        "price_label": price_label(e),
        "local_alternative": bool(e["local_alternative"]),
        "local_note": e["local_note"],
        "rating": e["rating"],
        "review_count": e["review_count"],
        "review_quote": e["review_quote"],
        "review_source": e["review_source"],
        "value_points": as_list(e["value_points"], ";"),
        "source": f"Amitylux catalogue – approved {e['approved_at']} by {e['approved_by']}",
    }


# ---------------------------------------------------------------- K3 Match med begrundelser
def score(e, p):
    """Returnerer None, hvis oplevelsen ikke kan bruges, ellers score, begrundelser og forbehold.
    Hver begrundelse peger på netop den præference, den bygger på."""
    if not e["min_group"] <= p["group_size"] <= e["max_group"]:
        return None
    customised = e["type_code"] == "customised"
    e_interests = as_list(e["interests"])
    e_practical = set(as_list(e["practical"]))
    matched = [i for i in p["interests"] if i in e_interests]
    if not matched:
        return None
    if any(need in HARD_PRACTICAL and need not in e_practical for need in p["practical"]):
        return None
    language_ok = p["language"] in as_list(e["languages"])
    if not language_ok and not customised:
        return None

    points, reasons, cautions, confirm = 0, [], [], []

    def reason(pref, text, pts):
        nonlocal points
        points += pts
        reasons.append({"preference": pref, "text": text})

    names = " and ".join(INTERESTS[i].lower() for i in matched)
    reason("interests", f"Matches your interest in {names}.", (1 if customised else 3) * len(matched))

    if language_ok:
        reason("language", f"Guided in {p['language']}.", 2)
    else:
        confirm.append(f"Guide in {p['language']}")

    if customised:
        reason("pace", f"The pace is planned with you – {PACES[p['pace']].lower()} if you like.", 1)
    else:
        gap = abs(PACE_ORDER.index(e["pace"]) - PACE_ORDER.index(p["pace"]))
        if gap == 0:
            reason("pace", f"{PACES[e['pace']]} pace, as you asked.", 2)
        elif gap == 2:
            points -= 3
            cautions.append(f"The pace is {e['pace']}, not {p['pace']}.")

    gt, size = p["group_type"], p["group_size"]
    if e["type_code"] == "public" and gt in ("solo", "couple"):
        reason("group", f"Easy to join as {'a solo traveller' if gt == 'solo' else 'a couple'} – "
                        f"a small group of max {e['max_group']} guests.", 2)
    elif e["type_code"] == "private" and gt in ("couple", "family", "friends"):
        reason("group", f"Only your {GROUP_TYPES[gt].lower()} of {size} – no other guests.", 2)
    elif customised and size > 8:
        reason("group", f"A party of {size} gets coordinated guides and logistics.", 3)

    for need in p["practical"]:
        if need in e_practical:
            reason("practical", f"{PRACTICAL[need]}.", 2)
        else:
            points -= 2
            cautions.append(f"Not marked as: {PRACTICAL[need].lower()}.")

    if customised:
        # Et skræddersyet forløb passer til alt – derfor skal der være reel kompleksitet, før det topper listen
        complexity = (size > 8) + (len(p["interests"]) >= 3) + (len(p["practical"]) >= 2) + (not language_ok)
        points += 2 * complexity - 3

    distinct = {r["preference"] for r in reasons}
    if len(distinct) < MIN_MATCHED_PREFERENCES:
        return None
    confirm.extend(as_list(e["needs_confirmation"], ";"))
    return {"score": points, "reasons": reasons, "cautions": cautions, "requires_confirmation": confirm}


# ---------------------------------------------------------------- K9 Datoafhængige forbehold
def date_notes(destination, travel_date, today=None):
    if not travel_date:
        return []
    start = date.fromisoformat(travel_date)
    notes = []
    days = (start - (today or date.today())).days
    if days < SHORT_NOTICE_DAYS:
        notes.append(f"Availability at short notice ({max(days, 0)} days)")
    if str(start.month) in destination["high_season_months"].split(","):
        notes.append(f"Availability in high season ({start.strftime('%B')})")
    return notes


# ---------------------------------------------------------------- K2, K6 Højst tre forslag i faste roller
def suggest(catalogue, destination, prefs, today=None):
    p = normalise(prefs)
    local = [e for e in catalogue if e["destination_id"] == destination["id"]]
    scored = []
    for e in local:
        s = score(e, p)
        if s:
            scored.append((e, s))
    # Deterministisk rækkefølge: score, derefter rating, derefter id
    scored.sort(key=lambda es: (-es[1]["score"], -(es[0]["rating"] or 0), es[0]["id"]))

    picked = []

    def take(slot, candidates):
        for e, s in candidates:
            if all(e["id"] != x[1]["id"] for x in picked):
                picked.append((slot, e, s))
                return True
        return False

    take("classic", [(e, s) for e, s in scored if not e["local_alternative"] and e["type_code"] != "customised"])
    take("local", [(e, s) for e, s in scored if e["local_alternative"]])
    used_types = {e["type_code"] for _, e, _ in picked}
    if not take("balanced", [(e, s) for e, s in scored if e["type_code"] not in used_types]):
        take("balanced", scored)
    while len(picked) < MAX_SUGGESTIONS and take("balanced", scored):
        pass

    order = list(SLOTS)
    picked.sort(key=lambda x: order.index(x[0]))
    extra = date_notes(destination, p["travel_date"], today)
    suggestions = []
    for slot, e, s in picked[:MAX_SUGGESTIONS]:
        label, hint = SLOTS[slot]
        suggestions.append({
            "slot": slot, "slot_label": label, "slot_hint": hint,
            "experience": describe(e),
            "score": s["score"],
            "reasons": s["reasons"],
            "cautions": s["cautions"],
            "requires_confirmation": s["requires_confirmation"] + extra,
        })
    return {
        "preferences": p,
        "checked": {"approved_in_destination": len(local), "matching": len(scored), "shown": len(suggestions)},
        "suggestions": suggestions,
    }


# ---------------------------------------------------------------- K3 Hvad ændrede sig efter en justering?
def compare(previous, current):
    before = {s["experience"]["id"]: s for s in previous["suggestions"]}
    after = {s["experience"]["id"]: s for s in current["suggestions"]}
    pp, cp = previous["preferences"], current["preferences"]
    return {
        "changed_preferences": [{"field": k, "from": pp.get(k), "to": cp.get(k)} for k in cp if pp.get(k) != cp.get(k)],
        "added": [after[i]["experience"]["title"] for i in after if i not in before],
        "removed": [before[i]["experience"]["title"] for i in before if i not in after],
        "reasons_changed": [after[i]["experience"]["title"] for i in after
                            if i in before and after[i]["reasons"] != before[i]["reasons"]],
    }
