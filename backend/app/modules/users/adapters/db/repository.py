import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from app.core.db.repository import BaseRepository
from app.core.exceptions import NotFoundError
from app.modules.memberships.adapters.db.models import Membership as MembershipModel
from app.modules.users.adapters.db.models import User as UserModel
from app.modules.users.application.dtos.filters import UserFilters
from app.modules.users.domain.entities import User, UserExpanded, UserMembership


class UsersRepository(BaseRepository[UserModel, User, UserFilters]):
    model = UserModel
    filters_type = UserFilters

    async def get_by_email_or_none(self, email: str) -> User | None:
        """
        Obtém um usuário pelo seu email. Retorna `None` se o usuário não for
        encontrado.
        """

        result = await self._session.execute(
            sa.select(self.model).where(self.model.email == email)
        )
        row = result.scalars().one_or_none()
        return self._to_entity(row) if row else None

    async def get_by_email(self, email: str) -> User:
        """
        Obtém um usuário pelo seu email. Lança `NotFoundError` se o usuário não for
        encontrado.
        """

        user = await self.get_by_email_or_none(email)
        if user is None:
            raise NotFoundError(f"Usuário com email '{email}' não encontrado.")
        return user

    async def get_by_id_expanded(self, id_: uuid.UUID) -> UserExpanded:
        """
        Obtém um usuário pelo seu id, com as memberships aninhadas. Lança
        `NotFoundError` se o usuário não for encontrado.
        """

        result = await self._session.execute(
            sa.select(self.model)
            .where(self.model.id == id_)
            .options(selectinload(self.model.memberships))
        )
        row = result.scalars().one_or_none()
        if row is None:
            raise NotFoundError(f"Entidade com ID {id_} não encontrada.")
        return self._to_expanded_entity(row)

    def _to_entity(self, row: UserModel) -> User:
        return User(
            id=row.id,
            name=row.name,
            email=row.email,
            phone=row.phone,
            password_hash=row.password_hash,
            is_global_admin=row.is_global_admin,
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _to_expanded_entity(self, row: UserModel) -> UserExpanded:
        return UserExpanded(
            id=row.id,
            name=row.name,
            email=row.email,
            phone=row.phone,
            is_active=row.is_active,
            is_global_admin=row.is_global_admin,
            created_at=row.created_at,
            updated_at=row.updated_at,
            memberships=[
                UserMembership(
                    id=m.id,
                    establishment_id=m.establishment_id,
                    role=m.role,
                    is_active=m.is_active,
                )
                for m in row.memberships
            ],
        )

    def _apply_filters(
        self,
        stmt: sa.Select[Any],
        filters: UserFilters,
    ) -> sa.Select[Any]:
        if filters.q is not None:
            stmt = stmt.where(
                self.model.name.ilike(f"%{filters.q}%")
                | self.model.email.ilike(f"%{filters.q}%")
            )

        if filters.is_active is not None:
            stmt = stmt.where(self.model.is_active == filters.is_active)

        if filters.role is not None or filters.establishment_id is not None:
            stmt = stmt.join(MembershipModel, MembershipModel.user_id == self.model.id)
            if filters.role is not None:
                stmt = stmt.where(MembershipModel.role == filters.role)
            if filters.establishment_id is not None:
                stmt = stmt.where(
                    MembershipModel.establishment_id == filters.establishment_id
                )

        return stmt
