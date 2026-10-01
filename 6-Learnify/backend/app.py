"""Learnify – elevevaluering (Læringsrum 2.0). Flask API (logiklag).

Kravgrundlag: ../Kravspecifikation.md og "Ændringer til vores produkt" (../Ændriger til vores produkt (1).docx)
Kør:  pip install -r requirements.txt  &&  python app.py  →  http://localhost:5106

Login med rolle, e-mail og adgangskode. Den indloggede bruger sendes derefter i headeren X-User-Id
som "rolle:id", fx "elev:6" (simuleret session – ingen tokens i prototypen).
"""
import os
from datetime import date

from flask import jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from core import ApiError, create_app, get_or_404, json_body, now, register_crud, require, run
from database import init_db, query_all, query_one, transaction

PORT = int(os.environ.get("PORT", 5106))
app = create_app(__name__, "Learnify")

CATEGORIES = ["trivsel", "læring", "møbler", "miljø"]          # vurderes 1–5 og vises i procent
STYLES = {"visuel": "Visuel", "auditiv": "Auditiv", "praktisk": "Praktisk"}
MIN_RESPONDENTS = 3     # klassens samlede resultater vises først ved mindst 3 elever
FEEDBACK = {
    "trivsel": "Tal med din lærer eller en voksen, du er tryg ved, hvis du ikke har det godt.",
    "læring": "Sig til, hvis opgaverne er uklare – det hjælper både dig og klassen.",
    "møbler": "Dit svar om møbler bruges til at forbedre indretningen af klasselokalet.",
    "miljø": "Prøv høreværn eller et stillerum, når der er meget larm.",
}
STUDENT_FIELDS = "s.id, s.class_id, s.name, s.username, s.email, s.age, c.name AS class_name, c.grade"


def current_period():
    """Testen tages hver måned."""
    return date.today().strftime("%Y-%m")


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
    """Måneder med nok besvarelser til at kunne vise klassens samlede resultat."""
    students = {}
    for r in rows:
        students.setdefault(r["period"], set()).add(r["student_id"])
    return sorted(p for p, s in students.items() if len(s) >= MIN_RESPONDENTS)


ANSWER_SQL = """
    SELECT a.value, a.note, q.id AS question_id, q.text, q.category, q.style, r.period, r.student_id,
           s.class_id, c.name AS class_name, c.grade
    FROM answer a
    JOIN response r ON r.id = a.response_id
    JOIN question q ON q.id = a.question_id
    JOIN student s ON s.id = r.student_id
    JOIN class c ON c.id = s.class_id
"""


# ---------------------------------------------------------------- Login og adgang
def current_user(*roles):
    """Den indloggede bruger ud fra X-User-Id ("rolle:id"). Afviser andre roller med 403."""
    role, _, user_id = (request.headers.get("X-User-Id") or "").partition(":")
    if role == "elev":
        user = query_one(f"SELECT {STUDENT_FIELDS} FROM student s JOIN class c ON c.id = s.class_id WHERE s.id = ?", (user_id,))
    elif role in ("lærer", "virksomhed"):
        user = query_one("SELECT id, school_id, class_id, name, username, email, role FROM teacher WHERE id = ? AND role = ?",
                         (user_id, role))
    else:
        user = None
    if user is None:
        raise ApiError("Log ind først", 401)
    if roles and role not in roles:
        raise ApiError("Din rolle har ikke adgang til denne side", 403)
    return {**user, "role": role}


def check_student_access(user, student_id):
    """Eleven ser sig selv. Læreren ser elever i sin klasse (eller alle, hvis læreren ikke har en fast klasse)."""
    student = query_one(f"SELECT {STUDENT_FIELDS} FROM student s JOIN class c ON c.id = s.class_id WHERE s.id = ?", (student_id,))
    if student is None:
        raise ApiError(f"Elev med id {student_id} findes ikke", 404)
    if user["role"] == "elev" and user["id"] != student["id"]:
        raise ApiError("Du kan kun se din egen profil", 403)
    if user["role"] == "lærer" and user["class_id"] and user["class_id"] != student["class_id"]:
        raise ApiError("Du kan kun se elever i din egen klasse", 403)
    if user["role"] == "virksomhed":
        raise ApiError("Virksomheden ser kun anonyme besvarelser", 403)
    return student


