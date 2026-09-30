"""Automatiske accepttests T01–T10 og N04 fra kravspecifikationen.

    python tests.py

Hver test kører på friske eksempeldata i en midlertidig database. T11 (tastatur) testes manuelt i browseren.
"""
import os
import tempfile
import time
import unittest

os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")

import planner  # noqa: E402
from app import app  # noqa: E402
from database import init_db  # noqa: E402

UGE = "2026-10-05"


class SunnyAiTest(unittest.TestCase):
    def setUp(self):
        init_db(reset=True)
        self.client = app.test_client()

    def post(self, path, body, status=None):
        response = self.client.post(f"/api{path}", json=body)
        if status:
            self.assertEqual(response.status_code, status, response.get_json())
        return response.get_json()

    def plan(self, **params):
        return self.post("/plans", {"uge_start": UGE, **params}, 201)

    @staticmethod
    def line(plan, ordre_id):
        return next(l for l in plan["resultat"]["linjer"] if l["ordre_id"] == ordre_id)

    @staticmethod
    def codes(line):
        return [a["kode"] for a in line["aarsager"]]

    def test_t01_startdata_og_plan(self):
        plan = self.plan()
        o1, o2, o3 = (self.line(plan, o) for o in ("O1", "O2", "O3"))
        self.assertEqual((o1["lagerfradrag_maengde"], o1["planlagt_maengde"], o1["minutter"]), (20000, 80000, 240))
        self.assertEqual(o2["status"], "blokeret")
        self.assertEqual(self.codes(o2), ["MATERIAL_SHORTAGE"])
        self.assertEqual(o2["mangel"][0]["mangel"], 10000)
        self.assertEqual([(d["dato"], d["maengde"]) for d in o3["dage"]], [("2026-10-05", 80000), ("2026-10-06", 120000)])
        dage = {d["dato"]: d["brugt"] for d in plan["resultat"]["dage"]}
        self.assertEqual((dage["2026-10-05"], dage["2026-10-06"]), (480, 360))
        self.assertTrue(all(d["brugt"] <= d["kapacitet"] for d in plan["resultat"]["dage"]))
        r1 = next(r for r in plan["resultat"]["raavarebehov"] if r["varenummer"] == "R1")
        self.assertEqual((r1["behov"], r1["disponibelt"], r1["mangel"]), (70000, 60000, 10000))
        self.assertEqual(plan["resultat"], self.plan()["resultat"], "samme input skal give samme plan (F07)")

    def test_t02_raavare_udloebet(self):
        self.post("/source/import", {"type": "udloeb_batch", "batchnummer": "B-R1-001"}, 201)
        plan = self.plan()
        for ordre in ("O1", "O2"):
            self.assertIn("MATERIAL_SHORTAGE", self.codes(self.line(plan, ordre)))
        r1 = next(r for r in plan["resultat"]["raavarebehov"] if r["varenummer"] == "R1")
        self.assertEqual(r1["disponibelt"], 0)
        stock = self.client.get("/api/stock?q=R1").get_json()
        self.assertEqual(stock[0]["spaerret_grund"], "Udløbet")
        self.assertTrue(all((s["disponibel"] or 0) >= 0 for s in self.client.get("/api/stock").get_json()))

    def test_t03_forsinket_faerdigmelding(self):
        self.post("/source/import", {"type": "uafklaret_faerdigmelding", "vare_id": 4}, 201)
        plan = self.plan()
        for ordre in ("O1", "O2"):
            line = self.line(plan, ordre)
            self.assertEqual(line["status"], "blokeret")
            self.assertEqual(self.codes(line), ["DATA_MISSING"])
        r1 = next(r for r in plan["resultat"]["raavarebehov"] if r["varenummer"] == "R1")
        self.assertIsNone(r1["disponibelt"], "uafklaret beholdning må ikke blive til et tal")
        svar = self.post("/assistant", {"spoergsmaal": "Hvor meget R1 har vi?"}, 200)
        self.assertIn("uafklaret", svar["svar"])

    def test_t04_aendret_kapacitet(self):
        v1 = self.plan()
        v2 = self.plan(kapacitet={"2026-10-05": 240})
        self.assertEqual(v2["versionsnummer"], v1["versionsnummer"] + 1)
        self.assertEqual(self.client.get(f"/api/plans/{v1['id']}").get_json()["status"], "stale")
        self.assertEqual(self.line(v2, "O1")["dage"], [{"dato": "2026-10-05", "maengde": 80000, "minutter": 240}])
        self.assertEqual([d["dato"] for d in self.line(v2, "O3")["dage"]], ["2026-10-06", "2026-10-07"])
        self.assertTrue(v2["manuelle_parametre"])

    def test_t05_saeson_og_lighed(self):
        for ordre, saeson in (("O5", False), ("O6", True)):
            self.post("/source/import", {"type": "ny_ordre", "ordre_id": ordre, "vare_id": 3, "antal": 10,
                                         "leveringsdato": "2026-10-09", "saesonmaerke": saeson}, 201)
        orden = [l["ordre_id"] for l in self.plan()["resultat"]["linjer"]]
        self.assertLess(orden.index("O6"), orden.index("O5"))
        ude_af_saeson = [{"id": i, "prioritet": "normal", "leveringsdato": "2026-12-10", "saeson_aktiv":
                          planner.saeson_aktiv({"saesonmaerke": s, "leveringsdato": "2026-12-10"})}
                         for i, s in ((5, 0), (6, 1))]
        self.assertEqual([l["id"] for l in sorted(ude_af_saeson, key=planner.sorteringsnoegle)], [5, 6])

    def test_t06_assistent_og_tal(self):
        plan = self.plan()
        svar = self.post("/assistant", {"spoergsmaal": "Kan ordre O2 produceres?"}, 200)
        self.assertIn("10 L", svar["svar"])
        self.assertEqual(svar["snapshot_tidspunkt"], "2026-10-05 08:00")
        self.assertEqual(svar["plan"]["id"], plan["id"])
        kilder = {(k["type"], k["id"]) for k in svar["kilder"]}
        self.assertTrue({("ordre", 2), ("vare", 4)} <= kilder)

    def test_t07_ukendt_og_tvetydigt(self):
        self.assertEqual(self.post("/assistant", {"spoergsmaal": "Kan ordre O9 produceres?"}, 200)["type"], "ikke_fundet")
        svar = self.post("/assistant", {"spoergsmaal": "Hvor meget æble har vi?"}, 200)
        self.assertEqual(svar["type"], "vaelg")
        self.assertEqual(len(svar["valg"]), 2)
        self.assertEqual(self.post("/assistant", {"spoergsmaal": "Hvad bliver vejret i morgen?"}, 200)["type"],
                         "uden_for_data")

    def test_t08_godkendelse_og_genindlaesning(self):
        plan = self.plan()
        self.post(f"/plans/{plan['id']}/approve", {"request_id": "a"}, 400)
        godkendt = self.post(f"/plans/{plan['id']}/approve", {"request_id": "b", "accepter_uplanlagte": True}, 200)
        self.assertEqual((godkendt["status"], godkendt["delvis"]), ("approved", 1))
        self.assertEqual(self.client.get(f"/api/plans/{plan['id']}").get_json()["status"], "approved")
        self.post("/source/import", {"type": "genindlaes"}, 201)
        self.assertEqual(self.client.get(f"/api/plans/{plan['id']}").get_json()["status"], "stale")

    def test_t09_dobbeltklik(self):
        plan = self.plan()
        body = {"request_id": "dobbelt", "accepter_uplanlagte": True}
        self.post(f"/plans/{plan['id']}/approve", body, 200)
        self.assertTrue(self.post(f"/plans/{plan['id']}/approve", body, 200)["gentaget"])
        events = [e for e in self.client.get("/api/events").get_json() if e["type"] == "Plan godkendt"]
        self.assertEqual(len(events), 1)
        self.post(f"/plans/{plan['id']}/approve", {"request_id": "ny", "accepter_uplanlagte": True}, 409)

    def test_t10_ugekapacitet_mangler(self):
        kapacitet = {"2026-10-05": 240, **{d: 0 for d in ("2026-10-06", "2026-10-07", "2026-10-08", "2026-10-09")}}
        plan = self.plan(kapacitet=kapacitet)
        self.assertEqual(plan["resultat"]["noegletal"]["planlagte_minutter"], 240)
        o3 = self.line(plan, "O3")
        self.assertEqual((o3["status"], self.codes(o3), o3["uplanlagt_maengde"]),
                         ("blokeret", ["CAPACITY_SHORTAGE"], 200000))

    def test_foraeldet_snapshot_og_nulstilling(self):
        plan = self.plan()
        self.client.put("/api/clock", json={"beregningstidspunkt": "2026-10-06 09:00"})
        self.assertEqual(self.client.get(f"/api/plans/{plan['id']}").get_json()["status"], "stale")
        ny = self.plan()
        self.post(f"/plans/{ny['id']}/approve", {"request_id": "x", "accepter_uplanlagte": True}, 409)
        self.post("/reset", {}, 400)
        status = self.post("/reset", {"bekraeft": True}, 200)
        self.assertEqual((status["beregningstidspunkt"], status["snapshot"]["id"]), ("2026-10-05 09:00", 1))

    def test_annulleret_ordre_kan_ikke_planlaegges(self):
        self.post("/plans", {"uge_start": UGE, "ordrelinje_ids": [4]}, 400)
        self.post("/plans", {"uge_start": "2026-10-06"}, 400)


