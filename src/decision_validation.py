from datetime import date

from . import validation as validate
from .errors import ApplicationError


FIELDS = {"project", "author", "title", "context", "alternatives", "decision", "tags", "date"}


def decision_data(data, *, draft=False, partial=False):
    required = () if partial else ("project", "author", "title")
    validate.validate_object(data, FIELDS, required)
    if partial and not data:
        raise ApplicationError("At least one field is required.")
    if not draft and not partial:
        validate.validate_object(data, FIELDS, ("context", "alternatives", "decision"))
    result = {}
    validators = {
        "project": lambda value: validate.word(value, "project"),
        "author": validate.author,
        "title": lambda value: validate.text(value, "title", 300),
        "tags": validate.tags,
        "date": validate.calendar_date,
    }
    for field in FIELDS & data.keys():
        if field in validators:
            result[field] = validators[field](data[field])
        else:
            result[field] = validate.text(data[field], field, allow_empty=draft)
    if not partial:
        for field in ("context", "alternatives", "decision"):
            result.setdefault(field, "")
        result.setdefault("tags", [])
        result.setdefault("date", date.today().isoformat())
    return result


def require_complete(data):
    for field in ("context", "alternatives", "decision"):
        validate.text(data[field], field)


def decision_filters(data):
    allowed = {"project", "author", "status", "tags", "date_from", "date_to", "q"}
    validate.validate_object(data, allowed)
    result = {}
    for field, value in data.items():
        if field == "status":
            result[field] = validate.status(value)
        elif field == "author":
            result[field] = validate.author(value)
        elif field == "project":
            result[field] = validate.word(value, field)
        elif field == "tags":
            result[field] = validate.tags(value)
        elif field in {"date_from", "date_to"}:
            result[field] = validate.calendar_date(value, field)
        else:
            result[field] = validate.text(value, field, 500)
    if result.get("date_from", "") > result.get("date_to", "9999-12-31"):
        validate.invalid("date_to", "Must not be earlier than date_from.")
    return result
