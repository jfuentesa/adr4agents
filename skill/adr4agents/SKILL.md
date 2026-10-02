---
name: adr4agents
description: Query and manage architecture decision records (ADRs), projects, and relations through the ADR4agents MCP server.
---

# ADR4agents

## Golden rule

The user must explicitly provide the ADR4agents project name established for the current project. Until they do, do not perform any ADR4agents operation, including queries. Ask for that name and wait for their answer; do not infer it from the repository, directory, or available projects.

## Connect and verify the server

The skill provides instructions; installing it does not connect the server or make its tools available. Before an operation, find the ADR4agents tools in the session's tool catalog, using the available discovery mechanism if tools are loaded on demand. Tool names may have a client prefix: check their source server and schema as well as their names.

If the tools are missing, provide the following concrete steps. Run the PowerShell commands from the root of the ADR4agents installation, which may differ from the project whose ADRs you want to manage. Replace example paths with the actual installation location.

### Streamable HTTP

1. Python 3.13 or later is required. Install dependencies with `.\src\install.bat --no-pause`.
2. Run `.\src\start_app.bat` to start the web interface and API. Run `.\src\start_mcp.bat` in another terminal; keep both processes running.
3. Register the connection in Codex:

   ```powershell
   codex mcp add adr4agents --url http://127.0.0.1:8001/mcp
   codex mcp list
   ```

   Alternatively, add this entry to `~/.codex/config.toml` (on Windows, usually `%USERPROFILE%\.codex\config.toml`):

   ```toml
   [mcp_servers.adr4agents]
   url = "http://127.0.0.1:8001/mcp"
   ```

The MCP URL ends in `/mcp`; it differs from the web and API URLs. No credentials, tokens, or login are required. `127.0.0.1` must be reachable from the environment running the MCP client; on another machine or in a remote environment, it does not refer to this local server.

### Local alternative: stdio

Install dependencies and keep the API running. Configure a single `adr4agents` entry, using stdio instead of HTTP:

```toml
[mcp_servers.adr4agents]
command = 'C:\PATH\TO\adr4agents\.venv\Scripts\python.exe'
args = ["-m", "src.mcp_server", "--transport", "stdio"]
```

Codex starts the MCP process: you do not need to run `start_mcp.bat` or use port 8001. The installer's editable installation allows importing `src` from other directories. The `command` path must point to the Python executable in the environment where ADR4agents is installed.

### Configuration and troubleshooting

- The default API URL is `http://127.0.0.1:5000/api/v1`. If it changes, pass the actual URL to MCP, for example `.\src\start_mcp.bat --api-url http://127.0.0.1:5001/api/v1`, or set `ADR4AGENTS_API_URL` in the MCP process environment. For stdio, append `"--api-url", "http://127.0.0.1:5001/api/v1"` to `args`.
- To change the MCP HTTP port, use `.\src\start_mcp.bat --port 8002` and update the client URL as well. `--timeout` controls the maximum duration of each API request; the default is 15 seconds.
- Check the API without querying ADRs: `Invoke-RestMethod http://127.0.0.1:5000/api/v1/health` should return `status: ok`. Adjust the URL as needed. If it fails, check API startup, address, and port before trying MCP operations.
- `codex mcp list` checks registration, but does not prove that tools are available or the API responds. Reload the connection or restart the client if it has not picked up the change, then discover the tools again. The server publishes 22 operations; verify that tools such as `get_project`, `get_current_decisions`, and `create_decision_draft` appear with their schemas.
- Once the user has explicitly provided the project name, test `get_current_decisions` with `{"filters":{"project":"CONFIRMED_PROJECT_NAME"}}`. A successful response containing `items` and `pagination`, even if empty, confirms an MCP call to the API. Before receiving the name, limit checks to connection status, the tool catalog, and API health; do not call `list_projects` as a test.
- If tools appear but a call returns an API connection error, check `--api-url` or `ADR4AGENTS_API_URL` and the API process. If a tool is missing, also check whether the client disabled or filtered it. Resolve validation or data errors using the schema and returned message, without reconfiguring the connection.

If the connection is still unavailable, report which check failed and the remaining steps. Do not invent results or replace MCP tools with direct SQLite access or API calls to manage ADRs. Loading the skill alone does not authorize client configuration changes; present the steps, or execute them when the user has requested connection setup. Do not test the connection through writes.

Client configuration reference: [official Codex MCP documentation](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).

## Choose a tool

| Need | Tools and selection criteria |
| --- | --- |
| Project context | `list_projects`, `get_project`; `create_project`, `update_project` to maintain the name, description, and context. |
| Current decisions | `get_current_decisions`: returns only accepted ADRs. |
| Browse or search | `list_decisions` for filtering; `search_decisions` requires text and searches the title, context, alternatives, and decision; `list_tags` discovers tags in use. |
| Read a complete ADR | `get_decision`. |
| Create an ADR | `create_decision` creates a complete proposal; `create_decision_draft` allows empty context, alternatives, and decision fields. The project must exist. |
| Edit content | `update_decision` preserves the status, including for accepted ADRs; `update_decision_draft` requires a draft. |
| Review | `request_decision_review` moves a complete draft to proposed; `approve_decision` and `reject_decision` act only on proposals. |
| Replace | `propose_decision_replacement` creates a draft linked to an accepted ADR in the same project. Approving the successor does not activate the replacement: `supersede_decision` takes the original as `decision_id` and the successor as `successor_id`, both accepted. |
| Relate | `get_decision_relations` queries incoming and outgoing relations; `create_relation`, `update_relation` manage `complements`, `contradicts`, and `supersedes` within one project. For `supersedes`, `source_id` is the successor and `target_id` the original; creating this relation or converting another type to it activates the replacement. An effective replacement cannot be reassigned or removed. |
| Contribute arguments | `comment_decision` adds a comment without editing the ADR. |

## Parameters that affect usage

- Projects are queried and edited by numeric ID; ADRs and their filters use the project **name**.
- ADR queries support project, author, tags, and inclusive dates (`date_from`, `date_to`); general queries also support status. Without a project filter, they cover all projects. Multiple tags are combined with **AND**.
- Collections return `items` and `pagination` (`page`, `page_size`, `total`, `pages`). The first page is 1; the default page size is 20 and the maximum is 100.
- In `data` objects, `alternatives` is free text and `tags` is a string of comma-separated words, not lists. Project names and tags cannot contain spaces; authors are alphanumeric. Dates use `YYYY-MM-DD` and are assigned automatically on creation if omitted.
- When editing, omitted fields retain their values; `tags: ""` clears the tags. Status and successor are managed through workflow operations rather than editable fields.
- In replacement relations, `effective` distinguishes a linked proposal from an active replacement.

Use each tool's published schema for exact arguments. API failures are returned with `isError` and, when an HTTP response exists, `http_status` and `response`.