@app.post("/api/login")
def login():
    """Log ind som elev, lærer eller virksomhed med e-mail og adgangskode."""
    data = json_body()
    require(data, "role", "email", "password")
    email = data["email"].strip().lower()
    if data["role"] == "elev":
        user = query_one(f"SELECT {STUDENT_FIELDS}, s.password_hash FROM student s JOIN class c ON c.id = s.class_id WHERE s.email = ?",
                         (email,))
    elif data["role"] in ("lærer", "virksomhed"):
        user = query_one("SELECT * FROM teacher WHERE email = ? AND role = ?", (email, data["role"]))
    else:
        raise ApiError("Vælg elev, lærer eller virksomhed")
    if user is None or not check_password_hash(user["password_hash"], data["password"]):
        raise ApiError("Forkert e-mail eller adgangskode", 401)
    user.pop("password_hash")
    return jsonify(role=data["role"], user=user)


# ---------------------------------------------------------------- CRUD
@app.after_request
def hide_password_hashes(response):
    """Adgangskoder (hash) sendes aldrig til klienten – heller ikke fra de generiske CRUD-endepunkter."""
    if response.is_json and b"password_hash" in response.get_data():
        def strip(value):
            if isinstance(value, dict):
                return {k: strip(v) for k, v in value.items() if k != "password_hash"}
            return [strip(v) for v in value] if isinstance(value, list) else value
        response.set_data(app.json.dumps(strip(response.get_json())))
    return response


register_crud(app, "schools", "school", fields=["name"], required=["name"])
register_crud(app, "classes", "class", fields=["school_id", "name", "grade"], required=["school_id", "name", "grade"],
              order_by="grade, name")
register_crud(app, "students", "student", fields=["class_id", "name", "username", "email", "age"],
              required=["class_id", "name", "username", "email"],
              defaults={"password_hash": lambda: generate_password_hash("learnify")}, order_by="class_id, name")
register_crud(app, "questions", "question", fields=["text", "category", "style", "active"], required=["text", "category"])


# ---------------------------------------------------------------- Elev: månedens spørgeskema
@app.get("/api/survey")
def survey():
    """Månedens aktive spørgsmål, og om eleven allerede har svaret."""
    user = current_user("elev")
    answered = query_one("SELECT id FROM response WHERE student_id = ? AND period = ?", (user["id"], current_period()))
    return jsonify(period=current_period(), already_answered=bool(answered),
                   questions=query_all("""SELECT * FROM question WHERE active = 1
                                          ORDER BY CASE category WHEN 'trivsel' THEN 1 WHEN 'læring' THEN 2 WHEN 'møbler' THEN 3
                                                   WHEN 'miljø' THEN 4 ELSE 5 END, id"""))


