"""Automatiske tests af kravene K1–K12 i ../kravspecifikation-2.md.

    python tests.py

Hver test kører på friske eksempeldata i en midlertidig database.
Brugertestene i kravspecifikationens sidste kolonne (forståelse, tillid, leverbarhed) kan ikke automatiseres –
her testes, at prototypen opfylder de tekniske forudsætninger for dem.
"""
import os
import tempfile
import unittest
from datetime import date, timedelta

os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")

import compass  # noqa: E402
from app import app  # noqa: E402
from database import init_db  # noqa: E402

FAMILY = {"destination_id": 1, "group_type": "family", "group_size": 4, "interests": ["history", "food"],
          "pace": "relaxed", "language": "English", "practical": ["kid_friendly"]}
K5_KEYS = ["title", "description", "location", "experience_type", "duration_hours", "group", "type_name",
           "transport", "included", "not_included", "price_label"]


class CompassTest(unittest.TestCase):
    def setUp(self):
        init_db(reset=True)
        self.client = app.test_client()

    def post(self, path, body, status=200):
        response = self.client.post(f"/api{path}", json=body)
        self.assertEqual(response.status_code, status, response.get_json())
        return response.get_json()

    def suggest(self, **changes):
        return self.post("/compass", {"preferences": {**FAMILY, **changes}})

    def titles(self, result):
        return [s["experience"]["title"] for s in result["suggestions"]]

    # K1
    def test_k1_missing_preferences_are_rejected_with_reasons(self):
        error = self.post("/compass", {"preferences": {"destination_id": 1}}, 400)["error"]
        for text in ("who is travelling", "interest", "pace", "language"):
            self.assertIn(text, error.lower())

    def test_k1_options_cover_all_required_preferences(self):
        options = self.client.get("/api/options").get_json()
        for key in ("group_types", "interests", "paces", "languages", "practical"):
            self.assertTrue(options[key], key)

    # K2
    def test_k2_one_to_three_different_suggestions(self):
        for prefs in (FAMILY, {**FAMILY, "destination_id": 2}, {**FAMILY, "interests": ["design"]}):
            ids = [s["experience"]["id"] for s in self.post("/compass", prefs)["suggestions"]]
            self.assertTrue(1 <= len(ids) <= compass.MAX_SUGGESTIONS, ids)
            self.assertEqual(len(ids), len(set(ids)))

    # K3
    def test_k3_every_suggestion_explains_at_least_two_preferences(self):
        for s in self.suggest()["suggestions"]:
            self.assertGreaterEqual(len({r["preference"] for r in s["reasons"]}), 2, s["experience"]["title"])

    def test_k3_changing_a_preference_changes_the_result_and_says_what_changed(self):
        before = self.suggest()
        after = self.post("/compass", {"preferences": {**FAMILY, "interests": ["design", "architecture"], "pace": "active"},
                                       "previous": FAMILY})
        self.assertNotEqual(self.titles(before), self.titles(after))
        changed = {c["field"] for c in after["changes"]["changed_preferences"]}
        self.assertEqual(changed, {"interests", "pace"})
        self.assertTrue(after["changes"]["added"])

    def test_k3_same_input_gives_same_output(self):
        self.assertEqual(self.suggest(), self.suggest())

    # K4
    def test_k4_three_product_types_with_all_differences(self):
        types = self.client.get("/api/product-types").get_json()
        self.assertEqual({t["code"] for t in types}, {"public", "private", "customised"})
        for t in types:
            for key in ("group_form", "flexibility", "personalisation", "booking_form", "price_principle"):
                self.assertTrue(t[key], (t["code"], key))

    # K5
    def test_k5_every_suggestion_has_the_required_fields(self):
        for s in self.suggest()["suggestions"] + self.suggest(destination_id=2)["suggestions"]:
            for key in K5_KEYS:
                self.assertTrue(s["experience"][key], (s["experience"]["title"], key))

    # K6
    def test_k6_local_alternative_is_shown_and_explained_when_relevant(self):
        local = [s for s in self.suggest()["suggestions"] if s["slot"] == "local"]
        self.assertEqual(len(local), 1)
        self.assertTrue(local[0]["experience"]["local_note"])
        for word in ("co2", "climate", "green", "sustainable"):
            self.assertNotIn(word, local[0]["experience"]["local_note"].lower())

    def test_k6_no_forced_local_alternative_when_nothing_fits(self):
        result = self.suggest(interests=["art"], practical=["step_free"], destination_id=2, group_type="couple",
                              group_size=2, pace="moderate")
        self.assertFalse([s for s in result["suggestions"] if s["slot"] == "local"])

    # K7
    def test_k7_value_claims_are_documented(self):
        for s in self.suggest()["suggestions"]:
            self.assertTrue(s["amitylux_value"])
            for claim in s["amitylux_value"]:
                self.assertTrue(claim["evidence"])

    # K8
    def test_k8_preview_and_inquiry_contain_the_same_structured_brief(self):
        body = {**FAMILY, "wanted_type": "customised", "experience_ids": [4, 7], "addons": ["boat"],
                "customer_unsure": "Boat with a 7-year-old", "travel_date": "2026-12-10"}
        preview = self.post("/inquiries/preview", body)
        self.assertEqual(preview["reference"], "(not sent yet)")
        sent = self.post("/inquiries", {**body, "contact_name": "Ada", "contact_email": "ada@example.com"}, 201)
        brief = sent["brief"]
        self.assertTrue(sent["receipt"]["next_steps"])
        self.assertEqual(brief["selected"]["experiences"], preview["selected"]["experiences"])
        self.assertEqual(brief["selected"]["add_ons"], ["Boat trip"])
        self.assertIn("Customer is unsure: Boat with a 7-year-old", brief["uncertainties"])
        self.assertTrue(any("high season" in u for u in brief["uncertainties"]))
        self.assertEqual(brief["preferences"]["interests"], ["History", "Food"])

    def test_k8_inquiry_requires_contact_details(self):
        self.post("/inquiries", {**FAMILY, "wanted_type": "private"}, 400)

    def test_k8_help_request_keeps_the_answers(self):
        help_request = self.post("/help-requests", {"name": "Ada", "contact": "ada@example.com", "step": "Your suggestions",
                                                    "answers": FAMILY}, 201)
        self.assertIn('"group_type": "family"', help_request["answers"])

    # K9
    def test_k9_draft_experiences_are_never_suggested(self):
        drafts = {a["title"] for a in self.client.get("/api/catalogue/audit").get_json() if not a["used_in_suggestions"]}
        self.assertIn("Royal Palace After Hours", drafts)
        for prefs in (FAMILY, {**FAMILY, "group_size": 14, "group_type": "friends", "interests": ["history", "art"]}):
            self.assertFalse(drafts & set(self.titles(self.post("/compass", prefs))))

    def test_k9_uncertain_facts_are_marked_requires_confirmation(self):
        customised = self.suggest(group_size=14, group_type="friends", interests=["history", "art", "food"])
        s = next(s for s in customised["suggestions"] if s["experience"]["type_code"] == "customised")
        self.assertEqual(s["experience"]["price_label"], "Price on request")
        self.assertIn("Final price", s["requires_confirmation"])
        soon = (date.today() + timedelta(days=3)).isoformat()
        for s in self.suggest(travel_date=soon)["suggestions"]:
            self.assertTrue(any("short notice" in c for c in s["requires_confirmation"]))

    def test_k9_every_suggestion_is_traceable_to_the_catalogue(self):
        for s in self.suggest()["suggestions"]:
            self.assertIn("Amitylux catalogue – approved", s["experience"]["source"])

    # K10 (teknisk forudsætning: små svar, som kan vises på mobil – flowet testes manuelt)
    def test_k10_step_free_is_a_hard_requirement(self):
        for s in self.suggest(destination_id=2, practical=["step_free"])["suggestions"]:
            self.assertIn("Step-free route", s["experience"]["practical"])

    # K11
    def test_k11_same_structure_in_two_destinations(self):
        cph, rome = self.suggest()["suggestions"][0], self.suggest(destination_id=2)["suggestions"][0]
        self.assertEqual(set(cph), set(rome))
        self.assertEqual(set(cph["experience"]), set(rome["experience"]))
        self.assertNotEqual(cph["experience"]["location"], rome["experience"]["location"])

    # K12
    def test_k12_mobility_is_shown_neutrally(self):
        bike = next(e for e in self.client.get("/api/catalogue").get_json() if e["title"] == "Harbour & Design by Bike")
        self.assertEqual(bike["transport"], ["Bike"])
        for e in self.client.get("/api/catalogue").get_json():
            for word in ("co2", "climate", "eco", "green"):
                self.assertNotIn(word, (e["mobility_note"] or "").lower(), e["title"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
