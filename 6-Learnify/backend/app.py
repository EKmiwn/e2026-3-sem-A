"""Learnify – elevevaluering (Læringsrum 2.0). Flask API (logiklag).

Kravgrundlag: ../Kravspecifikation.md
Kør:  pip install -r requirements.txt  &&  python app.py  →  http://localhost:5106
"""
import os
from datetime import date

from flask import jsonify, request

from core import ApiError, create_app, get_or_404, json_body, now, register_crud, require, run
from database import init_db, query_all, query_one, transaction

PORT = int(os.environ.get("PORT", 5106))
app = create_app(__name__, "Learnify")

CATEGORIES = ["trivsel", "læring", "møbler", "miljø"]
MIN_RESPONDENTS = 3     # færre svar vises ikke, så den enkelte elev ikke kan genkendes
FEEDBACK = {
    "trivsel": "Tal med din lærer eller en voksen, du er tryg ved, hvis du ikke har det godt.",
    "læring": "Sig til, hvis opgaverne er uklare – det hjælper både dig og klassen.",
    "møbler": "Dit svar om møbler bruges til at forbedre indretningen af klasselokalet.",
    "miljø": "Prøv høreværn eller et stillerum, når der er meget larm.",
}


def current_period():
    year, week, _ = date.today().isocalendar()
    return f"{year}-W{week:02d}"


def summarise(rows):
    """Gennemsnit og procentfordeling for en liste af svarværdier (1–5)."""
    values = [r["value"] for r in rows]
    if not values:
        return {"answers": 0, "average": None, "positive_pct": None, "negative_pct": None, "distribution": {}}
    n = len(values)
    return {
        "answers": n,
        "average": round(sum(values) / n, 2),
        "positive_pct": round(100 * sum(v >= 4 for v in values) / n),
        "negative_pct": round(100 * sum(v <= 2 for v in values) / n),
        "distribution": {str(k): round(100 * values.count(k) / n) for k in range(1, 6)},
    }


def reportable_periods(rows):
    """Perioder med nok besvarelser til at kunne vises anonymt."""
    students = {}
    for r in rows:
        students.setdefault(r["period"], set()).add(r["student_id"])
    return sorted(p for p, s in students.items() if len(s) >= MIN_RESPONDENTS)


ANSWER_SQL = """
    SELECT a.value, q.id AS question_id, q.text, q.category, r.period, r.student_id, s.class_id
    FROM answer a
    JOIN response r ON r.id = a.response_id
    JOIN question q ON q.id = a.question_id
    JOIN student s ON s.id = r.student_id
"""


# ---------------------------------------------------------------- CRUD
register_crud(app, "schools", "school", fields=["name"], required=["name"])
register_crud(app, "classes", "class", fields=["school_id", "name", "grade"], required=["school_id", "name", "grade"],
              order_by="grade, name")
register_crud(app, "students", "student", fields=["class_id", "name", "username"],
              required=["class_id", "name", "username"], order_by="class_id, name")
register_crud(app, "teachers", "teacher", fields=["school_id", "name", "username", "role"],
              required=["school_id", "name", "username"])
register_crud(app, "questions", "question", fields=["text", "category", "active"], required=["text", "category"])


# ---------------------------------------------------------------- Login (simpelt – kun brugernavn i prototypen)
@app.post("/api/login")
def login():
    """Log ind med brugernavn – returnerer rolle (elev, lærer, administrator)."""
    data = json_body()
    require(data, "username")
    username = data["username"].strip().lower()
    student = query_one("""SELECT s.*, c.name AS class_name FROM student s JOIN class c ON c.id = s.class_id
                           WHERE s.username = ?""", (username,))
    if student:
        return jsonify(role="elev", user=student)
    teacher = query_one("SELECT * FROM teacher WHERE username = ?", (username,))
    if teacher:
        return jsonify(role=teacher["role"], user=teacher)
    raise ApiError(f"Brugernavnet '{username}' findes ikke", 401)


# ---------------------------------------------------------------- Elev: besvar spørgsmål
@app.get("/api/survey")
def survey():
    """Aktive spørgsmål og om eleven allerede har svaret i denne uge."""
    student_id = request.args.get("student_id")
    answered = student_id and query_one("SELECT id FROM response WHERE student_id = ? AND period = ?",
                                        (student_id, current_period()))
    return jsonify(period=current_period(), already_answered=bool(answered),
                   questions=query_all("SELECT * FROM question WHERE active = 1 ORDER BY category, id"))