@app.post("/api/responses")
def submit_response():
    """Elevens månedlige besvarelse med uddybende tekst pr. svar, ønsker og holdning til klasselokalet."""
    user = current_user("elev")
    data = json_body()
    require(data, "answers")
    period = current_period()
    if query_one("SELECT id FROM response WHERE student_id = ? AND period = ?", (user["id"], period)):
        raise ApiError("Du har allerede svaret i denne måned. Du kan svare igen næste måned.", 409)

    active = {q["id"]: q for q in query_all("SELECT * FROM question WHERE active = 1")}
    answers = {int(a["question_id"]): a for a in data["answers"]}
    missing = [q["text"] for qid, q in active.items() if qid not in answers]
    if missing:
        raise ApiError(f"Besvar venligst alle spørgsmål ({len(missing)} mangler)")
    if any(not 1 <= int(a["value"]) <= 5 for a in answers.values()):
        raise ApiError("Svar skal være mellem 1 og 5")

    def text(value):
        return (value or "").strip()[:500] or None

    with transaction() as db:
        response_id = db.execute(
            "INSERT INTO response (student_id, period, submitted_at, comment, wishes, classroom) VALUES (?, ?, ?, ?, ?, ?)",
            (user["id"], period, now(), text(data.get("comment")), text(data.get("wishes")), text(data.get("classroom")))).lastrowid
        for qid, a in answers.items():
            if qid in active:
                db.execute("INSERT INTO answer (response_id, question_id, value, note) VALUES (?, ?, ?, ?)",
                           (response_id, qid, int(a["value"]), text(a.get("note"))))

    profile = student_profile(user)
    latest = profile["months"][-1]["categories"] if profile["months"] else {}
    rated = {c: v["average"] for c, v in latest.items() if v["average"] is not None}
    lowest = min(rated, key=rated.get) if rated else None
    return jsonify(
        response_id=response_id, period=period, profile=profile,
        feedback="Tak for dine svar! Din lærer kan se dine svar og bruge dem til at hjælpe dig bedst muligt.",
        suggestion=FEEDBACK[lowest] if lowest and rated[lowest] < 3.5 else "Godt gået – det lyder som en god måned.",
    ), 201


# ---------------------------------------------------------------- Personlig elevprofil
def student_profile(student):
    """Elevprofil: grundoplysninger, læringsstil, arbejdstempo, trivselsscore (1–10), ønsker og svar i procent pr. måned."""
    rows = query_all(ANSWER_SQL + " WHERE r.student_id = ? ORDER BY r.period, q.id", (student["id"],))
    responses = query_all("SELECT * FROM response WHERE student_id = ? ORDER BY period", (student["id"],))
    months = []
    for r in responses:
        month_rows = [x for x in rows if x["period"] == r["period"]]
        months.append({"period": r["period"],
                       "categories": {c: summarise([x for x in month_rows if x["category"] == c]) for c in CATEGORIES},
                       "overall": summarise([x for x in month_rows if x["category"] in CATEGORIES])})
    latest_rows = [x for x in rows if responses and x["period"] == responses[-1]["period"]]
    style = {x["style"]: x["value"] for x in latest_rows if x["category"] == "arbejdsstil"}

    # Læringsstil: de stilarter eleven er enig i (4–5) – ellers den højeste
    strong = [STYLES[s] for s in STYLES if style.get(s, 0) >= 4] or (
        [STYLES[max(STYLES, key=lambda s: style.get(s, 0))]] if style else [])
    tempo = style.get("tempo")
    pace = None if tempo is None else {1: "Langsomt", 2: "Langsomt/moderat", 3: "Moderat", 4: "Moderat/hurtigt", 5: "Hurtigt"}[tempo]
    trivsel = summarise([x for x in latest_rows if x["category"] == "trivsel"])["average"]
    room = summarise([x for x in latest_rows if x["category"] in ("møbler", "miljø")])["average"]
    latest = responses[-1] if responses else {}
    return {
        "student": {k: student[k] for k in ("id", "name", "class_name", "age", "email")},
        "learning_style": " + ".join(strong) or None,
        "work_pace": pace,
        "wellbeing_score": round(1 + (trivsel - 1) * 9 / 4) if trivsel else None,       # 1–5 omregnet til 1–10
        "classroom_score": round(1 + (room - 1) * 9 / 4) if room else None,
        "wishes": latest.get("wishes"),
        "classroom": latest.get("classroom"),
        "comment": latest.get("comment"),
        "notes": [{"question": x["text"], "category": x["category"], "value": x["value"], "note": x["note"]}
                  for x in latest_rows if x["note"]],
        "latest_period": latest.get("period"),
        "answered_this_month": latest.get("period") == current_period(),
        "months": months,
    }


@app.get("/api/me/profile")
def my_profile():
    """Elevens forside: egen profil og udvikling."""
    user = current_user("elev")
    return jsonify(student_profile(user))


