import json

from .mcp_support import McpTestCase, connected


class McpTests(McpTestCase):
    @connected
    async def test_discovery_exposes_contract_and_annotations(self):
        result = await self.client.list_tools()
        tools = {tool.name: tool for tool in result.tools}
        self.assertEqual(len(tools), 22)
        self.assertTrue(tools["get_decision"].annotations.read_only_hint)
        self.assertFalse(tools["approve_decision"].annotations.read_only_hint)
        schema = tools["create_decision"].input_schema
        self.assertIn("data", schema["properties"])
        self.assertTrue(all(tool.description for tool in tools.values()))

    @connected
    async def test_projects_queries_and_partial_edits(self):
        projects = await self.call("list_projects", q="demo", page_size=1)
        project = await self.call("get_project", project_id=projects["items"][0]["id"])
        await self.call("update_project", project_id=project["id"], data={"context": "Agent context"})
        item = await self.accepted(title="Almacén + SQLite & Python", date="2026-10-02")
        updated = await self.call("update_decision", decision_id=item["id"], data={"context": "Changed"})
        self.assertEqual(updated["date"], "2026-10-02")
        self.assertEqual(updated["status"], "accepted")
        await self.call("get_decision", decision_id=item["id"])
        filters = {"project": "demo", "tags": "storage,python", "date_from": "2026-10-02"}
        for tool in ("list_decisions", "search_decisions", "get_current_decisions"):
            found = await self.call(tool, q="Almacén + SQLite & Python", filters=filters, page_size=1)
            self.assertEqual(found["pagination"]["total"], 1)
        tags = await self.call("list_tags", project="demo")
        self.assertEqual(tags["pagination"]["total"], 2)

    @connected
    async def test_draft_review_rejection_and_comments(self):
        draft = await self.call("create_decision_draft", data={"project": "demo", "author": "Agent1", "title": "Draft"})
        await self.call("update_decision_draft", decision_id=draft["id"], data=self.payload())
        proposed = await self.call("request_decision_review", decision_id=draft["id"])
        self.assertEqual(proposed["status"], "proposed")
        rejected = await self.call("reject_decision", decision_id=draft["id"])
        self.assertEqual(rejected["status"], "rejected")
        comment = await self.call("comment_decision", decision_id=draft["id"], author="Agent2", text="Consider alternatives")
        self.assertEqual(comment["text"], "Consider alternatives")

    @connected
    async def test_replacement_only_becomes_effective_explicitly(self):
        original = await self.accepted()
        successor = await self.call("propose_decision_replacement", decision_id=original["id"], data={"author": "Agent2", "title": "Replace"})
        links = await self.call("get_decision_relations", decision_id=original["id"])
        self.assertFalse(links["items"][0]["effective"])
        await self.call("update_decision_draft", decision_id=successor["id"], data=self.payload())
        await self.call("request_decision_review", decision_id=successor["id"])
        await self.call("approve_decision", decision_id=successor["id"])
        current = await self.call("get_current_decisions")
        self.assertEqual(current["pagination"]["total"], 2)
        replaced = await self.call("supersede_decision", decision_id=original["id"], successor_id=successor["id"])
        self.assertEqual(replaced["status"], "superseded")

    @connected
    async def test_create_and_update_relations(self):
        first, second = await self.accepted(), await self.accepted(title="Second")
        relation = await self.call("create_relation", data={"source_id": first["id"], "target_id": second["id"], "type": "complements"})
        updated = await self.call("update_relation", relation_id=relation["id"], data={"type": "contradicts"})
        self.assertEqual(updated["type"], "contradicts")

    @connected
    async def test_api_errors_are_mcp_errors_with_details(self):
        item = await self.accepted()
        cases = [("get_decision", {"decision_id": 999}, 404),
                 ("approve_decision", {"decision_id": item["id"]}, 409),
                 ("update_decision", {"decision_id": item["id"], "data": {"title": None}}, 400)]
        for tool, arguments, status in cases:
            result = await self.client.call_tool(tool, arguments)
            self.assertTrue(result.is_error)
            details = json.loads(result.content[0].text)
            self.assertEqual(details["http_status"], status)
            self.assertIn("error", details["response"])

    @connected
    async def test_invalid_tool_arguments_do_not_write(self):
        for data in ({"name": "extra", "unknown": True}, {"name": 123}):
            result = await self.client.call_tool("create_project", {"data": data})
            self.assertTrue(result.is_error)
        projects = await self.call("list_projects")
        self.assertEqual(projects["pagination"]["total"], 1)
