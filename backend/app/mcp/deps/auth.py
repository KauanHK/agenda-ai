from typing import Annotated

from fastmcp.dependencies import CurrentHeaders, Depends

from app.core.actors.customer import CustomerActor
from app.core.security.mcp_tokens import decode_client_mcp_session_token


def get_current_client_actor() -> CustomerActor:

    headers = CurrentHeaders()
    authorization = headers.get("Authorization", "")

    claims = decode_client_mcp_session_token(token=authorization)
    return CustomerActor(
        establishment_id=claims["establishment_id"],
        client_id=claims["client_id"],
        phone=claims["phone"],
    )


CustomerActorDep = Annotated[CustomerActor, Depends(get_current_client_actor)]
