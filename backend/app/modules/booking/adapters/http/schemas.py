import uuid

from pydantic import Field

from app.core.schemas import BaseSchema


class IssueSessionRequest(BaseSchema):
    phone: str = Field(
        min_length=8,
        max_length=32,
        description="Telefone do cliente, em qualquer formato.",
    )
    name: str | None = Field(
        default=None,
        max_length=255,
        description="Nome a usar caso o cliente ainda não exista na base.",
    )


class SessionClientRead(BaseSchema):
    id: uuid.UUID
    name: str


class SessionRead(BaseSchema):
    session_token: str
    expires_in_minutes: int
    client: SessionClientRead
    is_new_client: bool
