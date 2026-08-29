import uuid
from typing import Any

import sqlalchemy as sa

from app.core.db.repository import BaseRepository
from app.core.phone import phone_lookup_keys
from app.modules.clients.adapters.db.models import Client as ClientModel
from app.modules.clients.application.dtos.filters import ClientFilters
from app.modules.clients.domain.entities import Client

# `clients.phone` é texto livre; a comparação por telefone é feita sobre os dígitos.
# O índice funcional `idx_clients_establishment_phone_digits` cobre esta expressão.
_PHONE_DIGITS = sa.func.regexp_replace(ClientModel.phone, r"\D", "", "g")


class ClientsRepository(BaseRepository[ClientModel, Client, ClientFilters]):
    model = ClientModel
    filters_type = ClientFilters

    async def get_by_establishment_and_phone(
        self,
        establishment_id: uuid.UUID,
        phone: str,
    ) -> Client | None:
        """
        Obtém um cliente pelo telefone dentro de um estabelecimento, ignorando o
        formato em que o número foi cadastrado e os clientes removidos (soft-delete).

        É o lookup de identidade do canal automático: o telefone recebido do WhatsApp
        é comparado com a base pelos dígitos, através das variantes de
        `phone_lookup_keys`.

        Args:
            establishment_id (uuid.UUID): O estabelecimento no qual buscar.
            phone (str): O telefone em qualquer formato.

        Returns:
            Client | None: O cliente encontrado ou `None` se não houver.
        """

        keys = phone_lookup_keys(phone)
        if not keys:
            return None

        result = await self._session.execute(
            sa.select(self.model)
            .where(self.model.establishment_id == establishment_id)
            .where(self.model.deleted_at.is_(None))
            .where(_PHONE_DIGITS.in_(keys))
            .order_by(self.model.created_at)
            .limit(1)
        )
        row = result.scalars().one_or_none()
        return self._to_entity(row) if row is not None else None

    async def get_by_id_or_none(self, id_: uuid.UUID) -> Client | None:
        """
        Obtém um cliente pelo seu ID, ignorando os removidos (soft-delete).
        Retorna `None` se o cliente não for encontrado.

        Args:
            id_ (uuid.UUID):
                ID do cliente a ser buscado.

        Returns:
            Client | None:
                O cliente encontrado ou `None` se não for encontrado.
        """

        row = await self._session.get(self.model, id_)
        if row is None or row.deleted_at is not None:
            return None
        return self._to_entity(row)

    def _to_entity(self, row: ClientModel) -> Client:
        return Client(
            id=row.id,
            establishment_id=row.establishment_id,
            name=row.name,
            phone=row.phone,
            email=row.email,
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _apply_filters(
        self,
        stmt: sa.Select[Any],
        filters: ClientFilters,
    ) -> sa.Select[Any]:
        stmt = stmt.where(self.model.deleted_at.is_(None))
        if filters.establishment_id is not None:
            stmt = stmt.where(self.model.establishment_id == filters.establishment_id)
        if filters.is_active is not None:
            stmt = stmt.where(self.model.is_active == filters.is_active)
        if filters.q is not None:
            like = f"%{filters.q}%"
            stmt = stmt.where(
                sa.or_(
                    self.model.name.ilike(like),
                    self.model.phone.ilike(like),
                    self.model.email.ilike(like),
                )
            )
        return stmt
