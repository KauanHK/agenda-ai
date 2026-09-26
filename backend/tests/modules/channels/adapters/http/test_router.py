import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps.auth import get_current_actor
from app.core.handlers import register_exception_handlers
from app.core.roles import UserRole
from app.modules.channels.adapters.db.factories import make_unit_of_work
from app.modules.channels.adapters.http.dependencies import get_bot_api
from app.modules.channels.adapters.http.router import router as channels_router
from app.modules.channels.domain.exceptions import (
    InvalidBotTokenError,
    TelegramApiError,
)
from tests.modules.channels.fakes import (
    TOKEN,
    FakeChannelsUnitOfWork,
    make_actor,
    make_bot_api,
    make_telegram_bot,
)


@pytest.fixture
def establishment_id() -> uuid.UUID:
    return uuid.uuid7()


@pytest.fixture
def uow() -> FakeChannelsUnitOfWork:
    return FakeChannelsUnitOfWork()


@pytest.fixture
def bot_api():
    return make_bot_api()


@pytest.fixture
def actor(establishment_id):
    return make_actor(establishment_id, UserRole.ESTABLISHMENT_ADMIN)


@pytest.fixture
def client(uow, bot_api, actor) -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(
        channels_router,
        prefix="/establishments/{establishment_id}/channels/telegram",
    )
    app.dependency_overrides[make_unit_of_work] = lambda: uow
    app.dependency_overrides[get_bot_api] = lambda: bot_api
    app.dependency_overrides[get_current_actor] = lambda: actor
    return TestClient(app)


@pytest.fixture
def url(establishment_id) -> str:
    return f"/establishments/{establishment_id}/channels/telegram"


def test_get_without_bot(client, url):
    response = client.get(url)

    assert response.status_code == 200
    assert response.json() == {
        "connected": False,
        "bot_id": None,
        "bot_username": None,
        "connected_at": None,
    }


def test_get_with_bot_hides_secrets(client, uow, url, establishment_id):
    bot = make_telegram_bot(establishment_id)
    uow.telegram_bots.get_by_establishment.return_value = bot

    response = client.get(url)

    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is True
    assert body["bot_id"] == bot.bot_id
    assert body["bot_username"] == bot.bot_username
    assert body["connected_at"] is not None
    assert TOKEN not in response.text
    assert bot.webhook_secret not in response.text


def test_put_connects(client, uow, url, establishment_id):
    uow.telegram_bots.save.return_value = make_telegram_bot(establishment_id)

    response = client.put(url, json={"bot_token": TOKEN})

    assert response.status_code == 200
    assert response.json()["connected"] is True
    assert TOKEN not in response.text


@pytest.mark.parametrize(
    "bot_token",
    ["sem-dois-pontos", "abc:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw", "1:curto"],
)
def test_put_malformed_token(client, bot_api, url, bot_token):
    response = client.put(url, json={"bot_token": bot_token})

    assert response.status_code == 422
    assert bot_token not in response.text
    bot_api.get_me.assert_not_awaited()


def test_put_rejected_token(client, bot_api, url):
    bot_api.get_me.side_effect = InvalidBotTokenError("recusado")

    response = client.put(url, json={"bot_token": TOKEN})

    assert response.status_code == 422
    assert response.json()["message"] == (
        "Token do bot inválido. Confira com o @BotFather."
    )
    assert TOKEN not in response.text


def test_put_bot_of_other_establishment(client, uow, url):
    uow.telegram_bots.get_by_bot_id.return_value = make_telegram_bot(uuid.uuid7())

    response = client.put(url, json={"bot_token": TOKEN})

    assert response.status_code == 409
    assert response.json()["message"] == (
        "Este bot já está conectado a outro estabelecimento."
    )


def test_put_missing_establishment(client, uow, url):
    uow.establishments.get_by_id_or_none.return_value = None

    response = client.put(url, json={"bot_token": TOKEN})

    assert response.status_code == 404


def test_put_telegram_unavailable(client, bot_api, url):
    bot_api.set_webhook.side_effect = TelegramApiError("falhou")

    response = client.put(url, json={"bot_token": TOKEN})

    assert response.status_code == 502
    assert response.json() == {
        "code": "external_service_error",
        "message": "Não foi possível falar com o Telegram. Tente novamente.",
        "details": None,
    }


@pytest.mark.parametrize("role", [UserRole.MEMBER])
def test_put_forbidden(client, url, actor, establishment_id, role):
    client.app.dependency_overrides[get_current_actor] = lambda: make_actor(
        establishment_id, role
    )

    response = client.put(url, json={"bot_token": TOKEN})

    assert response.status_code == 403
