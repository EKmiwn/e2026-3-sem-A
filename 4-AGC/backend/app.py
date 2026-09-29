"""AGC Biologics – informationshub for QC. Flask API (logiklag).

Kravgrundlag: ../Kravspecifikation.md
Kør:  pip install -r requirements.txt  &&  python app.py  →  http://localhost:5104

Testbrugeren vælges i frontenden og sendes i headeren X-User-Id (simuleret login).
"""
import json
import os
import re

from flask import jsonify, request

from core import ApiError, create_app, get_or_404, json_body, now, register_crud, require, run
from database import init_db, query_all, query_one, transaction

PORT = int(os.environ.get("PORT", 5104))
app = create_app(__name__, "AGC Informationshub")


# ---------------------------------------------------------------- Adgang (F01, BR3, BR7)
def current_user():
    user_id = request.headers.get("X-User-Id")
    user = user_id and query_one("SELECT * FROM user WHERE id = ? AND active = 1", (user_id,))
    if not user:
        raise ApiError("Log ind som en testbruger (header X-User-Id mangler eller er ugyldig)", 401)
    return user


def require_role(user, *roles):
    if user["role"] not in roles:
        raise ApiError(f"Rollen '{user['role']}' har ikke adgang til denne handling", 403)


def category_permissions(user_id):
    rows = query_all("SELECT category_id, permission FROM category_access WHERE user_id = ?", (user_id,))
    return {r["category_id"]: r["permission"] for r in rows}


def can_view(user, info):
    perms = category_permissions(user["id"])
    if user["role"] == "leder":
        return info["owner_id"] == user["id"] or info["category_id"] in perms
    if user["role"] == "medarbejder":
        # Medarbejdere ser kun godkendt information. Delte snapshots ligger i /api/shared-with-me.
        return info["status"] == "GODKENDT" and info["category_id"] in perms
    return False    # administratorrollen giver ikke adgang til kildetekst


def can_edit(user, info):
    if user["role"] != "leder":
        return False
    if info["category_id"] is None:
        return info["owner_id"] == user["id"]
    return category_permissions(user["id"]).get(info["category_id"]) == "redigér"


def log_event(db, type_, details, source_id=None, info_id=None, actor_id=None):
    db.execute("INSERT INTO event (source_id, info_id, actor_id, type, occurred_at, details) VALUES (?, ?, ?, ?, ?, ?)",
               (source_id, info_id, actor_id, type_, now(), details))


# ---------------------------------------------------------------- 2.0 Filtrér og strukturér (F03, F04, F05)
def normalise(text):
    return re.sub(r"\s+", " ", (text or "").lower())


def score_categories(text):
    """2.3.1–2.3.2: antal forskellige nøgleord pr. kategori, der findes i teksten."""
    content = normalise(text)
    candidates = []
    for category in query_all("SELECT * FROM category WHERE active = 1"):
        hits = [kw.strip() for kw in category["keywords"].split(",") if kw.strip() and kw.strip() in content]
        if hits:
            candidates.append({"category_id": category["id"], "name": category["name"], "score": len(hits),
                               "keywords": hits})
    return sorted(candidates, key=lambda c: c["score"], reverse=True)


def suggest_category(candidates):
    """2.3.3: kun et forslag, hvis højeste score er > 0 og entydig. Ellers Uklassificeret (BR6)."""
    if not candidates:
        return None, "Ingen nøgleord matchede – markeret til manuel vurdering"
    if len(candidates) > 1 and candidates[0]["score"] == candidates[1]["score"]:
        tied = " og ".join(c["name"] for c in candidates if c["score"] == candidates[0]["score"])
        return None, f"Tvetydigt match ({tied}) – Uklassificeret"
    best = candidates[0]
    return best["category_id"], f"{best['name']}: {', '.join(best['keywords'])} (score {best['score']})"


