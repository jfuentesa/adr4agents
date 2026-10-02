# ADR4agents

A small application for documenting architecture decisions. It provides a Flask/Jinja web interface, a JSON API under `/api/v1`, and 22 MCP tools for agents. SQLite stores projects, decisions, states, tags, comments and relations. Access is open; authors are metadata, with no accounts or roles.

## Installation on Windows

Python 3.13 or later is required. From the project root:

```powershell
.\src\install.bat --no-pause
```

The installer creates `.venv` if necessary and installs the project and dependencies. It can also be launched by double-clicking `src\install.bat`.

Alternatively:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

## Run all servers on Windows

Double-click `src\start_all.bat`, or run:

```powershell
.\src\start_all.bat
```

The launcher prepares missing dependencies once before opening separate windows for `start_app.bat` (web and API) and `start_mcp.bat` (MCP over Streamable HTTP). It works from any directory. Both windows remain open to show startup errors. Stop each server with `Ctrl+C` in its window; closing the launcher does not stop the servers. The launcher requests startup but does not wait for server readiness. Use the individual scripts below for custom command-line arguments.

## Run the web interface and API

Double-click `src\start_app.bat`, or run:

```powershell
.\src\start_app.bat
```

Open **http://127.0.0.1:5000/** for the web interface. The API is available at **http://127.0.0.1:5000/api/v1**. Waitress serves both in the same process. Stop it with `Ctrl+C`.

The web interface includes decision filters and previews, full records, project and decision forms, review and approval, replacements, comments and relations. It follows the supplied visual reference and adapts to mobile screens. Forms preserve invalid input and share the API's business rules. Form protection uses a temporary browser session, without authentication; reload an expired form after a server restart.

The BAT files locate the project root even when launched from another directory. Startup prepares missing dependencies and accepts command-line arguments:

```powershell
.\src\start_app.bat --host 127.0.0.1 --port 5001
```

Direct Python startup is also available:

```powershell
.\.venv\Scripts\python.exe -m src --host 127.0.0.1 --port 5000
Invoke-RestMethod http://127.0.0.1:5000/api/v1/health
```

An occupied port causes startup to fail. Use another port or stop the existing server. These commands do not configure automatic Windows startup.

The database defaults to `instance/adr4agents.sqlite3`. To use another location, set `ADR4AGENTS_DATABASE` before starting. Schema updates run automatically and preserve existing data.

```powershell
$env:ADR4AGENTS_DATABASE = 'D:\data\adr4agents.sqlite3'
```

For development:

```powershell
.\.venv\Scripts\python.exe -m flask --app src:create_app run --host 127.0.0.1 --port 5000
```

## Run MCP

Keep the API running and start MCP in a separate terminal:

```powershell
.\src\start_mcp.bat
```

Streamable HTTP listens at **http://127.0.0.1:8001/mcp**. Local stdio connections are also supported. See [MCP setup and Codex connection](docs/MCP.md).

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

Tests use temporary databases independent of runtime data and cover the API, persistence, MCP transports and web workflows.

## Documentation

- [Web interface](docs/WEB.md).
- [API contract and examples](docs/API.md).
- [MCP operation and connection](docs/MCP.md).
- [Project rules](AGENTS.md).
