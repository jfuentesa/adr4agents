from flask import Blueprint, jsonify, url_for

from . import project_repository, projects
from .db import get_db
from .http_helpers import body, collection, created, pagination, query_parameters
from .validation import text


blueprint = Blueprint("projects", __name__)


@blueprint.get("/projects")
def list_projects():
    parameters = query_parameters({"page", "page_size", "q"})
    page, page_size = pagination(parameters)
    query = text(parameters["q"], "q", 500) if "q" in parameters else None
    items, total = project_repository.list_projects(get_db(), page, page_size, query)
    return collection(items, total, page, page_size)


@blueprint.get("/projects/<int:project_id>")
def get_project(project_id):
    query_parameters(set())
    return jsonify(project_repository.get_project(get_db(), project_id))


@blueprint.post("/projects")
def create_project():
    query_parameters(set())
    item = projects.create_project(get_db(), body())
    return created(item, url_for("api.projects.get_project", project_id=item["id"]))


@blueprint.patch("/projects/<int:project_id>")
def update_project(project_id):
    query_parameters(set())
    return jsonify(projects.update_project(get_db(), project_id, body()))
