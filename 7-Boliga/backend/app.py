"""Boliga Insight Hub. Flask API (logiklag).

Kravgrundlag: ../Kravspecifikation.md
Kør:  pip install -r requirements.txt  &&  python app.py  →  http://localhost:5107

AI-sparringspartneren er her en regelbaseret prototype, der kun svarer ud fra boligens egne data
og altid angiver kilder (FK4). Funktionen answer_question() kan senere skiftes til et LLM (RAG)
uden at ændre API'et.
"""
import os
from datetime import date

from flask import jsonify, request

from core import ApiError, create_app, get_or_404, json_body, now, register_crud, require, run
from database import init_db, query_all, query_one, transaction

PORT = int(os.environ.get("PORT", 5107))
app = create_app(__name__, "Boliga Insight Hub")


def kr(value):
    return f"{value:,.0f} kr.".replace(",", ".")


# ---------------------------------------------------------------- Dataaggregering (FK1, FK2, FK8)
def boliga_data(property_id):
    p = get_or_404("property", property_id, "Bolig")
    p["days_on_market"] = (date.today() - date.fromisoformat(p["listed_date"])).days
    p["price_per_m2"] = round(p["list_price"] / p["size_m2"])
    p["price_changes"] = query_all("SELECT * FROM price_change WHERE property_id = ? ORDER BY changed_date",
                                   (property_id,))
    first_price = p["price_changes"][0]["old_price"] if p["price_changes"] else p["list_price"]
    p["total_price_drop"] = first_price - p["list_price"]
    p["total_price_drop_pct"] = round(100 * p["total_price_drop"] / first_price, 1)
    p["valuation_diff_pct"] = round(100 * (p["list_price"] - p["ai_valuation"]) / p["ai_valuation"], 1) \
        if p["ai_valuation"] else None
    return p


def market_data(postcode):
    sales = query_all("SELECT * FROM area_sale WHERE postcode = ? ORDER BY sold_date DESC", (postcode,))
    if not sales:
        return {"sales": [], "avg_price_per_m2": None, "avg_days_on_market": None}
    return {
        "sales": sales,
        "avg_price_per_m2": round(sum(s["price"] / s["size_m2"] for s in sales) / len(sales)),
        "avg_days_on_market": round(sum(s["days_on_market"] for s in sales) / len(sales)),
    }


def insight(property_id):
    p = boliga_data(property_id)
    market = market_data(p["postcode"])
    geo = query_one("SELECT * FROM geo_data WHERE property_id = ?", (property_id,))
    auctions = query_all("SELECT * FROM auction WHERE postcode = ? ORDER BY auction_date", (p["postcode"],))
    context = {"property": p, "market": market, "dingeo": geo, "auctions": auctions}
    context["ai_summary"] = make_summary(context)
    return context


# ---------------------------------------------------------------- AI-modul (FK3, FK4, FK5)
def make_summary(ctx):
    """FK5: kort automatisk resumé i hverdagssprog."""
    p, m, g = ctx["property"], ctx["market"], ctx["dingeo"]
    parts = [f"{p['property_type']} på {p['size_m2']} m² i {p['city']} til {kr(p['list_price'])}"]
    if m["avg_price_per_m2"]:
        diff = round(100 * (p["price_per_m2"] - m["avg_price_per_m2"]) / m["avg_price_per_m2"])
        parts.append(f"– m²-prisen er {abs(diff)} % {'over' if diff > 0 else 'under'} de seneste salg i {p['postcode']}.")
    else:
        parts[0] += "."
    if p["total_price_drop"] > 0:
        parts.append(f"Prisen er sat ned {len(p['price_changes'])} gang(e), i alt {p['total_price_drop_pct']} %.")
    if m["avg_days_on_market"] and p["days_on_market"] > m["avg_days_on_market"] * 1.5:
        parts.append(f"Den har været til salg i {p['days_on_market']} dage – længere end normalt i området.")
    if g:
        risks = [name for name, key in (("oversvømmelse", "flood_risk"), ("skybrud", "cloudburst_risk"),
                                        ("radon", "radon_risk")) if g[key] == "høj"]
        if risks:
            parts.append(f"Vær opmærksom på høj risiko for {' og '.join(risks)}.")
    return " ".join(parts)


TOPICS = [
    ("pris", ["pris", "dyr", "billig", "værd", "vurdering", "forhandl", "bud", "m2", "m²"]),
    ("liggetid", ["liggetid", "længe", "til salg", "dage", "hvorfor ikke solgt"]),
    ("oversvømmelse", ["oversvøm", "vand", "skybrud", "klima", "kælder", "regn"]),
    ("støj", ["støj", "larm", "trafik", "vej"]),
    ("familie", ["skole", "børn", "institution", "familie", "grønt", "park"]),
    ("transport", ["station", "tog", "metro", "bus", "transport", "pendl"]),
    ("energi", ["energi", "varme", "energimærke", "elforbrug", "isolering"]),
    ("tryghed", ["kriminal", "tryg", "indbrud", "sikker"]),
    ("radon", ["radon"]),
    ("auktion", ["tvangsauktion", "auktion"]),
]


