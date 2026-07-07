import uuid
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.exceptions import NotFoundError, ValidationAppError
from app.db.unit_of_work import UnitOfWork
from app.modules.memberships.infra.repository import MembershipRepository
from app.modules.operating_hours.infra.repository import OperatingHoursRepository
from app.modules.schedulings.infra.repository import SchedulingsRepository
from app.modules.services.infra.repository import ServicesRepository

_ESTABLISHMENT_TZ = ZoneInfo("America/Sao_Paulo")


class AgentSlotsReader:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def list(
        self,
        service_id: uuid.UUID,
        target_date: date,
        establishment_id: uuid.UUID,
    ) -> list[dict]:
        async with self._uow:
            services_repo = self._uow.repository(ServicesRepository)
            hours_repo = self._uow.repository(OperatingHoursRepository)
            membership_repo = self._uow.repository(MembershipRepository)
            scheduling_repo = self._uow.repository(SchedulingsRepository)

            service = await services_repo.get_by_id_or_none(service_id)
            if service is None or not service.is_active or service.establishment_id != establishment_id:
                raise NotFoundError("Serviço não encontrado.")

            weekday = target_date.weekday()
            all_hours = await hours_repo.list_by_establishment(establishment_id)
            operating = next((h for h in all_hours if h.weekday == weekday), None)
            if operating is None:
                return []

            memberships = await membership_repo.list_all_by_establishment(establishment_id)
            user_ids = [m.user_id for m in memberships]
            if not user_ids:
                raise ValidationAppError("Nenhum profissional cadastrado no estabelecimento.")

            duration = timedelta(minutes=service.duration_minutes)
            now_utc = datetime.now(UTC)

            current_local = datetime.combine(target_date, operating.start_time).replace(
                tzinfo=_ESTABLISHMENT_TZ
            )
            end_local = datetime.combine(target_date, operating.end_time).replace(
                tzinfo=_ESTABLISHMENT_TZ
            )

            slots = []
            while current_local + duration <= end_local:
                starts_utc = current_local.astimezone(UTC)
                ends_utc = starts_utc + duration

                if starts_utc > now_utc:
                    for user_id in user_ids:
                        has_overlap = await scheduling_repo.has_user_overlap(
                            user_id, starts_utc, ends_utc
                        )
                        if not has_overlap:
                            slots.append(
                                {
                                    "starts_at": starts_utc.isoformat(),
                                    "ends_at": ends_utc.isoformat(),
                                }
                            )
                            break

                current_local += duration

            return slots
