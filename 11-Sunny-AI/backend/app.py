"""Sunny AI – beslutningsstøtte til ugeplan og opslag hos Sunny Juice. Flask API (logiklag).

Kravgrundlag: ../kravspecifikation.md
Kør:  pip install -r requirements.txt  &&  python app.py  →  http://localhost:5111

Beregningsreglerne R01–R08 ligger i planner.py. Denne fil indeholder den simulerede Uniconta-adapter,
planversioner, godkendelse og den regelbaserede demoassistent (R09). Demobrugeren sendes i headeren
X-User-Id og bruges kun som navn på en godkendelse – det er ikke et login.
"""
import json
import os
import re
from datetime import timedelta

from flask import Response, jsonify, request

import planner
from core import ApiError, create_app, get_or_404, json_body, now, register_crud, require, run
from database import close_db, init_db, query_all, query_one, transaction

PORT = int(os.environ.get("PORT", 5111))
app = create_app(__name__, "Sunny AI")

KILDE_LABEL = "Simuleret datakilde (demo) – ikke forbundet til Uniconta"


# ---------------------------------------------------------------- Datakildeadapter (F01)
def beregningstidspunkt():
    return query_one("SELECT vaerdi FROM indstilling WHERE noegle = 'beregningstidspunkt'")["vaerdi"]


def current_snapshot():
    return query_one("SELECT * FROM snapshot ORDER BY id DESC LIMIT 1")


def load_data(snapshot):
    """Læser ét snapshot til planmotorens datakontrakt. Ved en rigtig integration udskiftes kun denne adapter."""
    sid = snapshot["id"]
    behov = {}
    for r in query_all("""SELECT r.* FROM ressourcebehov r JOIN ordrelinje o ON o.id = r.ordrelinje_id
                          WHERE o.snapshot_id = ? ORDER BY r.id""", (sid,)):
        behov.setdefault(r["ordrelinje_id"], []).append(r)
    return {
        "snapshot": snapshot,
        "varer": {v["id"]: v for v in query_all("SELECT * FROM vare ORDER BY id")},
        "rater": {r["vare_id"]: r["enheder_pr_time"] for r in query_all("SELECT * FROM produktionsrate")},
        "batches": query_all("SELECT * FROM lagerbatch WHERE snapshot_id = ? ORDER BY id", (sid,)),
        "ordrelinjer": query_all("SELECT * FROM ordrelinje WHERE snapshot_id = ? ORDER BY id", (sid,)),
        "produktionsstatus": query_all("SELECT * FROM produktionsstatus WHERE snapshot_id = ? ORDER BY id", (sid,)),
        "ressourcebehov": behov,
        "kapacitet": {k["dato"]: k["disponible_minutter"] for k in query_all("SELECT * FROM kapacitetsdag")},
    }


def copy_snapshot(db, old, source_updated_at, beskrivelse):
    """Nyt snapshot = kopi af det forrige. Det gamle ændres aldrig, så godkendte planer kan spores."""
    new_id = db.execute("INSERT INTO snapshot (source, source_updated_at, imported_at, schema_version, beskrivelse)"
                        " VALUES ('demo', ?, ?, ?, ?)",
                        (source_updated_at, beregningstidspunkt(), old["schema_version"], beskrivelse)).lastrowid
    ny_linje = {}
    for ol in query_all("SELECT * FROM ordrelinje WHERE snapshot_id = ? ORDER BY id", (old["id"],)):
        ny_linje[ol["id"]] = db.execute(
            "INSERT INTO ordrelinje (snapshot_id, ordre_id, kilde_id, vare_id, bestilt_maengde, leveret_maengde,"
            " leveringsdato, status, prioritet, saesonmaerke) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (new_id, ol["ordre_id"], ol["kilde_id"], ol["vare_id"], ol["bestilt_maengde"], ol["leveret_maengde"],
             ol["leveringsdato"], ol["status"], ol["prioritet"], ol["saesonmaerke"])).lastrowid
    for r in query_all("""SELECT r.* FROM ressourcebehov r JOIN ordrelinje o ON o.id = r.ordrelinje_id
                          WHERE o.snapshot_id = ?""", (old["id"],)):
        db.execute("INSERT INTO ressourcebehov (ordrelinje_id, raavare_id, maengde_pr_enhed) VALUES (?, ?, ?)",
                   (ny_linje[r["ordrelinje_id"]], r["raavare_id"], r["maengde_pr_enhed"]))
    db.execute("""INSERT INTO lagerbatch (snapshot_id, vare_id, batchnummer, fysisk_maengde, reserveret_maengde,
                                          udloebsdato, kvalitetsstatus, data_afklaret)
                  SELECT ?, vare_id, batchnummer, fysisk_maengde, reserveret_maengde, udloebsdato, kvalitetsstatus,
                         data_afklaret FROM lagerbatch WHERE snapshot_id = ?""", (new_id, old["id"]))
    for ps in query_all("SELECT * FROM produktionsstatus WHERE snapshot_id = ?", (old["id"],)):
        db.execute("INSERT INTO produktionsstatus (snapshot_id, ordrelinje_id, status, affected_item_ids,"
                   " afklaring_paakraevet, beskrivelse) VALUES (?, ?, ?, ?, ?, ?)",
                   (new_id, ny_linje.get(ps["ordrelinje_id"]), ps["status"], ps["affected_item_ids"],
                    ps["afklaring_paakraevet"], ps["beskrivelse"]))
    return new_id


