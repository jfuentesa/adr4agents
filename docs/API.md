# ADR4agents API

Base: `/api/v1`. Requests with a body use `Content-Type: application/json`. No credentials or tokens are required.

See [AGENTS.md](../AGENTS.md) for general ADR rules and statuses. This document describes the HTTP contract.

## Decision payloads

```json
{"project":"demo","author":"Agent1","title":"Choose SQLite","context":"Small application","alternatives":"PostgreSQL","decision":"Use SQLite","tags":"database,python","date":"2026-10-02"}
```

`project` must name an existing project and contain no spaces. `author` accepts letters and numbers without spaces or hyphens. Tags are comma-separated, deduplicated and sorted; each tag is a word without spaces and may contain hyphens. An empty string means no tags.

`date` accepts valid dates in `YYYY-MM-DD` format and defaults to the server's local date on creation. Text fields are trimmed. Proposals require `project`, `author`, `title`, `context`, `alternatives`, and `decision`; `tags` and `date` are optional.

Responses add `id`, `status`, and `superseded_by`. Status values are `draft`, `proposed`, `accepted`, `rejected`, and `superseded`. `superseded_by` is `null` until a replacement becomes effective.

Limits: 128 characters for project, author, and each tag; 300 for title; 100,000 for each long text field; 4096 for the tags string; 1 MiB per JSON body.

## Endpoints

Append these routes to `/api/v1`. Route identifiers are positive integers.

| Method | Route | Operation |
| --- | --- | --- |
| GET | `/health` | Check service and database availability. |
| GET | `/projects` | `list_projects` |
| GET | `/projects/{id}` | `get_project` |
| POST | `/projects` | `create_project` |
| PATCH | `/projects/{id}` | `update_project` |
| GET | `/decisions` | `list_decisions` |
| GET | `/decisions/search` | `search_decisions` |
| GET | `/decisions/current` | `get_current_decisions` |
| GET | `/decisions/{id}` | `get_decision` |
| POST | `/decisions` | `create_decision`: creates `proposed`. |
| POST | `/decisions/drafts` | `create_decision_draft`: creates `draft`. |
| PATCH | `/decisions/{id}` | `update_decision` |
| PATCH | `/decisions/{id}/draft` | `update_decision_draft` |
| POST | `/decisions/{id}/review` | `request_decision_review` |
| POST | `/decisions/{id}/approve` | `approve_decision` |
| POST | `/decisions/{id}/reject` | `reject_decision` |
| POST | `/decisions/{id}/supersede` | `supersede_decision` |
| POST | `/decisions/{id}/replacement` | `propose_decision_replacement` |
| GET | `/decisions/{id}/relations` | `get_decision_relations` |
| GET | `/relations/{id}` | Retrieve a relation. |
| POST | `/relations` | `create_relation` |
| PATCH | `/relations/{id}` | `update_relation` |
| GET | `/decisions/{id}/comments` | Retrieve comments. |
| POST | `/decisions/{id}/comments` | `comment_decision` |
| GET | `/tags` | `list_tags` |

## Projects and partial updates

Create a project with `{"name":"demo","description":"Description","context":"Context"}`. Only `name` is required and must be a word without spaces. `description` and `context` default to empty strings. Names are unique and case-sensitive.

PATCH requires at least one field and preserves omitted fields. Status and successor cannot be edited directly; use their dedicated endpoints.

## Draft and status requests

Draft payloads require only `project`, `author`, and `title`. `context`, `alternatives`, and `decision` may be omitted or empty, but must be complete for `/review`.

`/review`, `/approve`, and `/reject` receive `{}`. Invalid status transitions return `409`; incomplete text fields on review return `400`.

## Relation and replacement requests

Create a relation with `{"source_id":2,"target_id":1,"type":"complements"}`. Decisions must be distinct and belong to the same project. Types are `complements`, `contradicts`, and `supersedes`. The source complements, contradicts, or supersedes the target.

Responses contain `id`, `source_id`, `target_id`, `type`, and `effective`. Complement and contradiction relations are immediately effective. Collections include incoming and outgoing relations and support pagination.

`POST /decisions/{original_id}/replacement` accepts draft fields, with `author` and `title` required. The project is taken from the original. It creates a successor draft and a `supersedes` relation with `effective:false`; the original remains `accepted`.

`POST /decisions/{original_id}/supersede` receives `{"successor_id":2}` and requires both ADRs to be `accepted`. The original's response includes `status:"superseded"` and `superseded_by:2`; the relation becomes `effective:true`.

POST `/relations` with type `supersedes`, or PATCH converting another type to `supersedes`, also activates replacement and requires both ADRs accepted. An existing replacement proposal is activated without duplicating its relation.

PATCH rejects reassigning an effective supersession relation or changing its type. It also rejects moving a related ADR to another project.

## Queries and pagination

Collections accept `page` and `page_size`, defaulting to page 1 and 20 items, with a maximum page size of 100. Results are ordered by ascending identifier; tags are ordered by text.

```json
{"items":[],"pagination":{"page":1,"page_size":20,"total":0,"pages":0}}
```

Decision filters:

- `project`, `author`, and `status`: exact match.
- `tags`: comma-separated string; all specified tags must match.
- `date_from` and `date_to`: inclusive interval in `YYYY-MM-DD` format.
- `q`: search in title, context, alternatives, and decision.

`/decisions/search` requires `q`. `/decisions/current` returns only `accepted` and accepts the other filters. Search is case-insensitive, including Unicode, and treats `%`, `_`, and quotes as literal characters.

`/projects` accepts `q` to search names; `/tags` accepts `project`. Filters can be combined with pagination. Unknown, repeated, or invalid parameters are rejected.

## Comments

Create a comment with `{"author":"Agent1","text":"Observation","date":"2026-10-02"}`. `author` and `text` are required; the date defaults automatically. Collections support pagination.

## Errors and responses

- `200`: successful query, update, or transition.
- `201`: resource created; `Location` identifies its location or collection.
- `400`: invalid data, fields, filters, or JSON body.
- `404`: resource or route not found.
- `405`: method not allowed.
- `409`: duplicate name, duplicate relation, or status conflict.
- `413`: body too large.
- `415`: body without a JSON content type.
- `503`: SQLite is busy; the operation can be retried.

```json
{"error":{"code":"validation_error","message":"Must contain only letters and numbers.","field":"author"}}
```

Application errors use JSON. `field` appears for errors associated with a specific field. Unknown fields are rejected. Waitress may reject requests before they reach Flask, including bodies exceeding 1 MiB; transport responses may use a different format.

## PowerShell example

```powershell
$api = 'http://127.0.0.1:5000/api/v1'
Invoke-RestMethod "$api/projects" -Method Post -ContentType 'application/json' `
    -Body '{"name":"demo"}'

$payload = @{
    project = 'demo'
    author = 'Agent1'
    title = 'Choose SQLite'
    context = 'Small application'
    alternatives = 'PostgreSQL'
    decision = 'Use SQLite'
    tags = 'database,python'
} | ConvertTo-Json

$adr = Invoke-RestMethod "$api/decisions" -Method Post `
    -ContentType 'application/json' -Body $payload

Invoke-RestMethod "$api/decisions/$($adr.id)/approve" -Method Post `
    -ContentType 'application/json' -Body '{}'

Invoke-RestMethod "$api/decisions/current?project=demo"
```
