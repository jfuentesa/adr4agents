from . import project_repository as repository
from . import validation as validate
from .db import transaction
from .errors import ApplicationError


def project_data(data, partial=False):
    validate.validate_object(data, {"name", "description", "context"}, () if partial else ("name",))
    if partial and not data:
        raise ApplicationError("At least one field is required.")
    result = {}
    for field, value in data.items():
        result[field] = (
            validate.word(value, field) if field == "name"
            else validate.text(value, field, allow_empty=True)
        )
    if not partial:
        result.setdefault("description", "")
        result.setdefault("context", "")
    return result


def create_project(connection, data):
    validated = project_data(data)
    with transaction(connection):
        return repository.create_project(connection, validated)


def update_project(connection, project_id, data):
    validated = project_data(data, partial=True)
    with transaction(connection):
        return repository.update_project(connection, project_id, validated)
