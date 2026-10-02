from .support import ApiTestCase


class RelationTests(ApiTestCase):
    def test_create_read_edit_and_list_incoming_relations(self):
        first, second, third = [self.decision() for _ in range(3)]
        relation = self.post("/relations", {
            "source_id": first["id"], "target_id": second["id"], "type": "complements",
        }, 201)
        self.assertEqual(self.get(f"/relations/{relation['id']}"), relation)
        changed = self.patch(f"/relations/{relation['id']}", {
            "target_id": third["id"], "type": "contradicts",
        })
        self.assertEqual(self.get(f"/decisions/{second['id']}/relations")["items"], [])
        self.assertEqual(self.get(f"/decisions/{third['id']}/relations")["items"], [changed])

    def test_duplicate_relation_does_not_create_an_extra_row(self):
        first, second = self.decision(), self.decision()
        data = {"source_id": first["id"], "target_id": second["id"], "type": "complements"}
        self.post("/relations", data, 201)
        self.post("/relations", data, 409)
        self.assertEqual(self.get(f"/decisions/{first['id']}/relations")["pagination"]["total"], 1)

    def test_relation_validation(self):
        first, second = self.decision(), self.decision()
        valid = {"source_id": first["id"], "target_id": second["id"], "type": "complements"}
        for changes in ({"source_id": True}, {"source_id": "1"}, {"target_id": 0},
                        {"type": "unknown"}, {"type": []}, {"target_id": first["id"]}):
            self.post("/relations", {**valid, **changes}, 400)
        self.post("/relations", {**valid, "target_id": 999}, 404)
        self.get("/decisions/999/relations", 404)
        self.get("/relations/999", 404)

    def test_relation_pagination(self):
        first = self.decision()
        for _ in range(3):
            other = self.decision()
            self.post("/relations", {
                "source_id": first["id"], "target_id": other["id"], "type": "complements",
            }, 201)
        page = self.get(f"/decisions/{first['id']}/relations?page_size=2&page=2")
        self.assertEqual(len(page["items"]), 1)
        self.assertEqual(page["pagination"]["total"], 3)
