import re

from .support import ApiTestCase


class WebTests(ApiTestCase):
    def web_post(self, path, data, expected=303):
        page = self.client.get("/")
        token = re.search(r'name="csrf_token" value="([a-f0-9]+)"', page.get_data(as_text=True))
        if token is None:
            with self.client.session_transaction() as session:
                value = session["csrf_token"]
        else:
            value = token.group(1)
        response = self.client.post(path, data={"csrf_token": value, **data})
        self.assertEqual(response.status_code, expected, response.get_data(as_text=True))
        return response

    def test_empty_pages_and_assets(self):
        for path in ("/", "/projects", "/projects/new", "/decisions/new"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertIn("text/html", response.content_type)
        self.assertIn(b"No decisions found", self.client.get("/").data)
        for path in ("/static/css/layout.css", "/static/css/components.css", "/static/js/web.js"):
            with self.client.get(path) as response:
                self.assertEqual(response.status_code, 200)

    def test_create_edit_review_and_approve_are_visible_in_api(self):
        response = self.web_post("/decisions/new", {"project": "demo", "author": "Agent1", "title": "Web draft", "mode": "draft"})
        path = response.headers["Location"]
        item = self.get("/decisions")["items"][0]
        self.assertEqual(item["status"], "draft")
        self.web_post(path + "/edit", self.payload(title="Updated draft"))
        self.web_post(path + "/actions/review", {})
        self.web_post(path + "/actions/approve", {})
        current = self.get(f"/decisions/{item['id']}")
        self.assertEqual(current["status"], "accepted")
        self.web_post(path + "/edit", self.payload(title="Changed accepted", date=""))
        self.assertEqual(self.get(f"/decisions/{item['id']}")["date"], "2026-10-02")
        self.assertIn(b"Changed accepted", self.client.get(path).data)

    def test_invalid_forms_preserve_values_and_do_not_write(self):
        response = self.web_post("/decisions/new", self.payload(author="Not valid", title="Preserve this", mode="proposed"), 400)
        self.assertIn(b'aria-invalid="true"', response.data)
        self.assertIn(b'Preserve this', response.data)
        self.assertEqual(self.get("/decisions")["pagination"]["total"], 0)
        self.web_post("/projects/new", {"name": "demo"}, 409)

    def test_csrf_blocks_missing_wrong_and_unicode_tokens(self):
        self.client.get("/")
        for token in (None, "wrong", "invalidé"):
            data = {"name": "blocked"}
            if token is not None:
                data["csrf_token"] = token
            response = self.client.post("/projects/new", data=data)
            self.assertEqual(response.status_code, 400)
            self.assertIn(b"Reload the page", response.data)
        self.assertEqual(self.get("/projects")["pagination"]["total"], 1)

    def test_escape_untrusted_titles_text_and_comments(self):
        item = self.decision(title='<script>alert("title")</script>', context='<img src=x onerror=alert(1)>')
        path = f"/decisions/{item['id']}"
        self.web_post(path + "/actions/comment", {"author": "Agent1", "text": "<script>alert(1)</script>"})
        for url in ("/", path, path + "/edit"):
            html = self.client.get(url).get_data(as_text=True)
            self.assertNotIn('<script>alert', html)
            self.assertNotIn('<img src=x', html)
            self.assertIn('&lt;script&gt;', html)

    def test_filter_and_pagination_preserve_context(self):
        for index in range(21):
            self.decision(title=f"SQLite {index}")
        first = self.client.get("/?project=demo&tags=storage&q=SQLite")
        self.assertIn(b"Showing 1", first.data)
        self.assertIn(b"page=2", first.data)
        self.assertIn(b"project=demo", first.data)
        second = self.client.get("/?project=demo&tags=storage&q=SQLite&page=2")
        self.assertIn(b"Showing 21", second.data)
        self.assertIn(b"SQLite 20", second.data)
        self.assertEqual(self.client.get("/?date_from=2026-10-03&date_to=2026-10-01").status_code, 400)
        self.assertEqual(self.client.get("/?selected=" + "9" * 5000).status_code, 200)

    def test_projects_create_rename_and_preserve_decisions(self):
        item = self.decision()
        self.web_post(f"/projects/{self.project['id']}/edit", {"name": "renamed", "context": "Updated"})
        self.assertEqual(self.get(f"/decisions/{item['id']}")["project"], "renamed")
        self.web_post("/projects/new", {"name": "another", "description": "Second project"})
        self.assertIn(b"another", self.client.get("/projects").data)

    def test_replacement_review_approval_and_explicit_supersession(self):
        original = self.decision("accepted")
        path = f"/decisions/{original['id']}"
        response = self.web_post(path + "/replacement", {"author": "Agent2", "title": "Replacement"})
        replacement_path = response.headers["Location"]
        successor = self.get("/decisions")["items"][1]
        self.assertEqual(self.get(f"/decisions/{original['id']}")["status"], "accepted")
        self.web_post(replacement_path + "/edit", self.payload(title="Replacement"))
        self.web_post(replacement_path + "/actions/review", {})
        self.web_post(replacement_path + "/actions/approve", {})
        self.web_post(path + "/actions/supersede", {"successor_id": str(successor["id"])})
        self.assertEqual(self.get(f"/decisions/{original['id']}")["superseded_by"], successor["id"])
        self.assertIn(b"Effective", self.client.get(path).data)

    def test_relations_and_cross_project_validation(self):
        first, second = self.decision(), self.decision(title="Second")
        path = f"/decisions/{first['id']}"
        values = {"source_id": first["id"], "target_id": second["id"], "type": "complements"}
        self.web_post(path + "/relations/new", values)
        relation = self.get(f"/decisions/{first['id']}/relations")["items"][0]
        self.web_post(f"/relations/{relation['id']}/edit", {**values, "type": "contradicts"})
        self.assertIn(b"contradicts", self.client.get(path).data)
        self.post("/projects", {"name": "other"}, 201)
        outside = self.decision(project="other")
        self.web_post(path + "/relations/new", {**values, "target_id": outside["id"]}, 409)

    def test_workflow_errors_and_rejection(self):
        draft = self.post("/decisions/drafts", {"project": "demo", "author": "Agent1", "title": "Empty"}, 201)
        path = f"/decisions/{draft['id']}"
        self.web_post(path + "/actions/review", {}, 400)
        item = self.decision()
        path = f"/decisions/{item['id']}"
        self.web_post(path + "/actions/reject", {})
        self.web_post(path + "/actions/approve", {}, 409)
        self.assertEqual(self.get(f"/decisions/{item['id']}")["status"], "rejected")

    def test_web_errors_are_html_and_api_errors_remain_json(self):
        for path in ("/missing", "/decisions/999", "/projects/999/edit", "/relations/999/edit"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 404)
            self.assertIn("text/html", response.content_type)
        response = self.client.get("/api/v1/decisions/999")
        self.assertEqual(response.status_code, 404)
        self.assertTrue(response.is_json)
