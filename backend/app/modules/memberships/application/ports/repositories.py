import uuid
from typing import Protocol

from app.core.db.ports import BaseRepositoryProtocol
from app.core.pagination.params import PageParams
from app.modules.memberships.application.dtos.filters import MembershipFilters
from app.modules.memberships.domain.entities import (
    Membership,
    MembershipExpanded,
    MembershipWithUser,
    NewMembership,
    UpdateMembership,
)


class MembershipsRepositoryProtocol(
    BaseRepositoryProtocol[Membership, MembershipFilters, NewMembership, UpdateMembership],
    Protocol,
):
    """Contrato do repositório de memberships consumido pelos use cases."""

    async def get_by_user_and_establishment_or_none(
        self, user_id: uuid.UUID, establishment_id: uuid.UUID
    ) -> Membership | None: ...

    async def get_by_user_and_establishment(
        self, user_id: uuid.UUID, establishment_id: uuid.UUID
    ) -> Membership: ...

    async def get_by_user_and_establishment_expanded(
        self, user_id: uuid.UUID, establishment_id: uuid.UUID
    ) -> MembershipExpanded: ...

    async def list_by_user(self, user_id: uuid.UUID) -> list[MembershipWithUser]: ...

    async def list_by_establishment(
        self, establishment_id: uuid.UUID, page_params: PageParams
    ) -> list[MembershipWithUser]: ...

    async def count_by_establishment(self, establishment_id: uuid.UUID) -> int: ...

    async def list_all_by_establishment(
        self, establishment_id: uuid.UUID, only_active: bool = True
    ) -> list[Membership]: ...

    async def count_admins_in_establishment(self, establishment_id: uuid.UUID) -> int: ...

    async def update_by_user_and_establishment(
        self,
        user_id: uuid.UUID,
        establishment_id: uuid.UUID,
        update_command: UpdateMembership,
    ) -> MembershipWithUser: ...

    async def delete_by_user_and_establishment(
        self, user_id: uuid.UUID, establishment_id: uuid.UUID
    ) -> None: ...
