from flask import redirect, render_template, request, url_for

from .comments import create_comment
from .db import get_db
from .decisions import transition_decision
from .errors import ApplicationError
from .replacements import propose_replacement
from .relations import supersede_decision
from .web import blueprint
from .web_details import detail_context
from .web_helpers import error_details, form_data, form_integer


@blueprint.post("/decisions/<int:decision_id>/actions/<action>")
def decision_action(decision_id, action):
    connection = get_db()
    try:
        if action in {"review", "approve", "reject"}:
            transition_decision(connection, decision_id, action)
        elif action == "supersede":
            supersede_decision(connection, decision_id, form_integer("successor_id"))
        elif action == "comment":
            create_comment(connection, decision_id, form_data({"author", "text", "date"}))
        else:
            raise ApplicationError("Unknown action.", 404, "not_found")
    except ApplicationError as error:
        return render_template("decision_detail.html", **detail_context(decision_id),
                               error=error_details(error), form=request.form), error.status
    return redirect(url_for("web.decision_detail", decision_id=decision_id), code=303)


@blueprint.route("/decisions/<int:decision_id>/replacement", methods=["GET", "POST"])
def replacement_form(decision_id):
    context = detail_context(decision_id)
    data, error = {}, None
    if request.method == "POST":
        data = form_data({"author", "title", "context", "alternatives", "decision", "tags", "date"})
        try:
            item = propose_replacement(get_db(), decision_id, data)
            return redirect(url_for("web.decision_detail", decision_id=item["id"]), code=303)
        except ApplicationError as failure:
            error = error_details(failure)
    return render_template("replacement_form.html", item=context["item"], data=data,
                           error=error), (error["status"] if error else 200)
