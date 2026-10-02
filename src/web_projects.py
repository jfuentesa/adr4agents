from flask import redirect, render_template, request, url_for

from .db import get_db
from .errors import ApplicationError
from .project_repository import get_project, list_projects
from .projects import create_project, update_project
from .web import blueprint
from .web_helpers import error_details, form_data, page_data, page_number
from .validation import text


@blueprint.get("/projects")
def project_list():
    page = page_number()
    query = request.args.get("q", "").strip()
    if query:
        query = text(query, "q", 500)
    items, total = list_projects(get_db(), page, 20, query)
    return render_template("projects.html", items=items, paging=page_data(page, total), query=query)


@blueprint.route("/projects/new", methods=["GET", "POST"])
@blueprint.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
def project_form(project_id=None):
    current = get_project(get_db(), project_id) if project_id else None
    data, error = current or {}, None
    if request.method == "POST":
        data = form_data({"name", "description", "context"})
        try:
            if current:
                update_project(get_db(), project_id, data)
            else:
                create_project(get_db(), data)
            return redirect(url_for("web.project_list"), code=303)
        except ApplicationError as failure:
            error = error_details(failure)
    return render_template("project_form.html", current=current, data=data,
                           error=error), (error["status"] if error else 200)
