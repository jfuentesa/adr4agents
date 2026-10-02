import sqlite3

from flask import current_app, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from .errors import ApplicationError


def error_response(code, message, status, field=None):
    if not request.path.startswith("/api/"):
        return render_template("error.html", message=message, status=status), status
    error = {"code": code, "message": message}
    if field is not None:
        error["field"] = field
    response = jsonify({"error": error})
    response.status_code = status
    return response


def register_handlers(app):
    @app.errorhandler(ApplicationError)
    def application_error(error):
        return error_response(error.code, error.message, error.status, error.field)

    @app.errorhandler(HTTPException)
    def http_error(error):
        response = error.get_response()
        if not request.path.startswith("/api/"):
            response.data = render_template("error.html", message=error.description, status=error.code)
            response.content_type = "text/html; charset=utf-8"
            return response
        response.data = current_app.json.dumps({"error": {
            "code": error.name.lower().replace(" ", "_"), "message": error.description,
        }})
        response.content_type = "application/json"
        return response

    @app.errorhandler(sqlite3.OperationalError)
    def database_error(error):
        if "locked" in str(error).lower():
            return error_response("database_busy", "Database is busy. Retry later.", 503)
        current_app.logger.exception("Database operation failed.")
        return error_response("internal_error", "An internal error occurred.", 500)

    @app.errorhandler(Exception)
    def unexpected_error(error):
        current_app.logger.exception("Unexpected request failure.")
        return error_response("internal_error", "An internal error occurred.", 500)
