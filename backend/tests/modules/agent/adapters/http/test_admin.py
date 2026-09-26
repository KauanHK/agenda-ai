"""Testes das rotas `/admin/telegram/webhook` com `TestClient` e um container fake.

O fake registra as chamadas e devolve (ou levanta) o que o teste mandar; o
Telegram real fica coberto em `tests/modules/channels/adapters/telegram/test_bot_api.py`.
"""

from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.agent.adapters.http.routes import admin
from app.modules.agent.domain.exceptions import WebhookRegistrationError

_TOKEN = "t0ken-adm1n"
_INFO = {"url": "https://agente.exemplo/webhook/telegram/***", "pending_update_count": 0}
_AUTH = {"Authorization": f"Bearer {_TOKEN}"}


class _FakeContainer:
    def __init__(self, *, failure: Exception | None = None) -> None:
        self.admin_token = _TOKEN
        self.registered: list[tuple[str, bool]] = []
        self.info_calls = 0
        self._failure = failure

    async def register_webhook(self, base_url: str, drop_pending_updates: bool) -> dict[str, Any]:
        if self._failure is not None:
            raise self._failure
        self.registered.append((base_url, drop_pending_updates))
        return _INFO

    async def get_webhook_info(self) -> dict[str, Any]:
        if self._failure is not None:
            raise self._failure
        self.info_calls += 1
        return _INFO


def _client(container: _FakeContainer) -> TestClient:
    app = FastAPI()
    app.include_router(admin.router)
    app.state.container = container
    return TestClient(app)


@pytest.fixture
def container() -> _FakeContainer:
    return _FakeContainer()


def test_post_registra_e_devolve_o_info(container: _FakeContainer) -> None:
    response = _client(container).post(
        "/admin/telegram/webhook",
        json={"base_url": "https://agente.exemplo"},
        headers=_AUTH,
    )

    assert response.status_code == 200
    assert response.json() == _INFO
    assert container.registered == [("https://agente.exemplo", False)]


def test_post_repassa_drop_pending_updates(container: _FakeContainer) -> None:
    _client(container).post(
        "/admin/telegram/webhook",
        json={"base_url": "https://agente.exemplo", "drop_pending_updates": True},
        headers=_AUTH,
    )

    assert container.registered == [("https://agente.exemplo", True)]


def test_get_consulta_o_telegram(container: _FakeContainer) -> None:
    response = _client(container).get("/admin/telegram/webhook", headers=_AUTH)

    assert response.status_code == 200
    assert response.json() == _INFO
    assert container.info_calls == 1


@pytest.mark.parametrize(
    "headers",
    [{}, {"Authorization": "Bearer errado"}, {"Authorization": f"Basic {_TOKEN}"}],
    ids=["sem-header", "token-errado", "esquema-errado"],
)
def test_sem_bearer_valido_responde_401_e_nao_toca_no_telegram(
    container: _FakeContainer, headers: dict[str, str]
) -> None:
    client = _client(container)

    post = client.post(
        "/admin/telegram/webhook", json={"base_url": "https://agente.exemplo"}, headers=headers
    )
    get = client.get("/admin/telegram/webhook", headers=headers)

    assert post.status_code == 401
    assert get.status_code == 401
    assert post.headers["WWW-Authenticate"] == "Bearer"
    assert container.registered == []
    assert container.info_calls == 0


def test_base_url_sem_https_responde_422(container: _FakeContainer) -> None:
    response = _client(container).post(
        "/admin/telegram/webhook", json={"base_url": "http://agente.exemplo"}, headers=_AUTH
    )

    assert response.status_code == 422
    assert container.registered == []


def test_corpo_sem_base_url_responde_422(container: _FakeContainer) -> None:
    response = _client(container).post("/admin/telegram/webhook", json={}, headers=_AUTH)

    assert response.status_code == 422


def test_recusa_do_telegram_vira_502_com_a_descricao() -> None:
    container = _FakeContainer(failure=WebhookRegistrationError("O Telegram recusou o setWebhook"))
    client = _client(container)

    post = client.post(
        "/admin/telegram/webhook", json={"base_url": "https://agente.exemplo"}, headers=_AUTH
    )
    get = client.get("/admin/telegram/webhook", headers=_AUTH)

    assert post.status_code == 502
    assert post.json() == {"detail": "O Telegram recusou o setWebhook"}
    assert get.status_code == 502