def make_summary(text, limit=180):
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    summary = " ".join(sentences[:2])
    return summary if len(summary) <= limit else summary[:limit].rsplit(" ", 1)[0] + " …"


def pick_owner(category_id):
    if category_id:
        owner = query_one("""SELECT u.id FROM user u JOIN category_access a ON a.user_id = u.id
                             WHERE u.role = 'leder' AND a.category_id = ? AND a.permission = 'redigér'
                             ORDER BY u.id LIMIT 1""", (category_id,))
        if owner:
            return owner["id"]
    return query_one("SELECT id FROM user WHERE role = 'leder' ORDER BY id LIMIT 1")["id"]


def ingest(post, manual=False, actor_id=None):
    """1.0 Modtag kildedata → 2.0 Filtrér og strukturér. BR1: resultatet er altid et udkast."""
    require(post, "system", "title", "text")
    if post.get("external_id") and query_one("SELECT id FROM source WHERE system = ? AND external_id = ?",
                                             (post["system"], post["external_id"])):
        raise ApiError(f"{post['system']}-post {post['external_id']} er allerede modtaget (ingen dublet)", 409)

    candidates = score_categories(f"{post['title']} {post['text']}")
    relevant = bool(candidates) or manual
    category_id, basis = suggest_category(candidates)

    with transaction() as db:
        cur = db.execute(
            "INSERT INTO source (system, external_id, sender, channel, title, text, received_at, processing_status)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (post["system"], post.get("external_id"), post.get("sender"), post.get("channel"), post["title"],
             post["text"], now(), "RELEVANT" if relevant else "FRAVALGT"))
        source_id = cur.lastrowid
        log_event(db, "E01 KildedataModtaget", f"{post['system']} {post.get('external_id') or ''}".strip(),
                  source_id=source_id, actor_id=actor_id)
        if not relevant:
            log_event(db, "Fravalgt", "Ingen relevansregel matchede", source_id=source_id)
            return {"source_id": source_id, "relevant": False, "info": None, "candidates": []}

        log_event(db, "E02 RelevantInformationIdentificeret", basis, source_id=source_id)
        owner_id = actor_id if manual and actor_id else pick_owner(category_id)
        cur = db.execute(
            "INSERT INTO info (source_id, owner_id, title, summary, category_id, match_basis) VALUES (?, ?, ?, ?, ?, ?)",
            (source_id, owner_id, post["title"], make_summary(post["text"]), category_id, basis))
        log_event(db, "E03 UdkastOprettet", "Lagt i Til kontrol", source_id=source_id, info_id=cur.lastrowid)
    return {"source_id": source_id, "relevant": True, "info": get_info(cur.lastrowid), "candidates": candidates}


INFO_SQL = """
    SELECT i.*, COALESCE(c.name, 'Uklassificeret') AS category_name,
           s.system, s.external_id, s.sender, s.channel, s.received_at,
           o.name AS owner_name, a.name AS approver_name,
           (SELECT COUNT(*) FROM share WHERE info_id = i.id) AS share_count
    FROM info i
    JOIN source s ON s.id = i.source_id
    JOIN user o ON o.id = i.owner_id
    LEFT JOIN category c ON c.id = i.category_id
    LEFT JOIN user a ON a.id = i.approver_id
"""


def get_info(info_id):
    info = query_one(INFO_SQL + " WHERE i.id = ?", (info_id,))
    if info is None:
        raise ApiError(f"Informationspost {info_id} findes ikke", 404)
    return info


def get_visible_info(user, info_id):
    info = get_info(info_id)
    if not can_view(user, info):
        raise ApiError("Du har ikke adgang til denne informationspost", 403)
    return info


def check_version(info, data):
    require(data, "expected_version")
    if int(data["expected_version"]) != info["version"]:
        raise ApiError(f"Posten er ændret af en anden (version {info['version']}). Genindlæs og prøv igen.", 409)


