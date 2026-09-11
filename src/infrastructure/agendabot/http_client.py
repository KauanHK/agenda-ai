"""Cliente HTTP para a API do AgendaBot, com o `X-Service-Key` fixo.

O `X-Service-Key` vive só aqui dentro de `infrastructure/agendabot/`: nunca é
logado, nunca entra em mensagem de erro, nunca chega ao LLM.
"""

import httpx


def build_agendabot_client(
    *,
    base_url: str,
    service_key: str,
    connect_timeout_seconds: float,
    read_timeout_seconds: float,
) -> httpx.AsyncClient:
    """Cria o `AsyncClient` da API do AgendaBot já autenticado pelo serviço.

    O timeout é separado: `connect` curto (abrir a conexão) e `read`/`write`/`pool`
    mais folgados — a emissão da sessão faz trabalho no backend. Um estouro de
    qualquer um deles é um `httpx.TimeoutException`, que o `session_issuer` repete.
    """
    return httpx.AsyncClient(
        base_url=base_url,
        headers={"X-Service-Key": service_key},
        timeout=httpx.Timeout(read_timeout_seconds, connect=connect_timeout_seconds),
    )
