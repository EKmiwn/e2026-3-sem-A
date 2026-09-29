"""Solum A/S – vidensdelings- og fejlfindingsapp. Flask API (logiklag).

Kravgrundlag: ../Kravspecifikation-Vidensdeling-App-Solum-Samlet.md
Kør:  pip install -r requirements.txt  &&  python app.py  →  http://localhost:5105
"""
import os
import re

from flask import jsonify, request

from core import ApiError, create_app, get_or_404, json_body, now, register_crud, require, run
from database import init_db, query_all, transaction

PORT = int(os.environ.get("PORT", 5105))
app = create_app(__name__, "Solum Vidensdeling")

APPROVED_LEVELS = ("godkendt", "ekspert")

ARTICLE_SQL = """
    SELECT a.*, e.name AS author_name, m.name AS machine_name,
           SUM(f.status = 'LØST') AS solved, SUM(f.status = 'ULØST') AS unsolved
    FROM article a
    JOIN employee e ON e.id = a.author_id
    JOIN machine m ON m.id = a.machine_id
    LEFT JOIN fault_log f ON f.article_id = a.id
"""


def with_solve_rate(article):
    solved, unsolved = article["solved"] or 0, article["unsolved"] or 0
    article["solve_rate"] = round(solved / (solved + unsolved), 2) if solved + unsolved else None
    article["steps"] = [s.strip() for s in article["steps"].splitlines() if s.strip()]
    return article


# ---------------------------------------------------------------- 1.3 Match mod vidensartikler
def rank_articles(machine_id, symptom="", employee=None):
    """1.3.1 filtrér på maskine → 1.3.2 søg i tekst/tags → 1.3.3 ranger efter erfaringsniveau og løsningsrate."""
    articles = [with_solve_rate(a) for a in query_all(ARTICLE_SQL + " WHERE a.machine_id = ? GROUP BY a.id",
                                                      (machine_id,))]
    words = [w for w in re.split(r"[\s,]+", symptom.lower()) if len(w) > 2]
    for a in articles:
        haystack = " ".join([a["title"], a["fault_type"], a["tags"] or "", *a["steps"]]).lower()
        a["match_score"] = sum(w in haystack for w in words)
    if words and any(a["match_score"] for a in articles):
        articles = [a for a in articles if a["match_score"]]

    preferred = "grundlæggende" if not employee or employee["experience"] == "nyansat" else "dybdegående"
    articles.sort(key=lambda a: (-a["match_score"], a["level"] != preferred, -(a["solve_rate"] or 0)))
    return articles


def experts_for(machine_id):
    return query_all("""SELECT e.id, e.name, c.level FROM competence c JOIN employee e ON e.id = c.employee_id
                        WHERE c.machine_id = ? AND c.level IN ('godkendt', 'ekspert')
                        ORDER BY c.level = 'ekspert' DESC, e.name""", (machine_id,))


# ---------------------------------------------------------------- CRUD
def validate_article(data, existing):
    """Kun erfarne medarbejdere kan oprette og redigere vidensartikler."""
    author = get_or_404("employee", data["author_id"], "Forfatter")
    if author["experience"] != "erfaren":
        raise ApiError(f"{author['name']} er nyansat – kun erfarne medarbejdere kan skrive vidensartikler.", 403)
    if not str(data["steps"]).strip():
        raise ApiError("En vidensartikel skal have mindst ét løsningstrin.")


register_crud(app, "employees", "employee", fields=["name", "experience", "role"], required=["name"])
register_crud(app, "machines", "machine", fields=["name", "nickname", "location", "type", "icon"],
              required=["name", "location", "type"])
register_crud(app, "competences", "competence", fields=["employee_id", "machine_id", "level", "approved_date"],
              required=["employee_id", "machine_id", "level"])
register_crud(app, "articles", "article",
              fields=["machine_id", "author_id", "fault_type", "title", "steps", "tags", "level", "media_url"],
              required=["machine_id", "author_id", "fault_type", "title", "steps"], validate=validate_article)


# ---------------------------------------------------------------- Maskiner
@app.get("/api/machines/overview")
def machine_overview():
    """Startskærm: maskiner med antal godkendte operatører og sårbarhed ved fravær."""
    machines = query_all("""
        SELECT m.*,
               (SELECT COUNT(*) FROM competence c WHERE c.machine_id = m.id AND c.level IN ('godkendt', 'ekspert'))
                   AS approved_operators,
               (SELECT COUNT(*) FROM article a WHERE a.machine_id = m.id) AS articles,
               (SELECT COUNT(*) FROM fault_log f WHERE f.machine_id = m.id
                    AND f.timestamp >= date('now', '-30 days')) AS faults_30d,
               (SELECT COALESCE(SUM(duration_minutes), 0) FROM fault_log f WHERE f.machine_id = m.id
                    AND f.timestamp >= date('now', '-30 days')) AS downtime_minutes_30d
        FROM machine m ORDER BY m.location, m.name
    """)
    for m in machines:
        m["vulnerable"] = m["approved_operators"] <= 1
    return jsonify(machines)


