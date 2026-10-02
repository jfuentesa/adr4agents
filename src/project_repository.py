import sqlite3

from .errors import conflict, not_found


def get_project(connection, project_id):
    row = connection.execute(
        "SELECT id, name, description, context FROM projects WHERE id = ?",
        (project_id,),
    ).fetchone()
    if row is None:
        raise not_found("Project")
    return dict(row)


def get_project_by_name(connection, name):
    row = connection.execute("SELECT id FROM projects WHERE name = ?", (name,)).fetchone()
    if row is None:
        raise not_found("Project")
    return get_project(connection, row["id"])


def list_projects(connection, page, page_size, query=None):
    clause, params = "", []
    if query:
        clause = " WHERE instr(casefold(name), casefold(?)) > 0"
        params.append(query)
    total = connection.execute("SELECT COUNT(*) FROM projects" + clause, params).fetchone()[0]
    rows = connection.execute(
        "SELECT id, name, description, context FROM projects" + clause
        + " ORDER BY id LIMIT ? OFFSET ?",
        [*params, page_size, (page - 1) * page_size],
    ).fetchall()
    return [dict(row) for row in rows], total


def create_project(connection, data):
    try:
        result = connection.execute(
            "INSERT INTO projects (name, description, context) VALUES (?, ?, ?)",
            (data["name"], data["description"], data["context"]),
        )
    except sqlite3.IntegrityError as error:
        raise conflict("A project with this name already exists.") from error
    return get_project(connection, result.lastrowid)


def update_project(connection, project_id, data):
    current = get_project(connection, project_id)
    current.update(data)
    try:
        connection.execute(
            "UPDATE projects SET name = ?, description = ?, context = ? WHERE id = ?",
            (current["name"], current["description"], current["context"], project_id),
        )
    except sqlite3.IntegrityError as error:
        raise conflict("A project with this name already exists.") from error
    return get_project(connection, project_id)
