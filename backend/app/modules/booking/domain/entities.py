import uuid
from dataclasses import dataclass, replace
from datetime import datetime, tzinfo
from decimal import Decimal
from typing import Self

from app.modules.schedulings.domain.enums import SchedulingStatus


@dataclass(frozen=True, slots=True)
class Slot:
    """Um horário livre, já com o profissional que o atenderia."""

    starts_at: datetime
    ends_at: datetime
    user_id: uuid.UUID

    def in_timezone(self, timezone: tzinfo) -> Self:
        """
        Converte os horários para um fuso.

        Usado para entregar ao cliente os horários no fuso do estabelecimento — é
        sobre eles que a conversa acontece, não sobre UTC.
        """

        return replace(
            self,
            starts_at=self.starts_at.astimezone(timezone),
            ends_at=self.ends_at.astimezone(timezone),
        )


@dataclass(frozen=True, slots=True)
class BookableService:
    """Um serviço como o cliente precisa vê-lo para escolher."""

    id: uuid.UUID
    name: str
    description: str | None
    duration_minutes: int
    price: Decimal


@dataclass(frozen=True, slots=True)
class CustomerScheduling:
    """Um agendamento na perspectiva do cliente que o marcou."""

    id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    status: SchedulingStatus
    service_id: uuid.UUID
    service_name: str

    def in_timezone(self, timezone: tzinfo) -> Self:
        """Converte os horários para um fuso. Ver `Slot.in_timezone`."""

        return replace(
            self,
            starts_at=self.starts_at.astimezone(timezone),
            ends_at=self.ends_at.astimezone(timezone),
        )


@dataclass(frozen=True, slots=True)
class CustomerSession:
    """Resultado da identificação de um cliente pelo telefone."""

    token: str
    client_id: uuid.UUID
    client_name: str
    is_new_client: bool
