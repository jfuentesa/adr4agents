from . import decision_repository as decisions
from . import relation_repository as repository
from . import validation as validate
from .db import transaction
from .errors import ApplicationError, conflict


TYPES = {"complements", "contradicts", "supersedes"}


def relation_data(data, partial=False):
    fields = {"source_id", "target_id", "type"}
    validate.validate_object(data, fields, () if partial else fields)
    if partial and not data:
        raise ApplicationError("At least one field is required.")
    result = {}
    for field, value in data.items():
        if field == "type":
            if not isinstance(value, str) or value not in TYPES:
                validate.invalid(field, "Unknown relation type.")
            result[field] = value
        else:
            result[field] = validate.positive_integer(value, field)
    return result


def related_decisions(connection, source_id, target_id):
    if source_id == target_id:
        validate.invalid("target_id", "A decision cannot relate to itself.")
    source = decisions.get_decision(connection, source_id)
    target = decisions.get_decision(connection, target_id)
    if source["project"] != target["project"]:
        raise conflict("Related decisions must belong to the same project.")
    return source, target


def apply_supersession(connection, source, target):
    if source["status"] != "accepted" or target["status"] != "accepted":
        raise conflict("Both the original and successor must be accepted.")
    decisions.set_status(connection, target["id"], "superseded", source["id"])


def create_relation(connection, data):
    values = relation_data(data)
    with transaction(connection):
        source, target = related_decisions(connection, values["source_id"], values["target_id"])
        if values["type"] == "supersedes":
            apply_supersession(connection, source, target)
            return repository.record_supersession(connection, source["id"], target["id"])
        return repository.create_relation(connection, source["id"], target["id"], values["type"])


def update_relation(connection, relation_id, data):
    changes = relation_data(data, partial=True)
    with transaction(connection):
        current = repository.get_relation(connection, relation_id)
        values = {**current, **changes}
        source, target = related_decisions(connection, values["source_id"], values["target_id"])
        if current["type"] == "supersedes" and current["effective"] and values != current:
            raise conflict("An effective supersession cannot be reassigned or removed.")
        if current["type"] != "supersedes" and values["type"] == "supersedes":
            apply_supersession(connection, source, target)
            values["effective"] = True
        elif values["type"] != "supersedes":
            values["effective"] = True
        return repository.update_relation(connection, relation_id, values)


def supersede_decision(connection, decision_id, successor_id):
    validate.positive_integer(successor_id, "successor_id")
    with transaction(connection):
        successor, original = related_decisions(connection, successor_id, decision_id)
        apply_supersession(connection, successor, original)
        repository.record_supersession(connection, successor_id, decision_id)
        return decisions.get_decision(connection, decision_id)
