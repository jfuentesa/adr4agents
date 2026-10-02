from flask import Blueprint, url_for

from . import comments
from .db import get_db
from .http_helpers import body, collection, created, pagination, query_parameters


blueprint = Blueprint("comments", __name__)


@blueprint.get("/decisions/<int:decision_id>/comments")
def list_comments(decision_id):
    parameters = query_parameters({"page", "page_size"})
    page, page_size = pagination(parameters)
    items, total = comments.list_comments(get_db(), decision_id, page, page_size)
    return collection(items, total, page, page_size)


@blueprint.post("/decisions/<int:decision_id>/comments")
def comment_decision(decision_id):
    query_parameters(set())
    item = comments.create_comment(get_db(), decision_id, body())
    return created(item, url_for("api.comments.list_comments", decision_id=decision_id))