@app.get("/api/machines/<int:machine_id>/details")
def machine_details(machine_id):
    """Maskineskærm: hyppige fejl (historiske fejlmønstre), kompetente kolleger og guides."""
    machine = get_or_404("machine", machine_id, "Maskine")
    patterns = query_all("""
        SELECT COALESCE(f.fault_type, 'Ukendt') AS fault_type, COUNT(*) AS occurrences,
               ROUND(AVG(f.duration_minutes)) AS avg_minutes, MAX(f.timestamp) AS last_seen,
               SUM(f.status = 'LØST') AS solved
        FROM fault_log f WHERE f.machine_id = ?
        GROUP BY f.fault_type ORDER BY occurrences DESC
    """, (machine_id,))
    return jsonify(machine=machine, fault_patterns=patterns, experts=experts_for(machine_id),
                   articles=rank_articles(machine_id))


# ---------------------------------------------------------------- Fejlfinding (events: FejlRegistreret → GuideVist → FejlLøst/FejlUløst)
@app.get("/api/articles/search")
def search_articles():
    """Søg guides uden at logge en fejl: ?machine_id=1&q=stopper&employee_id=3"""
    require(request.args, "machine_id")
    employee = request.args.get("employee_id") and get_or_404("employee", request.args["employee_id"])
    return jsonify(rank_articles(int(request.args["machine_id"]), request.args.get("q", ""), employee or None))


@app.post("/api/faults")
def register_fault():
    """FejlRegistreret: medarbejder vælger maskine + symptom. Returnerer rangerede guides (GuideVist)."""
    data = json_body()
    require(data, "machine_id", "employee_id", "symptom")
    machine = get_or_404("machine", data["machine_id"], "Maskine")
    employee = get_or_404("employee", data["employee_id"], "Medarbejder")
    with transaction() as db:
        cur = db.execute("INSERT INTO fault_log (machine_id, employee_id, symptom, timestamp) VALUES (?, ?, ?, ?)",
                         (machine["id"], employee["id"], data["symptom"], now()))
    guides = rank_articles(machine["id"], data["symptom"], employee)
    return jsonify(fault=get_or_404("fault_log", cur.lastrowid), guides=guides,
                   no_guide_found=not guides, experts=experts_for(machine["id"])), 201


@app.post("/api/faults/<int:fault_id>/resolve")
def resolve_fault(fault_id):
    """FejlLøst / FejlUløst. Uløst giver en liste over kolleger at eskalere til."""
    fault = get_or_404("fault_log", fault_id, "Fejl")
    if fault["status"] != "ÅBEN":
        raise ApiError("Fejlen er allerede afsluttet.")
    data = json_body()
    require(data, "solved")
    article = data.get("article_id") and get_or_404("article", data["article_id"], "Vidensartikel")
    status = "LØST" if data["solved"] else "ULØST"
    started = fault["timestamp"]
    with transaction() as db:
        db.execute("""UPDATE fault_log SET status = ?, article_id = ?, fault_type = ?, comment = ?,
                      duration_minutes = COALESCE(?, CAST((julianday(?) - julianday(?)) * 1440 AS INTEGER))
                      WHERE id = ?""",
                   (status, article["id"] if article else None, article["fault_type"] if article else "Ukendt",
                    data.get("comment"), data.get("duration_minutes"), now(), started, fault_id))
    return jsonify(fault=get_or_404("fault_log", fault_id),
                   escalate_to=[] if data["solved"] else experts_for(fault["machine_id"]))


@app.get("/api/faults")
def fault_log():
    """Seneste fejl i loggen."""
    return jsonify(query_all("""
        SELECT f.*, m.name AS machine_name, e.name AS employee_name, a.title AS article_title
        FROM fault_log f JOIN machine m ON m.id = f.machine_id JOIN employee e ON e.id = f.employee_id
        LEFT JOIN article a ON a.id = f.article_id
        ORDER BY f.timestamp DESC LIMIT 50
    """))


# ---------------------------------------------------------------- Kompetenceoverblik (driftsledelse)
@app.get("/api/competence-matrix")
def competence_matrix():
    """Kompetenceoverblik: medarbejdere × maskiner."""
    employees = query_all("SELECT * FROM employee ORDER BY name")
    machines = query_all("SELECT * FROM machine ORDER BY location, name")
    cells = {}
    for c in query_all("SELECT * FROM competence"):
        cells.setdefault(str(c["employee_id"]), {})[str(c["machine_id"])] = {"id": c["id"], "level": c["level"]}
    coverage = {str(m["id"]): sum(1 for e in cells.values() if e.get(str(m["id"]), {}).get("level") in APPROVED_LEVELS)
                for m in machines}
    return jsonify(employees=employees, machines=machines, cells=cells, approved_per_machine=coverage)


if __name__ == "__main__":
    init_db()
    run(app, PORT)
