from dataclasses import dataclass


@dataclass
class ClientFilters:
    q: str | None = None
    is_active: bool | None = None
    establishment_id: str | None = None