def log_event(db, type_, detaljer, plan_id=None, actor="System", request_id=None):
    db.execute("INSERT INTO haendelse (plan_id, type, timestamp, actor, request_id, detaljer) VALUES (?, ?, ?, ?, ?, ?)",
               (plan_id, type_, now(), actor, request_id, detaljer))


def mark_plans_stale(db, grund, where="status != 'stale'", params=()):
    """R08: nye data, ny beregningsdato eller nye parametre gør eksisterende forslag og godkendelser forældede."""
    db.execute(f"UPDATE planversion SET status = 'stale', foraeldet_grund = ? WHERE {where}", (grund, *params))


def demo_user():
    user_id = request.headers.get("X-User-Id")
    user = user_id and query_one("SELECT * FROM bruger WHERE id = ?", (user_id,))
    return f"{user['navn']} ({user['rolle']})" if user else "Ukendt demobruger"


def status_payload(data=None, plan=None):
    """Kilde, tidspunkter og antal forhold, der kræver kontrol. Vises øverst på alle skærme (F01)."""
    snap = current_snapshot()
    tid = beregningstidspunkt()
    data = data or load_data(snap)
    problemer = planner.valider(data, tid)
    plan = plan or current_plan(uge_for(tid), data)["resultat"]
    return {
        "kilde": KILDE_LABEL,
        "snapshot": snap,
        "beregningstidspunkt": tid,
        **planner.snapshot_alder(snap, tid),
        "fejl": sum(1 for p in problemer if p["niveau"] == "fejl"),
        "advarsler": sum(1 for p in problemer if p["niveau"] == "advarsel"),
        "blokerede_ordrer": plan["noegletal"]["blokerede"],
        "kraever_kontrol": sum(1 for p in problemer if p["niveau"] == "fejl") + len(plan["uplanlagte"]),
    }


def uge_for(tidspunkt):
    dag = planner.as_datetime(tidspunkt).date()
    return (dag - timedelta(days=dag.weekday())).isoformat()


# ---------------------------------------------------------------- CRUD (kildedata er skrivebeskyttet)
register_crud(app, "users", "bruger", fields=["navn", "rolle"], read_only=True)
register_crud(app, "items", "vare", fields=["varenummer", "navn", "type", "basisenhed"], read_only=True)
register_crud(app, "snapshots", "snapshot", fields=["source"], read_only=True, order_by="id DESC")


@app.get("/api/status")
def status():
    """Datakilde, snapshot-tidspunkt, alder og antal forhold, der kræver kontrol."""
    return jsonify(status_payload())


@app.get("/api/validation")
def validation():
    """F02, F04, F05: kendte dataproblemer i det aktuelle snapshot med anbefalet handling."""
    snap = current_snapshot()
    data = load_data(snap)
    return jsonify(snapshot=snap, problemer=planner.valider(data, beregningstidspunkt()),
                   produktionsstatus=data["produktionsstatus"])


@app.put("/api/clock")
def set_clock():
    """Fastlås demo-uret. En ny beregningsdato gør eksisterende planer forældede (R08)."""
    data = json_body()
    require(data, "beregningstidspunkt")
    try:
        tid = planner.as_datetime(data["beregningstidspunkt"]).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        raise ApiError("Beregningstidspunkt skal have formatet YYYY-MM-DD HH:MM")
    with transaction() as db:
        db.execute("UPDATE indstilling SET vaerdi = ? WHERE noegle = 'beregningstidspunkt'", (tid,))
        mark_plans_stale(db, f"Beregningstidspunkt ændret til {tid}")
        log_event(db, "Beregningstidspunkt ændret", tid, actor=demo_user())
    return jsonify(status_payload())


