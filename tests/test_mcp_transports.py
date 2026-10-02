import asyncio
import socket
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

from .mcp_support import McpTestCase


class McpTransportTests(McpTestCase):
    async def check_remote(self, client):
        async with client:
            tools = await client.list_tools()
            self.assertEqual(len(tools.tools), 22)
            result = await client.call_tool("create_project", {"data": {"name": "transport"}})
            self.assertFalse(result.is_error, result.content)
            self.assertEqual(result.structured_content["name"], "transport")

    async def test_stdio_from_another_directory(self):
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "src.mcp_server", "--transport", "stdio", "--api-url", self.api_url],
            cwd=self.directory.name,
        )
        await self.check_remote(Client(parameters))

    async def test_streamable_http(self):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        log_path = Path(self.directory.name) / "mcp.log"
        with log_path.open("wb") as log:
            process = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "src.mcp_server", "--port", str(port),
                "--api-url", self.api_url, stdout=log, stderr=log,
            )
            try:
                for attempt in range(100):
                    if process.returncode is not None:
                        self.fail(log_path.read_text())
                    try:
                        reader, writer = await asyncio.open_connection("127.0.0.1", port)
                        writer.close()
                        await writer.wait_closed()
                        break
                    except OSError:
                        await asyncio.sleep(0.1)
                else:
                    self.fail("MCP HTTP server did not start.")
                url = f"http://127.0.0.1:{port}/mcp"
                async with Client(url) as client:
                    result = await client.call_tool("list_projects", {})
                    self.assertFalse(result.is_error, result.content)
                await self.check_remote(Client(url, mode="legacy"))
            except BaseException:
                print(log_path.read_text(errors="replace"))
                raise
            finally:
                if process.returncode is None:
                    process.terminate()
                await asyncio.wait_for(process.wait(), timeout=10)
