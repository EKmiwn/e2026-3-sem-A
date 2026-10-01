"""LoopAAS – gamification af New Loops retursystem. Flask API (logiklag).

Kravgrundlag: ../Kravspecifikationer.md (FR01–FR10)
Kør:  pip install -r requirements.txt  &&  python app.py  →  http://localhost:5112

Brugeren vælges i frontenden (simuleret login, FR01).
"""
import os
import secrets
from datetime import date, datetime, timedelta

from flask import jsonify, request

from core import ApiError, create_app, get_or_404, json_body, now, register_crud, require, run
from database import init_db, query_all, query_one, transaction

PORT = int(os.environ.get("PORT", 5112))
app = create_app(__name__, "LoopAAS")

LEVELS = [(0, "Bronze", "🥉"), (250, "Sølv", "🥈"), (600, "Guld", "🥇"), (1200, "Platin", "💎")]   # efter optjente point i alt
TYPE_TEXT = {"KOP": "kop", "SKÅL": "skål", "BOKS": "madboks"}


def setting(key):
    row = query_one("SELECT value FROM setting WHERE key = ?", (key,))
    if row is None:
        raise ApiError(f"Indstillingen {key} mangler", 500)
    return row["value"]


# ---------------------------------------------------------------- Gamification: niveau, badges og ugestreak
def level_for(total):
    current = [lvl for lvl in LEVELS if total >= lvl[0]][-1]
    following = next((lvl for lvl in LEVELS if lvl[0] > total), None)
    return {"name": current[1], "icon": current[2], "total_earned": total,
            "next": following[1] if following else None,
            "points_to_next": following[0] - total if following else 0,
            "progress_pct": round(100 * (total - current[0]) / (following[0] - current[0])) if following else 100}


def week_streak(dates):
    """Antal uger i træk (til og med denne eller sidste uge) med mindst én returnering."""
    weeks = {date.fromisoformat(d[:10]).isocalendar()[:2] for d in dates}
    streak, day = 0, date.today()
    if day.isocalendar()[:2] not in weeks:
        day -= timedelta(weeks=1)
    while day.isocalendar()[:2] in weeks:
        streak += 1
        day -= timedelta(weeks=1)
    return streak


def profile(user):
    returns = query_all("""SELECT r.*, p.type FROM return_event r JOIN package p ON p.id = r.package_id
                           WHERE r.user_id = ?""", (user["id"],))
    total = sum(r["points_earned"] for r in returns)
    redemptions = query_one("SELECT COUNT(*) AS n FROM redemption WHERE user_id = ?", (user["id"],))["n"]
    streak = week_streak([r["returned_at"] for r in returns])
    badges = [
        {"name": "Første retur", "icon": "♻️", "earned": len(returns) >= 1, "goal": "Returnér din første emballage"},
        {"name": "10 returneringer", "icon": "🔟", "earned": len(returns) >= 10, "goal": "Returnér 10 emballager"},
        {"name": "Alle typer", "icon": "🧩", "earned": {r["type"] for r in returns} >= set(TYPE_TEXT), "goal": "Returnér både kop, skål og madboks"},
        {"name": "3 uger i træk", "icon": "🔥", "earned": streak >= 3, "goal": "Returnér mindst én gang om ugen i 3 uger"},
        {"name": "Første reward", "icon": "🎁", "earned": redemptions >= 1, "goal": "Indløs din første reward"},
    ]
    return {"user": user, "points": user["points"], "returns": len(returns), "level": level_for(total),
            "week_streak": streak, "badges": badges,
            "co2_saved_kg": round(len(returns) * 0.05, 1)}       # antagelse: ca. 50 g CO₂ sparet pr. genbrugt emballage


# ---------------------------------------------------------------- CRUD (udvides let med flere rewards og partnere)
register_crud(app, "settings", "setting", fields=["key", "value", "description"], required=["key", "value"],
              update_fields=["value", "description"])
register_crud(app, "users", "app_user", fields=["name", "email"], required=["name", "email"], defaults={"created_at": now})
register_crud(app, "locations", "location", fields=["name", "address", "kind"], required=["name", "address", "kind"])
register_crud(app, "partners", "partner", fields=["name", "category", "address"], required=["name", "category"])
register_crud(app, "rewards", "reward", fields=["partner_id", "name", "description", "points_required", "stock", "active"],
              required=["partner_id", "name", "points_required"], order_by="points_required")


@app.get("/api/users/<int:user_id>/profile")
def user_profile(user_id):
    """Brugerens profil: pointsaldo, niveau, ugestreak og badges (FR04)."""
    return jsonify(profile(get_or_404("app_user", user_id, "Bruger")))


