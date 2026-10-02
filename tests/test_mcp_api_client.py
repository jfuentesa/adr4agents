import unittest
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from mcp import Client

from src.mcp_api_client import ApiClient, ApiError
from src.mcp_server import create_mcp_server


class McpApiClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_unavailable_api_is_reported_to_agent(self):
        server = create_mcp_server()
        with patch("src.mcp_api_client.urlopen", side_effect=URLError("offline")):
            async with Client(server) as client:
                result = await client.call_tool("list_projects", {})
        self.assertTrue(result.is_error)
        self.assertIn("Cannot reach", result.content[0].text)

    async def test_invalid_and_non_object_json(self):
        for body in (b"not JSON", b"[]"):
            with patch("src.mcp_api_client.urlopen", return_value=BytesIO(body)):
                with self.assertRaises(ApiError):
                    await ApiClient("http://127.0.0.1:5000/api/v1").request("GET", "/projects")

    async def test_non_json_http_error_preserves_status(self):
        error = HTTPError("http://localhost", 413, "Too large", {}, BytesIO(b"<html>Error</html>"))
        with patch("src.mcp_api_client.urlopen", side_effect=error):
            with self.assertRaises(ApiError) as raised:
                await ApiClient("http://127.0.0.1:5000/api/v1").request("POST", "/decisions", data={})
        self.assertEqual(raised.exception.status, 413)
        self.assertEqual(raised.exception.details["error"]["code"], "http_error")

    def test_invalid_configuration_is_rejected(self):
        for url in ("file:///database", "http://user:password@localhost", "http://localhost?x=1"):
            with self.assertRaises(ValueError):
                ApiClient(url)
        for timeout in (0, -1, 301):
            with self.assertRaises(ValueError):
                ApiClient("http://localhost", timeout)
