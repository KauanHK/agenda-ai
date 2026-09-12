"""Teste de fumaça de `create_app`: lifespan monta o container e as rotas existem.

`build_container` toca Redis/AgendaBot/LLM no boot; aqui ele é trocado por um
dublê para exercitar só a fábrica e o registro das rotas.
"""

import contextlib
from collections.abc import Mapping
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.interfaces.http.app import create_app
from src.settings import Settings


def _settings() -> Settings:
    return Settings(
        agendabot={
            "api_url": "https://agenda.test",
            "mcp_url": "https://agenda.test/mcp",
            "service_key": "service-key",
            "establishment_id": "01a04f5b-0e84-7530-be67-63f08e7b2269",
        },  # type: ignore[arg-type]
        telegram={
            "bot_token": "bot-token",
            "webhook_secret": "webhook-secret",
            "admin_token": "admin-token",
        },  # type: ignore[arg-type]
        redis={"url": "redis://localhost:6379/1"},  # type: ignore[arg-type]
        llm={"anthropic_api_key": "anthropic-key"},  # type: ignore[arg-type]
    )


class _FakeContainer:
    webhook_secret = "webhook-secret"
    admin_token = "admin-token"

    async def handle_update(self, payload: Mapping[str, Any]) -> None:
        return None

    async def check_readiness(self) -> dict[str, str]:
        return {"redis": "ok"}


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch) -> FastAPI:
    async def fake_build_container(_settings: Settings) -> tuple[_FakeContainer, Any]:
        return _FakeContainer(), contextlib.AsyncExitStack()

    monkeypatch.setattr("src.interfaces.http.app.build_container", fake_build_container)
    return create_app(_settings())


def test_lifespan_expoe_o_container_e_serve_o_health(app: FastAPI) -> None:
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert app.state.container.webhook_secret == "webhook-secret"


def test_ready_usa_o_check_readiness_do_container(app: FastAPI) -> None:
    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"redis": "ok"}


def test_webhook_ligado_ao_container_do_lifespan(app: FastAPI) -> None:
    with TestClient(app) as client:
        response = client.post("/webhook/telegram/webhook-secret", json={"update_id": 1})

    assert response.status_code == 200


def test_rotas_admin_estao_montadas_e_exigem_o_token(app: FastAPI) -> None:
    with TestClient(app) as client:
        assert client.get("/admin/telegram/webhook").status_code == 401
