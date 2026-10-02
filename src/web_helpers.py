from flask import request, url_for

from .http_helpers import pagination
from .validation import invalid


def page_link(**changes):
    values = request.args.to_dict()
    values.update(changes)
    return url_for(request.endpoint, **(request.view_args or {}), **values)


def page_number(parameter="page", default_size=20):
    return pagination({"page": request.args.get(parameter, "1"), "page_size": str(default_size)})[0]


def page_data(page, total, size=20):
    return {"page": page, "total": total, "pages": (total + size - 1) // size,
            "start": (page - 1) * size + 1 if total else 0, "end": min(page * size, total)}


def form_data(fields):
    data = {field: request.form[field] for field in fields if field in request.form}
    if not data.get("date", "").strip():
        data.pop("date", None)
    return data


def form_integer(field):
    value = request.form.get(field, "")
    if not value.isascii() or not value.isdecimal() or len(value) > 12:
        invalid(field, "Choose a decision.")
    number = int(value)
    if number <= 0:
        invalid(field, "Choose a decision.")
    return number


def error_details(error):
    return {"message": error.message, "field": error.field, "status": error.status}
