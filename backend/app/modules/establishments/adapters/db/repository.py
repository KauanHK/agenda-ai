import uuid
from typing import Any

import sqlalchemy as sa

from app.core.db.repository import BaseRepository
from app.core.exceptions import NotFoundError
from app.modules.establishments.adapters.db.models import (
    Establishment as EstablishmentModel,
)
from app.modules.establishments.application.dtos.filters import EstablishmentFilters
from app.modules.establishments.domain.entities import Establishment


class EstablishmentsRepository(
    BaseRepository[EstablishmentModel, Establishment, EstablishmentFilters]
):
    model = EstablishmentModel
    filters_type = EstablishmentFilters

    async def get_by_id_or_none(self, id_: uuid.UUID) -> Establishment | None:
        """
        Obtém um estabelecimento pelo seu ID, ignorando os removidos (soft-delete).
        Retorna `None` se o estabelecimento não for encontrado.

        Args:
            id_ (uuid.UUID):
                ID do estabelecimento a ser buscado.

        Returns:
            Establishment | None:
                O estabelecimento encontrado ou `None` se não for encontrado.
        """

        row = await self._session.get(self.model, id_)
        if row is None or row.deleted_at is not None:
            return None
        return self._to_entity(row)

    async def get_by_cnpj_or_none(self, cnpj: str) -> Establishment | None:
        """
        Obtém um estabelecimento pelo seu documento (CNPJ/CPF). Retorna `None` se o
        estabelecimento não for encontrado.

        Args:
            cnpj (str):
                Documento do estabelecimento a ser buscado.

        Returns:
            Establishment | None:
                O estabelecimento encontrado ou `None` se não for encontrado.
        """

        result = await self._session.execute(
            sa.select(self.model).where(
                self.model.document == cnpj,
                self.model.deleted_at.is_(None),
            )
        )
        row = result.scalars().one_or_none()
        return self._to_entity(row) if row else None

    async def get_by_cnpj(self, cnpj: str) -> Establishment:
        """
        Obtém um estabelecimento pelo seu documento (CNPJ/CPF). Lança `NotFoundError`
        se o estabelecimento não for encontrado.

        Args:
            cnpj (str):
                Documento do estabelecimento a ser buscado.

        Returns:
            Establishment:
                O estabelecimento encontrado.

        Raises:
            NotFoundError:
                Se nenhum estabelecimento for encontrado com o documento fornecido.
        """

        establishment = await self.get_by_cnpj_or_none(cnpj)
        if establishment is None:
            raise NotFoundError("Establishment not found")
        return establishment

    def _to_entity(self, row: EstablishmentModel) -> Establishment:
        return Establishment(
            id=row.id,
            name=row.name,
            document=row.document,
            document_type=row.document_type,
            timezone=row.timezone,
            street=row.street,
            number=row.number,
            complement=row.complement,
            neighborhood=row.neighborhood,
            city=row.city,
            state=row.state,
            zip_code=row.zip_code,
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _apply_filters(
        self,
        stmt: sa.Select[Any],
        filters: EstablishmentFilters,
    ) -> sa.Select[Any]:
        stmt = stmt.where(self.model.deleted_at.is_(None))
        if filters.name is not None:
            stmt = stmt.where(self.model.name.ilike(f"%{filters.name}%"))
        if filters.document is not None:
            stmt = stmt.where(self.model.document == filters.document)
        if filters.timezone is not None:
            stmt = stmt.where(self.model.timezone == filters.timezone)
        return stmt
