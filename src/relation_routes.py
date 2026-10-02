from flask import Blueprint, jsonify, url_for

from . import decision_repository, relation_repository, relations
from .db import get_db
from .http_helpers import body, collection, created, pagination, query_parameters


blueprint = Blueprint("relations", __name__)


@blueprint.get("/decisions/<int:decision_id>/relations")
def get_decision_relations(decision_id):
    parameters = query_parameters({"page", "page_size"})
    page, page_size = pagination(parameters)
    connection = get_db()
    decision_repository.get_decision(connection, decision_id)
    items, total = relation_repository.list_relations(connection, decision_id, page, page_size)
    return collection(items, total, page, page_size)


@blueprint.get("/relations/<int:relation_id>")
def get_relation(relation_id):
    query_parameters(set())
    return jsonify(relation_repository.get_relation(get_db(), relation_id))


@blueprint.post("/relations")
def create_relation():
    query_parameters(set())
    item = relations.create_relation(get_db(), body())
    return created(item, url_for("api.relations.get_relation", relation_id=item["id"]))


@blueprint.patch("/relations/<int:relation_id>")
def update_relation(relation_id):
    query_parameters(set())
    return jsonify(relations.update_relation(get_db(), relation_id, body()))