# ---------------------------------------------------------------- Returnering → LoopPoints (FR02, FR03)
@app.get("/api/packages/open")
def open_packages():
    """Udleverede emballager, der endnu ikke er returneret (eksempelkoder til at afprøve en returnering)."""
    return jsonify(query_all("""SELECT p.code, p.type, l.name AS location FROM package p JOIN location l ON l.id = p.location_id
                                WHERE p.id NOT IN (SELECT package_id FROM return_event) ORDER BY p.issued_at DESC LIMIT 20"""))


@app.post("/api/returns")
def register_return():
    """Registrér en returnering ved at scanne emballagens kode. Godkendes den, tildeles LoopPoints med det samme."""
    data = json_body()
    require(data, "user_id", "code", "location_id")
    user = get_or_404("app_user", data["user_id"], "Bruger")
    location = get_or_404("location", data["location_id"], "Returpunkt")
    code = str(data["code"]).strip().upper()
    package = query_one("SELECT * FROM package WHERE code = ?", (code,))
    # Validering af returneringen
    if package is None:
        raise ApiError(f"Koden {code} findes ikke. Tjek koden på emballagen, eller scan QR-koden igen.", 404)
    earlier = query_one("SELECT returned_at FROM return_event WHERE package_id = ?", (package["id"],))
    if earlier:
        raise ApiError(f"Emballagen {code} er allerede returneret {earlier['returned_at'][:10]} – point gives kun én gang.", 409)
    today_count = query_one("SELECT COUNT(*) AS n FROM return_event WHERE user_id = ? AND date(returned_at) = date('now', 'localtime')",
                            (user["id"],))["n"]
    if today_count >= setting("max_returns_per_day"):
        raise ApiError("Du har nået dagens maksimum for returneringer. Prøv igen i morgen.", 429)

    points = int(setting(f"points_{package['type'].lower()}"))
    before = profile(user)
    with transaction() as db:
        db.execute("""INSERT INTO return_event (user_id, package_id, location_id, points_earned, returned_at)
                      VALUES (?, ?, ?, ?, ?)""", (user["id"], package["id"], location["id"], points, now()))
        db.execute("UPDATE app_user SET points = points + ? WHERE id = ?", (points, user["id"]))
    after = profile(get_or_404("app_user", user["id"]))
    new_badges = [b for b, old in zip(after["badges"], before["badges"]) if b["earned"] and not old["earned"]]
    return jsonify(approved=True, code=code, type=package["type"], points_earned=points, new_balance=after["points"],
                   level_up=after["level"]["name"] if after["level"]["name"] != before["level"]["name"] else None,
                   new_badges=new_badges,
                   message=f"Tak! Din {TYPE_TEXT[package['type']]} er returneret – du har fået {points} LoopPoints."), 201


# ---------------------------------------------------------------- Rewards og indløsning (FR05 – FR08)
@app.get("/api/catalog")
def catalog():
    """Aktive rewards med partner, og hvor mange point brugeren mangler (?user_id=)."""
    user = query_one("SELECT * FROM app_user WHERE id = ?", (request.args.get("user_id", type=int),))
    rewards = query_all("""SELECT r.*, p.name AS partner, p.category, p.address FROM reward r JOIN partner p ON p.id = r.partner_id
                           WHERE r.active = 1 ORDER BY r.points_required""")
    for r in rewards:
        r["sold_out"] = r["stock"] == 0
        r["missing_points"] = max(0, r["points_required"] - user["points"]) if user else None
        r["can_redeem"] = bool(user) and not r["sold_out"] and r["missing_points"] == 0
    return jsonify(rewards)


@app.post("/api/redemptions")
def redeem():
    """Indløs en reward: pointsaldoen kontrolleres og reduceres, og brugeren får en kode til partneren."""
    data = json_body()
    require(data, "user_id", "reward_id")
    user = get_or_404("app_user", data["user_id"], "Bruger")
    reward = get_or_404("reward", data["reward_id"], "Reward")
    if not reward["active"]:
        raise ApiError("Rewarden er ikke længere tilgængelig", 409)
    if reward["stock"] == 0:
        raise ApiError("Rewarden er udsolgt", 409)
    if user["points"] < reward["points_required"]:            # FR07
        raise ApiError(f"Du har {user['points']} LoopPoints og mangler {reward['points_required'] - user['points']} "
                       f"for at indløse {reward['name']}.", 409)
    code = f"LOOP-{secrets.token_hex(2).upper()}"
    with transaction() as db:
        updated = db.execute("UPDATE app_user SET points = points - ? WHERE id = ? AND points >= ?",       # FR08
                             (reward["points_required"], user["id"], reward["points_required"])).rowcount
        if not updated:
            raise ApiError("Pointsaldoen er ændret – prøv igen", 409)
        if reward["stock"] is not None:
            db.execute("UPDATE reward SET stock = stock - 1 WHERE id = ?", (reward["id"],))
        redemption_id = db.execute("""INSERT INTO redemption (user_id, reward_id, points_used, code, redeemed_at)
                                      VALUES (?, ?, ?, ?, ?)""",
                                   (user["id"], reward["id"], reward["points_required"], code, now())).lastrowid
    partner = get_or_404("partner", reward["partner_id"])
    return jsonify(redemption=get_or_404("redemption", redemption_id), reward=reward["name"], partner=partner["name"],
                   new_balance=user["points"] - reward["points_required"],
                   message=f"Vis koden {code} hos {partner['name']} for at få {reward['name'].lower()}."), 201


