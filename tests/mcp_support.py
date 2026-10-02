import asyncio
import tempfile
import threading
import unittest
from functools import wraps
from pathlib import Path

from mcp import Client
from werkzeug.serving import WSGIRequestHandler, make_server

from src import create_app
from src.mcp_server import create_mcp_server


class QuietHandler(WSGIRequestHandler):
    def log(self, type, message, *args):
        pass


def connected(function):
    @wraps(function)
    async def run(self):
        async with self.client:
            await self.call("create_project", data={"name": "demo"})
            await function(self)
    return run


class McpTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        app = create_app({"TESTING": True, "DATABASE": str(Path(self.directory.name) / "test.sqlite3")})
        self.http = make_server("127.0.0.1", 0, app, request_handler=QuietHandler)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        self.api_url = f"http://127.0.0.1:{self.http.server_port}/api/v1"
        self.server = create_mcp_server(self.api_url)
        self.client = Client(self.server)

    async def asyncTearDown(self):
        await asyncio.to_thread(self.http.shutdown)
        self.thread.join(timeout=5)
        self.http.server_close()
        self.directory.cleanup()

    async def call(self, tool, **arguments):
        result = await self.client.call_tool(tool, arguments)
        self.assertFalse(result.is_error, result.content)
        return result.structured_content

    def payload(self, **changes):
        return {"project": "demo", "author": "Agent1", "title": "Choose SQLite",
                "context": "Small application", "alternatives": "PostgreSQL",
                "decision": "Use SQLite", "tags": "storage,python", **changes}

    async def accepted(self, **changes):
        item = await self.call("create_decision", data=self.payload(**changes))
        return await self.call("approve_decision", decision_id=item["id"])
