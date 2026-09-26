"""Healthchecks.

`GET /health` é *liveness* burro (200 enquanto o processo responde). `GET
/health/ready` é *readiness*: consulta o `check_readiness` do container (um `PING`
no Redis) e responde `503` se alguma dependência estiver fora.
"""

from fastapi import APIRouter, Response, status

from src.interfaces.http.dependencies import ContainerDep

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Responde `{"status": "ok"}` enquanto o processo está de pé."""
    return {"status": "ok"}


@router.get("/health/ready")
async def health_ready(container: ContainerDep, response: Response) -> dict[str, str]:
    """Relata as dependências; `503` se alguma não estiver `ok`."""
    report = await container.check_readiness()
    if any(state != "ok" for state in report.values()):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return report
