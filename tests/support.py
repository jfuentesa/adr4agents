import tempfile
import unittest
from pathlib import Path

from src import create_app


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.database = str(Path(self.directory.name) / "test.sqlite3")
        self.app = create_app({"TESTING": True, "DATABASE": self.database})
        self.client = self.app.test_client()
        self.project = self.post("/projects", {"name": "demo"}, 201)

    def tearDown(self):
        self.directory.cleanup()

    def post(self, path, data, expected=200):
        response = self.client.post("/api/v1" + path, json=data)
        self.assertEqual(response.status_code, expected, response.get_data(as_text=True))
        return response.json

    def patch(self, path, data, expected=200):
        response = self.client.patch("/api/v1" + path, json=data)
        self.assertEqual(response.status_code, expected, response.get_data(as_text=True))
        return response.json

    def get(self, path, expected=200):
        response = self.client.get("/api/v1" + path)
        self.assertEqual(response.status_code, expected, response.get_data(as_text=True))
        return response.json

    def payload(self, **changes):
        return {
            "project": "demo", "author": "Agent1", "title": "Choose SQLite",
            "context": "A small application", "alternatives": "PostgreSQL",
            "decision": "Use SQLite", "tags": "storage,python", "date": "2026-10-02",
            **changes,
        }

    def decision(self, status="proposed", **changes):
        path = "/decisions/drafts" if status == "draft" else "/decisions"
        item = self.post(path, self.payload(**changes), 201)
        if status == "accepted":
            item = self.post(f"/decisions/{item['id']}/approve", {})
        return item
