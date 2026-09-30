"""LOGIKLAG – planmotor for Sunny AI (datavalidering og R01–R08).

Ren Python uden Flask og SQLite, så beregningsreglerne kan testes alene (N07).
UI og assistent bruger begge resultatet herfra og har ingen egne kopier af nøgletal.

Mængder er heltal i tusindedele af varens basisenhed (1 stk = 1000), tid er hele minutter,
datoer er YYYY-MM-DD. Ukendte værdier er None og omfortolkes aldrig til nul.

data = {
    "snapshot":          {"id", "source_updated_at", ...},
    "varer":             {vare_id: {"id", "varenummer", "navn", "type", "basisenhed"}},
    "rater":             {vare_id: enheder_pr_time},
    "batches":           [{"id", "vare_id", "batchnummer", "fysisk_maengde", "reserveret_maengde",
                           "udloebsdato", "kvalitetsstatus", "data_afklaret"}],
    "ordrelinjer":       [{"id", "ordre_id", "kilde_id", "vare_id", "bestilt_maengde", "leveret_maengde",
                           "leveringsdato", "status", "prioritet", "saesonmaerke"}],
    "produktionsstatus": [{"id", "ordrelinje_id", "status", "affected_item_ids", "afklaring_paakraevet", "beskrivelse"}],
    "ressourcebehov":    {ordrelinje_id: [{"raavare_id", "maengde_pr_enhed"}]},
    "kapacitet":         {dato: disponible_minutter},
}
"""
import math
from datetime import date, datetime, timedelta

# ---------------------------------------------------------------- Navngivne parametre (N07)
STANDARD_KAPACITET_MIN = 480          # 8 timer pr. hverdag
MAX_KAPACITET_MIN = 1440
HVERDAGE = 5
SAESON_MAANEDER = (9, 10, 11)         # gløggsæson september–november (F08)
SNAPSHOT_MAX_ALDER_TIMER = 24         # R01, testantagelse
UDLOEB_ADVARSEL_DAGE = 7              # F05

AARSAGER = {
    "DATA_MISSING": "Mangler eller usikre data",
    "MATERIAL_SHORTAGE": "Råvaremangel",
    "CAPACITY_SHORTAGE": "Kapacitetsmangel",
    "DEADLINE_RISK": "Risiko for forsinkelse",
}

ANTAGELSER = [
    "Ét samlet lager og ét produktionscenter med én ressource.",
    f"Standardkapacitet {STANDARD_KAPACITET_MIN // 60} timer pr. hverdag, mandag–fredag.",
    "Omstillingstid er indregnet i produktionsraten (0 i eksempeldata).",
    "En ordre må deles mellem dage. Tid rundes op til hele minutter.",
    "Sæsonmærke tæller kun ved leveringsdato i september–november og skaber ikke ekstra efterspørgsel.",
    "Ressourcebehov og rater er fiktive demoværdier.",
    "Batches vælges efter først udløb først ud. Allokeringer er forslag og ændrer ikke kildelageret.",
]

UGEDAGE = ["mandag", "tirsdag", "onsdag", "torsdag", "fredag", "lørdag", "søndag"]


class PlanFejl(ValueError):
    """Ugyldige parametre, fx en ugestart der ikke er en mandag."""


def as_date(value):
    return date.fromisoformat(value[:10])


def as_datetime(value):
    return datetime.fromisoformat(value.replace("T", " "))


def fmt_maengde(milli, enhed):
    """Dansk visning: 40000, 'L' -> '40 L', 500, 'L' -> '0,5 L'."""
    if milli is None:
        return "ukendt"
    tal = f"{milli / 1000:,.3f}".rstrip("0").rstrip(".").replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{tal} {enhed or '(ukendt enhed)'}"


def fmt_minutter(minutter):
    timer, rest = divmod(minutter, 60)
    return f"{timer} t {rest} min" if rest else f"{timer} t"


def fmt_dag(dato):
    d = as_date(dato)
    return f"{UGEDAGE[d.weekday()]} {d.strftime('%d.%m.%Y')}"


