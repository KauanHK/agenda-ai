import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from app.core.actors.user import Membership, UserActor
from app.db.unit_of_work import UnitOfWork
from app.modules.clients.domain.model import Client
from app.modules.clients.infra.repository import ClientsRepository
from app.modules.memberships.domain.model import Membership as MembershipModel
from app.modules.memberships.infra.repository import MembershipRepository
from app.modules.operating_hours.domain.model import OperatingHour
from app.modules.operating_hours.infra.repository import OperatingHoursRepository
from app.modules.schedulings.application.create import SchedulingsCreator
from app.modules.schedulings.domain.model import Scheduling
from app.modules.schedulings.domain.schemas import SchedulingCreate
from app.modules.schedulings.infra.repository import SchedulingsRepository
from app.modules.services.domain.model import Service
from app.modules.services.infra.repository import ServicesRepository
from app.modules.users.domain.enums import UserRole
from app.modules.users.domain.model import User
from app.modules.users.infra.repository import UsersRepository

_TZ = ZoneInfo("America/Sao_Paulo")


def _make_actor(establishment_id: uuid.UUID) -> UserActor:
    return UserActor(
        user_id=uuid.uuid7(),
        is_global_admin=False,
        memberships=(
            Membership(
                establishment_id=establishment_id, role=UserRole.ESTABLISHMENT_ADMIN
            ),
        ),
    )


async def test_create_scheduling_calls_notifications_creator():
    establishment_id = uuid.uuid7()
    actor = _make_actor(establishment_id)
    # Monday noon BRT = Monday 15:00 UTC, safely in the future
    today = datetime.now(tz=UTC)
    next_monday = today + timedelta(days=(7 - today.weekday()) % 7 or 7)
    starts_at = next_monday.replace(hour=15, minute=0, second=0, microsecond=0)
    starts_local = starts_at.astimezone(_TZ)

    user = MagicMock(spec=User)
    user.id = actor.user_id
    user.is_active = True

    membership = MagicMock(spec=MembershipModel)

    client = MagicMock(spec=Client)
    client.id = uuid.uuid7()
    client.is_active = True
    client.establishment_id = establishment_id

    service = MagicMock(spec=Service)
    service.id = uuid.uuid7()
    service.is_active = True
    service.establishment_id = establishment_id
    service.duration_minutes = 30

    # OperatingHour must match the weekday and time window of starts_at in BRT
    hour = MagicMock(spec=OperatingHour)
    hour.weekday = starts_local.weekday()
    hour.start_time = datetime(2026, 6, 8, 8, 0).time()  # 08:00 — before 12:00 BRT
    hour.end_time = datetime(2026, 6, 8, 18, 0).time()  # 18:00 — after 12:00 BRT

    scheduling = MagicMock(spec=Scheduling)
    scheduling.id = uuid.uuid7()

    mock_schedulings_repo = AsyncMock()
    mock_schedulings_repo.has_user_overlap.return_value = False
    mock_schedulings_repo.has_client_overlap.return_value = False
    mock_schedulings_repo.create.return_value = scheduling
    mock_schedulings_repo.get_by_id_expanded.return_value = scheduling

    mock_uow = AsyncMock(spec=UnitOfWork)
    mock_uow.__aenter__.return_value = mock_uow
    mock_uow.__aexit__.return_value = None
    mock_uow.session = MagicMock()
    mock_uow.session.flush = AsyncMock()

    def get_repo(cls):
        mapping = {
            SchedulingsRepository: mock_schedulings_repo,
            UsersRepository: AsyncMock(**{"get_by_id_or_none.return_value": user}),
            ClientsRepository: AsyncMock(**{"get_by_id_or_none.return_value": client}),
            ServicesRepository: AsyncMock(
                **{"get_by_id_or_none.return_value": service}
            ),
            MembershipRepository: AsyncMock(
                **{"get_by_user_and_establishment_or_none.return_value": membership}
            ),
            OperatingHoursRepository: AsyncMock(
                **{"list_by_establishment.return_value": [hour]}
            ),
        }
        if cls not in mapping:
            pytest.fail(f"Unexpected repository requested: {cls}")
        return mapping[cls]

    mock_uow.repository.side_effect = get_repo

    data = SchedulingCreate(
        user_id=actor.user_id,
        client_id=client.id,
        service_id=service.id,
        starts_at=starts_at,
    )

    with (
        patch(
            "app.modules.schedulings.application.create.SchedulingNotificationsCreator"
        ) as mock_creator_cls,
        patch(
            "app.modules.schedulings.domain.schemas.SchedulingExpandedRead.model_validate",
            return_value=MagicMock(),
        ),
    ):
        mock_creator = AsyncMock()
        mock_creator_cls.return_value = mock_creator

        creator = SchedulingsCreator(mock_uow)
        await creator.create(data, actor, establishment_id)

    mock_creator_cls.assert_called_once_with(mock_uow)
    mock_creator.create_for_scheduling.assert_called_once_with(scheduling)
