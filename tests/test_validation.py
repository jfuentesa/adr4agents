from .support import ApiTestCase


class ValidationTests(ApiTestCase):
    def test_invalid_decision_fields_are_rejected(self):
        invalid = {
            "project": ["two words", "", 12],
            "author": ["agent_1", "two words", "", True],
            "title": ["", [], "x" * 301],
            "context": ["", None],
            "alternatives": [[], None, ""],
            "decision": ["", False],
            "tags": ["two words", "tag,,other", ["python"]],
            "date": ["2026-02-30", "20261002", "2026-10-02T12:00:00", None],
        }
        for field, values in invalid.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    error = self.post("/decisions", self.payload(**{field: value}), 400)
                    self.assertEqual(error["error"]["field"], field)
        self.assertEqual(self.get("/decisions")["pagination"]["total"], 0)

    def test_unknown_fields_are_not_silently_ignored(self):
        for key in ("consequences", "user_id", "status", "superseded_by"):
            with self.subTest(field=key):
                self.post("/decisions", self.payload(**{key: "value"}), 400)

    def test_json_transport_errors_are_json(self):
        response = self.client.post("/api/v1/decisions", data="not json")
        self.assertEqual(response.status_code, 415)
        self.assertIn("error", response.json)
        response = self.client.post("/api/v1/decisions", data="{", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json)
        for payload in (None, [], "text", 42):
            response = self.client.post(
                "/api/v1/decisions", data=__import__("json").dumps(payload),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 400)

    def test_unknown_routes_and_methods_return_json(self):
        self.assertEqual(self.get("/missing", 404)["error"]["code"], "not_found")
        response = self.client.delete("/api/v1/decisions/1")
        self.assertEqual(response.status_code, 405)
        self.assertIn("Allow", response.headers)
        self.assertIn("error", response.json)

    def test_request_body_size_is_limited(self):
        response = self.client.post("/api/v1/decisions", json=self.payload(context="x" * 1_048_576))
        self.assertEqual(response.status_code, 413)
        self.assertIn("error", response.json)

    def test_author_is_plain_metadata_and_no_credentials_are_needed(self):
        self.assertEqual(self.decision(author="Someone123")["author"], "Someone123")
        self.assertEqual(self.get("/health"), {"status": "ok"})

    def test_query_parameters_are_validated(self):
        paths = (
            "/decisions?page=0", "/decisions?page_size=101", "/decisions?page=1.5",
            "/decisions?page=1&page=2", "/decisions?unknown=x", "/decisions?status=other",
            "/decisions?date_from=2026-12-01&date_to=2026-01-01", "/decisions/search",
            "/decisions/current?status=draft", "/decisions?page=999999999999999999999",
        )
        for path in paths:
            with self.subTest(path=path):
                self.get(path, 400)

    def test_workflow_requires_explicit_empty_json_object(self):
        item = self.decision()
        self.post(f"/decisions/{item['id']}/approve", {"status": "accepted"}, 400)
        self.assertEqual(self.get(f"/decisions/{item['id']}")["status"], "proposed")