def minutter_for(maengde, rate):
    """R06: tid ud fra mængde og rate, rundet op til hele minutter."""
    return math.ceil(maengde * 60 / (rate * 1000))


def max_maengde(minutter, rate, enhed):
    """Største mængde, hvis afrundede tid holder sig inden for minutterne. Stk. produceres i hele enheder."""
    maengde = minutter * rate * 1000 // 60
    return maengde - maengde % 1000 if enhed == "stk" else maengde


def raavarebehov_for(maengde, pr_enhed):
    """R05: råvarebehov = produktionsmængde × mængde pr. enhed (rundet op, så der aldrig mangler)."""
    return math.ceil(maengde * pr_enhed / 1000)


def snapshot_alder(snapshot, tidspunkt):
    timer = (as_datetime(tidspunkt) - as_datetime(snapshot["source_updated_at"])).total_seconds() / 3600
    return {"alder_timer": round(timer, 1), "foraeldet": timer > SNAPSHOT_MAX_ALDER_TIMER}


def usikre_varer(data):
    """R01: en kendt uafklaret færdigmelding gør de angivne varer usikre, indtil et afklaret snapshot modtages."""
    ids = set()
    for ps in data["produktionsstatus"]:
        if ps["afklaring_paakraevet"]:
            ids.update(int(x) for x in str(ps["affected_item_ids"] or "").split(",") if x.strip())
    return ids


def batch_status(batch, data, beregningsdato, usikre=None):
    """R02: returnerer (disponibel mængde, grund). Grund er None, når batchen må bruges."""
    vare = data["varer"][batch["vare_id"]]
    usikre = usikre_varer(data) if usikre is None else usikre
    if not vare["basisenhed"]:
        return 0, "Varen mangler enhed"
    if batch["fysisk_maengde"] < 0:
        return 0, "Negativ beholdning i kilden"
    if batch["reserveret_maengde"] > batch["fysisk_maengde"]:
        return 0, "Reservation overstiger fysisk mængde"
    if batch["kvalitetsstatus"] != "frigivet":
        return 0, f"Ikke frigivet ({batch['kvalitetsstatus']})"
    if not batch["data_afklaret"]:
        return 0, "Batchdata er ikke afklaret"
    if not batch["udloebsdato"]:
        return 0, "Ukendt udløbsdato"
    if as_date(batch["udloebsdato"]) < beregningsdato:
        return 0, "Udløbet"
    if batch["vare_id"] in usikre:
        return 0, "Uafklaret færdigmelding"
    return batch["fysisk_maengde"] - batch["reserveret_maengde"], None


def disponibelt_pr_vare(data, beregningsdato):
    """Disponibelt lager pr. vare. None betyder, at beholdningen er uafklaret (ikke nul)."""
    usikre = usikre_varer(data)
    total = {vare_id: (None if vare_id in usikre else 0) for vare_id in data["varer"]}
    for b in data["batches"]:
        maengde, grund = batch_status(b, data, beregningsdato, usikre)
        if grund is None:
            total[b["vare_id"]] += maengde
    return total


