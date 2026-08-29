"""Cliente HTTP para a API do AgendaBot, com o `X-Service-Key` fixo.

O `X-Service-Key` vive só aqui dentro de `infrastructure/agendabot/`: nunca é
logado, nunca entra em mensagem de erro, nunca chega ao LLM.
"""

import httpx


def build_agendabot_client(
    *,
    base_url: str,
    service_key: str,
    timeout_seconds: float,
) -> httpx.AsyncClient:
    """Cria o `AsyncClient` da API do AgendaBot já autenticado pelo serviço."""
    return httpx.AsyncClient(
        base_url=base_url,
        headers={"X-Service-Key": service_key},
        timeout=httpx.Timeout(timeout_seconds),
    )
