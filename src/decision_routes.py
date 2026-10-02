from flask import Blueprint, jsonify, url_for

from . import decision_queries, decision_repository, decisions
from .db import get_db
from .decision_validation import decision_filters
from .http_helpers import body, collection, created, pagination, query_parameters
from .validation import invalid, word


blueprint = Blueprint("decisions", __name__)
FILTERS = {"project", "author", "status", "tags", "date_from", "date_to", "q"}


def decision_collection(*, search=False, current=False):
    parameters = query_parameters(FILTERS | {"page", "page_size"})
    page, page_size = pagination(parameters)
    filters = decision_filters(parameters)
    if search and "q" not in filters:
        invalid("q", "Required query parameter.")
    if current:
        if filters.get("status", "accepted") != "accepted":
            invalid("status", "Current decisions must have status accepted.")
        filters["status"] = "accepted"
    items, total = decision_queries.list_decisions(get_db(), filters, page, page_size)
    return collection(items, total, page, page_size)


@blueprint.get("/decisions")
def list_decisions():
    return decision_collection()


@blueprint.get("/decisions/search")
def search_decisions():
    return decision_collection(search=True)


@blueprint.get("/decisions/current")
def get_current_decisions():
    return decision_collection(current=True)


@blueprint.get("/decisions/<int:decision_id>")
def get_decision(decision_id):
    query_parameters(set())
    return jsonify(decision_repository.get_decision(get_db(), decision_id))


def create(*, draft=False):
    query_parameters(set())
    item = decisions.create_decision(get_db(), body(), draft=draft)
    return created(item, url_for("api.decisions.get_decision", decision_id=item["id"]))


@blueprint.post("/decisions")
def create_decision():
    return create()


@blueprint.post("/decisions/drafts")
def create_decision_draft():
    return create(draft=True)


@blueprint.patch("/decisions/<int:decision_id>")
def update_decision(decision_id):
    query_parameters(set())
    return jsonify(decisions.update_decision(get_db(), decision_id, body()))


@blueprint.patch("/decisions/<int:decision_id>/draft")
def update_decision_draft(decision_id):
    query_parameters(set())
    return jsonify(decisions.update_decision(get_db(), decision_id, body(), draft_only=True))


@blueprint.get("/tags")
def list_tags():
    parameters = query_parameters({"project", "page", "page_size"})
    page, page_size = pagination(parameters)
    project = word(parameters["project"], "project") if "project" in parameters else None
    items = decision_queries.list_tags(get_db(), project)
    offset = (page - 1) * page_size
    return collection(items[offset:offset + page_size], len(items), page, page_size)
