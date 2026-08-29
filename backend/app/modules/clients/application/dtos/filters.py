from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ClientFilters:
    q: str | None = None
    is_active: bool | None = None
    establishment_id: str | None = None
