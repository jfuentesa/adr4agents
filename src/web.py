import secrets

from flask import Blueprint, abort, request, session


blueprint = Blueprint("web", __name__)


@blueprint.record_once
def configure(state):
    if not state.app.secret_key:
        state.app.secret_key = secrets.token_hex(32)
    state.app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")


@blueprint.before_request
def protect_forms():
    if request.method == "POST":
        expected = session.get("csrf_token", "")
        supplied = request.form.get("csrf_token", "")
        if not expected or not secrets.compare_digest(expected.encode(), supplied.encode()):
            abort(400, description="The form expired. Reload the page and try again.")


@blueprint.after_request
def browser_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
    )
    return response


@blueprint.app_context_processor
def template_helpers():
    from .web_helpers import page_link
    session.setdefault("csrf_token", secrets.token_hex(32))
    return {"csrf_token": session["csrf_token"], "page_link": page_link,
            "states": ("draft", "proposed", "accepted", "rejected", "superseded")}


from . import web_decisions, web_details, web_projects, web_relations, web_workflow  # noqa: E402,F401