def answer_question(ctx, question):
    """Svarer kun ud fra boligens data og returnerer de kilder, svaret bygger på."""
    q = question.lower()
    p, m, g = ctx["property"], ctx["market"], ctx["dingeo"]
    answers, sources = [], []

    for topic, words in TOPICS:
        if not any(w in q for w in words):
            continue
        if topic == "pris":
            text = (f"Udbudsprisen er {kr(p['list_price'])} ({kr(p['price_per_m2'])} pr. m²). "
                    f"Boligas AI-vurdering er {kr(p['ai_valuation'])} (±{p['valuation_uncertainty']:g} %), "
                    f"så prisen ligger {abs(p['valuation_diff_pct'])} % {'over' if p['valuation_diff_pct'] > 0 else 'under'} vurderingen.")
            if m["avg_price_per_m2"]:
                text += f" Solgte boliger i {p['postcode']} har i snit kostet {kr(m['avg_price_per_m2'])} pr. m²."
            if p["total_price_drop"] > 0:
                text += f" Prisen er allerede sat ned med {kr(p['total_price_drop'])}."
            answers.append(text)
            sources += ["Boliga.dk: udbudspris og prisfald", "Boliga AI-vurdering", "Boliga salgsdata for postnummeret"]
        elif topic == "liggetid":
            text = f"Boligen har været til salg i {p['days_on_market']} dage."
            if m["avg_days_on_market"]:
                text += f" Normal liggetid i {p['postcode']} er ca. {m['avg_days_on_market']} dage."
                if p["days_on_market"] > m["avg_days_on_market"] * 1.5:
                    text += " Lang liggetid kan give bedre forhandlingsmuligheder."
            answers.append(text)
            sources += ["Boliga.dk: liggetid", "Boliga salgsdata for postnummeret"]
        elif topic == "oversvømmelse" and g:
            answers.append(f"DinGeo vurderer risikoen for oversvømmelse som {g['flood_risk']} og for skybrud som "
                           f"{g['cloudburst_risk']}." + (" Spørg sælger om kælder, dræn og forsikring."
                                                         if "høj" in (g["flood_risk"], g["cloudburst_risk"]) else ""))
            sources.append("DinGeo: oversvømmelse og skybrud")
        elif topic == "støj" and g:
            level = "højt" if g["noise_db"] >= 58 else "moderat" if g["noise_db"] >= 50 else "lavt"
            answers.append(f"Vejstøjen ved adressen er ca. {g['noise_db']} dB, hvilket er {level}.")
            sources.append("DinGeo: støj")
        elif topic == "familie" and g:
            answers.append(f"Der er {g['school_m']} m til nærmeste skole og {g['green_area_m']} m til nærmeste grønne område.")
            sources.append("DinGeo: nabolag")
        elif topic == "transport" and g:
            answers.append(f"Der er {g['station_m']} m til nærmeste station og {g['grocery_m']} m til dagligvarer.")
            sources.append("DinGeo: nabolag")
        elif topic == "energi":
            answers.append(f"Boligen har energimærke {p['energy_label'] or 'ukendt'} og er opført i {p['built_year']}.")
            sources.append("Boliga.dk / BBR: energimærke og byggeår")
        elif topic == "tryghed" and g:
            answers.append(f"Indbrudsindekset er {g['burglary_index']} (100 = landsgennemsnit).")
            sources.append("DinGeo: tryghed")
        elif topic == "radon" and g:
            answers.append(f"Radonrisikoen er {g['radon_risk']}.")
            sources.append("DinGeo: radon")
        elif topic == "auktion":
            answers.append(f"Der er {len(ctx['auctions'])} kommende tvangsauktion(er) i {p['postcode']}: "
                           + ", ".join(f"{a['address']} ({a['auction_date']})" for a in ctx["auctions"])
                           if ctx["auctions"] else f"Der er ingen kommende tvangsauktioner i {p['postcode']}.")
            sources.append("Tvangsauktioner.dk")

    if not answers:
        return ("Det kan jeg desværre ikke svare på ud fra boligens data. Prøv at spørge om pris, liggetid, "
                "oversvømmelse, støj, skoler, transport, energi eller tryghed. Her er et resumé: "
                + ctx["ai_summary"]), ["Insight Hub-resumé"]
    return " ".join(answers), sorted(set(sources))


# ---------------------------------------------------------------- CRUD
register_crud(app, "properties", "property",
              fields=["address", "postcode", "city", "property_type", "size_m2", "rooms", "built_year",
                      "energy_label", "list_price", "listed_date", "ai_valuation", "sales_channel"],
              required=["address", "postcode", "city", "property_type", "size_m2", "list_price", "listed_date"])
register_crud(app, "geo-data", "geo_data",
              fields=["property_id", "flood_risk", "cloudburst_risk", "radon_risk", "noise_db", "school_m",
                      "station_m", "grocery_m", "green_area_m", "burglary_index", "broadband_mbit"],
              required=["property_id", "flood_risk", "cloudburst_risk", "radon_risk"])
register_crud(app, "users", "user", fields=["name", "email"], required=["name", "email"])