# ---------------------------------------------------------------- CRUD (administration, F13)
register_crud(app, "users", "user", fields=["name", "login", "role", "active"], required=["name", "login", "role"])
register_crud(app, "categories", "category", fields=["name", "keywords", "active"], required=["name", "keywords"])
register_crud(app, "category-access", "category_access", fields=["user_id", "category_id", "permission"],
              required=["user_id", "category_id"])
register_crud(app, "feed", "test_feed", fields=["system", "delivered"], read_only=True)


@app.get("/api/me")
def me():
    """Den indloggede testbruger og dennes kategoriadgang."""
    user = current_user()
    return jsonify({**user, "categories": category_permissions(user["id"])})


# ---------------------------------------------------------------- 1.0 Connectors (F02, F10)
@app.post("/api/connectors/<system>")
def connector(system):
    """Simuleret Outlook-/Teams-connector: modtager én kildepost som JSON."""
    systems = {"outlook": "Outlook", "teams": "Teams"}
    if system not in systems:
        raise ApiError("Ukendt kildesystem – brug outlook eller teams", 404)
    post = {**json_body(), "system": systems[system]}
    require(post, "external_id")
    return jsonify(ingest(post)), 201


@app.post("/api/connectors/simulate")
def simulate_feed():
    """Afleverer næste fiktive post fra testfeedet gennem connectoren."""
    item = query_one("SELECT * FROM test_feed WHERE delivered = 0 ORDER BY id LIMIT 1")
    if item is None:
        raise ApiError("Testfeedet er tomt – alle poster er modtaget", 404)
    with transaction() as db:
        db.execute("UPDATE test_feed SET delivered = 1 WHERE id = ?", (item["id"],))
    try:
        result = ingest(item)
    except ApiError as err:
        return jsonify(feed_item=item, relevant=False, duplicate=True, message=err.message), 200
    return jsonify(feed_item=item, **result), 201


@app.post("/api/notes")
def manual_note():
    """F10: manuel note som supplement – gennemgår samme strukturering og kontrol."""
    user = current_user()
    require_role(user, "leder")
    data = json_body()
    require(data, "title", "text")
    return jsonify(ingest({"system": "Manuel", "title": data["title"], "text": data["text"],
                           "sender": user["name"]}, manual=True, actor_id=user["id"])), 201


# ---------------------------------------------------------------- 3.0 Kontrollér, godkend og del
@app.get("/api/review-queue")
def review_queue():
    """Til kontrol: udkast, som lederen må se."""
    user = current_user()
    require_role(user, "leder")
    rows = query_all(INFO_SQL + " WHERE i.status = 'UDKAST' ORDER BY s.received_at DESC")
    return jsonify([r for r in rows if can_view(user, r)])


@app.get("/api/info/<int:info_id>")
def info_detail(info_id):
    """Informationspost med originalkilde, delinger og hændelser."""
    user = current_user()
    info = get_visible_info(user, info_id)
    source = query_one("SELECT * FROM source WHERE id = ?", (info["source_id"],))
    shares = query_all("""SELECT s.id, s.version, s.shared_at, u.name AS sender_name,
                                 GROUP_CONCAT(ru.name, ', ') AS recipients
                          FROM share s JOIN user u ON u.id = s.sender_id
                          JOIN share_recipient r ON r.share_id = s.id JOIN user ru ON ru.id = r.user_id
                          WHERE s.info_id = ? GROUP BY s.id ORDER BY s.id DESC""", (info_id,))
    history = query_all("""SELECT e.*, u.name AS actor_name FROM event e LEFT JOIN user u ON u.id = e.actor_id
                           WHERE e.info_id = ? OR e.source_id = ? ORDER BY e.id""", (info_id, info["source_id"]))
    return jsonify(info=info, source=source, shares=shares, history=history, can_edit=can_edit(user, info))