@app.post("/api/source/import")
def import_snapshot():
    """Simuleret Uniconta-adapter: indlæs et nyt snapshot, evt. med en demoændring i kildedata.

    type: genindlaes | udloeb_batch (batchnummer) | uafklaret_faerdigmelding (vare_id)
          | afklar | ny_ordre (ordre_id, vare_id, antal, leveringsdato, prioritet, saesonmaerke)
    """
    body = json_body()
    typ = body.get("type", "genindlaes")
    old = current_snapshot()
    tid = beregningstidspunkt()
    beskrivelser = {
        "genindlaes": "Ny indlæsning uden ændringer",
        "udloeb_batch": f"Batch {body.get('batchnummer')} registreret som udløbet",
        "uafklaret_faerdigmelding": "Kendt uafklaret færdigmelding registreret",
        "afklar": "Færdigmeldinger afklaret",
        "ny_ordre": f"Ny ordre {body.get('ordre_id')}",
    }
    if typ not in beskrivelser:
        raise ApiError("Ukendt type. Brug " + ", ".join(beskrivelser))
    dag = planner.as_datetime(tid).date()

    with transaction() as db:
        new_id = copy_snapshot(db, old, tid, beskrivelser[typ])
        if typ == "udloeb_batch":
            require(body, "batchnummer")
            cur = db.execute("UPDATE lagerbatch SET udloebsdato = ? WHERE snapshot_id = ? AND batchnummer = ?",
                             ((dag - timedelta(days=1)).isoformat(), new_id, body["batchnummer"]))
            if not cur.rowcount:
                raise ApiError(f"Batch {body['batchnummer']} findes ikke i snapshottet", 404)
        elif typ == "uafklaret_faerdigmelding":
            require(body, "vare_id")
            vare = get_or_404("vare", body["vare_id"], "Vare")
            db.execute("INSERT INTO produktionsstatus (snapshot_id, status, affected_item_ids, afklaring_paakraevet,"
                       " beskrivelse) VALUES (?, 'Produktion ikke færdigmeldt', ?, 1, ?)",
                       (new_id, str(vare["id"]), f"Forbrug af {vare['varenummer']} er ikke registreret i kildesystemet."))
        elif typ == "afklar":
            db.execute("UPDATE produktionsstatus SET afklaring_paakraevet = 0 WHERE snapshot_id = ?", (new_id,))
            db.execute("UPDATE lagerbatch SET data_afklaret = 1 WHERE snapshot_id = ?", (new_id,))
        elif typ == "ny_ordre":
            require(body, "ordre_id", "vare_id", "antal", "leveringsdato")
            vare = get_or_404("vare", body["vare_id"], "Vare")
            if vare["type"] != "færdigvare":
                raise ApiError("En ordre skal være på en færdigvare")
            try:
                antal = float(body["antal"])
                planner.as_date(body["leveringsdato"])
            except (TypeError, ValueError):
                raise ApiError("Antal skal være et tal og leveringsdato en dato (YYYY-MM-DD)")
            if antal <= 0:
                raise ApiError("Antal skal være større end 0")
            if body.get("prioritet", "normal") not in ("normal", "høj"):
                raise ApiError("Prioritet skal være normal eller høj")
            ordre_id = str(body["ordre_id"]).strip().upper()
            linje_id = db.execute(
                "INSERT INTO ordrelinje (snapshot_id, ordre_id, kilde_id, vare_id, bestilt_maengde, leveringsdato,"
                " prioritet, saesonmaerke) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (new_id, ordre_id, f"UC-DEMO-{ordre_id}", vare["id"], round(antal * 1000),
                 body["leveringsdato"], body.get("prioritet", "normal"), 1 if body.get("saesonmaerke") else 0)).lastrowid
            # Fiktivt ressourcebehov kopieres fra en eksisterende linje med samme vare. Findes ingen, er behovet ukendt.
            kilde = query_one("""SELECT o.id FROM ordrelinje o WHERE o.snapshot_id = ? AND o.vare_id = ?
                                 AND EXISTS (SELECT 1 FROM ressourcebehov r WHERE r.ordrelinje_id = o.id)
                                 ORDER BY o.id LIMIT 1""", (old["id"], vare["id"]))
            if kilde:
                db.execute("""INSERT INTO ressourcebehov (ordrelinje_id, raavare_id, maengde_pr_enhed)
                              SELECT ?, raavare_id, maengde_pr_enhed FROM ressourcebehov WHERE ordrelinje_id = ?""",
                           (linje_id, kilde["id"]))
        mark_plans_stale(db, f"Nyt snapshot #{new_id} indlæst")
        log_event(db, "Snapshot indlæst", f"Snapshot #{new_id}: {beskrivelser[typ]}", actor=demo_user())
    return jsonify(status_payload()), 201


# ---------------------------------------------------------------- Opslag i ordrer og lager (F03)
ORDER_SQL = """
    SELECT o.*, o.bestilt_maengde - o.leveret_maengde AS rest, v.varenummer, v.navn AS varenavn,
           v.basisenhed AS enhed, s.source_updated_at
    FROM ordrelinje o JOIN vare v ON v.id = o.vare_id JOIN snapshot s ON s.id = o.snapshot_id
"""


def matches(q, *values):
    q = (q or "").strip().lower()
    return not q or any(q in str(v or "").lower() for v in values)


@app.get("/api/orders")
def orders():
    """Ordrelinjer i det aktuelle snapshot. Søg på ordrenummer, varenummer eller navn med ?q= og filtrér med ?status=."""
    rows = query_all(ORDER_SQL + " WHERE o.snapshot_id = ? ORDER BY o.leveringsdato, o.id", (current_snapshot()["id"],))
    status_filter = request.args.get("status")
    return jsonify([r for r in rows if matches(request.args.get("q"), r["ordre_id"], r["kilde_id"], r["varenummer"],
                                               r["varenavn"]) and (not status_filter or r["status"] == status_filter)])


