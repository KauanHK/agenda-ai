"""Teste do healthcheck."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.interfaces.http.routes import health


def test_health_responde_ok_sem_dependencias() -> None:
    app = FastAPI()
    app.include_router(health.router)

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
