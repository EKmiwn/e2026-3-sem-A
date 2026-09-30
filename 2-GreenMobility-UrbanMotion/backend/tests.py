"""Automatiske tests af forretningsreglerne.  Kør:  python tests.py

Bruger en midlertidig database, så database.db ikke røres.
"""
import os
import tempfile
import threading
import unittest

os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")

import database  # noqa: E402
from app import app  # noqa: E402


class HotspotTests(unittest.TestCase):
    def setUp(self):
        database.init_db(reset=True)
        self.client = app.test_client()

    def post(self, path, body=None):
        return self.client.post(f"/api{path}", json=body or {})

    def hotspot(self, hotspot_id):
        return next(h for h in self.client.get("/api/hotspots/overview").get_json() if h["id"] == hotspot_id)

    def test_counts_add_up(self):
        self.post("/reservations", {"customer_id": 1, "hotspot_id": 2})
        for h in self.client.get("/api/hotspots/overview").get_json():
            self.assertEqual(h["free"] + h["reserved"] + h["occupied"] + h["blocked"], h["total"], h["name"])
            self.assertTrue(h["consistent"], h["name"])

    def test_search(self):
        names = [h["name"] for h in self.client.get("/api/hotspots/overview?q=nørre").get_json()]
        self.assertEqual(names, ["Nørreport Station"])

    def test_cancel_frees_spot(self):
        r = self.post("/reservations", {"customer_id": 1, "hotspot_id": 1}).get_json()
        self.assertEqual(self.hotspot(1)["free"], 0)
        self.post(f"/reservations/{r['id']}/cancel")
        self.assertEqual(self.hotspot(1)["free"], 1)

    def test_arrival_makes_spot_occupied(self):
        r = self.post("/reservations", {"customer_id": 1, "hotspot_id": 2}).get_json()
        self.assertEqual(r["spot_status"], "RESERVERET")
        self.assertEqual(self.post(f"/reservations/{r['id']}/arrive").get_json()["spot_status"], "OPTAGET")

    def test_full_hotspot_has_alternatives(self):
        res = self.post("/reservations", {"customer_id": 1, "hotspot_id": 3})   # Lyngbyvej er fuldt
        self.assertEqual(res.status_code, 409)
        alternatives = self.client.get("/api/hotspots/3/alternatives").get_json()
        self.assertTrue(alternatives)
        self.assertTrue(all(a["free"] > 0 for a in alternatives))

    def test_no_double_booking_under_concurrency(self):
        """Tre kunder forsøger samtidig at få den eneste ledige plads ved Nørreport."""
        results = []

        def book(customer_id):
            with app.test_client() as client:
                results.append(client.post("/api/reservations", json={"customer_id": customer_id, "hotspot_id": 1}).status_code)

        threads = [threading.Thread(target=book, args=(c,)) for c in (1, 2, 3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(sorted(results), [201, 409, 409])
        self.assertEqual(self.hotspot(1)["reserved"], 1)

    def test_report_occupied_moves_customer(self):
        r = self.post("/reservations", {"customer_id": 1, "hotspot_id": 2}).get_json()
        res = self.post(f"/reservations/{r['id']}/report", {"type": "PLADS_OPTAGET"}).get_json()
        self.assertEqual(res["outcome"], "MOVED")
        self.assertNotEqual(res["reservation"]["spot_label"], r["spot_label"])
        self.assertTrue(self.hotspot(2)["consistent"])

    def test_report_occupied_without_free_spot_cancels(self):
        r = self.post("/reservations", {"customer_id": 1, "hotspot_id": 1}).get_json()
        res = self.post(f"/reservations/{r['id']}/report", {"type": "PLADS_OPTAGET"}).get_json()
        self.assertEqual(res["outcome"], "CANCELLED")
        self.assertTrue(res["alternatives"])

    def test_report_cannot_find_creates_case(self):
        r = self.post("/reservations", {"customer_id": 1, "hotspot_id": 2}).get_json()
        res = self.post(f"/reservations/{r['id']}/report", {"type": "KAN_IKKE_FINDE"}).get_json()
        self.assertEqual(res["outcome"], "HELP")
        self.assertEqual(len(self.client.get("/api/support?customer_id=1").get_json()), 1)

    def test_contact_staff_directly(self):
        case = self.post("/support", {"customer_id": 1, "text": "Hej", "staff_id": 3}).get_json()
        self.assertEqual(case["staff_name"], "Line Krogh")
        case = self.post(f"/support/{case['id']}/messages", {"sender": "MEDARBEJDER", "text": "Hej Gustav"}).get_json()
        self.assertEqual(case["messages"][-1]["sender"], "MEDARBEJDER")

    def test_assistant(self):
        self.assertEqual(self.post("/assistant", {"text": "Hvordan annullerer jeg min reservation?"}).get_json()["topic"], "cancel")
        self.assertEqual(self.post("/assistant", {"text": "Hvad sker der hvis jeg kommer for sent?"}).get_json()["topic"], "late")
        self.assertEqual(self.post("/assistant", {"text": "Kan jeg få kontakt til en medarbejder"}).get_json()["topic"], "human")
        self.assertTrue(self.post("/assistant", {"text": "Hvad er meningen med livet?"}).get_json()["handoff"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
