import json
from functools import wraps

from mcp.types import CallToolResult, TextContent, ToolAnnotations

from .mcp_api_client import ApiError


def model_data(model, *, partial=False):
    return model.model_dump(exclude_unset=partial, exclude_none=not partial)


def api_tool(server, *, read_only=False, idempotent=False, destructive=False):
    def decorate(function):
        @wraps(function)
        async def handler(*args, **kwargs):
            try:
                result = await function(*args, **kwargs)
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False))],
                    structured_content=result,
                )
            except ApiError as error:
                result = error.details or {"error": {"message": str(error)}}
                if error.status is not None:
                    result = {"http_status": error.status, "response": result}
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False))],
                    structured_content=result, is_error=True,
                )

        annotations = ToolAnnotations(
            read_only_hint=read_only, idempotent_hint=idempotent,
            destructive_hint=destructive, open_world_hint=False,
        )
        return server.tool(annotations=annotations)(handler)
    return decorate
