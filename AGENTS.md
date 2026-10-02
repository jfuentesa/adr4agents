# ADR4agents

ADR4agents is an application for managing and querying decisions. It provides a web interface for people, a JSON API for other programs, and an MCP server for agents.

## Golden rules

1. **Keep it simple:** use Python, Flask, Jinja, and SQLite; add complexity only when necessary.
2. **English first:** all application implementation, code comments, AGENTS.md, README.md, and documentation must be written in English.
3. **Ask before implementing:** every implementation uncertainty requires an explicit answer from the user, except for internal code organization, which is delegated to the agent. This rule does not restrict operations on ADRs managed by the application.
4. **Share business logic:** the web interface and API use the same operations to manage decisions.
5. **Organize code directly in `src/`:** create modules and folders as needed.
6. **Apply SOLID and clean code pragmatically:** use good practices without overengineering.
7. **Complete each implementation without technical debt:** include relevant validation, error handling, security, tests, and documentation, and verify behavior and integration.
8. **Store only final agreements in `AGENTS.md`:** no proposals, uncertainties, or pending tasks.

## Changes to AGENTS.md

- Include only final information confirmed by the user, without proposals, uncertainties, or pending tasks.

## Project technologies

| Project component | Approved technology |
| --- | --- |
| Backend and JSON API | Python + Flask. |
| Web interface | HTML and CSS with Jinja templates, served by Flask. |
| Web interactivity | Simple JavaScript when needed. |
| Persistence | SQLite through Python's standard-library `sqlite3` module, using direct SQL and parameterized queries, without an ORM. |
| Tests | Python's `unittest` and Flask's test client. |
| HTTP server | Waitress, compatible with Windows, for continuous API operation. |
| MCP server | Official MCP SDK for Python, with Streamable HTTP and an stdio option. |

## Application organization

- Serve the web interface and API from the same Flask application.
- Share the business functions for managing decisions between web views and API endpoints, avoiding duplicated rules.

## Frontend–API–MCP operation

- **Frontend:** Flask serves the HTML interface through Jinja. Web views and the API share decision logic.
- **API:** exposes operations through HTTP and JSON and validates data before accessing business logic and SQLite.
- **MCP:** presents tools with descriptions and parameters to the agent, converts tool calls into HTTP requests to the API, and returns the results. It neither accesses SQLite directly nor duplicates business logic.

```text
Person → Flask/Jinja web interface → Decision logic → SQLite
Agent → MCP server → Flask API → Decision logic → SQLite
Other programs → Flask API → Decision logic → SQLite
```

The API listens by default at `127.0.0.1:5000/api/v1`; MCP listens at `127.0.0.1:8001/mcp` through Streamable HTTP. It also supports stdio for local connections.

## System access

Access to the web interface, API, and MCP must always be enabled, without user accounts, roles, authentication, or authorization. No operation requires credentials or tokens.

## Decision data

| JSON field | Content |
| --- | --- |
| `project` | Project name: one word without spaces. |
| `author` | Author name: one alphanumeric word, without an associated user account. |
| `title` | Decision title. |
| `context` | Context as free text. |
| `alternatives` | Alternatives as free text. |
| `decision` | Decision as free text. |
| `tags` | Comma-separated words without spaces. |
| `date` | Date in `YYYY-MM-DD` format; assigned automatically on creation if omitted. |

The identifier, status, and successor reference are system metadata.

## API contract

- JSON API under `/api/v1`, with the agreed operations, filters, and pagination.
- Include creation and editing of projects and relations.
- `create_decision` creates a proposal with status `proposed`; `create_decision_draft` creates a draft with status `draft`.
- Drafts require a project, author, and title. Context, alternatives, and decision may be empty until review is requested, when they must be complete.
- Relations are limited to decisions within the same project. An effective replacement requires both the original and successor to be `accepted`.
- A proposed replacement remains linked to the original without changing its status; replacement becomes effective through `supersede_decision` or an effective `supersedes` relation.

## Decision statuses

