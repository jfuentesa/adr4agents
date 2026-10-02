from .support import ApiTestCase


class ProjectTests(ApiTestCase):
    def test_project_creation_read_and_partial_update(self):
        project = self.post("/projects", {
            "name": "another", "description": "Another project", "context": "Research",
        }, 201)
        self.assertEqual(self.get(f"/projects/{project['id']}"), project)
        changed = self.patch(f"/projects/{project['id']}", {"description": "Updated"})
        self.assertEqual(changed["context"], "Research")
        self.assertEqual(changed["description"], "Updated")

    def test_duplicate_project_names_are_conflicts(self):
        self.post("/projects", {"name": "demo"}, 409)
        other = self.post("/projects", {"name": "other"}, 201)
        self.patch(f"/projects/{other['id']}", {"name": "demo"}, 409)
        self.assertEqual(self.get(f"/projects/{other['id']}")["name"], "other")

    def test_renaming_project_keeps_decisions_attached(self):
        decision = self.decision()
        self.patch(f"/projects/{self.project['id']}", {"name": "renamed"})
        self.assertEqual(self.get(f"/decisions/{decision['id']}")["project"], "renamed")
        self.assertEqual(self.get("/decisions?project=renamed")["pagination"]["total"], 1)

    def test_project_names_and_unknown_fields_are_validated(self):
        for data in ({"name": "two words"}, {"name": ""}, {"name": "ok", "owner": "alice"}):
            self.post("/projects", data, 400)
        self.patch(f"/projects/{self.project['id']}", {}, 400)
        self.get("/projects/999", 404)

    def test_project_listing_supports_search_and_pagination(self):
        self.post("/projects", {"name": "demo2"}, 201)
        self.post("/projects", {"name": "other"}, 201)
        page = self.get("/projects?q=demo&page_size=1&page=2")
        self.assertEqual([item["name"] for item in page["items"]], ["demo2"])
        self.assertEqual(page["pagination"], {"page": 2, "page_size": 1, "total": 2, "pages": 2})
