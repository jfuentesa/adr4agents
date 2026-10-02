from . import decision_repository as repository
from . import project_repository
from .db import transaction
from .decision_validation import decision_data, require_complete
from .errors import conflict


def create_decision(connection, data, *, draft=False):
    validated = decision_data(data, draft=draft)
    with transaction(connection):
        project = project_repository.get_project_by_name(connection, validated["project"])
        return repository.create_decision(
            connection, project["id"], validated, "draft" if draft else "proposed"
        )


def update_decision(connection, decision_id, data, *, draft_only=False):
    with transaction(connection):
        current = repository.get_decision(connection, decision_id)
        if draft_only and current["status"] != "draft":
            raise conflict("Only draft decisions can be updated through this operation.")
        changes = decision_data(data, draft=current["status"] == "draft", partial=True)
        if "project" in changes and changes["project"] != current["project"]:
            related = connection.execute(
                "SELECT 1 FROM relations WHERE source_id = ? OR target_id = ? LIMIT 1",
                (decision_id, decision_id),
            ).fetchone()
            if related:
                raise conflict("A decision with relations cannot move to another project.")
        current["tags"] = current["tags"].split(",") if current["tags"] else []
        current.update(changes)
        if current["status"] != "draft":
            require_complete(current)
        project = project_repository.get_project_by_name(connection, current["project"])
        return repository.update_decision(connection, decision_id, project["id"], current)


def transition_decision(connection, decision_id, action):
    transitions = {
        "review": ("draft", "proposed"),
        "approve": ("proposed", "accepted"),
        "reject": ("proposed", "rejected"),
    }
    expected, target = transitions[action]
    with transaction(connection):
        current = repository.get_decision(connection, decision_id)
        if current["status"] != expected:
            raise conflict(f"This operation requires status '{expected}'.")
        if target in {"proposed", "accepted"}:
            require_complete(current)
        return repository.set_status(connection, decision_id, target)
