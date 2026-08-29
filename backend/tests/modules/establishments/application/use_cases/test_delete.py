from app.core.types import UNSET
from app.modules.establishments.application.use_cases.delete import (
    EstablishmentsDeleter,
)
from app.modules.establishments.domain.entities import UpdateEstablishment


async def test_delete_marks_deleted_at(uow, establishments_repo, establishment):
    await EstablishmentsDeleter(uow).delete(establishment.id)

    establishments_repo.update.assert_awaited_once()
    sent: UpdateEstablishment = establishments_repo.update.call_args.kwargs[
        "update_command"
    ]
    assert sent.deleted_at is not UNSET
    assert sent.deleted_at is not None
    assert establishments_repo.update.call_args.kwargs["id_"] == establishment.id


async def test_delete_does_not_touch_other_fields(
    uow, establishments_repo, establishment
):
    await EstablishmentsDeleter(uow).delete(establishment.id)

    sent: UpdateEstablishment = establishments_repo.update.call_args.kwargs[
        "update_command"
    ]
    assert sent.name is UNSET
    assert sent.is_active is UNSET
