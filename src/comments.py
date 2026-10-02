from datetime import date

from . import validation as validate
from .db import transaction
from .decision_repository import get_decision


def create_comment(connection, decision_id, data):
    validate.validate_object(data, {"author", "text", "date"}, {"author", "text"})
    values = {
        "author": validate.author(data["author"]),
        "text": validate.text(data["text"], "text"),
        "date": validate.calendar_date(data.get("date", date.today().isoformat())),
    }
    with transaction(connection):
        get_decision(connection, decision_id)
        cursor = connection.execute(
            "INSERT INTO comments (decision_id, author, text, date) VALUES (?, ?, ?, ?)",
            (decision_id, values["author"], values["text"], values["date"]),
        )
        return {"id": cursor.lastrowid, "decision_id": decision_id, **values}


def list_comments(connection, decision_id, page, page_size):
    get_decision(connection, decision_id)
    total = connection.execute(
        "SELECT COUNT(*) FROM comments WHERE decision_id = ?", (decision_id,)
    ).fetchone()[0]
    rows = connection.execute(
        "SELECT * FROM comments WHERE decision_id = ? ORDER BY id LIMIT ? OFFSET ?",
        (decision_id, page_size, (page - 1) * page_size),
    ).fetchall()
    return [dict(row) for row in rows], total