| Status | Meaning |
| --- | --- |
| `draft` | Draft in progress. |
| `proposed` | Ready for review and approval. |
| `accepted` | Approved and current. |
| `rejected` | Reviewed and rejected. |
| `superseded` | Replaced by another ADR, with a reference to its successor. |

```text
draft → proposed → accepted → superseded
                 → rejected
```

- Requesting review of a draft moves it from `draft` to `proposed`.
- Approving a proposal moves it from `proposed` to `accepted`; rejecting it moves it to `rejected`.
- Proposing a replacement creates a successor draft without changing the original ADR's status. Making the replacement effective moves the original from `accepted` to `superseded` and links it to its accepted successor.
- Editing an accepted ADR preserves its `accepted` status.

## MCP operations

All MCP operation names must be in English. Agents may query and manage ADRs, including approving them and editing accepted ADRs.

| Operation | Description |
| --- | --- |
| `list_projects` | List projects. |
| `get_project` | Retrieve a project's context and description. |
| `create_project` | Create a project. |
| `update_project` | Edit a project. |
| `list_decisions` | List a project's ADRs with filters and pagination. |
| `search_decisions` | Search ADRs by text, status, tags, or other criteria. |
| `get_decision` | Retrieve a complete ADR by its identifier. |
| `get_current_decisions` | Retrieve a project's accepted decisions that remain current. |
| `get_decision_relations` | Retrieve decisions that an ADR complements, supersedes, or contradicts. |
| `create_relation` | Create a relation between decisions. |
| `update_relation` | Edit a relation between decisions. |
| `create_decision` | Create a proposal with the defined decision fields. |
| `create_decision_draft` | Create an ADR draft. |
| `update_decision_draft` | Edit an ADR draft. |
| `approve_decision` | Move a proposal to `accepted`. |
| `reject_decision` | Move a proposal to `rejected`. |
| `supersede_decision` | Move an accepted ADR to `superseded` and link it to its accepted successor. |
| `update_decision` | Edit an ADR, including an accepted ADR. |
| `comment_decision` | Add questions, observations, or arguments to an ADR. |
| `request_decision_review` | Request review of a draft and move it to `proposed`. |
| `propose_decision_replacement` | Create a draft proposing to replace an existing decision. |
| `list_tags` | List tags available for classifying and searching ADRs. |

## Folder and file structure

The application code root must be directly in `src/`, without an intermediate `adr4agents/` subdirectory.

```text
adr4agents/
├── AGENTS.md
├── README.md
├── pyproject.toml
├── src/
│   ├── __init__.py
│   ├── __main__.py
│   ├── install.bat
│   ├── start_app.bat
│   ├── start_mcp.bat
│   ├── start_all.bat
│   ├── config.py
│   ├── web.py
│   ├── web_decisions.py
│   ├── web_details.py
│   ├── web_projects.py
│   ├── web_workflow.py
│   ├── web_relations.py
│   ├── web_helpers.py
│   ├── web_queries.py
│   ├── api.py
│   ├── project_routes.py
│   ├── decision_routes.py
│   ├── workflow_routes.py
│   ├── relation_routes.py
│   ├── comment_routes.py
│   ├── http_helpers.py
│   ├── http_errors.py
│   ├── mcp_server.py
│   ├── mcp_api_client.py
│   ├── mcp_models.py
│   ├── mcp_registration.py
│   ├── mcp_project_tools.py
│   ├── mcp_query_tools.py
│   ├── mcp_decision_tools.py
│   ├── mcp_workflow_tools.py
│   ├── mcp_relation_tools.py
│   ├── decisions.py
│   ├── decision_validation.py
│   ├── decision_queries.py
│   ├── projects.py
│   ├── relations.py
│   ├── replacements.py
│   ├── comments.py
│   ├── validation.py
│   ├── errors.py
│   ├── db.py
│   ├── project_repository.py
│   ├── decision_repository.py
│   ├── relation_repository.py
│   ├── sql/
│   ├── templates/
│   └── static/
│       ├── css/
│       └── js/
├── tests/
├── docs/
└── instance/
```

