from typing import Protocol

from app.core.db.ports import BaseRepositoryProtocol
from app.modules.establishments.application.dtos.filters import EstablishmentFilters
from app.modules.establishments.domain.entities import (
    Establishment,
    NewEstablishment,
    UpdateEstablishment,
)


class EstablishmentsRepositoryProtocol(
    BaseRepositoryProtocol[
        Establishment, EstablishmentFilters, NewEstablishment, UpdateEstablishment
    ],
    Protocol,
):
    async def get_by_cnpj_or_none(self, cnpj: str) -> Establishment | None: ...
    async def get_by_cnpj(self, cnpj: str) -> Establishment: ...
