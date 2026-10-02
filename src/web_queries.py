from .decision_queries import build_filters


def project_choices(connection):
    return connection.execute("SELECT id, name FROM projects ORDER BY name").fetchall()


def decision_choices(connection, project=None):
    where = " WHERE p.name = ?" if project else ""
    return connection.execute(
        "SELECT d.id, d.title, d.status, p.name AS project FROM decisions d"
        " JOIN projects p ON p.id = d.project_id" + where + " ORDER BY d.id",
        (project,) if project else (),
    ).fetchall()


def decision_counts(connection, filters):
    where, params = build_filters({key: value for key, value in filters.items() if key != "status"})
    rows = connection.execute(
        "SELECT d.status, COUNT(*) AS total FROM decisions d"
        " JOIN projects p ON p.id = d.project_id" + where + " GROUP BY d.status", params,
    ).fetchall()
    return {row["status"]: row["total"] for row in rows}
