from typing import Protocol

from app.core.db.ports import BaseRepositoryProtocol
from app.modules.unavailabilities.application.dtos.filters import (
    UnavailabilityFilters,
)
from app.modules.unavailabilities.domain.entities import (
    NewUnavailability,
    Unavailability,
    UpdateUnavailability,
)


class UnavailabilitiesRepositoryProtocol(
    BaseRepositoryProtocol[
        Unavailability,
        UnavailabilityFilters,
        NewUnavailability,
        UpdateUnavailability,
    ],
    Protocol,
):
    pass
