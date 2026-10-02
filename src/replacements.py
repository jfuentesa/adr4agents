from . import decision_repository as decisions
from . import project_repository
from . import relation_repository
from .db import transaction
from .decision_validation import FIELDS, decision_data
from .errors import conflict
from .validation import validate_object


def propose_replacement(connection, decision_id, data):
    validate_object(data, FIELDS, ("author", "title"))
    with transaction(connection):
        original = decisions.get_decision(connection, decision_id)
        if original["status"] != "accepted":
            raise conflict("Only an accepted decision can have a replacement proposed.")
        values = decision_data({"project": original["project"], **data}, draft=True)
        if values["project"] != original["project"]:
            raise conflict("The replacement must belong to the same project.")
        project = project_repository.get_project_by_name(connection, original["project"])
        replacement = decisions.create_decision(connection, project["id"], values, "draft")
        relation_repository.create_relation(
            connection, replacement["id"], decision_id, "supersedes", effective=False
        )
        return replacement
