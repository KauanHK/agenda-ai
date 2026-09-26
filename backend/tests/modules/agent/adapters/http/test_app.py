"""Teste de fumaça de `create_app`: lifespan monta o container e as rotas existem.

`build_container` toca banco/Redis/LLM no boot; aqui ele é trocado por um
dublê para exercitar só a fábrica e o registro das rotas.
"""

import contextlib
import uuid
from collections.abc import Mapping
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.agent.adapters.http.app import create_app
from app.modules.agent.domain.entities import Establishment, TelegramChannel
from app.modules.agent.settings import Settings
from tests.modules.agent.fakes.channel_directory import FakeChannelDirectory


def _settings() -> Settings:
    return Settings(
        agendabot={"mcp_url": "https://agenda.test/mcp"},  # type: ignore[arg-type]
        redis={"url": "redis://localhost:6379/1"},  # type: ignore[arg-type]
        llm={"anthropic_api_key": "anthropic-key"},  # type: ignore[arg-type]
    )


_CHANNEL = TelegramChannel(
    establishment=Establishment(
        id=uuid.UUID("01a04f5b-0e84-7530-be67-63f08e7b2269"),
        timezone=ZoneInfo("America/Sao_Paulo"),
    ),
    bot_token="bot-token",
    webhook_secret="webhook-secret",
)


class _FakeContainer:
    channels = FakeChannelDirectory(_CHANNEL)

    async def handle_update(
        self, establishment: Establishment, payload: Mapping[str, Any]
    ) -> None:
        return None

    async def check_readiness(self) -> dict[str, str]:
        return {"redis": "ok"}


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch) -> FastAPI:
    async def fake_build_container(_settings: Settings) -> tuple[_FakeContainer, Any]:
        return _FakeContainer(), contextlib.AsyncExitStack()

    monkeypatch.setattr("app.modules.agent.adapters.http.app.build_container", fake_build_container)
    return create_app(_settings())


def test_lifespan_expoe_o_container_e_serve_o_health(app: FastAPI) -> None:
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert isinstance(app.state.container, _FakeContainer)


def test_ready_usa_o_check_readiness_do_container(app: FastAPI) -> None:
    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"redis": "ok"}


def test_webhook_ligado_ao_container_do_lifespan(app: FastAPI) -> None:
    with TestClient(app) as client:
        response = client.post(
            f"/webhook/telegram/{_CHANNEL.establishment.id}",
            json={"update_id": 1},
            headers={"X-Telegram-Bot-Api-Secret-Token": "webhook-secret"},
        )

    assert response.status_code == 200


def test_rotas_admin_nao_existem_mais(app: FastAPI) -> None:
    with TestClient(app) as client:
        assert client.get("/admin/telegram/webhook").status_code == 404
