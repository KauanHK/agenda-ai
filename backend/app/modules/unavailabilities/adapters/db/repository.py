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
