from .mcp_models import Identifier, Page, PageSize, RelationInput, RelationUpdate
from .mcp_registration import api_tool, model_data


def register_tools(server, api):
    @api_tool(server, read_only=True)
    async def get_decision_relations(decision_id: Identifier, page: Page = 1, page_size: PageSize = 20) -> dict:
        """List incoming and outgoing ADR relations. effective distinguishes planned from active replacements."""
        return await api.request("GET", f"/decisions/{decision_id}/relations", query={"page": page, "page_size": page_size})

    @api_tool(server)
    async def create_relation(data: RelationInput) -> dict:
        """Relate ADRs in one project. supersedes activates replacement and requires both ADRs accepted."""
        return await api.request("POST", "/relations", data=model_data(data))

    @api_tool(server, idempotent=True, destructive=True)
    async def update_relation(relation_id: Identifier, data: RelationUpdate) -> dict:
        """Edit supplied relation fields. Converting to supersedes activates it; active replacements cannot be reassigned."""
        return await api.request("PATCH", f"/relations/{relation_id}", data=model_data(data, partial=True))

    @api_tool(server)
    async def comment_decision(decision_id: Identifier, author: str, text: str, date: str | None = None) -> dict:
        """Add an observation without modifying the ADR. Author is alphanumeric; optional date uses YYYY-MM-DD."""
        data = {"author": author, "text": text}
        if date is not None:
            data["date"] = date
        return await api.request("POST", f"/decisions/{decision_id}/comments", data=data)