@app.get("/api/orders/<int:line_id>")
def order_detail(line_id):
    """Ordrelinje med ressourcebehov og forklaring fra den aktuelle plan (F10)."""
    row = query_one(ORDER_SQL + " WHERE o.id = ?", (line_id,))
    if row is None:
        raise ApiError(f"Ordrelinje {line_id} findes ikke", 404)
    behov = query_all("""SELECT r.*, v.varenummer, v.navn, v.basisenhed AS enhed FROM ressourcebehov r
                         JOIN vare v ON v.id = r.raavare_id WHERE r.ordrelinje_id = ?""", (line_id,))
    plan = current_plan(uge_for(beregningstidspunkt()))
    forklaring = next((l for l in plan["resultat"]["linjer"] if l["ordrelinje_id"] == line_id), None)
    return jsonify(ordrelinje=row, ressourcebehov=behov, plan={k: plan[k] for k in ("id", "label", "status")},
                   forklaring=forklaring, aktuelt_snapshot=row["snapshot_id"] == current_snapshot()["id"])


def stock_rows(snap, data):
    tid = beregningstidspunkt()
    dag = planner.as_datetime(tid).date()
    usikre = planner.usikre_varer(data)
    rows = []
    for b in data["batches"]:
        vare = data["varer"][b["vare_id"]]
        disponibel, grund = planner.batch_status(b, data, dag, usikre)
        udloeb_snart = grund is None and disponibel > 0 and \
            (planner.as_date(b["udloebsdato"]) - dag).days <= planner.UDLOEB_ADVARSEL_DAGE
        rows.append({**b, "varenummer": vare["varenummer"], "varenavn": vare["navn"], "enhed": vare["basisenhed"],
                     "type": vare["type"], "disponibel": None if b["vare_id"] in usikre else disponibel,
                     "spaerret_grund": grund, "udloeb_snart": udloeb_snart,
                     "source_updated_at": snap["source_updated_at"]})
    return rows


@app.get("/api/stock")
def stock():
    """Lagerbatches i det aktuelle snapshot med disponibel mængde og grund, hvis batchen ikke kan bruges (R02)."""
    snap = current_snapshot()
    rows = stock_rows(snap, load_data(snap))
    return jsonify([r for r in rows if matches(request.args.get("q"), r["varenummer"], r["varenavn"], r["batchnummer"])])


@app.get("/api/items/<int:item_id>/details")
def item_detail(item_id):
    """Vare med batches, disponibelt lager og ordrer, der bruger den."""
    vare = get_or_404("vare", item_id, "Vare")
    snap = current_snapshot()
    data = load_data(snap)
    dag = planner.as_datetime(beregningstidspunkt()).date()
    batches = [r for r in stock_rows(snap, data) if r["vare_id"] == item_id]
    ordrer = query_all(ORDER_SQL + """ WHERE o.snapshot_id = ? AND (o.vare_id = ? OR o.id IN
                                       (SELECT ordrelinje_id FROM ressourcebehov WHERE raavare_id = ?))
                                       ORDER BY o.leveringsdato""", (snap["id"], item_id, item_id))
    return jsonify(vare=vare, disponibelt=planner.disponibelt_pr_vare(data, dag)[item_id],
                   usikker=item_id in planner.usikre_varer(data), batches=batches, ordrer=ordrer,
                   rate=data["rater"].get(item_id), snapshot=snap)


# ---------------------------------------------------------------- Planversioner (F06–F12)
def plan_row(plan_id):
    plan = query_one("SELECT * FROM planversion WHERE id = ?", (plan_id,))
    if plan is None:
        raise ApiError(f"Planversion {plan_id} findes ikke", 404)
    for key in ("parametre", "manuelle_parametre", "resultat"):
        plan[key] = json.loads(plan[key])
    plan["label"] = f"Planversion {plan['versionsnummer']}"
    return plan


def current_plan(uge_start, data=None):
    """Seneste gyldige planversion for ugen. Findes ingen, beregnes et foreløbigt forslag, som ikke gemmes.
    Overblik, ordredetaljer og assistent bruger denne ene funktion, så tallene altid er de samme."""
    snap = current_snapshot()
    row = query_one("""SELECT id FROM planversion WHERE uge_start = ? AND snapshot_id = ? AND status != 'stale'
                       ORDER BY id DESC LIMIT 1""", (uge_start, snap["id"]))
    if row:
        return plan_row(row["id"])
    resultat = planner.beregn_plan(data or load_data(snap), uge_start, beregningstidspunkt())
    return {"id": None, "label": "Foreløbig beregning (ikke gemt)", "status": "preview", "resultat": resultat,
            "uge_start": uge_start}


def manual_parameters(data, params):
    """F11: hvilke parametre afviger fra kildedata/standard. Vises som manuelle i planen."""
    manuelle = []
    for dato, minutter in (params.get("kapacitet") or {}).items():
        if int(minutter) != data["kapacitet"].get(dato, planner.STANDARD_KAPACITET_MIN):
            manuelle.append(f"Kapacitet {planner.fmt_dag(dato)}: {planner.fmt_minutter(int(minutter))}")
    linjer = {ol["id"]: ol for ol in data["ordrelinjer"]}
    for linje_id, prioritet in (params.get("prioritet") or {}).items():
        ol = linjer.get(int(linje_id))
        if ol and prioritet != ol["prioritet"]:
            manuelle.append(f"Prioritet {ol['ordre_id']}: {prioritet}")
    if params.get("ordrelinje_ids") is not None:
        aabne = {ol["id"] for ol in data["ordrelinjer"] if ol["status"] == "åben"}
        fravalgt = sorted(linjer[i]["ordre_id"] for i in aabne - set(params["ordrelinje_ids"]))
        if fravalgt:
            manuelle.append("Fravalgte ordrer: " + ", ".join(fravalgt))
    return manuelle