# ---------------------------------------------------------------- Datavalidering (F02, F04, F05)
def valider(data, tidspunkt):
    """Kendte dataproblemer. Hvert problem siger, hvad der mangler, og hvad brugeren kan gøre (N02)."""
    beregningsdato = as_datetime(tidspunkt).date()
    varer = data["varer"]
    problemer = []

    def tilfoej(niveau, kode, besked, handling, **ref):
        problemer.append({"niveau": niveau, "kode": kode, "besked": besked, "handling": handling, **ref})

    alder = snapshot_alder(data["snapshot"], tidspunkt)
    if alder["foraeldet"]:
        tilfoej("fejl", "SNAPSHOT_FORAELDET",
                f"Kildedata er {alder['alder_timer']:.0f} timer gamle (grænse {SNAPSHOT_MAX_ALDER_TIMER} timer).",
                "Indlæs et nyt snapshot, før en plan godkendes.")

    for vare in varer.values():
        if not vare["basisenhed"]:
            tilfoej("fejl", "ENHED_MANGLER", f"{vare['varenummer']} {vare['navn']} mangler basisenhed.",
                    "Ret enheden på varekortet i kildesystemet.", vare_id=vare["id"])
        if vare["type"] == "færdigvare" and not data["rater"].get(vare["id"]):
            tilfoej("fejl", "RATE_MANGLER", f"{vare['varenummer']} {vare['navn']} har ingen produktionsrate.",
                    "Aftal en rate med produktionen.", vare_id=vare["id"])

    usikre = usikre_varer(data)
    for b in data["batches"]:
        vare = varer[b["vare_id"]]
        navn = f"{vare['varenummer']} batch {b['batchnummer']}"
        maengde, grund = batch_status(b, data, beregningsdato, usikre)
        if grund in ("Negativ beholdning i kilden", "Reservation overstiger fysisk mængde", "Ukendt udløbsdato",
                     "Batchdata er ikke afklaret"):
            tilfoej("fejl", "BATCH_DATA", f"{navn}: {grund.lower()}. Batchen indgår ikke i disponibelt lager.",
                    "Kontrollér batchen fysisk og ret registreringen i kildesystemet.",
                    vare_id=vare["id"], batch_id=b["id"])
        elif grund == "Udløbet":
            tilfoej("advarsel", "BATCH_UDLOEBET",
                    f"{navn} udløb {as_date(b['udloebsdato']).strftime('%d.%m.%Y')} og er udelukket fra disponibelt lager.",
                    "Kassér eller spær batchen i kildesystemet.", vare_id=vare["id"], batch_id=b["id"])
        elif grund is None and maengde > 0 and \
                (as_date(b["udloebsdato"]) - beregningsdato).days <= UDLOEB_ADVARSEL_DAGE:
            tilfoej("advarsel", "UDLOEB_SNART",
                    f"{navn} ({fmt_maengde(maengde, vare['basisenhed'])}) udløber "
                    f"{as_date(b['udloebsdato']).strftime('%d.%m.%Y')}.",
                    "Overvej at bruge batchen først eller undgå nyt indkøb.", vare_id=vare["id"], batch_id=b["id"])

    for ps in data["produktionsstatus"]:
        if ps["afklaring_paakraevet"]:
            navne = ", ".join(f"{varer[i]['varenummer']} {varer[i]['navn']}"
                              for i in sorted(usikre_varer({"produktionsstatus": [ps]})) if i in varer)
            tilfoej("fejl", "UAFKLARET_FAERDIGMELDING",
                    f"{ps['status']}: beholdningen af {navne} er usikker. {ps['beskrivelse'] or ''}".strip(),
                    "Afklar færdigmeldingen med lageret og indlæs et nyt snapshot. Sunny AI retter ikke kildetallet.",
                    produktionsstatus_id=ps["id"])

    for ol in data["ordrelinjer"]:
        if ol["status"] == "åben" and not data["ressourcebehov"].get(ol["id"]):
            tilfoej("fejl", "RESSOURCEBEHOV_UKENDT", f"Ordre {ol['ordre_id']} har ukendt råvarebehov.",
                    "Angiv ressourcebehov for ordrelinjen, før den kan planlægges.", ordrelinje_id=ol["id"])
    return problemer


# ---------------------------------------------------------------- Sortering (R03)
def saeson_aktiv(ordrelinje):
    return bool(ordrelinje["saesonmaerke"]) and as_date(ordrelinje["leveringsdato"]).month in SAESON_MAANEDER


def sorteringsnoegle(linje):
    """R03: høj prioritet før normal, så tidligste leveringsdato, så aktivt sæsonmærke, til sidst id."""
    return (0 if linje["prioritet"] == "høj" else 1, linje["leveringsdato"], 0 if linje["saeson_aktiv"] else 1, linje["id"])