@app.put("/api/info/<int:info_id>")
def edit_info(info_id):
    """F06: rettelse øger versionen og ophæver tidligere godkendelse. Originalkilden ændres ikke."""
    user = current_user()
    info = get_visible_info(user, info_id)
    if not can_edit(user, info):
        raise ApiError("Du har ikke redigeringsret til denne post", 403)
    data = json_body()
    check_version(info, data)
    changes = {k: data[k] for k in ("title", "summary", "category_id") if k in data}
    if not changes:
        raise ApiError("Intet at rette")
    if "category_id" in changes and changes["category_id"] not in (None, ""):
        get_or_404("category", changes["category_id"], "Kategori")
    changes["category_id"] = changes.get("category_id", info["category_id"]) or None
    with transaction() as db:
        db.execute("""UPDATE info SET title = ?, summary = ?, category_id = ?, version = version + 1,
                      status = 'UDKAST', approver_id = NULL, approved_at = NULL WHERE id = ?""",
                   (changes.get("title", info["title"]), changes.get("summary", info["summary"]),
                    changes["category_id"], info_id))
        log_event(db, "E04 UdkastRettet", f"Version {info['version'] + 1}", info_id=info_id, actor_id=user["id"])
    return jsonify(get_info(info_id))


@app.post("/api/info/<int:info_id>/approve")
def approve_info(info_id):
    """Godkend den aktuelle version (kræver expected_version)."""
    user = current_user()
    info = get_visible_info(user, info_id)
    if not can_edit(user, info):
        raise ApiError("Kun en leder med ejer- eller redigeringsret må godkende (BR3)", 403)
    check_version(info, json_body())
    if info["category_id"] is None:
        raise ApiError("Vælg en kategori, før posten godkendes")
    with transaction() as db:
        db.execute("UPDATE info SET status = 'GODKENDT', approver_id = ?, approved_at = ? WHERE id = ?",
                   (user["id"], now(), info_id))
        log_event(db, "E05 InformationGodkendt", f"Version {info['version']}", info_id=info_id, actor_id=user["id"])
    return jsonify(get_info(info_id))


@app.post("/api/info/<int:info_id>/discard")
def discard_info(info_id):
    """Fravælg en post, så den ikke vises som normal information."""
    user = current_user()
    info = get_visible_info(user, info_id)
    if not can_edit(user, info):
        raise ApiError("Du har ikke redigeringsret til denne post", 403)
    with transaction() as db:
        db.execute("UPDATE info SET status = 'FRAVALGT' WHERE id = ?", (info_id,))
        log_event(db, "Fravalgt", "Fravalgt af leder", info_id=info_id, actor_id=user["id"])
    return jsonify(get_info(info_id))


@app.post("/api/info/<int:info_id>/share")
def share_info(info_id):
    """F07, BR4, BR5: kun godkendt, aktuel version. Én ugyldig modtager afviser hele delingen."""
    user = current_user()
    info = get_visible_info(user, info_id)
    if not can_edit(user, info):
        raise ApiError("Du har ikke ret til at dele denne post", 403)
    data = json_body()
    check_version(info, data)
    if info["status"] != "GODKENDT":
        raise ApiError("Kun godkendt information kan deles – godkend den aktuelle version først")
    recipient_ids = [int(r) for r in data.get("recipient_ids") or []]
    if not recipient_ids:
        raise ApiError("Vælg mindst én modtager")
    invalid = [query_one("SELECT name FROM user WHERE id = ?", (rid,)) or {"name": f"#{rid}"}
               for rid in recipient_ids if info["category_id"] not in category_permissions(rid)]
    if invalid:
        raise ApiError("Delingen er afvist. Ingen adgang til kategorien for: "
                       + ", ".join(u["name"] for u in invalid), 403)

    snapshot = json.dumps({k: info[k] for k in ("title", "summary", "category_name", "system", "external_id",
                                                  "received_at", "version")}, ensure_ascii=False)
    with transaction() as db:
        cur = db.execute("INSERT INTO share (info_id, sender_id, version, snapshot, shared_at) VALUES (?, ?, ?, ?, ?)",
                         (info_id, user["id"], info["version"], snapshot, now()))
        for rid in recipient_ids:
            db.execute("INSERT INTO share_recipient (share_id, user_id) VALUES (?, ?)", (cur.lastrowid, rid))
        log_event(db, "E06 InformationDelt", f"Version {info['version']} delt med {len(recipient_ids)} modtager(e)",
                  info_id=info_id, actor_id=user["id"])
    return jsonify(share_id=cur.lastrowid, recipients=len(recipient_ids)), 201