- `README.md`: installation, execution, and testing instructions.
- `pyproject.toml`: Python package configuration and dependencies.
- `src/__init__.py`: Flask application creation and configuration through `create_app`.
- `src/__main__.py`: API execution with Waitress through `python -m src`.
- `src/install.bat`: virtual environment setup and dependency installation on Windows.
- `src/start_app.bat`: API startup with Waitress from any directory, with automatic setup if dependencies are missing.
- `src/start_mcp.bat`: MCP startup from any directory, with automatic setup if dependencies are missing.
- `src/start_all.bat`: launch `start_app.bat` and `start_mcp.bat` in separate Windows command windows, preparing missing dependencies before launching them.
- `config.py`: application configuration and SQLite location through environment settings.
- `web.py`: web interface registration, form protection, and browser headers.
- `web_decisions.py`, `web_details.py`, and `web_projects.py`: decision and project listings, details, and forms.
- `web_workflow.py` and `web_relations.py`: actions on statuses, comments, replacements, and relations.
- `web_helpers.py` and `web_queries.py`: form parameters, pagination, and presentation queries.
- `api.py`: route registration under `/api/v1` and service health checks.
- `*_routes.py`: endpoints grouped by projects, decisions, statuses, relations, and comments.
- `http_helpers.py` and `http_errors.py`: request parsing, pagination, responses, and JSON errors.
- `mcp_server.py`: MCP configuration and startup through Streamable HTTP or stdio.
- `mcp_api_client.py`: HTTP JSON requests to the API and connection error handling.
- `mcp_models.py` and `mcp_registration.py`: typed parameters, registration, and MCP tool responses.
- `mcp_*_tools.py`: tools grouped by projects, queries, decisions, statuses, and relations.
- `decisions.py`: business rules and operations shared by the web interface and API.
- `projects.py`, `relations.py`, `replacements.py`, and `comments.py`: operations for their respective entities.
- `validation.py` and `decision_validation.py`: validation of fields, decisions, and filters.
- `errors.py`: application errors independent of HTTP.
- `decision_queries.py`: decision queries, filters, and tags.
- `db.py`: SQLite connections and data access through parameterized queries.
- `*_repository.py`: SQL queries and writes for projects, decisions, and relations.
- `sql/`: SQL scripts for the database schema and its evolution.
- `templates/`: Jinja HTML templates.
- `static/css/` and `static/js/`: interface styles and JavaScript.
- `tests/`: automated tests for business logic, persistence, API, MCP, and web interface.
- `docs/`: functional and technical documentation requiring files beyond the README.
- `instance/`: local runtime data, including the SQLite database; its contents must not be committed to version control.

Create files and folders when a feature needs them; do not add empty modules or layers in advance.

## Web interface

- Design based on the supplied visual reference: light background, primary blue, sidebar, cards, decision table, and status badges.
- Listing with search, filters, pagination, and a preview of the selected ADR; dedicated detail and editing pages.
- Forms for managing projects, decisions, statuses, replacements, comments, and relations through the business operations shared with the API.
- Mobile-responsive presentation, without adding template, activity, or history features.

## Programming approach

- Use simple technologies and solutions proportionate to the project, without overengineering or unnecessary layers, abstractions, dependencies, or infrastructure.
- Apply good programming practices, SOLID principles, and clean code pragmatically.

## Mandatory consultation of uncertainties

These consultations concern project development and implementation, not decisions stored in the database. The application and MCP allow creating, approving, and editing accepted ADRs without this rule requiring consultation with the user for each operation.

- Ask the user about every uncertainty before implementing and wait for their explicit answer. This includes functionality, architecture, technologies, dependencies, data models, API contracts, interface, and deployment.
- Internal code organization is delegated to the agent according to the documented structure; uncertainties still require consultation.
- Present relevant alternatives, their consequences, and a simple recommendation to help the user decide.
- Consult the user about any change from approved alternatives.

## Quality and absence of technical debt

- Leave no technical debt in any implementation. If a constraint prevents this, consult the user before continuing.
- Complete input validation, error handling, security, and tests relevant to the scope of each implementation.
- Verify implemented behavior and integration with affected components before considering the work complete.
- Update documentation and execution instructions when the change requires it.
