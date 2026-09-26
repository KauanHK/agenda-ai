import uuid
from typing import Any, cast

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from app.core.db.repository import BaseRepository
from app.core.exceptions import NotFoundError
from app.core.pagination.params import PageParams
from app.core.roles import UserRole
from app.modules.establishments.adapters.db.models import (
    Establishment as EstablishmentModel,
)
from app.modules.memberships.adapters.db.models import Membership as MembershipModel
from app.modules.memberships.application.dtos.filters import MembershipFilters
from app.modules.memberships.domain.entities import (
    Membership,
    MembershipExpanded,
    MembershipUser,
    MembershipWithUser,
    UpdateMembership,
)
from app.modules.users.adapters.db.models import User as UserModel


class MembershipsRepository(
    BaseRepository[MembershipModel, Membership, MembershipFilters]
):
    model = MembershipModel
    filters_type = MembershipFilters

    async def get_by_user_and_establishment_or_none(
        self,
        user_id: uuid.UUID,
        establishment_id: uuid.UUID,
    ) -> Membership | None:
        """Obtém uma membership pelo par (usuário, estabelecimento)."""

        result = await self._session.execute(
            sa.select(self.model)
            .where(self.model.user_id == user_id)
            .where(self.model.establishment_id == establishment_id)
        )
        row = result.scalars().one_or_none()
        return self._to_entity(row) if row else None

    async def get_by_user_and_establishment(
        self,
        user_id: uuid.UUID,
        establishment_id: uuid.UUID,
    ) -> Membership:
        """Obtém uma membership pelo par (usuário, estabelecimento). Lança
        `NotFoundError` se não encontrada."""

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
    ) -> MembershipExpanded:
        """Obtém uma membership com usuário e estabelecimento completos
        embutidos."""

        result = await self._session.execute(
            sa.select(self.model)
            .where(self.model.user_id == user_id)
            .where(self.model.establishment_id == establishment_id)
            .options(
                selectinload(self.model.user),
                selectinload(self.model.establishment),
            )
        )
        row = result.scalars().one_or_none()
        if row is None:
            raise NotFoundError("Membership não encontrada.")
        return MembershipExpanded(
            role=row.role,
            is_active=row.is_active,
            user=self._to_membership_user(row.user),
            establishment=self._establishment_to_dict(row.establishment),
        )

    async def list_by_user(self, user_id: uuid.UUID) -> list[MembershipWithUser]:
        """Lista as memberships de um usuário, com o usuário embutido."""

        result = await self._session.execute(
            sa.select(self.model)
            .where(self.model.user_id == user_id)
            .options(selectinload(self.model.user))
        )
        return [self._to_entity_with_user(row) for row in result.scalars().all()]

    async def list_by_establishment(
        self,
        establishment_id: uuid.UUID,
        page_params: PageParams,
    ) -> list[MembershipWithUser]:
        """Lista os membros de um estabelecimento, paginados."""

        result = await self._session.execute(
            sa.select(self.model)
            .where(self.model.establishment_id == establishment_id)
            .options(selectinload(self.model.user))
            .limit(page_params.page_size)
            .offset((page_params.page - 1) * page_params.page_size)
        )
        return [self._to_entity_with_user(row) for row in result.scalars().all()]

    async def count_by_establishment(self, establishment_id: uuid.UUID) -> int:
        """Conta os membros de um estabelecimento."""

        result = await self._session.execute(
            sa.select(sa.func.count())
            .select_from(self.model)
            .where(self.model.establishment_id == establishment_id)
        )
        return result.scalar_one()

    async def list_all_by_establishment(
        self,
        establishment_id: uuid.UUID,
        only_active: bool = True,
    ) -> list[Membership]:
        """Lista todas as memberships de um estabelecimento, sem paginação."""

        stmt = (
            sa.select(self.model)
            .where(self.model.establishment_id == establishment_id)
            .order_by(self.model.user_id)
        )
        if only_active:
            stmt = stmt.where(self.model.is_active.is_(True))
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    async def count_admins_in_establishment(self, establishment_id: uuid.UUID) -> int:
        """Conta os administradores de um estabelecimento."""

        result = await self._session.execute(
            sa.select(sa.func.count())
            .select_from(self.model)
            .where(self.model.establishment_id == establishment_id)
            .where(self.model.role == UserRole.ESTABLISHMENT_ADMIN)
        )
        return result.scalar_one()

    async def update_by_user_and_establishment(
        self,
        user_id: uuid.UUID,
        establishment_id: uuid.UUID,
        update_command: UpdateMembership,
    ) -> MembershipWithUser:
        """Atualiza uma membership pelo par (usuário, estabelecimento)."""

        result = await self._session.execute(
            sa.select(self.model)
            .where(self.model.user_id == user_id)
            .where(self.model.establishment_id == establishment_id)
            .options(selectinload(self.model.user))
        )
        row = result.scalars().one_or_none()
        if row is None:
            raise NotFoundError("Membership não encontrada.")

        for field, value in update_command.defined_values().items():
            setattr(row, field, value)

        await self._session.flush()
        return self._to_entity_with_user(row)

    async def delete_by_user_and_establishment(
        self,
        user_id: uuid.UUID,
        establishment_id: uuid.UUID,
    ) -> None:
        """Remove uma membership pelo par (usuário, estabelecimento)."""

        stmt = sa.delete(self.model).where(
            self.model.user_id == user_id,
            self.model.establishment_id == establishment_id,
        )
        result = await self._session.execute(stmt)
        if cast("sa.CursorResult[Any]", result).rowcount == 0:
            raise NotFoundError("Membership não encontrada.")

    def _to_entity(self, row: MembershipModel) -> Membership:
        return Membership(
            id=row.id,
            user_id=row.user_id,
            establishment_id=row.establishment_id,
            role=row.role,
            is_active=row.is_active,
        )

    def _to_entity_with_user(self, row: MembershipModel) -> MembershipWithUser:
        return MembershipWithUser(
            id=row.id,
            establishment_id=row.establishment_id,
            role=row.role,
            is_active=row.is_active,
            user=self._to_membership_user(row.user),
        )

    def _to_membership_user(self, user: UserModel) -> MembershipUser:
        return MembershipUser(
            id=user.id,
            name=user.name,
            email=user.email,
            phone=user.phone,
            is_active=user.is_active,
        )

    def _establishment_to_dict(self, establishment: EstablishmentModel) -> dict[str, Any]:
        return {
            "id": establishment.id,
            "name": establishment.name,
            "document": establishment.document,
            "document_type": establishment.document_type,
            "is_active": establishment.is_active,
            "timezone": establishment.timezone,
            "street": establishment.street,
            "number": establishment.number,
            "complement": establishment.complement,
            "neighborhood": establishment.neighborhood,
            "city": establishment.city,
            "state": establishment.state,
            "zip_code": establishment.zip_code,
            "created_at": establishment.created_at,
            "updated_at": establishment.updated_at,
        }
