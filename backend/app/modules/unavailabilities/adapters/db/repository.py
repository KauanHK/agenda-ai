import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa

from app.core.db.repository import BaseRepository
from app.modules.unavailabilities.adapters.db.models import (
    Unavailability as UnavailabilityModel,
)
from app.modules.unavailabilities.application.dtos.filters import (
    UnavailabilityFilters,
)
from app.modules.unavailabilities.domain.entities import Unavailability


class UnavailabilitiesRepository(
    BaseRepository[UnavailabilityModel, Unavailability, UnavailabilityFilters]
):
    model = UnavailabilityModel
    filters_type = UnavailabilityFilters

    async def list_overlapping(
        self,
        establishment_id: uuid.UUID,
        starts_at: datetime,
        ends_at: datetime,
    ) -> list[Unavailability]:
        """
        Lista os bloqueios de um estabelecimento que cobrem qualquer parte da janela
        informada.

        Diferente do filtro `starts_at_from`/`starts_at_to`, que só olha o início do
        bloqueio, aqui um bloqueio que começou antes da janela e ainda está em vigor
        também é retornado.

        Args:
            establishment_id (uuid.UUID): O estabelecimento.
            starts_at (datetime): Início da janela.
            ends_at (datetime): Fim da janela.

        Returns:
            list[Unavailability]: Os bloqueios que sobrepõem a janela.
        """

        result = await self._session.execute(
            sa.select(self.model).where(
                self.model.establishment_id == establishment_id,
                self.model.starts_at < ends_at,
                self.model.ends_at > starts_at,
            )
        )
        return [self._to_entity(row) for row in result.scalars().all()]

    def _to_entity(self, row: UnavailabilityModel) -> Unavailability:
        return Unavailability(
            id=row.id,
            establishment_id=row.establishment_id,
            starts_at=row.starts_at,
            ends_at=row.ends_at,
            reason=row.reason,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _apply_filters(
        self,
        stmt: sa.Select[Any],
        filters: UnavailabilityFilters,
    ) -> sa.Select[Any]:
        if filters.establishment_id is not None:
            stmt = stmt.where(
                UnavailabilityModel.establishment_id == filters.establishment_id
            )
        if filters.starts_at_from is not None:
            stmt = stmt.where(UnavailabilityModel.starts_at >= filters.starts_at_from)
        if filters.starts_at_to is not None:
            stmt = stmt.where(UnavailabilityModel.starts_at <= filters.starts_at_to)
        return stmt
