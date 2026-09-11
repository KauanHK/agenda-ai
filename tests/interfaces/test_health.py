"""Testes dos healthchecks.

`/health` é montado sozinho (não toca em nada). `/health/ready` consome o
`check_readiness` do container; aqui ele é um fake que devolve o relatório dado.
"""

from collections.abc import Awaitable, Callable

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.interfaces.http.routes import health


def _app_with_readiness(report: dict[str, str]) -> FastAPI:
    async def check_readiness() -> dict[str, str]:
        return report

    app = FastAPI()
    app.include_router(health.router)
    app.state.container = _FakeContainer(check_readiness)
    return app


class _FakeContainer:
    def __init__(self, check_readiness: Callable[[], Awaitable[dict[str, str]]]) -> None:
        self.check_readiness = check_readiness


def test_health_responde_ok_sem_dependencias() -> None:
    app = FastAPI()
    app.include_router(health.router)

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_responde_200_com_redis_de_pe() -> None:
    client = TestClient(_app_with_readiness({"redis": "ok"}))

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"redis": "ok"}


def test_ready_responde_503_com_redis_fora() -> None:
    client = TestClient(_app_with_readiness({"redis": "down"}))

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"redis": "down"}