class YdeevneTest(unittest.TestCase):
    def test_n04_stor_plan_under_to_sekunder(self):
        varer = {i: {"id": i, "varenummer": f"V{i}", "navn": f"Vare {i}", "type": "færdigvare" if i <= 100 else "råvare",
                     "basisenhed": "stk" if i <= 100 else "kg"} for i in range(1, 201)}
        batches = [{"id": i, "vare_id": 1 + i % 200, "batchnummer": f"B{i}", "fysisk_maengde": 50000,
                    "reserveret_maengde": 0, "udloebsdato": "2026-10-31", "kvalitetsstatus": "frigivet",
                    "data_afklaret": 1} for i in range(1000)]
        ordrer = [{"id": i, "ordre_id": f"O{i}", "kilde_id": f"K{i}", "vare_id": i, "bestilt_maengde": 30000,
                   "leveret_maengde": 0, "leveringsdato": "2026-10-08", "status": "åben", "prioritet": "normal",
                   "saesonmaerke": i % 2} for i in range(1, 101)]
        data = {"snapshot": {"id": 1, "source_updated_at": "2026-10-05 08:00"}, "varer": varer,
                "rater": {i: 60 for i in range(1, 101)}, "batches": batches, "ordrelinjer": ordrer,
                "produktionsstatus": [], "kapacitet": {},
                "ressourcebehov": {i: [{"raavare_id": 100 + i, "maengde_pr_enhed": 500}] for i in range(1, 101)}}
        start = time.perf_counter()
        planner.beregn_plan(data, UGE, "2026-10-05 09:00")
        self.assertLess(time.perf_counter() - start, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
