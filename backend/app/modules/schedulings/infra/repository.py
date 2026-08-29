import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginationParams
from app.modules.dashboard.domain.filters import DashboardFilters
from app.modules.schedulings.domain.enums import SchedulingStatus
from app.modules.schedulings.domain.filters import SchedulingFilters
from app.modules.schedulings.domain.model import Scheduling, SchedulingStatusLog


@dataclass
class SchedulingsDashboardData:
    total: int
    confirmed: int
    pending: int
    expected_revenue: Decimal
    schedulings: list[Scheduling]


class SchedulingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id_or_none(self, scheduling_id: uuid.UUID) -> Scheduling | None:
        return await self._session.get(Scheduling, scheduling_id)

    async def get_by_id(self, scheduling_id: uuid.UUID) -> Scheduling:
        scheduling = await self.get_by_id_or_none(scheduling_id)
        if scheduling is None:
            raise NotFoundError("Agendamento não encontrado.")
        return scheduling

    async def get_by_id_expanded(self, scheduling_id: uuid.UUID) -> Scheduling | None:
        query = (
            select(Scheduling)
            .options(
                selectinload(Scheduling.user),
                selectinload(Scheduling.client),
                selectinload(Scheduling.service),
            )
            .where(Scheduling.id == scheduling_id)
        )
        result = await self._session.execute(
            query, execution_options={"populate_existing": True}
        )
        return result.scalar_one_or_none()

    async def get_dashboard_by_establishment(
        self,
        establishment_id: uuid.UUID,
        filters: DashboardFilters,
    ) -> SchedulingsDashboardData:

        query = (
            select(Scheduling)
            .where(
                Scheduling.establishment_id == establishment_id,
                func.date(Scheduling.starts_at) >= filters.start_date.date(),
                func.date(Scheduling.starts_at) <= filters.end_date.date(),
            )
            .order_by(Scheduling.starts_at)
            .options(
                selectinload(Scheduling.user),
                selectinload(Scheduling.client),
                selectinload(Scheduling.service),
            )
        )
        result = await self._session.execute(query)
        schedulings = list(result.scalars())

        confirmed = sum(
            1 for s in schedulings if s.status == SchedulingStatus.CONFIRMED
        )
        pending = sum(1 for s in schedulings if s.status == SchedulingStatus.PENDING)
        expected_revenue = sum(
            (
                s.service.price
                for s in schedulings
                if s.status != SchedulingStatus.CANCELLED
            ),
            Decimal(0),
        )

        return SchedulingsDashboardData(
            total=len(schedulings),
            confirmed=confirmed,
            pending=pending,
            expected_revenue=expected_revenue,
            schedulings=schedulings,
        )

    async def create(self, scheduling: Scheduling) -> Scheduling:
        self._session.add(scheduling)
        await self._session.flush()
        await self._session.refresh(scheduling)
        return scheduling

    async def update(self, scheduling: Scheduling) -> Scheduling:
        merged = await self._session.merge(scheduling)
        await self._session.flush()
        await self._session.refresh(merged)
        return merged

    async def list_overlapping(
        self,
        establishment_id: uuid.UUID,
        starts_at: datetime,
        ends_at: datetime,
        exclude_id: uuid.UUID | None = None,
    ) -> list[Scheduling]:
        """
        Lista os agendamentos ativos de um estabelecimento que ocupam qualquer parte da
        janela informada.

        Serve ao cálculo de disponibilidade: em vez de uma consulta por
        (horário candidato x profissional), carrega a agenda da janela inteira de uma
        vez e a sobreposição é resolvida em memória.

        Args:
            establishment_id (uuid.UUID): O estabelecimento.
            starts_at (datetime): Início da janela.
            ends_at (datetime): Fim da janela.
            exclude_id (uuid.UUID | None):
                Agendamento a ignorar — usado no reagendamento, para que ele não
                conflite consigo mesmo.

        Returns:
            list[Scheduling]: Os agendamentos que sobrepõem a janela.
        """

        query = select(Scheduling).where(
            Scheduling.establishment_id == establishment_id,
            Scheduling.status != SchedulingStatus.CANCELLED,
            Scheduling.starts_at < ends_at,
            Scheduling.ends_at > starts_at,
        )
        if exclude_id is not None:
            query = query.where(Scheduling.id != exclude_id)
        result = await self._session.execute(query)
        return list(result.scalars())

    async def list(
        self,
        pagination: PaginationParams,
        filters: SchedulingFilters | None = None,
    ) -> list[Scheduling]:
        query = self._construct_select_query(filters)
        query = query.limit(pagination.size).offset(pagination.offset)
        result = await self._session.execute(query)
        return list(result.scalars())

    async def count(self, filters: SchedulingFilters | None = None) -> int:
        query = select(func.count()).select_from(  # pylint: disable=not-callable
            self._construct_select_query(filters).subquery()
        )
        result = await self._session.execute(query)
        return result.scalar_one()

    async def has_user_overlap(
        self,
        user_id: uuid.UUID,
        starts_at: datetime,
        ends_at: datetime,
        exclude_id: uuid.UUID | None = None,
    ) -> bool:
        query = select(Scheduling).where(
            Scheduling.user_id == user_id,
            Scheduling.status != SchedulingStatus.CANCELLED,
            Scheduling.starts_at < ends_at,
            Scheduling.ends_at > starts_at,
        )
        if exclude_id is not None:
            query = query.where(Scheduling.id != exclude_id)
        result = await self._session.execute(query.limit(1))
        return result.scalar_one_or_none() is not None

    async def has_client_overlap(
        self,
        client_id: uuid.UUID,
        starts_at: datetime,
        ends_at: datetime,
        exclude_id: uuid.UUID | None = None,
    ) -> bool:
        query = select(Scheduling).where(
            Scheduling.client_id == client_id,
            Scheduling.status != SchedulingStatus.CANCELLED,
            Scheduling.starts_at < ends_at,
            Scheduling.ends_at > starts_at,
        )
        if exclude_id is not None:
            query = query.where(Scheduling.id != exclude_id)
        result = await self._session.execute(query.limit(1))
        return result.scalar_one_or_none() is not None

    def _construct_select_query(
        self,
        filters: SchedulingFilters | None = None,
    ) -> Select[tuple[Scheduling]]:

        query = (
            select(Scheduling)
            .order_by(Scheduling.starts_at)
            .options(
                selectinload(Scheduling.user),
                selectinload(Scheduling.client),
                selectinload(Scheduling.service),
            )
        )

        if filters is None:
            return query
        if filters.establishment_id is not None:
            query = query.where(Scheduling.establishment_id == filters.establishment_id)
        if filters.status is not None:
            query = query.where(Scheduling.status == filters.status)
        if filters.source is not None:
            query = query.where(Scheduling.source == filters.source)
        if filters.user_id is not None:
            query = query.where(Scheduling.user_id == filters.user_id)
        if filters.client_id is not None:
            query = query.where(Scheduling.client_id == filters.client_id)
        if filters.service_id is not None:
            query = query.where(Scheduling.service_id == filters.service_id)
        if filters.starts_at_from is not None:
            query = query.where(Scheduling.starts_at >= filters.starts_at_from)
        if filters.starts_at_to is not None:
            query = query.where(Scheduling.starts_at <= filters.starts_at_to)
        return query


class SchedulingStatusLogsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, log: SchedulingStatusLog) -> SchedulingStatusLog:
        self._session.add(log)
        await self._session.flush()
        await self._session.refresh(log)
        return log

    async def list_by_scheduling(
        self,
        scheduling_id: uuid.UUID,
        pagination: PaginationParams,
    ) -> list[SchedulingStatusLog]:
        query = (
            select(SchedulingStatusLog)
            .where(SchedulingStatusLog.scheduling_id == scheduling_id)
            .order_by(SchedulingStatusLog.changed_at)
            .limit(pagination.size)
            .offset(pagination.offset)
        )
        result = await self._session.execute(query)
        return list(result.scalars())

    async def count_by_scheduling(self, scheduling_id: uuid.UUID) -> int:
        query = select(func.count()).where(  # pylint: disable=not-callable
            SchedulingStatusLog.scheduling_id == scheduling_id
        )
        result = await self._session.execute(query)
        return result.scalar_one()
