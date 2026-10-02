from .support import ApiTestCase


class SearchTests(ApiTestCase):
    def test_filters_can_be_combined(self):
        expected = self.decision("accepted")
        self.decision("accepted", author="Other", date="2026-01-01")
        self.decision("draft", tags="python")
        page = self.get(
            "/decisions?project=demo&status=accepted&author=Agent1"
            "&tags=python,storage&date_from=2026-10-01&date_to=2026-10-03"
        )
        self.assertEqual(page["items"], [expected])

    def test_current_decisions_only_returns_accepted(self):
        accepted = self.decision("accepted")
        self.decision("draft")
        self.decision()
        rejected = self.decision()
        self.post(f"/decisions/{rejected['id']}/reject", {})
        self.assertEqual(self.get("/decisions/current")["items"], [accepted])

    def test_search_matches_all_business_texts(self):
        self.decision(title="UniqueTitle", context="UniqueContext", alternatives="UniqueOption",
                      decision="UniqueChoice")
        for query in ("uniquetitle", "uniquecontext", "uniqueoption", "uniquechoice"):
            with self.subTest(query=query):
                self.assertEqual(self.get(f"/decisions/search?q={query}")["pagination"]["total"], 1)

    def test_search_treats_sql_and_wildcards_as_literal_text(self):
        self.decision(title="Contains 100% and_under")
        self.assertEqual(self.get("/decisions/search?q=%25")["pagination"]["total"], 1)
        self.assertEqual(self.get("/decisions/search?q=_")["pagination"]["total"], 1)
        self.assertEqual(self.get("/decisions/search?q=%27%20OR%201%3D1--")["pagination"]["total"], 0)
        self.assertEqual(self.get("/projects")["pagination"]["total"], 1)

    def test_search_supports_unicode_case_insensitivity(self):
        self.decision(title="DECISIÓN TÉCNICA")
        self.assertEqual(self.get("/decisions/search?q=decisi%C3%B3n")["pagination"]["total"], 1)

    def test_pagination_is_stable_and_empty_pages_are_valid(self):
        items = [self.decision(title=f"Decision {index}") for index in range(3)]
        result = self.get("/decisions?page_size=2&page=2")
        self.assertEqual(result["items"], items[2:])
        self.assertEqual(result["pagination"]["total"], 3)
        self.assertEqual(self.get("/decisions?page=10")["items"], [])

    def test_tag_replacement_and_project_filter(self):
        decision = self.decision(tags="python,python,storage")
        self.post("/projects", {"name": "other"}, 201)
        self.decision(project="other", tags="other")
        self.assertEqual(self.get("/tags?project=demo")["items"], ["python", "storage"])
        self.patch(f"/decisions/{decision['id']}", {"tags": "new"})
        self.assertEqual(self.get("/tags?project=demo")["items"], ["new"])
        self.assertEqual(self.get("/tags?page_size=1")["pagination"]["total"], 2)

    def test_empty_tags_are_supported(self):
        item = self.decision(tags="")
        self.assertEqual(item["tags"], "")
        self.assertEqual(self.get("/tags")["items"], [])
