import argparse
import os

from mcp.server import MCPServer

from . import mcp_decision_tools, mcp_project_tools, mcp_query_tools, mcp_relation_tools, mcp_workflow_tools
from .mcp_api_client import ApiClient


DEFAULT_API_URL = "http://127.0.0.1:5000/api/v1"
INSTRUCTIONS = (
    "Manage architectural decisions through the ADR4agents API. "
    "Use list_projects to discover project names and IDs, and get_current_decisions "
    "to retrieve applicable ADRs. Tools return JSON objects; collections include pagination. "
    "Authors are labels, not accounts. Drafts need project, author and title; complete their "
    "texts before review. Approve proposed ADRs. Replacements only become effective when "
    "explicitly superseded, with both ADRs accepted in the same project. "
    "Do not blindly retry writes after a connection error: check the resulting state first."
)


def create_mcp_server(api_url=DEFAULT_API_URL, *, timeout=15):
    api = ApiClient(api_url, timeout)
    server = MCPServer("ADR4agents", version="0.1.0", instructions=INSTRUCTIONS)
    for tools in (mcp_project_tools, mcp_query_tools, mcp_decision_tools,
                  mcp_workflow_tools, mcp_relation_tools):
        tools.register_tools(server, api)
    return server


def main():
    parser = argparse.ArgumentParser(description="Run the ADR4agents MCP-to-API adapter.")
    parser.add_argument("--transport", choices=("streamable-http", "stdio"), default="streamable-http")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--api-url", default=os.environ.get("ADR4AGENTS_API_URL", DEFAULT_API_URL))
    parser.add_argument("--timeout", type=float, default=15)
    arguments = parser.parse_args()
    if not 1 <= arguments.port <= 65535:
        parser.error("Port must be between 1 and 65535.")
    try:
        server = create_mcp_server(arguments.api_url, timeout=arguments.timeout)
    except ValueError as error:
        parser.error(str(error))
    if arguments.transport == "stdio":
        server.run(transport="stdio")
    else:
        server.run(transport="streamable-http", host=arguments.host, port=arguments.port)


if __name__ == "__main__":
    main()
