from .mcp_models import Identifier, ReplacementInput
from .mcp_registration import api_tool, model_data


def register_tools(server, api):
    @api_tool(server)
    async def request_decision_review(decision_id: Identifier) -> dict:
        """Move a complete draft to proposed. Context, alternatives and decision must be non-empty."""
        return await api.request("POST", f"/decisions/{decision_id}/review", data={})

    @api_tool(server)
    async def approve_decision(decision_id: Identifier) -> dict:
        """Approve a proposed ADR, making it accepted and applicable. Does not activate replacements."""
        return await api.request("POST", f"/decisions/{decision_id}/approve", data={})

    @api_tool(server)
    async def reject_decision(decision_id: Identifier) -> dict:
        """Reject a proposed ADR. Only proposed decisions can transition to rejected."""
        return await api.request("POST", f"/decisions/{decision_id}/reject", data={})

    @api_tool(server)
    async def supersede_decision(decision_id: Identifier, successor_id: Identifier) -> dict:
        """Replace an accepted ADR with another accepted ADR in the same project; mark original superseded."""
        return await api.request("POST", f"/decisions/{decision_id}/supersede", data={"successor_id": successor_id})

    @api_tool(server)
    async def propose_decision_replacement(decision_id: Identifier, data: ReplacementInput) -> dict:
        """Create a linked replacement draft for an accepted ADR. Original stays accepted until superseded."""
        return await api.request("POST", f"/decisions/{decision_id}/replacement", data=model_data(data))
