import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CustomerActor:
    establishment_id: uuid.UUID
    client_id: uuid.UUID
    phone: str
