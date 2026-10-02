from .support import ApiTestCase


class CommentTests(ApiTestCase):
    def test_comments_are_visible_and_paginated(self):
        decision = self.decision()
        first = self.post(f"/decisions/{decision['id']}/comments", {
            "author": "Agent2", "text": "Consider backups", "date": "2026-10-02",
        }, 201)
        second = self.post(f"/decisions/{decision['id']}/comments", {
            "author": "Human1", "text": "Agreed",
        }, 201)
        self.assertEqual(first["decision_id"], decision["id"])
        page = self.get(f"/decisions/{decision['id']}/comments?page_size=1&page=2")
        self.assertEqual(page["items"], [second])
        self.assertEqual(page["pagination"]["total"], 2)

    def test_comments_do_not_modify_decisions(self):
        decision = self.decision("accepted")
        self.post(f"/decisions/{decision['id']}/comments", {
            "author": "Agent2", "text": "A question",
        }, 201)
        self.assertEqual(self.get(f"/decisions/{decision['id']}"), decision)

    def test_comment_validation_and_missing_decisions(self):
        decision = self.decision()
        for data in ({"author": "bad_name", "text": "ok"}, {"author": "Agent1", "text": ""},
                     {"author": "Agent1"}, {"author": "Agent1", "text": "ok", "date": "bad"}):
            self.post(f"/decisions/{decision['id']}/comments", data, 400)
        self.assertEqual(self.get(f"/decisions/{decision['id']}/comments")["items"], [])
        self.post("/decisions/999/comments", {"author": "Agent1", "text": "ok"}, 404)
        self.get("/decisions/999/comments", 404)