@app.get("/api/students/<int:student_id>/profile")
def profile(student_id):
    """Lærerens visning af én elev: navn, klasse, profil og besvarelser i procent pr. måned."""
    user = current_user("elev", "lærer")
    return jsonify(student_profile(check_student_access(user, student_id)))


# ---------------------------------------------------------------- Lærer: overblik over hver elev og klassen
@app.get("/api/teacher/students")
def teacher_students():
    """Lærerens overblik: hver elev i klassen med andel positive svar pr. måned og seneste profil."""
    user = current_user("lærer")
    class_id = user["class_id"] or request.args.get("class_id", type=int)
    sql = f"SELECT {STUDENT_FIELDS} FROM student s JOIN class c ON c.id = s.class_id"
    students = query_all(sql + (" WHERE s.class_id = ?" if class_id else "") + " ORDER BY c.grade, s.name",
                         (class_id,) if class_id else ())
    periods = sorted({r["period"] for r in query_all("SELECT DISTINCT period FROM response")})
    result = []
    for s in students:
        p = student_profile(s)
        by_month = {m["period"]: m for m in p["months"]}
        result.append({**p["student"], "learning_style": p["learning_style"], "work_pace": p["work_pace"],
                       "wellbeing_score": p["wellbeing_score"], "answered_this_month": p["answered_this_month"],
                       "months": {period: ({c: by_month[period]["categories"][c]["positive_pct"] for c in CATEGORIES}
                                           | {"samlet": by_month[period]["overall"]["positive_pct"]})
                                  if period in by_month else None for period in periods}})
    return jsonify(periods=periods, class_id=class_id, students=result)


def class_filter(user):
    class_id = request.args.get("class_id", type=int)
    if user["role"] == "lærer" and user["class_id"]:
        class_id = user["class_id"]
    return class_id


@app.get("/api/results")
def results():
    """Klassens samlede resultat i en måned: gennemsnit og procenttal (vises ved mindst 3 besvarelser)."""
    user = current_user("lærer", "virksomhed")
    class_id, period = class_filter(user), request.args.get("period")
    all_rows = query_all(ANSWER_SQL + " WHERE q.category != 'arbejdsstil'" + (" AND s.class_id = ?" if class_id else ""),
                         (class_id,) if class_id else ())
    periods = reportable_periods(all_rows)
    period = period or (periods[-1] if periods else None)
    rows = [r for r in all_rows if r["period"] == period]
    respondents = len({r["student_id"] for r in rows})
    if respondents < MIN_RESPONDENTS:
        return jsonify(period=period, respondents=respondents, hidden=True, periods=periods,
                       message=f"Der vises først resultater, når mindst {MIN_RESPONDENTS} elever har svaret.")
    questions = query_all("SELECT * FROM question WHERE category != 'arbejdsstil' ORDER BY category, id")
    return jsonify(
        period=period, periods=periods, hidden=False, respondents=respondents,
        overall=summarise(rows),
        categories={c: summarise([r for r in rows if r["category"] == c]) for c in CATEGORIES},
        questions=[{**q, **summarise([r for r in rows if r["question_id"] == q["id"]])} for q in questions],
    )


@app.get("/api/results/trend")
def trend():
    """Sammenlign svar over tid: gennemsnit og andel positive svar pr. kategori pr. måned."""
    user = current_user("lærer", "virksomhed")
    class_id = class_filter(user)
    rows = query_all(ANSWER_SQL + " WHERE q.category != 'arbejdsstil'" + (" AND s.class_id = ?" if class_id else "")
                     + " ORDER BY r.period", (class_id,) if class_id else ())
    periods = reportable_periods(rows)
    series = {c: [summarise([r for r in rows if r["period"] == p and r["category"] == c]) for p in periods]
              for c in CATEGORIES}
    changes = {c: (round(s[-1]["average"] - s[0]["average"], 2) if len(s) > 1 and s[0]["average"] else None)
               for c, s in series.items()}
    return jsonify(periods=periods, series=series, change_since_first=changes)


