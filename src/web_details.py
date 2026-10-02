from flask import render_template

from .comments import list_comments
from .db import get_db
from .decision_repository import get_decision
from .relation_repository import list_relations
from .web import blueprint
from .web_helpers import page_data, page_number
from .web_queries import decision_choices


def detail_context(decision_id):
    connection = get_db()
    item = get_decision(connection, decision_id)
    comment_page, relation_page = page_number("comment_page"), page_number("relation_page")
    comments, comment_total = list_comments(connection, decision_id, comment_page, 20)
    relations, relation_total = list_relations(connection, decision_id, relation_page, 20)
    choices = decision_choices(connection, item["project"])
    names = {choice["id"]: choice["title"] for choice in choices}
    return {"item": item, "comments": comments, "relations": relations, "decision_names": names,
            "comment_paging": page_data(comment_page, comment_total),
            "relation_paging": page_data(relation_page, relation_total),
            "successors": [choice for choice in choices
                           if choice["status"] == "accepted" and choice["id"] != decision_id]}


@blueprint.get("/decisions/<int:decision_id>")
def decision_detail(decision_id):
    return render_template("decision_detail.html", **detail_context(decision_id), error=None, form={})