@app.get("/api/plans")
def list_plans():
    """Versionshistorik for en uge: ?uge_start=YYYY-MM-DD (standard: ugen for beregningstidspunktet)."""
    uge = request.args.get("uge_start") or uge_for(beregningstidspunkt())
    rows = query_all("""SELECT id, snapshot_id, uge_start, versionsnummer, beregningstidspunkt, manuelle_parametre,
                               oprettet_at, status, foraeldet_grund, godkendt_at, godkendt_af, delvis
                        FROM planversion WHERE uge_start = ? ORDER BY id DESC""", (uge,))
    for r in rows:
        r["manuelle_parametre"] = json.loads(r["manuelle_parametre"])
    return jsonify(rows)


@app.get("/api/plans/current")
def get_current_plan():
    """Seneste gyldige plan for ugen, ellers et foreløbigt forslag (ikke gemt)."""
    return jsonify(current_plan(request.args.get("uge_start") or uge_for(beregningstidspunkt())))


@app.get("/api/plans/<int:plan_id>")
def get_plan(plan_id):
    """Én planversion med parametre, resultat og hændelser."""
    plan = plan_row(plan_id)
    plan["haendelser"] = query_all("SELECT * FROM haendelse WHERE plan_id = ? ORDER BY id", (plan_id,))
    return jsonify(plan)


