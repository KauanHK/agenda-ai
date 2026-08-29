import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.types import is_unset
from app.modules.unavailabilities.application.dtos.commands import (
    UpdateUnavailabilityCommand,
)
from app.modules.unavailabilities.application.use_cases.update import (
    UnavailabilitiesUpdater,
)
from app.modules.unavailabilities.domain.entities import UpdateUnavailability
from tests.modules.unavailabilities.application.use_cases.conftest import (
    make_unavailability,
)


async def test_update_applies_only_defined_fields(
    uow, unavailabilities_repo, admin_user, establishment_id
):
    existing = make_unavailability(establishment_id)
    unavailabilities_repo.get_by_id.return_value = existing
    new_starts_at = datetime.now(UTC) + timedelta(days=2)
    unavailabilities_repo.update.return_value = make_unavailability(
        establishment_id, starts_at=new_starts_at
    )

    result = await UnavailabilitiesUpdater(uow).update(
        existing.id,
        UpdateUnavailabilityCommand(starts_at=new_starts_at),
        admin_user,
        establishment_id,
    )

    assert result.starts_at == new_starts_at
    unavailabilities_repo.update.assert_awaited_once()
    _, kwargs = unavailabilities_repo.update.call_args
    sent: UpdateUnavailability = kwargs["update_command"]
    assert sent.starts_at == new_starts_at
    assert is_unset(sent.ends_at)


async def test_update_raises_not_found_out_of_scope(
    uow, unavailabilities_repo, admin_user, establishment_id
):
    unavailabilities_repo.get_by_id.return_value = make_unavailability(uuid.uuid7())

    with pytest.raises(NotFoundError):
        await UnavailabilitiesUpdater(uow).update(
            uuid.uuid7(),
            UpdateUnavailabilityCommand(reason="Novo motivo"),
            admin_user,
            establishment_id,
        )


async def test_update_forbidden_for_member(uow, member_user, establishment_id):
    with pytest.raises(ForbiddenError, match="establishment_admin"):
        await UnavailabilitiesUpdater(uow).update(
            uuid.uuid7(),
            UpdateUnavailabilityCommand(reason="Novo motivo"),
            member_user,
            establishment_id,
        )
