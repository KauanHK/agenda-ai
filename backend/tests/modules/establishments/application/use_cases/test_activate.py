from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.types import UNSET
from app.modules.establishments.application.use_cases.activate import (
    EstablishmentsActivator,
)
from app.modules.establishments.domain.entities import UpdateEstablishment


async def test_activate_sets_is_active_true(uow, establishments_repo, establishment):
    result = await EstablishmentsActivator(uow).activate(establishment.id)

    assert result == establishment
    sent: UpdateEstablishment = establishments_repo.update.call_args.kwargs[
        "update_command"
    ]
    assert sent.is_active is True
    assert sent.deleted_at is UNSET


async def test_activate_does_not_fetch_establishment(
    uow, establishments_repo, establishment
):
    await EstablishmentsActivator(uow).activate(establishment.id)

    establishments_repo.get_by_id.assert_not_awaited()


async def test_deactivate_sets_is_active_false_and_deleted_at(
    uow, establishments_repo, establishment
):
    result = await EstablishmentsActivator(uow).deactivate(establishment.id)

    assert result == establishment
    sent: UpdateEstablishment = establishments_repo.update.call_args.kwargs[
        "update_command"
    ]
    assert sent.is_active is False
    assert isinstance(sent.deleted_at, datetime)


async def test_deactivate_uses_establishment_timezone(
    uow, establishments_repo, establishment
):
    await EstablishmentsActivator(uow).deactivate(establishment.id)

    establishments_repo.get_by_id.assert_awaited_once_with(establishment.id)
    sent: UpdateEstablishment = establishments_repo.update.call_args.kwargs[
        "update_command"
    ]
    assert sent.deleted_at.tzinfo == ZoneInfo(establishment.timezone)
