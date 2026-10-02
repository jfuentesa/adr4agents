from .decision_repository import SELECT_DECISION, serialize_decision


def build_filters(filters):
    clauses, params = [], []
    for key, column in (("project", "p.name"), ("status", "d.status"), ("author", "d.author")):
        if key in filters:
            clauses.append(f"{column} = ?")
            params.append(filters[key])
    for tag in filters.get("tags", []):
        clauses.append(
            "EXISTS (SELECT 1 FROM decision_tags t WHERE t.decision_id = d.id AND t.tag = ?)"
        )
        params.append(tag)
    for key, operator in (("date_from", ">="), ("date_to", "<=")):
        if key in filters:
            clauses.append(f"d.date {operator} ?")
            params.append(filters[key])
    if "q" in filters:
        columns = ("d.title", "d.context", "d.alternatives", "d.decision")
        clauses.append("(" + " OR ".join(
            f"instr(casefold({column}), casefold(?)) > 0" for column in columns
        ) + ")")
        params.extend([filters["q"]] * len(columns))
    return (" WHERE " + " AND ".join(clauses) if clauses else ""), params


def list_decisions(connection, filters, page, page_size):
    where, params = build_filters(filters)
    total = connection.execute(
        "SELECT COUNT(*) FROM decisions d JOIN projects p ON p.id = d.project_id" + where,
        params,
    ).fetchone()[0]
    rows = connection.execute(
        SELECT_DECISION + where + " ORDER BY d.id LIMIT ? OFFSET ?",
        [*params, page_size, (page - 1) * page_size],
    ).fetchall()
    return [serialize_decision(connection, row) for row in rows], total


def list_tags(connection, project=None):
    statement = "SELECT DISTINCT t.tag FROM decision_tags t"
    params = []
    if project is not None:
        statement += (
            " JOIN decisions d ON d.id = t.decision_id"
            " JOIN projects p ON p.id = d.project_id WHERE p.name = ?"
        )
        params.append(project)
    rows = connection.execute(statement + " ORDER BY t.tag", params).fetchall()
    return [row["tag"] for row in rows]