@app.post("/api/plans")
def create_plan():
    """F07, F11: beregn et nyt planforslag som ny version. Tidligere forslag for ugen bliver forældede.

    Body: {"uge_start": "2026-10-05", "ordrelinje_ids": [1, 2, 3], "kapacitet": {"2026-10-05": 240},
           "prioritet": {"2": "høj"}}
    """
    body = json_body()
    require(body, "uge_start")
    snap = current_snapshot()
    data = load_data(snap)
    tid = beregningstidspunkt()
    params = {"ordrelinje_ids": body.get("ordrelinje_ids"), "kapacitet": body.get("kapacitet") or {},
              "prioritet": body.get("prioritet") or {}}
    try:
        resultat = planner.beregn_plan(data, body["uge_start"], tid, params)
    except (planner.PlanFejl, ValueError) as err:
        raise ApiError(str(err))
    if not resultat["linjer"]:
        raise ApiError("Der er ingen åbne ordrelinjer at planlægge. Vælg mindst én ordre.")

    with transaction() as db:
        naeste = db.execute("SELECT COALESCE(MAX(versionsnummer), 0) + 1 FROM planversion WHERE uge_start = ?",
                            (body["uge_start"],)).fetchone()[0]
        mark_plans_stale(db, f"Erstattet af version {naeste}", "uge_start = ? AND status != 'stale'", (body["uge_start"],))
        plan_id = db.execute(
            """INSERT INTO planversion (snapshot_id, uge_start, versionsnummer, beregningstidspunkt, parametre,
                                        manuelle_parametre, resultat, oprettet_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (snap["id"], body["uge_start"], naeste, tid, json.dumps(params, ensure_ascii=False),
             json.dumps(manual_parameters(data, params), ensure_ascii=False),
             json.dumps(resultat, ensure_ascii=False), now())).lastrowid
        for p in resultat["planlinjer"]:
            db.execute("INSERT INTO planlinje (plan_id, ordrelinje_id, dato, maengde, minutter, allocated_batch_refs)"
                       " VALUES (?, ?, ?, ?, ?, ?)",
                       (plan_id, p["ordrelinje_id"], p["dato"], p["maengde"], p["minutter"],
                        json.dumps(p["allocated_batch_refs"])))
        log_event(db, "Planforslag beregnet", f"Version {naeste} på snapshot #{snap['id']}", plan_id=plan_id,
                  actor=demo_user())
    return jsonify(plan_row(plan_id)), 201


@app.post("/api/plans/<int:plan_id>/approve")
def approve_plan(plan_id):
    """F12, R08: godkend præcis denne version. Samme request_id to gange giver én godkendelse.

    Body: {"request_id": "...", "accepter_uplanlagte": true}  (påkrævet, hvis planen har uplanlagte ordrer)
    """
    body = json_body()
    require(body, "request_id")
    tidligere = query_one("SELECT * FROM haendelse WHERE request_id = ?", (body["request_id"],))
    if tidligere:
        if tidligere["plan_id"] != plan_id:
            raise ApiError("request_id er allerede brugt til en anden handling", 409)
        return jsonify({**plan_row(plan_id), "gentaget": True})

    plan = plan_row(plan_id)
    snap = current_snapshot()
    tid = beregningstidspunkt()
    if plan["status"] == "approved":
        raise ApiError("Planversionen er allerede godkendt", 409)
    if plan["status"] == "stale":
        raise ApiError(f"Planversionen er forældet ({plan['foraeldet_grund']}). Beregn et nyt forslag.", 409)
    if plan["snapshot_id"] != snap["id"] or plan["beregningstidspunkt"] != tid:
        with transaction() as db:
            mark_plans_stale(db, "Data eller beregningstidspunkt er ændret", "id = ?", (plan_id,))
        raise ApiError("Data eller beregningstidspunkt er ændret siden beregningen. Beregn et nyt forslag.", 409)
    if planner.snapshot_alder(snap, tid)["foraeldet"]:
        raise ApiError(f"Kildedata er over {planner.SNAPSHOT_MAX_ALDER_TIMER} timer gamle. Indlæs et nyt snapshot "
                       "før godkendelse (R01).", 409)
    uplanlagte = plan["resultat"]["uplanlagte"]
    if uplanlagte and not body.get("accepter_uplanlagte"):
        raise ApiError("Planen har uplanlagte ordrer (" + ", ".join(u["ordre_id"] for u in uplanlagte) +
                       "). Acceptér listen for at godkende planen delvist.")

    actor = demo_user()
    with transaction() as db:
        cur = db.execute("""UPDATE planversion SET status = 'approved', godkendt_at = ?, godkendt_af = ?, delvis = ?
                            WHERE id = ? AND status = 'draft'""", (now(), actor, 1 if uplanlagte else 0, plan_id))
        if not cur.rowcount:
            raise ApiError("Planversionen kan ikke længere godkendes", 409)
        log_event(db, "Plan godkendt", ("Delvis godkendelse. Uplanlagt: " + ", ".join(u["ordre_id"] for u in uplanlagte))
                  if uplanlagte else "Fuld godkendelse", plan_id=plan_id, actor=actor, request_id=body["request_id"])
    return jsonify(plan_row(plan_id))


@app.get("/api/plans/<int:plan_id>/calendar.ics")
def plan_calendar(plan_id):
    """F16 (Should): kalenderfil med godkendte planlinjer. Sendes ikke nogen steder hen automatisk."""
    plan = plan_row(plan_id)
    if plan["status"] != "approved":
        raise ApiError("Kun en godkendt planversion kan eksporteres", 409)
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Sunny AI demo//DA", "CALSCALE:GREGORIAN"]
    stamp = plan["godkendt_at"].replace("-", "").replace(":", "").replace(" ", "T")
    for i, p in enumerate(plan["resultat"]["planlinjer"], start=1):
        dag = p["dato"].replace("-", "")
        naeste = (planner.as_date(p["dato"]) + timedelta(days=1)).strftime("%Y%m%d")
        lines += ["BEGIN:VEVENT",
                  f"UID:sunny-ai-uge{plan['uge_start']}-v{plan['versionsnummer']}-{p['ordrelinje_id']}-{i}@sunny-ai.demo",
                  f"DTSTAMP:{stamp}", f"DTSTART;VALUE=DATE:{dag}", f"DTEND;VALUE=DATE:{naeste}",
                  f"SUMMARY:Produktion {p['ordre_id']}: {planner.fmt_maengde(p['maengde'], p['enhed'])} {p['varenummer']}",
                  f"DESCRIPTION:Ordre {p['ordre_id']} · {planner.fmt_minutter(p['minutter'])} · Godkendt planversion "
                  f"{plan['versionsnummer']} (demo)", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return Response("\r\n".join(lines) + "\r\n", mimetype="text/calendar",
                    headers={"Content-Disposition": f"attachment; filename=sunny-ai-uge-{plan['uge_start']}.ics"})


# ---------------------------------------------------------------- Overblik
@app.get("/api/overview")
def overview():
    """Nøgletal og forhold, der kræver handling, fra samme plan som Ugeplan og assistent."""
    snap = current_snapshot()
    data = load_data(snap)
    tid = beregningstidspunkt()
    plan = current_plan(uge_for(tid), data)
    resultat = plan["resultat"]
    handlinger = [{"type": "ordre", "niveau": "fejl", "ordrelinje_id": u["ordrelinje_id"],
                   "titel": f"{u['ordre_id']}: {', '.join(a['tekst'] for a in u['aarsager'])}",
                   "besked": " ".join(a["besked"] for a in u["aarsager"])} for u in resultat["uplanlagte"]]
    handlinger += [{"type": "ordre", "niveau": "advarsel", "ordrelinje_id": a["ordrelinje_id"],
                    "titel": f"{a['ordre_id']}: {a['tekst']}", "besked": a["besked"]} for a in resultat["advarsler"]]
    handlinger += [{"type": "data", "niveau": p["niveau"], "titel": p["besked"], "besked": p["handling"],
                    "vare_id": p.get("vare_id")} for p in planner.valider(data, tid)]
    return jsonify(status=status_payload(data, resultat), plan={k: plan[k] for k in ("id", "label", "status")},
                   uge_start=plan["uge_start"], noegletal=resultat["noegletal"], raavarebehov=resultat["raavarebehov"],
                   handlinger=handlinger)


# ---------------------------------------------------------------- Regelbaseret demoassistent (F13, F14, R09)
def find_varer(tekst, varer):
    """Varenummer (fx R1) eller ord på mindst fire bogstaver, der indgår i varenavnet."""
    ord_ = re.findall(r"[\wæøå]+", tekst.lower())
    numre = [v for v in varer.values() if v["varenummer"].lower() in ord_]
    if numre:
        return numre
    return [v for v in varer.values() if any(len(o) >= 4 and o in v["navn"].lower() for o in ord_)]


def answer_order(ordre_id, data, plan, snap):
    linjer = [ol for ol in data["ordrelinjer"] if ol["ordre_id"].upper() == ordre_id]
    kilder = [{"type": "snapshot", "id": snap["id"], "label": f"Snapshot #{snap['id']}"}]
    if not linjer:
        return {"type": "ikke_fundet", "kilder": kilder,
                "svar": f"Ordre {ordre_id} findes ikke i snapshot #{snap['id']}. Jeg gætter ikke – kontrollér "
                        "ordrenummeret, eller spørg den ansvarlige for ordren."}
    dele = []
    for ol in linjer:
        vare = data["varer"][ol["vare_id"]]
        kilder.append({"type": "ordre", "id": ol["id"], "label": f"Ordre {ol['ordre_id']} ({ol['kilde_id']})"})
        res = next((l for l in plan["resultat"]["linjer"] if l["ordrelinje_id"] == ol["id"]), None)
        rest = planner.fmt_maengde(ol["bestilt_maengde"] - ol["leveret_maengde"], vare["basisenhed"])
        intro = f"Ordre {ol['ordre_id']} ({rest} {vare['navn']}, levering {planner.fmt_dag(ol['leveringsdato'])})"
        if ol["status"] != "åben":
            dele.append(f"{intro} er {ol['status']} og indgår ikke i planlægningen.")
            continue
        if res is None:
            dele.append(f"{intro} er ikke valgt i {plan['label'].lower()}.")
            continue
        for r in res["raavarebehov"]:
            kilder.append({"type": "vare", "id": r["raavare_id"], "label": f"{r['varenummer']} {r['navn']}"})
        if res["status"] == "dækket af lager":
            dele.append(f"{intro} dækkes af færdigvarelageret ({planner.fmt_maengde(res['lagerfradrag_maengde'], res['enhed'])}).")
        elif res["status"] == "blokeret":
            dele.append(f"{intro} kan ikke produceres i planforslaget. " +
                        " ".join(a["besked"] for a in res["aarsager"]))
        else:
            fordeling = "; ".join(f"{planner.fmt_dag(d['dato'])} {planner.fmt_maengde(d['maengde'], res['enhed'])} "
                                  f"({planner.fmt_minutter(d['minutter'])})" for d in res["dage"])
            tekst = f"{intro} kan produceres. Lagerfradrag {planner.fmt_maengde(res['lagerfradrag_maengde'], res['enhed'])}, " \
                    f"produktion: {fordeling}."
            if res["aarsager"]:
                tekst += " " + " ".join(a["besked"] for a in res["aarsager"])
            dele.append(tekst)
    kilder.append({"type": "plan", "id": plan["id"], "label": plan["label"]})
    return {"type": "svar", "svar": " ".join(dele), "kilder": kilder}


def answer_item(vare, data, snap, tid):
    dag = planner.as_datetime(tid).date()
    usikre = planner.usikre_varer(data)
    kilder = [{"type": "vare", "id": vare["id"], "label": f"{vare['varenummer']} {vare['navn']}"},
              {"type": "snapshot", "id": snap["id"], "label": f"Snapshot #{snap['id']}"}]
    if vare["id"] in usikre:
        return {"type": "svar", "kilder": kilder,
                "svar": f"Beholdningen af {vare['varenummer']} {vare['navn']} er uafklaret, fordi en færdigmelding "
                        "mangler. Jeg kan ikke give et sikkert tal. Afklar registreringen med lageret."}
    batches = [(b, *planner.batch_status(b, data, dag, usikre)) for b in data["batches"] if b["vare_id"] == vare["id"]]
    disponibelt = sum(m for _, m, grund in batches if grund is None)
    brugbare = sorted((b for b, m, grund in batches if grund is None and m > 0), key=lambda b: b["udloebsdato"])
    tekst = f"{vare['varenummer']} {vare['navn']}: {planner.fmt_maengde(disponibelt, vare['basisenhed'])} disponibelt"
    tekst += f" fordelt på {len(brugbare)} batch(es)." if brugbare else "."
    if brugbare:
        tekst += f" Første udløb er {planner.as_date(brugbare[0]['udloebsdato']).strftime('%d.%m.%Y')}."
    udelukket = [f"{b['batchnummer']} ({grund.lower()})" for b, _, grund in batches if grund]
    if udelukket:
        tekst += " Udelukket: " + ", ".join(udelukket) + "."
    return {"type": "svar", "svar": tekst, "kilder": kilder}


def answer_needs(plan):
    mangler = [r for r in plan["resultat"]["raavarebehov"] if r["mangel"] or r["disponibelt"] is None]
    kilder = [{"type": "plan", "id": plan["id"], "label": plan["label"]}]
    if not mangler:
        return {"type": "svar", "kilder": kilder, "svar": "Der mangler ingen råvarer i planforslaget."}
    dele = []
    for r in mangler:
        kilder.append({"type": "vare", "id": r["raavare_id"], "label": f"{r['varenummer']} {r['navn']}"})
        if r["disponibelt"] is None:
            dele.append(f"{r['varenummer']} {r['navn']}: behov {planner.fmt_maengde(r['behov'], r['enhed'])}, "
                        "beholdningen er uafklaret")
        else:
            dele.append(f"{r['varenummer']} {r['navn']}: behov {planner.fmt_maengde(r['behov'], r['enhed'])}, "
                        f"disponibelt {planner.fmt_maengde(r['disponibelt'], r['enhed'])}, "
                        f"mangel {planner.fmt_maengde(r['mangel'], r['enhed'])}")
    return {"type": "svar", "kilder": kilder,
            "svar": "Råvarer i mangel: " + "; ".join(dele) + ". Listen er et bruttobehov til vurdering – ikke en købsordre."}


def answer_plan(plan):
    r = plan["resultat"]
    dage = ", ".join(f"{d['ugedag']} {planner.fmt_minutter(d['brugt'])} af {planner.fmt_minutter(d['kapacitet'])}"
                     for d in r["dage"])
    tekst = f"{plan['label']}: {planner.fmt_minutter(r['noegletal']['planlagte_minutter'])} planlagt ({dage})."
    if r["uplanlagte"]:
        tekst += " Ikke planlagt: " + ", ".join(
            f"{u['ordre_id']} ({', '.join(a['tekst'].lower() for a in u['aarsager'])})" for u in r["uplanlagte"]) + "."
    return {"type": "svar", "svar": tekst, "kilder": [{"type": "plan", "id": plan["id"], "label": plan["label"]}]}


@app.post("/api/assistant")
def assistant():
    """Afgrænsede spørgsmål på dansk. Svarene bygger på samme plan og data som skærmene og opfinder intet.

    Body: {"spoergsmaal": "Kan ordre O2 produceres?", "vare_id": 4 (valgfri, når et varenavn var tvetydigt)}
    """
    body = json_body()
    require(body, "spoergsmaal")
    tekst = str(body["spoergsmaal"])[:500]
    lav = tekst.lower()
    snap = current_snapshot()
    data = load_data(snap)
    tid = beregningstidspunkt()
    plan = current_plan(uge_for(tid), data)

    ordre = re.search(r"\b(?:ordre\s*)?(o\s?\d+)\b", lav) or re.search(r"\bordre\s+(?:nr\.?\s*)?(\d+)\b", lav)
    if body.get("vare_id"):
        vare = data["varer"].get(int(body["vare_id"]))
        if vare is None:
            raise ApiError("Varen findes ikke", 404)
        svar = answer_item(vare, data, snap, tid)
    elif ordre:
        nummer = re.sub(r"\D", "", ordre.group(1))
        svar = answer_order(f"O{nummer}", data, plan, snap)
    elif any(k in lav for k in ("mangl", "indkøb", "råvarebehov", "købe", "bestille")):
        svar = answer_needs(plan)
    elif (varer := find_varer(tekst, data["varer"])):
        if len(varer) > 1:
            svar = {"type": "vaelg", "svar": "Flere varer passer på spørgsmålet. Hvilken mener du?",
                    "valg": [{"vare_id": v["id"], "label": f"{v['varenummer']} {v['navn']}"} for v in varer],
                    "kilder": []}
        else:
            svar = answer_item(varer[0], data, snap, tid)
    elif any(k in lav for k in ("plan", "uge", "kapacitet", "timer")):
        svar = answer_plan(plan)
    elif any(k in lav for k in ("uniconta", "hvordan", "vejledning")):
        svar = {"type": "uden_for_data", "kilder": [],
                "svar": "Der findes ingen godkendt vejledning i Sunny AI, så jeg giver ingen instruks. "
                        "Spørg den ansvarlige for Uniconta."}
    else:
        svar = {"type": "uden_for_data", "kilder": [],
                "svar": "Det kan jeg ikke svare på ud fra ordrer, lager og planforslag. Prøv fx “Kan ordre O2 "
                        "produceres?”, “Hvor meget R1 har vi?” eller “Hvilke råvarer mangler?”."}
    return jsonify({**svar, "spoergsmaal": tekst, "assistent": "Regelbaseret demoassistent (ingen sprogmodel)",
                    "snapshot_tidspunkt": snap["source_updated_at"], "snapshot_id": snap["id"],
                    "plan": {k: plan[k] for k in ("id", "label", "status")}})


# ---------------------------------------------------------------- Historik og nulstilling (F15)
@app.get("/api/events")
def events():
    """Hændelseslog: snapshots, beregninger, godkendelser og ændringer af demo-uret."""
    return jsonify(query_all("SELECT * FROM haendelse ORDER BY id DESC LIMIT 100"))


@app.post("/api/reset")
def reset():
    """Genskab demoens startdata. Kræver {"bekraeft": true}."""
    if json_body().get("bekraeft") is not True:
        raise ApiError("Nulstilling kræver bekræftelse: {\"bekraeft\": true}")
    close_db()
    init_db(reset=True)
    return jsonify(status_payload())


if __name__ == "__main__":
    init_db()
    run(app, PORT)
