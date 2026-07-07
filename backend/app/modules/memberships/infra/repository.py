import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginationParams
from app.modules.memberships.domain.model import Membership
from app.modules.users.domain.enums import UserRole


class MembershipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, membership: Membership) -> Membership:
        self._session.add(membership)
        await self._session.flush()
        await self._session.refresh(membership)
        return membership

    async def delete(self, membership: Membership) -> None:
        await self._session.delete(membership)

    async def update(self, membership: Membership) -> Membership:
        membership = await self._session.merge(membership)
        await self._session.refresh(membership)
        return membership

    async def get_by_user_and_establishment_or_none(
        self,
        user_id: uuid.UUID,
        establishment_id: uuid.UUID,
    ) -> Membership | None:
        result = await self._session.execute(
            select(Membership)
            .join(Membership.user)
            .options(selectinload(Membership.user))
            .where(Membership.user_id == user_id)
            .where(Membership.establishment_id == establishment_id)
        )
        return result.scalars().one_or_none()

    async def get_by_user_and_establishment(
        self,
        user_id: uuid.UUID,
        establishment_id: uuid.UUID,
    ) -> Membership:
        membership = await self.get_by_user_and_establishment_or_none(
            user_id=user_id, establishment_id=establishment_id
        )
        if membership is None:
            raise NotFoundError("Membership não encontrada.")
        return membership

    async def get_by_user_and_establishment_expanded(
        self,
        user_id: uuid.UUID,
        establishment_id: uuid.UUID,
    ) -> Membership:
        result = await self._session.execute(
            select(Membership)
            .where(Membership.user_id == user_id)
            .where(Membership.establishment_id == establishment_id)
            .options(
                selectinload(Membership.user),
                selectinload(Membership.establishment),
            )
        )
        membership = result.scalars().one_or_none()
        if membership is None:
            raise NotFoundError("Membership não encontrada.")
        return membership

    async def list_by_user(self, user_id: uuid.UUID) -> list[Membership]:
        result = await self._session.execute(
            select(Membership)
            .where(Membership.user_id == user_id)
            .join(Membership.user)
            .options(selectinload(Membership.user))
        )
        return list(result.scalars().all())

    async def list_by_establishment(
        self,
        establishment_id: uuid.UUID,
        pagination: PaginationParams,
    ) -> list[Membership]:
        result = await self._session.execute(
            select(Membership)
            .join(Membership.user)
            .options(selectinload(Membership.user))
            .where(Membership.establishment_id == establishment_id)
            .limit(pagination.size)
            .offset(pagination.offset)
        )
        return list(result.scalars().all())

    async def count_by_establishment(self, establishment_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(Membership)
            .where(Membership.establishment_id == establishment_id)
        )
        return result.scalar_one()

    async def list_all_by_establishment(
        self,
        establishment_id: uuid.UUID,
        only_active: bool = True,
    ) -> list[Membership]:
        query = (
            select(Membership)
            .where(Membership.establishment_id == establishment_id)
            .order_by(Membership.user_id)
        )
        if only_active:
            query = query.where(Membership.is_active.is_(True))
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count_admins_in_establishment(self, establishment_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(Membership)
            .where(Membership.establishment_id == establishment_id)
            .where(Membership.role == UserRole.ESTABLISHMENT_ADMIN)
        )
        return result.scalar_one()
