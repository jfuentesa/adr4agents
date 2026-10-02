from datetime import date

from .errors import ApplicationError


STATES = {"draft", "proposed", "accepted", "rejected", "superseded"}


def invalid(field, message):
    raise ApplicationError(message, field=field)


def validate_object(data, allowed, required=()):
    if not isinstance(data, dict):
        raise ApplicationError("The JSON body must be an object.")
    unknown = set(data) - set(allowed)
    if unknown:
        invalid(sorted(unknown)[0], "Unknown field.")
    missing = set(required) - set(data)
    if missing:
        invalid(sorted(missing)[0], "Required field.")


def text(value, field, maximum=100_000, allow_empty=False):
    if not isinstance(value, str):
        invalid(field, "Must be a string.")
    value = value.strip()
    if not allow_empty and not value:
        invalid(field, "Must not be empty.")
    if len(value) > maximum or "\x00" in value:
        invalid(field, f"Must contain at most {maximum} characters and no null characters.")
    return value


def word(value, field):
    value = text(value, field, 128)
    if any(character.isspace() for character in value):
        invalid(field, "Must be a single word without spaces.")
    return value


def author(value):
    value = word(value, "author")
    if not value.isalnum():
        invalid("author", "Must contain only letters and numbers.")
    return value


def tags(value):
    value = text(value, "tags", 4096, allow_empty=True)
    if not value:
        return []
    result = []
    for item in value.split(","):
        item = word(item, "tags")
        if item not in result:
            result.append(item)
    return sorted(result)


def calendar_date(value, field="date"):
    value = text(value, field, 10)
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        invalid(field, "Must be a valid date in YYYY-MM-DD format.")
    if parsed.isoformat() != value:
        invalid(field, "Must use YYYY-MM-DD format.")
    return value


def positive_integer(value, field):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        invalid(field, "Must be a positive integer.")
    return value


def status(value):
    if not isinstance(value, str) or value not in STATES:
        invalid("status", "Unknown decision status.")
    return value
