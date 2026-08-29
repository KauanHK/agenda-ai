"""
Cálculo de disponibilidade.

É a única fonte de verdade sobre "este horário pode ser marcado?" no canal automático:
tanto a listagem de horários livres quanto a criação e o reagendamento passam por aqui,
de modo que o agente nunca ofereça um horário que a gravação depois recusaria.

Considera, nesta ordem: os turnos de funcionamento do dia, os bloqueios do
estabelecimento, a agenda de cada profissional e a agenda do próprio cliente.
"""

import uuid
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.modules.booking.application.ports.unit_of_work import BookingUnitOfWorkProtocol
from app.modules.booking.domain.entities import Slot
from app.modules.booking.domain.exceptions import (
    ClosedOnWeekdayError,
    EstablishmentUnavailableError,
    NoProfessionalAvailableError,
    NoProfessionalsError,
    OutsideOperatingHoursError,
    PastDateTimeError,
    ServiceUnavailableError,
)
from app.modules.operating_hours.domain.entities import OperatingHour
from app.modules.schedulings.domain.exceptions import SchedulingOverlapClientError
from app.modules.services.domain.model import Service

# Passo do grid de horários oferecidos. Independe da duração do serviço: com 15 min o
# cliente recebe opções em horários redondos (9:00, 9:15, ...) mesmo para serviços de
# duração quebrada.
SLOT_STEP_MINUTES = 15

# Teto de horários devolvidos por consulta — o resultado vai para o contexto de um LLM.
MAX_SLOTS = 60

_FALLBACK_TIMEZONE = ZoneInfo("America/Sao_Paulo")

type _Interval = tuple[datetime, datetime]


def _overlaps(interval: _Interval, others: list[_Interval]) -> bool:
    """Verifica se um intervalo cruza qualquer um dos demais (meio-aberto)."""

    starts_at, ends_at = interval
    return any(starts_at < other_end and ends_at > other_start
               for other_start, other_end in others)


