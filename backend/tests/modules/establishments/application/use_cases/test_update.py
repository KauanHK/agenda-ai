from app.core.types import UNSET
from app.modules.establishments.application.dtos.commands import (
    UpdateEstablishmentCommand,
)
from app.modules.establishments.application.use_cases.update import (
    EstablishmentsUpdater,
)
from app.modules.establishments.domain.entities import UpdateEstablishment


async def test_update_returns_entity(uow, establishment):
    result = await EstablishmentsUpdater(uow).update(
        establishment.id, UpdateEstablishmentCommand(name="Novo Nome")
    )

    assert result == establishment


async def test_update_sends_only_defined_values(
    uow, establishments_repo, establishment
):
    await EstablishmentsUpdater(uow).update(
        establishment.id, UpdateEstablishmentCommand(name="Novo Nome")
    )

    establishments_repo.update.assert_awaited_once()
    sent: UpdateEstablishment = establishments_repo.update.call_args.kwargs[
        "update_command"
    ]
    assert sent.name == "Novo Nome"
    assert sent.document is UNSET
    assert sent.timezone is UNSET


async def test_update_passes_id(uow, establishments_repo, establishment):
    await EstablishmentsUpdater(uow).update(
        establishment.id, UpdateEstablishmentCommand()
    )

    assert establishments_repo.update.call_args.kwargs["id_"] == establishment.id
