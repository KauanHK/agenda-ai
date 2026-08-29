import uuid
from typing import Any

import sqlalchemy as sa

from app.core.db.repository import BaseRepository
from app.modules.clients.adapters.db.models import Client as ClientModel
from app.modules.clients.application.dtos.filters import ClientFilters
from app.modules.clients.domain.entities import Client


class ClientsRepository(BaseRepository[ClientModel, Client, ClientFilters]):
    model = ClientModel
    filters_type = ClientFilters

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