class AvailabilityCalculator:
    """
    Opera sobre uma unidade de trabalho **já aberta** pelo chamador, para que a leitura
    da disponibilidade e a gravação do agendamento aconteçam na mesma transação.
    """

    def __init__(self, uow: BookingUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def get_timezone(self, establishment_id: uuid.UUID) -> ZoneInfo:
        """
        Obtém o fuso horário do estabelecimento.

        Args:
            establishment_id (uuid.UUID): O estabelecimento.

        Returns:
            ZoneInfo:
                O fuso configurado. Cai para America/Sao_Paulo se o valor gravado não
                for um fuso IANA válido.
        """

        establishment = await self._uow.establishments.get_by_id(establishment_id)
        try:
            return ZoneInfo(establishment.timezone)
        except (ZoneInfoNotFoundError, ValueError):
            return _FALLBACK_TIMEZONE

    async def get_bookable_service(
        self,
        establishment_id: uuid.UUID,
        service_id: uuid.UUID,
    ) -> Service:
        """
        Obtém um serviço garantindo que ele pode ser agendado pelo cliente.

        Args:
            establishment_id (uuid.UUID): O estabelecimento da sessão.
            service_id (uuid.UUID): O serviço escolhido.

        Returns:
            Service: O serviço.

        Raises:
            ServiceUnavailableError:
                Se o serviço não existe, está inativo ou é de outro estabelecimento.
                A mesma exceção nos três casos, para não revelar a existência de
                serviços de terceiros.
        """

        service = await self._uow.services.get_by_id_or_none(service_id)
        if (
            service is None
            or not service.is_active
            or service.establishment_id != establishment_id
        ):
            raise ServiceUnavailableError()
        return service

    async def free_slots(
        self,
        *,
        establishment_id: uuid.UUID,
        service: Service,
        target_date: date,
        client_id: uuid.UUID | None = None,
        now: datetime | None = None,
        exclude_scheduling_id: uuid.UUID | None = None,
        step_minutes: int = SLOT_STEP_MINUTES,
        limit: int = MAX_SLOTS,
    ) -> list[Slot]:
        """
        Lista os horários livres de um serviço em um dia.

        Args:
            establishment_id (uuid.UUID): O estabelecimento.
            service (Service): O serviço, que define a duração de cada horário.
            target_date (date): O dia desejado, na data local do estabelecimento.
            client_id (uuid.UUID | None):
                Se informado, oculta horários em que o próprio cliente já tem
                compromisso.
            now (datetime | None): Instante de referência; por padrão, agora em UTC.
            exclude_scheduling_id (uuid.UUID | None):
                Agendamento a desconsiderar — usado ao reagendar, para que o horário
                atual não bloqueie a si mesmo.
            step_minutes (int): Espaçamento entre horários candidatos.
            limit (int): Máximo de horários devolvidos.

        Returns:
            list[Slot]: Os horários livres, em ordem cronológica.
        """

        now = now or datetime.now(UTC)
        timezone = await self.get_timezone(establishment_id)
        hours = await self._uow.operating_hours.list_by_establishment(establishment_id)
        windows = self._operating_windows(hours, timezone, target_date)
        if not windows:
            return []

        professionals = await self._active_professionals(establishment_id)

        day_start, day_end = windows[0][0], windows[-1][1]
        busy_by_professional, client_busy = await self._load_agenda(
            establishment_id=establishment_id,
            starts_at=day_start,
            ends_at=day_end,
            client_id=client_id,
            exclude_scheduling_id=exclude_scheduling_id,
        )
        blocks = await self._load_blocks(establishment_id, day_start, day_end)

        duration = timedelta(minutes=service.duration_minutes)
        step = timedelta(minutes=step_minutes)

        slots: list[Slot] = []
        for window_start, window_end in windows:
            cursor = window_start
            while cursor + duration <= window_end:
                candidate = (cursor, cursor + duration)
                cursor += step

                if candidate[0] <= now:
                    continue
                if _overlaps(candidate, blocks):
                    continue
                if _overlaps(candidate, client_busy):
                    continue

                available = next(
                    (
                        professional
                        for professional in professionals
                        if not _overlaps(candidate, busy_by_professional[professional])
                    ),
                    None,
                )
                if available is None:
                    continue

                slots.append(
                    Slot(
                        starts_at=candidate[0],
                        ends_at=candidate[1],
                        user_id=available,
                    )
                )
                if len(slots) >= limit:
                    return slots

        return slots

    async def assign_professional(
        self,
        *,
        establishment_id: uuid.UUID,
        service: Service,
        starts_at: datetime,
        client_id: uuid.UUID,
        now: datetime | None = None,
        exclude_scheduling_id: uuid.UUID | None = None,
    ) -> uuid.UUID:
        """
        Valida um horário específico e escolhe o profissional que vai atendê-lo.

        Aplica exatamente os mesmos critérios de `free_slots`, mas sobre um único
        horário — é a checagem feita no momento de gravar.

        Args:
            establishment_id (uuid.UUID): O estabelecimento.
            service (Service): O serviço escolhido.
            starts_at (datetime): O início desejado, com fuso.
            client_id (uuid.UUID): O cliente que está marcando.
            now (datetime | None): Instante de referência; por padrão, agora em UTC.
            exclude_scheduling_id (uuid.UUID | None):
                Agendamento a desconsiderar, no reagendamento.

        Returns:
            uuid.UUID: O profissional livre para o horário.

        Raises:
            PastDateTimeError: Se o horário já passou.
            ClosedOnWeekdayError: Se o estabelecimento não abre nesse dia.
            OutsideOperatingHoursError: Se o serviço não cabe em nenhum turno do dia.
            EstablishmentUnavailableError: Se há um bloqueio no período.
            SchedulingOverlapClientError: Se o cliente já tem compromisso no período.
            NoProfessionalsError: Se não há profissionais cadastrados.
            NoProfessionalAvailableError: Se todos já estão ocupados.
        """

        now = now or datetime.now(UTC)
        if starts_at <= now:
            raise PastDateTimeError()

        ends_at = starts_at + timedelta(minutes=service.duration_minutes)

        timezone = await self.get_timezone(establishment_id)
        hours = await self._uow.operating_hours.list_by_establishment(establishment_id)
        local_date = starts_at.astimezone(timezone).date()
        windows = self._operating_windows(hours, timezone, local_date)

        if not windows:
            raise ClosedOnWeekdayError()
        fits = any(
            window_start <= starts_at and ends_at <= window_end
            for window_start, window_end in windows
        )
        if not fits:
            raise OutsideOperatingHoursError()

        blocks = await self._load_blocks(establishment_id, starts_at, ends_at)
        if blocks:
            raise EstablishmentUnavailableError()

        professionals = await self._active_professionals(establishment_id)

        busy_by_professional, client_busy = await self._load_agenda(
            establishment_id=establishment_id,
            starts_at=starts_at,
            ends_at=ends_at,
            client_id=client_id,
            exclude_scheduling_id=exclude_scheduling_id,
        )
        if client_busy:
            raise SchedulingOverlapClientError()

        available = next(
            (
                professional
                for professional in professionals
                if not busy_by_professional[professional]
            ),
            None,
        )
        if available is None:
            raise NoProfessionalAvailableError()
        return available

    async def _active_professionals(
        self,
        establishment_id: uuid.UUID,
    ) -> list[uuid.UUID]:
        """Lista os profissionais ativos do estabelecimento."""

        memberships = await self._uow.memberships.list_all_by_establishment(
            establishment_id, only_active=True
        )
        professionals = [membership.user_id for membership in memberships]
        if not professionals:
            raise NoProfessionalsError()
        return professionals

    async def _load_agenda(
        self,
        *,
        establishment_id: uuid.UUID,
        starts_at: datetime,
        ends_at: datetime,
        client_id: uuid.UUID | None,
        exclude_scheduling_id: uuid.UUID | None,
    ) -> tuple[dict[uuid.UUID, list[_Interval]], list[_Interval]]:
        """
        Carrega a agenda da janela em uma única consulta.

        Returns:
            tuple[dict[uuid.UUID, list[_Interval]], list[_Interval]]:
                Os períodos ocupados por profissional (dict que nunca levanta
                `KeyError`) e os períodos ocupados pelo cliente.
        """

        schedulings = await self._uow.schedulings.list_overlapping(
            establishment_id=establishment_id,
            starts_at=starts_at,
            ends_at=ends_at,
            exclude_id=exclude_scheduling_id,
        )

        busy_by_professional: dict[uuid.UUID, list[_Interval]] = defaultdict(list)
        client_busy: list[_Interval] = []

        for scheduling in schedulings:
            interval = (scheduling.starts_at, scheduling.ends_at)
            busy_by_professional[scheduling.user_id].append(interval)
            if client_id is not None and scheduling.client_id == client_id:
                client_busy.append(interval)

        return busy_by_professional, client_busy

    async def _load_blocks(
        self,
        establishment_id: uuid.UUID,
        starts_at: datetime,
        ends_at: datetime,
    ) -> list[_Interval]:
        """Carrega os bloqueios do estabelecimento que cruzam a janela."""

        unavailabilities = await self._uow.unavailabilities.list_overlapping(
            establishment_id=establishment_id,
            starts_at=starts_at,
            ends_at=ends_at,
        )
        return [
            (unavailability.starts_at, unavailability.ends_at)
            for unavailability in unavailabilities
        ]

    def _operating_windows(
        self,
        hours: list[OperatingHour],
        timezone: ZoneInfo,
        target_date: date,
    ) -> list[_Interval]:
        """
        Converte os turnos de funcionamento de um dia da semana em janelas UTC.

        Ao contrário do código anterior, considera **todos** os turnos do dia — um
        estabelecimento que fecha para o almoço tem duas janelas, e a da tarde não é
        mais descartada.

        Args:
            hours (list[OperatingHour]): Os horários de funcionamento cadastrados.
            timezone (ZoneInfo): O fuso do estabelecimento.
            target_date (date): O dia desejado, na data local.

        Returns:
            list[_Interval]: As janelas em UTC, em ordem cronológica.
        """

        windows = [
            (
                datetime.combine(
                    target_date, hour.start_time, tzinfo=timezone
                ).astimezone(UTC),
                datetime.combine(
                    target_date, hour.end_time, tzinfo=timezone
                ).astimezone(UTC),
            )
            for hour in hours
            if hour.weekday == target_date.weekday()
        ]
        return sorted(windows)