# ---------------------------------------------------------------- Planberegning (R02–R07)
def beregn_plan(data, uge_start, tidspunkt, parametre=None):
    """Deterministisk ugeplanforslag (F07). Samme snapshot, tidspunkt og parametre giver samme plan.

    parametre = {"ordrelinje_ids": [..] eller None (alle åbne),
                 "kapacitet": {"2026-10-05": 240, ...},
                 "prioritet": {"2": "høj", ...}}
    """
    parametre = parametre or {}
    beregningsdato = as_datetime(tidspunkt).date()
    try:
        start = date.fromisoformat(uge_start)
    except (TypeError, ValueError):
        raise PlanFejl("Ugestart skal være en dato (YYYY-MM-DD)")
    if start.weekday() != 0:
        raise PlanFejl("Ugestart skal være en mandag")
    varer, rater = data["varer"], data["rater"]

    # Kapacitet pr. dag. Dage før beregningsdatoen kan ikke planlægges.
    kap_param = {k: int(v) for k, v in (parametre.get("kapacitet") or {}).items()}
    dage = []
    for i in range(HVERDAGE):
        dato = (start + timedelta(days=i)).isoformat()
        kapacitet = kap_param.get(dato, data["kapacitet"].get(dato, STANDARD_KAPACITET_MIN))
        if not 0 <= kapacitet <= MAX_KAPACITET_MIN:
            raise PlanFejl(f"Kapacitet for {dato} skal være mellem 0 og {MAX_KAPACITET_MIN} minutter")
        fortid = as_date(dato) < beregningsdato
        dage.append({"dato": dato, "ugedag": UGEDAGE[i], "kapacitet": kapacitet, "brugt": 0, "fortid": fortid,
                     "manuel": dato in kap_param})
    ledig = {d["dato"]: 0 if d["fortid"] else d["kapacitet"] for d in dage}

    # Disponibelt lager som arbejdskopi: batch_id -> resterende mængde (R02, R04)
    usikre = usikre_varer(data)
    lager, batches = {}, {}
    for b in data["batches"]:
        maengde, grund = batch_status(b, data, beregningsdato, usikre)
        if grund is None and maengde > 0:
            lager[b["id"]] = maengde
            batches[b["id"]] = b
    disponibelt_start = disponibelt_pr_vare(data, beregningsdato)

    def alloker(arbejdskopi, vare_id, behov, senest_brugt):
        """FEFO: tag fra batchen med først udløb, som holder til brugsdatoen. Returnerer (fået, referencer)."""
        kandidater = sorted((b for bid, b in batches.items()
                             if b["vare_id"] == vare_id and arbejdskopi.get(bid, 0) > 0
                             and as_date(b["udloebsdato"]) >= as_date(senest_brugt)),
                            key=lambda b: (b["udloebsdato"], b["id"]))
        faaet, refs = 0, []
        for b in kandidater:
            if faaet >= behov:
                break
            tag = min(behov - faaet, arbejdskopi[b["id"]])
            arbejdskopi[b["id"]] -= tag
            faaet += tag
            refs.append({"batch_id": b["id"], "batchnummer": b["batchnummer"], "vare_id": vare_id, "maengde": tag})
        return faaet, refs

    # Åbne ordrelinjer (F06)
    valgte = parametre.get("ordrelinje_ids")
    valgte = None if valgte is None else {int(i) for i in valgte}
    prio_param = {int(k): v for k, v in (parametre.get("prioritet") or {}).items()}
    linjer = []
    for ol in data["ordrelinjer"]:
        if valgte is not None and ol["id"] not in valgte:
            continue
        if ol["status"] != "åben":
            if valgte is not None:
                raise PlanFejl(f"Ordre {ol['ordre_id']} er {ol['status']} og kan ikke planlægges")
            continue
        rest = ol["bestilt_maengde"] - ol["leveret_maengde"]
        if rest <= 0:
            continue
        prioritet = prio_param.get(ol["id"], ol["prioritet"])
        if prioritet not in ("normal", "høj"):
            raise PlanFejl("Prioritet skal være normal eller høj")
        linjer.append({**ol, "rest": rest, "prioritet": prioritet, "prioritet_manuel": ol["id"] in prio_param,
                       "saeson_aktiv": saeson_aktiv(ol)})
    linjer.sort(key=sorteringsnoegle)

    planlinjer, resultater, behov_pr_raavare = [], [], {}

    for linje in linjer:
        vare = varer[linje["vare_id"]]
        enhed = vare["basisenhed"]
        res = {
            "ordrelinje_id": linje["id"], "ordre_id": linje["ordre_id"], "kilde_id": linje["kilde_id"],
            "vare_id": vare["id"], "varenummer": vare["varenummer"], "varenavn": vare["navn"], "enhed": enhed,
            "rest": linje["rest"], "leveringsdato": linje["leveringsdato"], "prioritet": linje["prioritet"],
            "prioritet_manuel": linje["prioritet_manuel"], "saeson_aktiv": linje["saeson_aktiv"],
            "forfalden": as_date(linje["leveringsdato"]) < beregningsdato,
            "lagerfradrag": [], "lagerfradrag_maengde": 0, "produktionsbehov": None, "rate": rater.get(vare["id"]),
            "raavarebehov": [], "dage": [], "planlagt_maengde": 0, "minutter": 0, "uplanlagt_maengde": 0,
            "aarsager": [], "status": "planlagt", "forklaring": [],
        }
        forklaring = res["forklaring"]
        forklaring.append(f"Ordre {linje['ordre_id']}: {fmt_maengde(linje['rest'], enhed)} {vare['navn']} "
                          f"med levering {fmt_dag(linje['leveringsdato'])}. Prioritet {linje['prioritet']}"
                          + (" (manuelt ændret)" if linje["prioritet_manuel"] else "")
                          + (", sæsonmærket" if linje["saeson_aktiv"] else "") + ".")

        def aarsag(kode, besked):
            res["aarsager"].append({"kode": kode, "tekst": AARSAGER[kode], "besked": besked})
            forklaring.append(besked)

        if res["forfalden"]:
            aarsag("DEADLINE_RISK", "Leveringsdatoen er allerede overskredet.")

        # R04: færdigvarer fra lager først
        if vare["id"] in usikre:
            aarsag("DATA_MISSING", f"Beholdningen af {vare['varenummer']} er uafklaret. Lagerfradrag og "
                                   "produktionsbehov kan ikke beregnes sikkert.")
            res.update(status="blokeret", uplanlagt_maengde=linje["rest"])
            resultater.append(res)
            continue
        faaet, refs = alloker(lager, vare["id"], linje["rest"], linje["leveringsdato"])
        res["lagerfradrag"], res["lagerfradrag_maengde"] = refs, faaet
        produktion = max(0, linje["rest"] - faaet)
        res["produktionsbehov"] = produktion
        forklaring.append(f"Lagerfradrag: {fmt_maengde(faaet, enhed)} færdigvare. "
                          f"Produktionsbehov: {fmt_maengde(produktion, enhed)}.")
        if produktion == 0:
            res["status"] = "dækket af lager"
            resultater.append(res)
            continue

        # Råvarebehov for hele produktionsbehovet (bruges også i indkøbslisten, R07)
        mangler = []
        behov = data["ressourcebehov"].get(linje["id"]) or []
        if not res["rate"]:
            mangler.append("produktionsrate")
        if not behov:
            mangler.append("ressourcebehov")
        for r in behov:
            raavare = varer[r["raavare_id"]]
            maengde = raavarebehov_for(produktion, r["maengde_pr_enhed"])
            res["raavarebehov"].append({"raavare_id": raavare["id"], "varenummer": raavare["varenummer"],
                                        "navn": raavare["navn"], "enhed": raavare["basisenhed"],
                                        "pr_enhed": r["maengde_pr_enhed"], "behov": maengde})
            post = behov_pr_raavare.setdefault(raavare["id"], {"planlagt": 0, "uplanlagt": 0})
            post["uplanlagt"] += maengde           # flyttes til planlagt, hvis produktionen planlægges
            if not raavare["basisenhed"]:
                mangler.append(f"enhed på {raavare['varenummer']}")
            if raavare["id"] in usikre:
                mangler.append(f"afklaret beholdning af {raavare['varenummer']} (uafklaret færdigmelding)")
        if res["raavarebehov"]:
            forklaring.append("Råvarebehov: " + ", ".join(
                f"{fmt_maengde(r['behov'], r['enhed'])} {r['varenummer']} "
                f"({fmt_maengde(r['pr_enhed'], r['enhed'])} pr. {enhed})" for r in res["raavarebehov"]) + ".")
        if mangler:
            aarsag("DATA_MISSING", "Kan ikke planlægges, fordi der mangler: " + ", ".join(mangler) + ".")
            res.update(status="blokeret", uplanlagt_maengde=produktion)
            resultater.append(res)
            continue

        # R06: midlertidig dagfordeling på tidligst mulige hverdage
        rate = res["rate"]
        forklaring.append(f"Produktionsrate: {rate} {enhed}/time.")
        forsoeg, rest = [], produktion
        for dag in dage:
            if rest == 0:
                break
            maengde = min(rest, max_maengde(ledig[dag["dato"]], rate, enhed))
            if maengde > 0:
                forsoeg.append({"dato": dag["dato"], "maengde": maengde, "minutter": minutter_for(maengde, rate)})
                rest -= maengde

        if not forsoeg:
            aarsag("CAPACITY_SHORTAGE", f"Ingen ledig kapacitet i ugen. {fmt_maengde(produktion, enhed)} er ikke planlagt.")
            res.update(status="blokeret", uplanlagt_maengde=produktion)
            resultater.append(res)
            continue

        # R05: råvarer og holdbarhed på hver brugsdato. Mangler noget, afvises hele produktionen.
        arbejdskopi = dict(lager)
        mangel = {}
        for r in behov:
            skal_i_alt = 0
            for chunk in forsoeg:
                skal = raavarebehov_for(chunk["maengde"], r["maengde_pr_enhed"])
                fik, refs = alloker(arbejdskopi, r["raavare_id"], skal, chunk["dato"])
                chunk.setdefault("refs", []).extend(refs)
                skal_i_alt += skal
                if fik < skal:
                    mangel.setdefault(r["raavare_id"], {"mangel": 0})["mangel"] += skal - fik
            if r["raavare_id"] in mangel:
                mangel[r["raavare_id"]]["behov"] = skal_i_alt
        if mangel:
            tekst = ", ".join(
                f"{varer[rid]['varenummer']} {varer[rid]['navn']} mangler {fmt_maengde(m['mangel'], varer[rid]['basisenhed'])} "
                f"(behov {fmt_maengde(m['behov'], varer[rid]['basisenhed'])}, tilbage "
                f"{fmt_maengde(m['behov'] - m['mangel'], varer[rid]['basisenhed'])} efter tidligere ordrer)"
                for rid, m in mangel.items())
            aarsag("MATERIAL_SHORTAGE", f"Råvaremangel: {tekst}. Produktionen er ikke planlagt, og der er ikke "
                                        "reserveret tid eller råvarer.")
            res["mangel"] = [{"raavare_id": rid, "varenummer": varer[rid]["varenummer"],
                              "enhed": varer[rid]["basisenhed"], **m} for rid, m in mangel.items()]
            res.update(status="blokeret", uplanlagt_maengde=produktion)
            resultater.append(res)
            continue

        # Forsøget holder: bind tid og råvarer i planens arbejdskopi
        lager = arbejdskopi
        for chunk in forsoeg:
            ledig[chunk["dato"]] -= chunk["minutter"]
            planlinjer.append({"ordrelinje_id": linje["id"], "ordre_id": linje["ordre_id"], "varenummer": vare["varenummer"],
                               "enhed": enhed, "dato": chunk["dato"], "maengde": chunk["maengde"],
                               "minutter": chunk["minutter"], "allocated_batch_refs": chunk["refs"]})
        planlagt = produktion - rest
        for r in res["raavarebehov"]:
            planlagt_behov = raavarebehov_for(planlagt, r["pr_enhed"])
            behov_pr_raavare[r["raavare_id"]]["planlagt"] += planlagt_behov
            behov_pr_raavare[r["raavare_id"]]["uplanlagt"] -= planlagt_behov
        res["dage"] = [{k: c[k] for k in ("dato", "maengde", "minutter")} for c in forsoeg]
        res["planlagt_maengde"] = planlagt
        res["minutter"] = sum(c["minutter"] for c in forsoeg)
        forklaring.append("Fordeling: " + "; ".join(
            f"{fmt_dag(c['dato'])} {fmt_maengde(c['maengde'], enhed)} ({fmt_minutter(c['minutter'])})" for c in forsoeg) + ".")
        if rest > 0:
            aarsag("CAPACITY_SHORTAGE", f"Ugekapaciteten rækker ikke: {fmt_maengde(rest, enhed)} er ikke planlagt (restbehov).")
            res.update(status="delvist planlagt", uplanlagt_maengde=rest)
        if any(c["dato"] > linje["leveringsdato"] for c in forsoeg):
            aarsag("DEADLINE_RISK", f"Produktion efter leveringsdatoen {fmt_dag(linje['leveringsdato'])}.")
        resultater.append(res)

    for dag in dage:
        dag["brugt"] = sum(p["minutter"] for p in planlinjer if p["dato"] == dag["dato"])

    # R07: bruttobehov pr. råvare for planlagt og uplanlagt produktion
    raavarebehov = []
    for raavare_id, post in sorted(behov_pr_raavare.items()):
        raavare = varer[raavare_id]
        disponibelt = disponibelt_start.get(raavare_id)
        total = post["planlagt"] + post["uplanlagt"]
        raavarebehov.append({
            "raavare_id": raavare_id, "varenummer": raavare["varenummer"], "navn": raavare["navn"],
            "enhed": raavare["basisenhed"], "behov_planlagt": post["planlagt"], "behov_uplanlagt": post["uplanlagt"],
            "behov": total, "disponibelt": disponibelt,
            "mangel": None if disponibelt is None else max(0, total - disponibelt),
        })

    uplanlagte = [{"ordrelinje_id": r["ordrelinje_id"], "ordre_id": r["ordre_id"], "status": r["status"],
                   "uplanlagt_maengde": r["uplanlagt_maengde"], "enhed": r["enhed"],
                   "aarsager": [a for a in r["aarsager"] if a["kode"] != "DEADLINE_RISK"]}
                  for r in resultater if r["status"] in ("blokeret", "delvist planlagt")]
    advarsler = [{"ordrelinje_id": r["ordrelinje_id"], "ordre_id": r["ordre_id"], **a}
                 for r in resultater for a in r["aarsager"] if a["kode"] == "DEADLINE_RISK"]

    return {
        "uge_start": uge_start,
        "beregningstidspunkt": tidspunkt,
        "snapshot_id": data["snapshot"]["id"],
        "dage": dage,
        "linjer": resultater,
        "planlinjer": planlinjer,
        "uplanlagte": uplanlagte,
        "advarsler": advarsler,
        "raavarebehov": raavarebehov,
        "antagelser": ANTAGELSER,
        "noegletal": {
            "ordrer_i_plan": len(resultater),
            "planlagte_minutter": sum(p["minutter"] for p in planlinjer),
            "kapacitet_minutter": sum(0 if d["fortid"] else d["kapacitet"] for d in dage),
            "blokerede": sum(1 for r in resultater if r["status"] == "blokeret"),
            "delvist_planlagte": sum(1 for r in resultater if r["status"] == "delvist planlagt"),
            "raavarer_i_mangel": sum(1 for r in raavarebehov if r["mangel"]),
        },
    }
