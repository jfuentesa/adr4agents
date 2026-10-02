import sqlite3

from .errors import conflict, not_found


def serialize(row):
    result = dict(row)
    result["effective"] = bool(result["effective"])
    return result


def get_relation(connection, relation_id):
    row = connection.execute("SELECT * FROM relations WHERE id = ?", (relation_id,)).fetchone()
    if row is None:
        raise not_found("Relation")
    return serialize(row)


def list_relations(connection, decision_id, page, page_size):
    condition = " WHERE source_id = ? OR target_id = ?"
    params = (decision_id, decision_id)
    total = connection.execute("SELECT COUNT(*) FROM relations" + condition, params).fetchone()[0]
    rows = connection.execute(
        "SELECT * FROM relations" + condition + " ORDER BY id LIMIT ? OFFSET ?",
        (*params, page_size, (page - 1) * page_size),
    ).fetchall()
    return [serialize(row) for row in rows], total


def create_relation(connection, source_id, target_id, relation_type, *, effective=True):
    try:
        result = connection.execute(
            "INSERT INTO relations (source_id, target_id, type, effective) VALUES (?, ?, ?, ?)",
            (source_id, target_id, relation_type, int(effective)),
        )
    except sqlite3.IntegrityError as error:
        raise conflict("This relation already exists.") from error
    return get_relation(connection, result.lastrowid)


def update_relation(connection, relation_id, data):
    try:
        connection.execute(
            "UPDATE relations SET source_id = ?, target_id = ?, type = ?, effective = ? WHERE id = ?",
            (data["source_id"], data["target_id"], data["type"], int(data["effective"]), relation_id),
        )
    except sqlite3.IntegrityError as error:
        raise conflict("This relation already exists.") from error
    return get_relation(connection, relation_id)


def record_supersession(connection, source_id, target_id):
    existing = connection.execute(
        "SELECT id, effective FROM relations WHERE source_id = ? AND target_id = ? AND type = 'supersedes'",
        (source_id, target_id),
    ).fetchone()
    if existing is not None and not existing["effective"]:
        connection.execute("UPDATE relations SET effective = 1 WHERE id = ?", (existing["id"],))
        return get_relation(connection, existing["id"])
    return create_relation(connection, source_id, target_id, "supersedes")
