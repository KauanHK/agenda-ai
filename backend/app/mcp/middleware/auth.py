from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_headers
from fastmcp.server.middleware import Middleware, MiddlewareContext

from app.core.actors.customer import CustomerActor
from app.core.exceptions import UnauthorizedError
from app.core.security.mcp_tokens import decode_client_mcp_session_token


class AuthMiddleware(Middleware):
    async def on_call_tool(
        self,
        context: MiddlewareContext,
        call_next,
    ):
        headers = get_http_headers() or {}
        auth = headers.get("Authorization", "")
        print(auth)

        if not auth.startswith("Bearer "):
            raise ToolError("Missing or invalid Authorization header.")

        try:
            session_payload = decode_client_mcp_session_token(
                auth.removeprefix("Bearer ")
            )
        except UnauthorizedError as exc:
            raise ToolError(str(exc)) from exc

        actor = CustomerActor(
            client_id=session_payload["client_id"],
            establishment_id=session_payload["establishment_id"],
            phone=session_payload["phone"],
        )

        if context.fastmcp_context:
            context.fastmcp_context.set_state("actor", actor)

        return await call_next(context)
