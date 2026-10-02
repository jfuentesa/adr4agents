from flask import redirect, render_template, request, url_for

from .db import get_db
from .decision_repository import get_decision
from .errors import ApplicationError
from .relation_repository import get_relation
from .relations import create_relation, update_relation
from .web import blueprint
from .web_helpers import error_details, form_integer
from .web_queries import decision_choices


@blueprint.route("/decisions/<int:decision_id>/relations/new", methods=["GET", "POST"])
@blueprint.route("/relations/<int:relation_id>/edit", methods=["GET", "POST"])
def relation_form(decision_id=None, relation_id=None):
    connection = get_db()
    current = get_relation(connection, relation_id) if relation_id else None
    item = get_decision(connection, current["source_id"] if current else decision_id)
    data = current or {"source_id": decision_id, "type": "complements"}
    error = None
    if request.method == "POST":
        data = request.form.to_dict()
        try:
            values = {"source_id": form_integer("source_id"), "target_id": form_integer("target_id"),
                      "type": request.form.get("type", "")}
            if current:
                relation = update_relation(connection, relation_id, values)
            else:
                relation = create_relation(connection, values)
            return redirect(url_for("web.decision_detail", decision_id=relation["source_id"]), code=303)
        except ApplicationError as failure:
            error = error_details(failure)
    return render_template("relation_form.html", current=current, data=data, item=item,
                           choices=decision_choices(connection, item["project"]), error=error), (error["status"] if error else 200)
