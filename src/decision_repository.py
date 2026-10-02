from .errors import not_found


SELECT_DECISION = """
    SELECT d.id, p.name AS project, d.author, d.title, d.context,
           d.alternatives, d.decision, d.date, d.status, d.superseded_by
    FROM decisions d JOIN projects p ON p.id = d.project_id
"""


def serialize_decision(connection, row):
    result = dict(row)
    tags = connection.execute(
        "SELECT tag FROM decision_tags WHERE decision_id = ? ORDER BY tag",
        (row["id"],),
    ).fetchall()
    result["tags"] = ",".join(tag["tag"] for tag in tags)
    return result


def get_decision(connection, decision_id):
    row = connection.execute(SELECT_DECISION + " WHERE d.id = ?", (decision_id,)).fetchone()
    if row is None:
        raise not_found("Decision")
    return serialize_decision(connection, row)


def set_tags(connection, decision_id, tags):
    connection.execute("DELETE FROM decision_tags WHERE decision_id = ?", (decision_id,))
    connection.executemany(
        "INSERT INTO decision_tags (decision_id, tag) VALUES (?, ?)",
        [(decision_id, tag) for tag in tags],
    )


def create_decision(connection, project_id, data, status):
    result = connection.execute(
        """INSERT INTO decisions
           (project_id, author, title, context, alternatives, decision, date, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (project_id, data["author"], data["title"], data["context"],
         data["alternatives"], data["decision"], data["date"], status),
    )
    set_tags(connection, result.lastrowid, data["tags"])
    return get_decision(connection, result.lastrowid)


def update_decision(connection, decision_id, project_id, data):
    connection.execute(
        """UPDATE decisions SET project_id = ?, author = ?, title = ?, context = ?,
           alternatives = ?, decision = ?, date = ? WHERE id = ?""",
        (project_id, data["author"], data["title"], data["context"],
         data["alternatives"], data["decision"], data["date"], decision_id),
    )
    set_tags(connection, decision_id, data["tags"])
    return get_decision(connection, decision_id)


def set_status(connection, decision_id, status, successor=None):
    connection.execute(
        "UPDATE decisions SET status = ?, superseded_by = ? WHERE id = ?",
        (status, successor, decision_id),
    )
    return get_decision(connection, decision_id)
