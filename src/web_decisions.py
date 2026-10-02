from flask import redirect, render_template, request, url_for

from . import decisions
from .db import get_db
from .decision_queries import list_decisions
from .decision_repository import get_decision
from .decision_validation import FIELDS, decision_filters
from .errors import ApplicationError
from .web import blueprint
from .web_helpers import error_details, form_data, page_data, page_number
from .web_queries import decision_counts, project_choices


@blueprint.get("/")
def decision_list():
    raw = {key: value for key, value in request.args.items()
           if key in {"project", "author", "status", "tags", "date_from", "date_to", "q"} and value.strip()}
    filters = decision_filters(raw)
    page = page_number()
    connection = get_db()
    items, total = list_decisions(connection, filters, page, 20)
    selected = None
    selected_id = request.args.get("selected", "")
    if selected_id.isascii() and selected_id.isdecimal() and len(selected_id) <= 12:
        selected = next((item for item in items if item["id"] == int(request.args["selected"])), None)
    selected = selected or (items[0] if items else None)
    return render_template("decisions.html", items=items, selected=selected, filters=raw,
                           paging=page_data(page, total), projects=project_choices(connection),
                           counts=decision_counts(connection, filters))


@blueprint.route("/decisions/new", methods=["GET", "POST"])
@blueprint.route("/decisions/<int:decision_id>/edit", methods=["GET", "POST"])
def decision_form(decision_id=None):
    connection = get_db()
    current = get_decision(connection, decision_id) if decision_id else None
    data = current or {"project": request.args.get("project", ""), "status": "draft"}
    error = None
    if request.method == "POST":
        data = form_data(FIELDS)
        mode = request.form.get("mode", "draft")
        try:
            if current:
                item = decisions.update_decision(connection, decision_id, data)
            else:
                if mode not in {"draft", "proposed"}:
                    raise ApplicationError("Choose draft or proposed.", field="mode")
                item = decisions.create_decision(connection, data, draft=mode == "draft")
            return redirect(url_for("web.decision_detail", decision_id=item["id"]), code=303)
        except ApplicationError as failure:
            error = error_details(failure)
        data["status"] = current["status"] if current else mode
    return render_template("decision_form.html", data=data, current=current, error=error,
                           projects=project_choices(connection)), (error["status"] if error else 200)
