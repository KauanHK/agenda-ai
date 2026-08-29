import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError
from app.modules.establishments.application.dtos.commands import (
    CreateEstablishmentCommand,
)
from app.modules.establishments.application.use_cases.create import (
    EstablishmentsCreator,
)
from app.modules.establishments.domain.entities import NewEstablishment
from app.modules.establishments.domain.enums import DocumentType


@pytest.fixture
def payload() -> CreateEstablishmentCommand:
    return CreateEstablishmentCommand(
        name="Clínica Nova",
        document="11222333000181",
        document_type=DocumentType.CNPJ,
        is_active=True,
        timezone="America/Sao_Paulo",
        street="Rua das Flores",
        number="123",
        complement="",
        neighborhood="Centro",
        city="São Paulo",
        state="SP",
        zip_code="01310100",
    )


async def test_create_returns_entity(uow, establishment, payload):
    result = await EstablishmentsCreator(uow).create(payload)

    assert result == establishment


async def test_create_sends_new_establishment_command(
    uow, establishments_repo, payload
):
    await EstablishmentsCreator(uow).create(payload)

    establishments_repo.create.assert_awaited_once()
    sent: NewEstablishment = establishments_repo.create.call_args.kwargs[
        "create_command"
    ]
    assert isinstance(sent, NewEstablishment)
    assert sent.name == payload.name
    assert sent.document == payload.document
    assert sent.document_type == payload.document_type
    assert sent.timezone == payload.timezone


async def test_create_uses_unit_of_work(uow, payload):
    await EstablishmentsCreator(uow).create(payload)

    assert uow.entered
    assert uow.exited


async def test_create_raises_conflict_on_duplicate_document(
    uow, establishments_repo, payload
):
    establishments_repo.create.side_effect = IntegrityError(None, None, Exception())

    with pytest.raises(ConflictError, match="cpf/cnpj"):
        await EstablishmentsCreator(uow).create(payload)
