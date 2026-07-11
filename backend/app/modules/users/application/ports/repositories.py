import uuid
from typing import Protocol

from app.core.db.ports import BaseRepositoryProtocol
from app.modules.users.application.dtos.filters import UserFilters
from app.modules.users.domain.entities import NewUser, UpdateUser, User, UserExpanded


class UsersRepositoryProtocol(
    BaseRepositoryProtocol[User, UserFilters, NewUser, UpdateUser],
    Protocol,
):
    """Contrato do repositório de usuários consumido pelos use cases."""

    async def get_by_email_or_none(self, email: str) -> User | None: ...
    async def get_by_email(self, email: str) -> User: ...
    async def get_by_id_expanded(self, id_: uuid.UUID) -> UserExpanded: ...
