from flask import Blueprint, jsonify, url_for

from . import decisions, relations, replacements
from .db import get_db
from .http_helpers import body, created, query_parameters
from .validation import validate_object


blueprint = Blueprint("workflow", __name__)


def transition(decision_id, action):
    query_parameters(set())
    validate_object(body(), set())
    return jsonify(decisions.transition_decision(get_db(), decision_id, action))


@blueprint.post("/decisions/<int:decision_id>/review")
def request_decision_review(decision_id):
    return transition(decision_id, "review")


@blueprint.post("/decisions/<int:decision_id>/approve")
def approve_decision(decision_id):
    return transition(decision_id, "approve")


@blueprint.post("/decisions/<int:decision_id>/reject")
def reject_decision(decision_id):
    return transition(decision_id, "reject")


@blueprint.post("/decisions/<int:decision_id>/supersede")
def supersede_decision(decision_id):
    query_parameters(set())
    data = body()
    validate_object(data, {"successor_id"}, {"successor_id"})
    return jsonify(relations.supersede_decision(get_db(), decision_id, data["successor_id"]))


@blueprint.post("/decisions/<int:decision_id>/replacement")
def propose_decision_replacement(decision_id):
    query_parameters(set())
    item = replacements.propose_replacement(get_db(), decision_id, body())
    return created(item, url_for("api.decisions.get_decision", decision_id=item["id"]))
