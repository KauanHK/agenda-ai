import uuid

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginationParams
from app.modules.memberships.domain.model import Membership
from app.modules.users.domain.filters import UserFilters
from app.modules.users.domain.model import User


class UsersRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id_or_none(
        self,
        id: uuid.UUID,
    ) -> User | None:
        return await self._session.get(User, id)

    async def get_by_id(
        self,
        id: uuid.UUID,
    ) -> User:

        user = await self.get_by_id_or_none(id)
        if user is None:
            raise NotFoundError("User not found.")
        return user

    async def get_by_id_expanded(
        self,
        id: uuid.UUID,
    ) -> User:

        query = (
            select(User)
            .where(User.id == id)
            .options(
                selectinload(User.memberships).selectinload(Membership.establishment)
            )
        )
        result = await self._session.execute(query)
        user = result.scalars().one_or_none()
        if user is None:
            raise NotFoundError("User not found.")
        return user

    async def get_by_email_or_none(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalars().one_or_none()

    async def create(self, user: User) -> User:
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def list(
        self,
        pagination: PaginationParams,
        filters: UserFilters | None = None,
    ) -> list[User]:
        query = self._construct_select_query(filters)
        query = query.limit(pagination.size).offset(pagination.offset)
        result = await self._session.execute(query)
        return list(result.scalars())

    async def count(
        self,
        filters: UserFilters | None = None,
        include_deleted: bool = False,
    ) -> int:
        query = select(func.count()).select_from(
            self._construct_select_query(filters).subquery()
        )
        result = await self._session.execute(query)
        return result.scalar_one()

    async def update(self, user: User) -> User:
        user = await self._session.merge(user)
        await self._session.refresh(user)
        return user

    def _construct_select_query(
        self,
        filters: UserFilters | None,
    ) -> Select[tuple[User]]:

        query = select(User)
        if filters is None:
            return query

        if filters.q is not None:
            query = query.where(
                User.name.ilike(f"%{filters.q}%") | User.email.ilike(f"%{filters.q}%")
            )

        if filters.is_active is not None:
            query = query.where(User.is_active == filters.is_active)

        if filters.role is not None or filters.establishment_id is not None:
            query = query.join(Membership, Membership.user_id == User.id)
            if filters.role is not None:
                query = query.where(Membership.role == filters.role)
            if filters.establishment_id is not None:
                query = query.where(
                    Membership.establishment_id == filters.establishment_id
                )

        return query