# ---------------------------------------------------------------- Virksomheden: filtrerede, anonyme besvarelser
@app.get("/api/company/answers")
def company_answers():
    """Virksomhedens adgang til besvarelser til idéudvikling. Filtrér med ?class_id=&grade=&period=&category=
    &question_id=&max_value=&with_text=1. Eleverne er anonymiseret (fx "Elev 7.B-3")."""
    current_user("virksomhed")
    args = request.args
    where, params = [], []
    for column, key in (("s.class_id", "class_id"), ("c.grade", "grade"), ("r.period", "period"),
                        ("q.category", "category"), ("q.id", "question_id")):
        if args.get(key):
            where.append(f"{column} = ?")
            params.append(args[key])
    if args.get("max_value"):
        where.append("a.value <= ?")
        params.append(int(args["max_value"]))
    if args.get("with_text") == "1":
        where.append("a.note IS NOT NULL")
    rows = query_all(ANSWER_SQL + (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY r.period DESC, c.name, q.id",
                     tuple(params))
    # Pseudonym pr. elev inden for klassen – virksomheden ser aldrig navne
    numbers, counters = {}, {}
    for s in query_all("SELECT s.id, c.name AS class_name FROM student s JOIN class c ON c.id = s.class_id ORDER BY s.id"):
        counters[s["class_name"]] = counters.get(s["class_name"], 0) + 1
        numbers[s["id"]] = f"Elev {s['class_name']}-{counters[s['class_name']]}"
    rated = [r for r in rows if r["category"] != "arbejdsstil"]
    wishes = query_all("""SELECT r.period, c.name AS class_name, r.wishes, r.classroom FROM response r
                          JOIN student s ON s.id = r.student_id JOIN class c ON c.id = s.class_id
                          WHERE (r.wishes IS NOT NULL OR r.classroom IS NOT NULL)"""
                       + (" AND s.class_id = ?" if args.get("class_id") else "")
                       + (" AND r.period = ?" if args.get("period") else "") + " ORDER BY r.period DESC",
                       tuple(v for v in (args.get("class_id"), args.get("period")) if v))
    return jsonify(
        count=len(rows), summary=summarise(rated),
        per_category={c: summarise([r for r in rated if r["category"] == c]) for c in CATEGORIES},
        answers=[{"student": numbers[r["student_id"]], "class_name": r["class_name"], "grade": r["grade"], "period": r["period"],
                  "category": r["category"], "question": r["text"], "value": r["value"], "note": r["note"]} for r in rows[:300]],
        wishes=wishes,
        filters={"periods": [p["period"] for p in query_all("SELECT DISTINCT period FROM response ORDER BY period")],
                 "categories": CATEGORIES + ["arbejdsstil"]},
    )


@app.get("/api/overview")
def overview():
    """Virksomhedens overblik (Læringsrum 2.0): alle klasser med seneste resultat sammenlignet med første måling."""
    current_user("virksomhed")
    classes = query_all("SELECT * FROM class ORDER BY grade, name")
    result = []
    for c in classes:
        rows = query_all(ANSWER_SQL + " WHERE s.class_id = ? AND q.category != 'arbejdsstil' ORDER BY r.period", (c["id"],))
        periods = reportable_periods(rows)
        latest = [r for r in rows if periods and r["period"] == periods[-1]]
        first = [r for r in rows if periods and r["period"] == periods[0]]
        result.append({**c, "latest_period": periods[-1] if periods else None,
                       "students": query_one("SELECT COUNT(*) AS n FROM student WHERE class_id = ?", (c["id"],))["n"],
                       "latest": {cat: summarise([r for r in latest if r["category"] == cat])["average"] for cat in CATEGORIES},
                       "first": {cat: summarise([r for r in first if r["category"] == cat])["average"] for cat in CATEGORIES}})
    return jsonify(result)


if __name__ == "__main__":
    init_db()
    run(app, PORT)
