from .mcp_models import Identifier, Page, PageSize, ProjectInput, ProjectUpdate
from .mcp_registration import api_tool, model_data


def register_tools(server, api):
    @api_tool(server, read_only=True)
    async def list_projects(q: str | None = None, page: Page = 1, page_size: PageSize = 20) -> dict:
        """List projects, optionally searching names. Returns items and pagination metadata."""
        return await api.request("GET", "/projects", query={"q": q, "page": page, "page_size": page_size})

    @api_tool(server, read_only=True)
    async def get_project(project_id: Identifier) -> dict:
        """Get a project's name, description and context by its numeric ID."""
        return await api.request("GET", f"/projects/{project_id}")

    @api_tool(server)
    async def create_project(data: ProjectInput) -> dict:
        """Create a project with a unique single-word name and optional description and context."""
        return await api.request("POST", "/projects", data=model_data(data))

    @api_tool(server, idempotent=True, destructive=True)
    async def update_project(project_id: Identifier, data: ProjectUpdate) -> dict:
        """Edit supplied project fields. Renaming preserves its decisions. Omit unchanged fields."""
        return await api.request("PATCH", f"/projects/{project_id}", data=model_data(data, partial=True))
