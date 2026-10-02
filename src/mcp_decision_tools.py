from .mcp_models import DecisionDraft, DecisionInput, DecisionUpdate, Identifier
from .mcp_registration import api_tool, model_data


def register_tools(server, api):
    @api_tool(server)
    async def create_decision(data: DecisionInput) -> dict:
        """Create a complete ADR in proposed state. Project must exist; date defaults to today."""
        return await api.request("POST", "/decisions", data=model_data(data))

    @api_tool(server)
    async def create_decision_draft(data: DecisionDraft) -> dict:
        """Create a draft requiring project, author and title. Other texts may be empty until review."""
        return await api.request("POST", "/decisions/drafts", data=model_data(data))

    @api_tool(server, idempotent=True, destructive=True)
    async def update_decision(decision_id: Identifier, data: DecisionUpdate) -> dict:
        """Edit supplied ADR fields, including accepted ADRs, without changing state. Omit unchanged fields."""
        return await api.request("PATCH", f"/decisions/{decision_id}", data=model_data(data, partial=True))

    @api_tool(server, idempotent=True, destructive=True)
    async def update_decision_draft(decision_id: Identifier, data: DecisionUpdate) -> dict:
        """Edit only a draft ADR. Omit unchanged fields; an empty tags string clears its tags."""
        return await api.request("PATCH", f"/decisions/{decision_id}/draft", data=model_data(data, partial=True))
