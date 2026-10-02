# ADR4agents MCP

The server uses the official MCP SDK for Python and exposes the 22 operations agreed upon in [AGENTS.md](../AGENTS.md), with names, descriptions, and typed parameters in English. Agents discover these tools when connecting and can query projects and ADRs, create and edit decisions, and manage states, relations, and comments.

```text
Agent → MCP → API /api/v1 → Decision logic → SQLite
```

Each tool calls the API over HTTP; MCP does not access SQLite or duplicate business rules. It returns the API's JSON as structured content and text. Collections include pagination. Errors are marked with `isError`; errors from the API include their HTTP status code and details. No authentication or tokens are required.

## Startup on Windows

From the project root, start the API and MCP in separate terminals:

```powershell
.\src\start_app.bat
.\src\start_mcp.bat
```

The API listens at `http://127.0.0.1:5000/api/v1`, and MCP uses **Streamable HTTP** at `http://127.0.0.1:8001/mcp`. The BAT files install missing dependencies. Stop each server with `Ctrl+C`.

You can also run MCP directly, adjusting the API URL or port:

```powershell
.\.venv\Scripts\python.exe -m src.mcp_server --port 8001 --api-url http://127.0.0.1:5000/api/v1
```

The API URL can also be set through `ADR4AGENTS_API_URL`. `--timeout` sets the maximum time for each API request in seconds; the default is 15.

## Connect to Codex

With both servers running, register the HTTP connection:

```powershell
codex mcp add adr4agents --url http://127.0.0.1:8001/mcp
codex mcp list
```

The listing checks the configuration. To verify the connection, ask the agent: "List the available projects through ADR4agents."

As a local alternative, **stdio** lets Codex launch MCP. Keep the API running and add this configuration to `~/.codex/config.toml`, adjusting the project path:

```toml
[mcp_servers.adr4agents]
command = 'C:\PATH\TO\adr4agents\.venv\Scripts\python.exe'
args = ["-m", "src.mcp_server", "--transport", "stdio"]
```

Choose a single configuration for `adr4agents`. With stdio, you do not need to start the MCP server beforehand or use port 8001. Install the dependencies first with `src\install.bat`; the editable installation allows importing `src` from other directories.

Creation and editing parameters are grouped under `data`; filters are grouped under `filters`. For example, `create_decision_draft` accepts `{"data":{"project":"demo","author":"Agent1","title":"Use SQLite"}}`. To query current decisions, use `get_current_decisions` with `{"filters":{"project":"demo"}}`.

References: [API contract](API.md), [official MCP SDK](https://github.com/modelcontextprotocol/python-sdk), and [Codex MCP documentation](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).
