from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EstablishmentFilters:
    name: str | None = None
    document: str | None = None
    timezone: str | None = None