@app.post("/api/responses")
def submit_response():
    """Elevens ugentlige besvarelse. Returnerer personlig feedback."""
    data = json_body()
    require(data, "student_id", "answers")
    student = get_or_404("student", data["student_id"], "Elev")
    period = current_period()
    if query_one("SELECT id FROM response WHERE student_id = ? AND period = ?", (student["id"], period)):
        raise ApiError(f"Du har allerede svaret i uge {period[-2:]}. Du kan svare igen i næste uge.", 409)

    active = {q["id"]: q for q in query_all("SELECT * FROM question WHERE active = 1")}
    answers = {int(a["question_id"]): int(a["value"]) for a in data["answers"]}
    missing = [q["text"] for qid, q in active.items() if qid not in answers]
    if missing:
        raise ApiError(f"Besvar venligst alle spørgsmål ({len(missing)} mangler)")
    if any(not 1 <= v <= 5 for v in answers.values()):
        raise ApiError("Svar skal være mellem 1 og 5")

    with transaction() as db:
        cur = db.execute("INSERT INTO response (student_id, period, submitted_at, comment) VALUES (?, ?, ?, ?)",
                         (student["id"], period, now(), data.get("comment") or None))
        for qid, value in answers.items():
            if qid in active:
                db.execute("INSERT INTO answer (response_id, question_id, value) VALUES (?, ?, ?)",
                           (cur.lastrowid, qid, value))

    # Personlig feedback: laveste kategori får et konkret forslag
    by_category = {}
    for qid, value in answers.items():
        if qid in active:
            by_category.setdefault(active[qid]["category"], []).append(value)
    averages = {c: round(sum(v) / len(v), 1) for c, v in by_category.items()}
    lowest = min(averages, key=averages.get)
    return jsonify(
        response_id=cur.lastrowid, period=period, your_averages=averages,
        feedback="Tak for dine svar! Din lærer ser kun resultater for hele klassen – ikke dine enkelte svar.",
        suggestion=FEEDBACK[lowest] if averages[lowest] < 3.5 else "Godt gået – det lyder som en god uge.",
    ), 201


@app.get("/api/students/<int:student_id>/history")
def student_history(student_id):
    """Elevens egen udvikling over tid pr. kategori."""
    get_or_404("student", student_id, "Elev")
    rows = query_all(ANSWER_SQL + " WHERE r.student_id = ? ORDER BY r.period", (student_id,))
    periods = sorted({r["period"] for r in rows})
    return jsonify(periods=periods, categories={
        c: [summarise([r for r in rows if r["period"] == p and r["category"] == c])["average"] for p in periods]
        for c in CATEGORIES})


# ---------------------------------------------------------------- Lærer: samlede resultater
@app.get("/api/results")
def results():
    """Samlet resultat for en klasse (eller hele skolen) i en periode: gennemsnit og procenttal."""
    class_id, period = request.args.get("class_id"), request.args.get("period")
    sql, params = ANSWER_SQL + (" WHERE s.class_id = ?" if class_id else ""), [class_id] if class_id else []
    all_rows = query_all(sql, params)
    periods = reportable_periods(all_rows)
    period = period or (periods[-1] if periods else None)
    rows = [r for r in all_rows if r["period"] == period]
    respondents = len({r["student_id"] for r in rows})
    if respondents < MIN_RESPONDENTS:
        return jsonify(period=period, respondents=respondents, hidden=True, periods=periods,
                       message=f"Der vises først resultater, når mindst {MIN_RESPONDENTS} elever har svaret.")
    questions = query_all("SELECT * FROM question ORDER BY category, id")
    comments = query_all("""SELECT r.comment FROM response r JOIN student s ON s.id = r.student_id
                            WHERE r.comment IS NOT NULL AND r.period = ?""" + (" AND s.class_id = ?" if class_id else ""),
                         [period] + ([class_id] if class_id else []))
    return jsonify(
        period=period,
        periods=periods,
        hidden=False,
        respondents=respondents,
        overall=summarise(rows),
        categories={c: summarise([r for r in rows if r["category"] == c]) for c in CATEGORIES},
        questions=[{**q, **summarise([r for r in rows if r["question_id"] == q["id"]])} for q in questions],
        comments=[c["comment"] for c in comments],   # anonyme – uden elevnavn
    )


@app.get("/api/results/trend")
def trend():
    """Sammenlign svar over tid: gennemsnit og andel positive svar pr. kategori pr. uge."""
    class_id = request.args.get("class_id")
    rows = query_all(ANSWER_SQL + (" WHERE s.class_id = ?" if class_id else "") + " ORDER BY r.period",
                     (class_id,) if class_id else ())
    periods = reportable_periods(rows)
    series = {c: [summarise([r for r in rows if r["period"] == p and r["category"] == c]) for p in periods]
              for c in CATEGORIES}
    changes = {c: (round(s[-1]["average"] - s[0]["average"], 2) if len(s) > 1 and s[0]["average"] else None)
               for c, s in series.items()}
    return jsonify(periods=periods, series=series, change_since_first=changes)


@app.get("/api/overview")
def overview():
    """Virksomheds-/skolevisning (Læringsrum 2.0): alle klasser med seneste resultat og udvikling."""
    classes = query_all("SELECT * FROM class ORDER BY grade, name")
    result = []
    for c in classes:
        rows = query_all(ANSWER_SQL + " WHERE s.class_id = ? ORDER BY r.period", (c["id"],))
        periods = reportable_periods(rows)
        latest = [r for r in rows if periods and r["period"] == periods[-1]]
        first = [r for r in rows if periods and r["period"] == periods[0]]
        result.append({**c, "latest_period": periods[-1] if periods else None,
                       "students": query_one("SELECT COUNT(*) AS n FROM student WHERE class_id = ?", (c["id"],))["n"],
                       "latest": {cat: summarise([r for r in latest if r["category"] == cat])["average"]
                                  for cat in CATEGORIES},
                       "first": {cat: summarise([r for r in first if r["category"] == cat])["average"]
                                 for cat in CATEGORIES}})
    return jsonify(result)


if __name__ == "__main__":
    init_db()
    run(app, PORT)
