from datetime import date

from .support import ApiTestCase


class DecisionTests(ApiTestCase):
    def test_create_proposal_has_exact_business_fields(self):
        response = self.client.post("/api/v1/decisions", json=self.payload())
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.headers["Location"], "/api/v1/decisions/1")
        item = response.json
        self.assertEqual(item["status"], "proposed")
        self.assertEqual(item["tags"], "python,storage")
        self.assertEqual(set(item), {
            "id", "project", "author", "title", "context", "alternatives", "decision",
            "tags", "date", "status", "superseded_by",
        })
        self.assertEqual(self.get("/decisions/1"), item)

    def test_default_date_is_a_calendar_date(self):
        data = self.payload()
        del data["date"]
        item = self.post("/decisions", data, 201)
        self.assertEqual(item["date"], date.today().isoformat())

    def test_complete_draft_can_be_reviewed_and_approved(self):
        item = self.decision("draft")
        self.assertEqual(item["status"], "draft")
        item = self.post(f"/decisions/{item['id']}/review", {})
        self.assertEqual(item["status"], "proposed")
        item = self.post(f"/decisions/{item['id']}/approve", {})
        self.assertEqual(item["status"], "accepted")

    def test_reject_proposal(self):
        item = self.decision()
        item = self.post(f"/decisions/{item['id']}/reject", {})
        self.assertEqual(item["status"], "rejected")
        self.post(f"/decisions/{item['id']}/approve", {}, 409)

    def test_illegal_transitions_preserve_status(self):
        item = self.decision("draft")
        for action in ("approve", "reject"):
            self.post(f"/decisions/{item['id']}/{action}", {}, 409)
        self.assertEqual(self.get(f"/decisions/{item['id']}")["status"], "draft")

    def test_edit_accepted_decision_preserves_status(self):
        item = self.decision("accepted")
        updated = self.patch(f"/decisions/{item['id']}", {"decision": "Use SQLite with backups"})
        self.assertEqual(updated["status"], "accepted")
        self.assertEqual(updated["decision"], "Use SQLite with backups")
        self.patch(f"/decisions/{item['id']}/draft", {"title": "Changed"}, 409)
        self.patch(f"/decisions/{item['id']}", {"status": "draft"}, 400)

    def test_unknown_project_is_rejected_without_creating_a_decision(self):
        self.post("/decisions", self.payload(project="missing"), 404)
        self.assertEqual(self.get("/decisions")["pagination"]["total"], 0)

    def test_data_persists_across_application_instances(self):
        item = self.decision()
        from src import create_app
        other = create_app({"TESTING": True, "DATABASE": self.database})
        response = other.test_client().get(f"/api/v1/decisions/{item['id']}")
        self.assertEqual(response.json, item)

    def test_no_previous_versions_are_stored(self):
        item = self.decision()
        self.patch(f"/decisions/{item['id']}", {"title": "Updated title"})
        from src.db import connect
        connection = connect(self.database)
        try:
            rows = connection.execute("SELECT title FROM decisions").fetchall()
            self.assertEqual([row["title"] for row in rows], ["Updated title"])
            tables = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
            self.assertFalse(any("history" in row["name"] for row in tables))
        finally:
            connection.close()