@app.post("/api/redemptions/verify")
def verify():
    """Samarbejdspartneren indtaster koden og markerer rewarden som brugt."""
    data = json_body()
    require(data, "code", "partner_id")
    row = query_one("""SELECT d.*, r.name AS reward, r.partner_id, u.name AS user_name FROM redemption d
                       JOIN reward r ON r.id = d.reward_id JOIN app_user u ON u.id = d.user_id WHERE d.code = ?""",
                    (str(data["code"]).strip().upper(),))
    if row is None:
        raise ApiError("Koden findes ikke", 404)
    if row["partner_id"] != int(data["partner_id"]):
        raise ApiError("Koden hører til en anden samarbejdspartner", 403)
    if row["status"] == "BRUGT":
        raise ApiError(f"Koden er allerede brugt {row['used_at']}", 409)
    with transaction() as db:
        db.execute("UPDATE redemption SET status = 'BRUGT', used_at = ? WHERE id = ?", (now(), row["id"]))
    return jsonify(valid=True, reward=row["reward"], user=row["user_name"].split()[0],
                   message=f"Godkendt: {row['reward']} til {row['user_name'].split()[0]}.")


# ---------------------------------------------------------------- Historik (FR09)
@app.get("/api/users/<int:user_id>/history")
def history(user_id):
    """Returneringer og indløsninger samlet, nyeste først, med pointændring."""
    get_or_404("app_user", user_id, "Bruger")
    returns = query_all("""SELECT 'RETUR' AS kind, r.returned_at AS time, r.points_earned AS points, p.code, p.type,
                                  l.name AS place, NULL AS status
                           FROM return_event r JOIN package p ON p.id = r.package_id JOIN location l ON l.id = r.location_id
                           WHERE r.user_id = ?""", (user_id,))
    redemptions = query_all("""SELECT 'INDLØSNING' AS kind, d.redeemed_at AS time, -d.points_used AS points, d.code,
                                      r.name AS type, p.name AS place, d.status
                               FROM redemption d JOIN reward r ON r.id = d.reward_id JOIN partner p ON p.id = r.partner_id
                               WHERE d.user_id = ?""", (user_id,))
    rows = sorted(returns + redemptions, key=lambda r: r["time"], reverse=True)
    monthly = {}
    for r in returns:
        month = r["time"][:7]
        monthly[month] = monthly.get(month, 0) + 1
    return jsonify(history=rows, returns_per_month=dict(sorted(monthly.items())),
                   active_codes=[r for r in redemptions if r["status"] == "AKTIV"])


# ---------------------------------------------------------------- New Loop og partnere: nøgletal
@app.get("/api/stats")
def stats():
    """Nøgletal for New Loop: returneringer, returrate, point og rewards pr. partner."""
    issued = query_one("SELECT COUNT(*) AS n FROM package")["n"]
    returned = query_one("SELECT COUNT(*) AS n FROM return_event")["n"]
    since = (datetime.now() - timedelta(days=30)).isoformat(sep=" ", timespec="seconds")
    return jsonify(
        users=query_one("SELECT COUNT(*) AS n FROM app_user")["n"], packages_issued=issued, packages_returned=returned,
        return_rate_pct=round(100 * returned / issued) if issued else 0,
        returns_30d=query_one("SELECT COUNT(*) AS n FROM return_event WHERE returned_at >= ?", (since,))["n"],
        points_earned=query_one("SELECT COALESCE(SUM(points_earned), 0) AS n FROM return_event")["n"],
        points_redeemed=query_one("SELECT COALESCE(SUM(points_used), 0) AS n FROM redemption")["n"],
        per_partner=query_all("""SELECT p.name, COUNT(d.id) AS redemptions, COALESCE(SUM(d.status = 'BRUGT'), 0) AS used
                                 FROM partner p LEFT JOIN reward r ON r.partner_id = p.id LEFT JOIN redemption d ON d.reward_id = r.id
                                 GROUP BY p.id ORDER BY redemptions DESC"""),
        leaderboard=[{"name": u["name"].split()[0], "returns": u["n"]} for u in query_all(
            """SELECT u.name, COUNT(r.id) AS n FROM app_user u JOIN return_event r ON r.user_id = u.id
               WHERE r.returned_at >= ? GROUP BY u.id ORDER BY n DESC LIMIT 5""", (since,))],
    )


if __name__ == "__main__":
    init_db()
    run(app, PORT)
