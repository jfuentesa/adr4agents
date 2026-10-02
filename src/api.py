from flask import Blueprint, jsonify

from . import comment_routes, decision_routes, project_routes, relation_routes, workflow_routes
from .db import get_db
from .http_helpers import query_parameters


blueprint = Blueprint("api", __name__, url_prefix="/api/v1")
for routes in (project_routes, decision_routes, workflow_routes, relation_routes, comment_routes):
    blueprint.register_blueprint(routes.blueprint)


@blueprint.get("/health")
def health():
    query_parameters(set())
    get_db().execute("SELECT 1").fetchone()
    return jsonify({"status": "ok"})
