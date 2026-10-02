from unittest.mock import patch

from src.errors import conflict

from .support import ApiTestCase


class WorkflowTests(ApiTestCase):
    def test_incomplete_draft_must_be_completed_before_review(self):
        draft = self.post("/decisions/drafts", {
            "project": "demo", "author": "Agent1", "title": "A draft",
        }, 201)
        self.assertEqual(draft["context"], "")
        self.post(f"/decisions/{draft['id']}/review", {}, 400)
        self.assertEqual(self.get(f"/decisions/{draft['id']}")["status"], "draft")
        self.patch(f"/decisions/{draft['id']}/draft", {
            "context": "Context", "alternatives": "Options", "decision": "Choice",
        })
        reviewed = self.post(f"/decisions/{draft['id']}/review", {})
        self.assertEqual(reviewed["status"], "proposed")

    def test_draft_minimum_fields_are_required(self):
        data = {"project": "demo", "author": "Agent1", "title": "Draft"}
        for field in data:
            self.post("/decisions/drafts", {key: value for key, value in data.items() if key != field}, 400)

    def test_replacement_is_linked_but_not_effective_until_explicit_supersession(self):
        original = self.decision("accepted")
        replacement = self.post(f"/decisions/{original['id']}/replacement", {
            "author": "Agent2", "title": "Replacement",
        }, 201)
        relation = self.get(f"/decisions/{original['id']}/relations")["items"][0]
        self.assertEqual(relation["type"], "supersedes")
        self.assertFalse(relation["effective"])
        self.assertEqual(relation["source_id"], replacement["id"])
        self.assertEqual(self.get(f"/decisions/{original['id']}"), original)
        self.post(f"/decisions/{original['id']}/supersede", {"successor_id": replacement["id"]}, 409)
        self.patch(f"/decisions/{replacement['id']}", {
            "context": "New context", "alternatives": "Options", "decision": "New choice",
        })
        self.post(f"/decisions/{replacement['id']}/review", {})
        self.post(f"/decisions/{replacement['id']}/approve", {})
        self.assertFalse(self.get(f"/relations/{relation['id']}")["effective"])
        changed = self.post(f"/decisions/{original['id']}/supersede", {"successor_id": replacement["id"]})
        self.assertEqual(changed["status"], "superseded")
        self.assertEqual(changed["superseded_by"], replacement["id"])
        relations = self.get(f"/decisions/{original['id']}/relations")["items"]
        self.assertEqual(len(relations), 1)
        self.assertTrue(relations[0]["effective"])
        self.assertEqual(self.get("/decisions/current")["items"][0]["id"], replacement["id"])

    def test_direct_superseding_relation_updates_original(self):
        original, successor = self.decision("accepted"), self.decision("accepted")
        relation = self.post("/relations", {
            "source_id": successor["id"], "target_id": original["id"], "type": "supersedes",
        }, 201)
        self.assertTrue(relation["effective"])
        self.assertEqual(self.get(f"/decisions/{original['id']}")["superseded_by"], successor["id"])
        self.patch(f"/relations/{relation['id']}", {"type": "complements"}, 409)

    def test_converting_relation_to_supersession_is_effective(self):
        original, successor = self.decision("accepted"), self.decision("accepted")
        relation = self.post("/relations", {
            "source_id": successor["id"], "target_id": original["id"], "type": "complements",
        }, 201)
        changed = self.patch(f"/relations/{relation['id']}", {"type": "supersedes"})
        self.assertTrue(changed["effective"])
        self.assertEqual(self.get(f"/decisions/{original['id']}")["status"], "superseded")

    def test_failed_relation_write_rolls_back_status(self):
        original, successor = self.decision("accepted"), self.decision("accepted")
        with patch("src.relations.repository.record_supersession", side_effect=conflict("Write failed")):
            self.post(f"/decisions/{original['id']}/supersede", {"successor_id": successor["id"]}, 409)
        self.assertEqual(self.get(f"/decisions/{original['id']}"), original)
        self.assertEqual(self.get(f"/decisions/{original['id']}/relations")["items"], [])

    def test_cross_project_relations_and_replacements_are_rejected(self):
        self.post("/projects", {"name": "other"}, 201)
        original = self.decision("accepted")
        other = self.decision("accepted", project="other")
        self.post("/relations", {
            "source_id": other["id"], "target_id": original["id"], "type": "complements",
        }, 409)
        self.post(f"/decisions/{original['id']}/supersede", {"successor_id": other["id"]}, 409)
        self.post(f"/decisions/{original['id']}/replacement", {
            "project": "other", "author": "Agent1", "title": "Replacement",
        }, 409)
        self.assertEqual(self.get("/decisions")["pagination"]["total"], 2)

    def test_related_decision_cannot_move_to_another_project(self):
        self.post("/projects", {"name": "other"}, 201)
        first, second = self.decision(), self.decision()
        self.post("/relations", {
            "source_id": first["id"], "target_id": second["id"], "type": "contradicts",
        }, 201)
        self.patch(f"/decisions/{first['id']}", {"project": "other"}, 409)
        self.assertEqual(self.get(f"/decisions/{first['id']}")["project"], "demo")

    def test_supersession_requires_distinct_accepted_decisions(self):
        original = self.decision("accepted")
        proposal = self.decision()
        self.post(f"/decisions/{original['id']}/supersede", {"successor_id": proposal["id"]}, 409)
        self.post(f"/decisions/{original['id']}/supersede", {"successor_id": original["id"]}, 400)
        self.post(f"/decisions/{original['id']}/supersede", {"successor_id": True}, 400)
        self.post(f"/decisions/{proposal['id']}/replacement", {"author": "Agent1", "title": "New"}, 409)
