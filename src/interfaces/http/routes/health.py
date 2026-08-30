"""Healthcheck para o load balancer — sem tocar em Redis nem no AgendaBot."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Responde `{"status": "ok"}` enquanto o processo está de pé."""
    return {"status": "ok"}