@app.get("/api/properties/search")
def search_properties():
    """Søg boliger: ?q=&max_price=&min_size=&property_type="""
    args = request.args
    sql, params = "SELECT id FROM property WHERE 1 = 1", []
    if args.get("q"):
        sql += " AND (address LIKE ? OR city LIKE ? OR postcode = ?)"
        params += [f"%{args['q']}%", f"%{args['q']}%", args["q"]]
    if args.get("max_price"):
        sql += " AND list_price <= ?"
        params.append(args["max_price"])
    if args.get("min_size"):
        sql += " AND size_m2 >= ?"
        params.append(args["min_size"])
    if args.get("property_type"):
        sql += " AND property_type = ?"
        params.append(args["property_type"])
    return jsonify([boliga_data(r["id"]) for r in query_all(sql + " ORDER BY listed_date DESC", params)])


# ---------------------------------------------------------------- Insight Hub (event: BoligValgt → BoligDataAggregeret)
@app.get("/api/properties/<int:property_id>/insight")
def property_insight(property_id):
    """Samlet data for boligen: Boliga.dk, marked, DinGeo, tvangsauktioner og AI-resumé."""
    return jsonify(insight(property_id))


# ---------------------------------------------------------------- AI-dialog (AISpoergsmaalStillet → AISvarGenereret → SamtaleGemt)
@app.post("/api/properties/<int:property_id>/ask")
def ask(property_id):
    """Stil et spørgsmål til AI-sparringspartneren. Svar og kilder logges."""
    data = json_body()
    require(data, "user_id", "question")
    get_or_404("user", data["user_id"], "Bruger")
    ctx = insight(property_id)
    answer, sources = answer_question(ctx, data["question"])

    with transaction() as db:
        conv = db.execute("SELECT id FROM conversation WHERE user_id = ? AND property_id = ?",
                          (data["user_id"], property_id)).fetchone()
        conv_id = conv[0] if conv else db.execute(
            "INSERT INTO conversation (user_id, property_id, started_at) VALUES (?, ?, ?)",
            (data["user_id"], property_id, now())).lastrowid
        db.execute("INSERT INTO message (conversation_id, role, text, created_at) VALUES (?, 'bruger', ?, ?)",
                   (conv_id, data["question"], now()))
        db.execute("INSERT INTO message (conversation_id, role, text, sources, created_at) VALUES (?, 'ai', ?, ?, ?)",
                   (conv_id, answer, "; ".join(sources), now()))
    return jsonify(question=data["question"], answer=answer, sources=sources, conversation_id=conv_id), 201


@app.get("/api/conversations")
def conversations():
    """Gemt samtale for bruger og bolig: ?user_id=1&property_id=1"""
    require(request.args, "user_id", "property_id")
    conv = query_one("SELECT * FROM conversation WHERE user_id = ? AND property_id = ?",
                     (request.args["user_id"], request.args["property_id"]))
    messages = query_all("SELECT * FROM message WHERE conversation_id = ? ORDER BY id", (conv["id"],)) if conv else []
    return jsonify(conversation=conv, messages=messages)


# ---------------------------------------------------------------- Gem og sammenlign (FK6)
@app.get("/api/users/<int:user_id>/saved")
def saved(user_id):
    """Brugerens gemte boliger."""
    get_or_404("user", user_id, "Bruger")
    rows = query_all("SELECT * FROM saved_property WHERE user_id = ? ORDER BY saved_at DESC", (user_id,))
    return jsonify([{**r, "property": boliga_data(r["property_id"])} for r in rows])


@app.post("/api/users/<int:user_id>/saved")
def save_property(user_id):
    """Gem en bolig."""
    data = json_body()
    require(data, "property_id")
    get_or_404("user", user_id, "Bruger")
    get_or_404("property", data["property_id"], "Bolig")
    with transaction() as db:
        db.execute("INSERT INTO saved_property (user_id, property_id, note, saved_at) VALUES (?, ?, ?, ?)",
                   (user_id, data["property_id"], data.get("note"), now()))
    return jsonify(saved(user_id).get_json()), 201


@app.delete("/api/users/<int:user_id>/saved/<int:property_id>")
def unsave_property(user_id, property_id):
    """Fjern en gemt bolig."""
    with transaction() as db:
        db.execute("DELETE FROM saved_property WHERE user_id = ? AND property_id = ?", (user_id, property_id))
    return "", 204


@app.get("/api/compare")
def compare():
    """Sammenlign 2–4 boliger: ?ids=1,5"""
    ids = [int(i) for i in request.args.get("ids", "").split(",") if i.strip()]
    if not 2 <= len(ids) <= 4:
        raise ApiError("Vælg mellem 2 og 4 boliger at sammenligne")
    result = []
    for pid in ids:
        ctx = insight(pid)
        result.append({"property": ctx["property"], "dingeo": ctx["dingeo"],
                       "area_avg_price_per_m2": ctx["market"]["avg_price_per_m2"], "ai_summary": ctx["ai_summary"]})
    return jsonify(result)


if __name__ == "__main__":
    init_db()
    run(app, PORT)
