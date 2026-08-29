import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.security.mcp_tokens import decode_client_mcp_session_token
from app.modules.booking.application.use_cases.sessions import CustomerSessionIssuer
from app.modules.clients.domain.entities import Client
from tests.modules.booking.application.use_cases.conftest import FakeBookingUnitOfWork


def make_client(establishment_id: uuid.UUID, **overrides) -> Client:
    now = datetime.now(UTC)
    defaults = {
        "id": uuid.uuid7(),
        "establishment_id": establishment_id,
        "name": "Cliente Teste",
        "phone": "+5547999998888",
        "email": None,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    return Client(**(defaults | overrides))


@pytest.fixture
def existing_client(establishment_id: uuid.UUID) -> Client:
    return make_client(establishment_id)


@pytest.fixture
def clients_repo(existing_client: Client) -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_establishment_and_phone.return_value = existing_client
    repo.create.return_value = existing_client
    return repo


@pytest.fixture
def session_uow(
    clients_repo: AsyncMock,
    establishments_repo: AsyncMock,
) -> FakeBookingUnitOfWork:
    return FakeBookingUnitOfWork(
        clients=clients_repo,
        establishments=establishments_repo,
    )


class TestCustomerSessionIssuer:
    async def test_emite_token_para_cliente_existente(
        self,
        session_uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        existing_client: Client,
    ) -> None:
        session = await CustomerSessionIssuer(session_uow).issue(
            establishment_id=establishment_id,
            phone="(47) 99999-8888",
        )

        assert session.client_id == existing_client.id
        assert session.is_new_client is False

    async def test_token_carrega_a_identidade_verificada(
        self,
        session_uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        existing_client: Client,
    ) -> None:
        session = await CustomerSessionIssuer(session_uow).issue(
            establishment_id=establishment_id,
            phone="47999998888",
        )

        payload = decode_client_mcp_session_token(session.token)
        assert payload["client_id"] == existing_client.id
        assert payload["establishment_id"] == establishment_id
        assert payload["phone"] == "+5547999998888"

    async def test_busca_o_cliente_pelo_telefone_normalizado(
        self,
        session_uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        clients_repo: AsyncMock,
    ) -> None:
        await CustomerSessionIssuer(session_uow).issue(
            establishment_id=establishment_id,
            phone="(47) 99999-8888",
        )

        assert (
            clients_repo.get_by_establishment_and_phone.await_args.kwargs["phone"]
            == "+5547999998888"
        )

    async def test_cria_o_cliente_na_primeira_mensagem(
        self,
        session_uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        clients_repo: AsyncMock,
    ) -> None:
        clients_repo.get_by_establishment_and_phone.return_value = None

        session = await CustomerSessionIssuer(session_uow).issue(
            establishment_id=establishment_id,
            phone="47999998888",
            name="João",
        )

        assert session.is_new_client is True
        criado = clients_repo.create.await_args.kwargs["create_command"]
        assert criado.name == "João"
        assert criado.phone == "+5547999998888"
        assert criado.establishment_id == establishment_id

    async def test_sem_nome_usa_o_telefone_como_nome(
        self,
        session_uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        clients_repo: AsyncMock,
    ) -> None:
        clients_repo.get_by_establishment_and_phone.return_value = None

        await CustomerSessionIssuer(session_uow).issue(
            establishment_id=establishment_id,
            phone="47999998888",
        )

        assert clients_repo.create.await_args.kwargs["create_command"].name == (
            "+5547999998888"
        )

    async def test_rejeita_estabelecimento_inexistente(
        self,
        session_uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        establishments_repo: AsyncMock,
    ) -> None:
        establishments_repo.get_by_id_or_none.return_value = None

        with pytest.raises(NotFoundError):
            await CustomerSessionIssuer(session_uow).issue(
                establishment_id=establishment_id,
                phone="47999998888",
            )

    async def test_rejeita_estabelecimento_inativo(
        self,
        session_uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        establishments_repo: AsyncMock,
        establishment,
    ) -> None:
        import dataclasses

        establishments_repo.get_by_id_or_none.return_value = dataclasses.replace(
            establishment, is_active=False
        )

        with pytest.raises(NotFoundError):
            await CustomerSessionIssuer(session_uow).issue(
                establishment_id=establishment_id,
                phone="47999998888",
            )

    async def test_rejeita_cliente_inativo(
        self,
        session_uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        clients_repo: AsyncMock,
    ) -> None:
        clients_repo.get_by_establishment_and_phone.return_value = make_client(
            establishment_id, is_active=False
        )

        with pytest.raises(ForbiddenError):
            await CustomerSessionIssuer(session_uow).issue(
                establishment_id=establishment_id,
                phone="47999998888",
            )

    async def test_traduz_criacao_concorrente_em_conflito(
        self,
        session_uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        clients_repo: AsyncMock,
    ) -> None:
        clients_repo.get_by_establishment_and_phone.return_value = None
        clients_repo.create.side_effect = IntegrityError("", {}, Exception())

        with pytest.raises(ConflictError):
            await CustomerSessionIssuer(session_uow).issue(
                establishment_id=establishment_id,
                phone="47999998888",
            )

    async def test_rejeita_telefone_invalido(
        self,
        session_uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
    ) -> None:
        with pytest.raises(ValueError):
            await CustomerSessionIssuer(session_uow).issue(
                establishment_id=establishment_id,
                phone="abc",
            )
