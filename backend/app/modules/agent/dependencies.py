import uuid
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from jose import ExpiredSignatureError, JWTError, jwt

from app.core.settings import settings
from app.modules.agent.actors import ClientAgentActor


def get_session_actor(
    x_session_token: Annotated[str, Header(alias="X-Session-Token")],
) -> ClientAgentActor:

    try:
        payload = jwt.decode(
            x_session_token,
            settings.AGENT_SESSION_SECRET,
            algorithms=["HS256"],
        )
    except ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=401,
            detail="Session token expired",
        ) from exc
    except JWTError as exc:
        raise HTTPException(
            status_code=401,
            detail="Invalid session token",
        ) from exc

    if payload.get("type") != "client":
        raise HTTPException(
            status_code=403, detail="Token type not allowed for this scope"
        )

    return ClientAgentActor(
        client_id=uuid.UUID(payload["client_id"]),
        establishment_id=uuid.UUID(payload["establishment_id"]),
        phone=payload["phone"],
    )


SessionActorDep = Annotated[ClientAgentActor, Depends(get_session_actor)]
