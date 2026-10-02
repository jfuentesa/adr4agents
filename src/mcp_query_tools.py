from .mcp_models import DecisionFilters, DecisionScope, Identifier, Page, PageSize
from .mcp_registration import api_tool, model_data


def query_parameters(filters, q, page, page_size):
    return {**(model_data(filters) if filters else {}), "q": q, "page": page, "page_size": page_size}


def register_tools(server, api):
    @api_tool(server, read_only=True)
    async def list_decisions(filters: DecisionFilters | None = None, q: str | None = None,
                             page: Page = 1, page_size: PageSize = 20) -> dict:
        """List ADRs with project, author, status, tags and date filters. Text search is optional."""
        return await api.request("GET", "/decisions", query=query_parameters(filters, q, page, page_size))

    @api_tool(server, read_only=True)
    async def search_decisions(q: str, filters: DecisionFilters | None = None,
                               page: Page = 1, page_size: PageSize = 20) -> dict:
        """Search titles, context, alternatives and decisions. q is required; filters can narrow results."""
        return await api.request("GET", "/decisions/search", query=query_parameters(filters, q, page, page_size))

    @api_tool(server, read_only=True)
    async def get_current_decisions(filters: DecisionScope | None = None, q: str | None = None,
                                    page: Page = 1, page_size: PageSize = 20) -> dict:
        """Get accepted, currently applicable ADRs. Use the project filter to scope the result."""
        return await api.request("GET", "/decisions/current", query=query_parameters(filters, q, page, page_size))

    @api_tool(server, read_only=True)
    async def get_decision(decision_id: Identifier) -> dict:
        """Get the complete ADR, status, tags and successor reference by numeric ID."""
        return await api.request("GET", f"/decisions/{decision_id}")

    @api_tool(server, read_only=True)
    async def list_tags(project: str | None = None, page: Page = 1, page_size: PageSize = 20) -> dict:
        """List used tags, optionally scoped to a project's single-word name."""
        return await api.request("GET", "/tags", query={"project": project, "page": page, "page_size": page_size})