@app.get("/api/info/<int:info_id>/recipients")
def possible_recipients(info_id):
    """Medarbejdere, der har adgang til postens kategori."""
    user = current_user()
    info = get_visible_info(user, info_id)
    return jsonify(query_all("""SELECT u.id, u.name FROM user u JOIN category_access a ON a.user_id = u.id
                                WHERE a.category_id = ? AND u.role = 'medarbejder' AND u.active = 1
                                ORDER BY u.name""", (info["category_id"],)))


# ---------------------------------------------------------------- 4.0 Find og vis (F08, F09, F14)
@app.get("/api/info")
def search_info():
    """Søg i tilladt information: ?q=&category_id=&system=&status="""
    user = current_user()
    require_role(user, "leder", "medarbejder")
    sql, params = INFO_SQL + " WHERE i.status != 'FRAVALGT'", []
    if request.args.get("q"):
        sql += " AND (i.title LIKE ? OR i.summary LIKE ?)"
        params += [f"%{request.args['q']}%"] * 2
    for arg, column in (("category_id", "i.category_id"), ("system", "s.system"), ("status", "i.status")):
        if request.args.get(arg):
            sql += f" AND {column} = ?"
            params.append(request.args[arg])
    rows = query_all(sql + " ORDER BY s.received_at DESC", params)
    return jsonify([r for r in rows if can_view(user, r)])


@app.get("/api/shared-with-me")
def shared_with_me():
    """Delinger til den indloggede medarbejder (snapshots)."""
    user = current_user()
    rows = query_all("""SELECT s.id AS share_id, s.info_id, s.version, s.snapshot, s.shared_at, r.read_at,
                               u.name AS sender_name
                        FROM share s JOIN share_recipient r ON r.share_id = s.id JOIN user u ON u.id = s.sender_id
                        WHERE r.user_id = ? ORDER BY s.id DESC""", (user["id"],))
    for r in rows:
        r["snapshot"] = json.loads(r["snapshot"])
    return jsonify(rows)


@app.post("/api/shares/<int:share_id>/read")
def mark_read(share_id):
    """Markér en deling som læst."""
    user = current_user()
    with transaction() as db:
        cur = db.execute("UPDATE share_recipient SET read_at = ? WHERE share_id = ? AND user_id = ? AND read_at IS NULL",
                         (now(), share_id, user["id"]))
    if not cur.rowcount:
        raise ApiError("Delingen findes ikke for dig eller er allerede markeret som læst", 404)
    return jsonify(share_id=share_id, read_at=now())


@app.get("/api/events")
def events():
    """Hændelseslog (leder og administrator)."""
    user = current_user()
    require_role(user, "leder", "administrator")
    return jsonify(query_all("""SELECT e.*, u.name AS actor_name FROM event e LEFT JOIN user u ON u.id = e.actor_id
                                ORDER BY e.id DESC LIMIT 100"""))


def deliver_initial_feed(count=8):
    """Første gang databasen oprettes, modtages de første testposter, så Til kontrol ikke er tom."""
    with app.test_request_context():
        for _ in range(count):
            simulate_feed()


if __name__ == "__main__":
    if init_db():
        deliver_initial_feed()
    run(app, PORT)
