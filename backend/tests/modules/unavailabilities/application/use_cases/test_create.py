from datetime import UTC, datetime, timedelta

import pytest

from app.core.exceptions import ForbiddenError
from app.modules.unavailabilities.application.dtos.commands import (
    CreateUnavailabilityCommand,
)
from app.modules.unavailabilities.application.use_cases.create import (
    UnavailabilitiesCreator,
)
from app.modules.unavailabilities.domain.entities import NewUnavailability
from tests.modules.unavailabilities.application.use_cases.conftest import (
    make_actor,
    make_unavailability,
)


@pytest.fixture
def payload() -> CreateUnavailabilityCommand:
    starts_at = datetime.now(UTC) + timedelta(days=1)
    return CreateUnavailabilityCommand(
        starts_at=starts_at,
        ends_at=starts_at + timedelta(hours=1),
        reason="Manutenção",
    )


async def test_create_returns_entity(
    uow, unavailabilities_repo, admin_user, establishment_id, payload
):
    unavailabilities_repo.create.return_value = make_unavailability(establishment_id)

    result = await UnavailabilitiesCreator(uow).create(
        payload, admin_user, establishment_id
    )

    assert result.establishment_id == establishment_id


async def test_create_scopes_command_to_establishment(
    uow, unavailabilities_repo, admin_user, establishment_id, payload
):
    unavailabilities_repo.create.return_value = make_unavailability(establishment_id)

    await UnavailabilitiesCreator(uow).create(payload, admin_user, establishment_id)

    unavailabilities_repo.create.assert_awaited_once()
    sent: NewUnavailability = unavailabilities_repo.create.call_args[0][0]
    assert sent.establishment_id == establishment_id
    assert sent.starts_at == payload.starts_at
    assert sent.ends_at == payload.ends_at
    assert sent.reason == payload.reason


async def test_create_forbidden_for_member(uow, member_user, establishment_id, payload):
    with pytest.raises(ForbiddenError, match="establishment_admin"):
        await UnavailabilitiesCreator(uow).create(
            payload, member_user, establishment_id
        )


async def test_create_forbidden_for_global_admin(
    uow, global_admin_user, establishment_id, payload
):
    with pytest.raises(ForbiddenError, match="global_admin"):
        await UnavailabilitiesCreator(uow).create(
            payload, global_admin_user, establishment_id
        )


async def test_create_forbidden_when_not_member(uow, establishment_id, payload):
    actor = make_actor()

    with pytest.raises(ForbiddenError, match="Acesso negado"):
        await UnavailabilitiesCreator(uow).create(payload, actor, establishment_id)
