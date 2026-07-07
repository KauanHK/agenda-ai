# 03 — MCP server

## Repositório

Novo repositório: `agendabot-mcp`

## Estrutura

```
agendabot-mcp/
├── src/
│   ├── __init__.py
│   ├── server.py              # instância FastMCP
│   ├── main.py                # entry point (uvicorn)
│   ├── config.py              # settings via pydantic-settings
│   ├── http_client.py         # httpx client compartilhado
│   ├── auth.py                # verificação do header da OpenAI
│   └── tools/
│       ├── __init__.py
│       ├── scheduling.py      # criar, cancelar, reagendar
│       ├── availability.py    # consultar horários disponíveis
│       └── services.py        # consultar serviços
├── pyproject.toml
├── Dockerfile
├── .env.example
└── README.md
```

## Dependências (pyproject.toml)

```toml
[project]
name = "agendabot-mcp"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastmcp>=0.2",
    "httpx>=0.27",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "uvicorn[standard]>=0.30",
]
```

## Configuração

`src/config.py`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    AGENDABOT_API_URL: str  # ex: https://api.agendabot.com.br
    MCP_INCOMING_SECRET: str  # validado no header da OpenAI
    HTTP_TIMEOUT_SECONDS: float = 10.0

    class Config:
        env_file = ".env"

settings = Settings()
```

## HTTP client compartilhado

`src/http_client.py`:

```python
import httpx
from src.config import settings

http_client = httpx.AsyncClient(
    base_url=settings.AGENDABOT_API_URL,
    timeout=settings.HTTP_TIMEOUT_SECONDS,
)
```

## Auth de entrada

A OpenAI envia o header customizado configurado pela FastAPI no `mcp_servers[].headers`. O MCP server valida esse header antes de qualquer tool.

`src/auth.py`:

```python
import hmac
from fastmcp import Context

def verify_request_origin(context: Context) -> str:
    """
    Retorna o X-Session-Token se válido.
    Lança exceção se a chave de origem do MCP não bater.
    """
    headers = context.request_headers
    mcp_key = headers.get("X-MCP-Key", "")

    if not hmac.compare_digest(mcp_key, settings.MCP_INCOMING_SECRET):
        raise PermissionError("Unauthorized MCP caller")

    session_token = headers.get("X-Session-Token", "")
    if not session_token:
        raise PermissionError("Missing session token")

    return session_token
```

## Server

`src/server.py`:

```python
from fastmcp import FastMCP

mcp = FastMCP(name="AgendaBot")

def register_all_tools():
    from src.tools.scheduling import register_tools as sched
    from src.tools.availability import register_tools as avail
    from src.tools.services import register_tools as svcs
    sched(mcp)
    avail(mcp)
    svcs(mcp)

register_all_tools()
```

`src/main.py`:

```python
from src.server import mcp

app = mcp.http_app()  # ASGI app para uvicorn

# uvicorn src.main:app --host 0.0.0.0 --port 8001
```

## Padrão de tool

Cada tool segue o mesmo padrão: extrai o session token do contexto, chama a API correspondente, retorna envelope padronizado.

`src/tools/scheduling.py`:

```python
from datetime import datetime
from fastmcp import Context
from src.auth import verify_request_origin
from src.http_client import http_client

def register_tools(mcp):
    @mcp.tool()
    async def criar_agendamento(
        ctx: Context,
        service_id: str,
        scheduled_at: str,  # ISO 8601
    ) -> dict:
        """
        Cria um novo agendamento para o cliente atual.
        Use APÓS confirmar com o cliente os detalhes do serviço e horário.
        """
        token = verify_request_origin(ctx)
        response = await http_client.post(
            "/agent-tools/schedulings",
            json={
                "service_id": service_id,
                "scheduled_at": scheduled_at,
            },
            headers={"X-Session-Token": token},
        )
        return response.json()

    @mcp.tool()
    async def cancelar_agendamento(
        ctx: Context,
        scheduling_id: str,
    ) -> dict:
        """Cancela um agendamento existente do cliente atual."""
        token = verify_request_origin(ctx)
        response = await http_client.delete(
            f"/agent-tools/schedulings/{scheduling_id}",
            headers={"X-Session-Token": token},
        )
        return response.json()

    @mcp.tool()
    async def reagendar(
        ctx: Context,
        scheduling_id: str,
        new_scheduled_at: str,
    ) -> dict:
        """Reagenda um atendimento existente para um novo horário."""
        token = verify_request_origin(ctx)
        response = await http_client.patch(
            f"/agent-tools/schedulings/{scheduling_id}/reschedule",
            json={"new_scheduled_at": new_scheduled_at},
            headers={"X-Session-Token": token},
        )
        return response.json()
```

## Envelope de resposta

Todas as tools retornam um envelope padronizado para o LLM interpretar erros:

**Sucesso:**
```json
{
    "success": true,
    "data": { ... }
}
```

**Erro:**
```json
{
    "success": false,
    "error_code": "SLOT_UNAVAILABLE",
    "message": "Esse horário já foi reservado",
    "details": { "alternatives": ["11:00", "14:00"] }
}
```

A FastAPI é responsável por traduzir exceções de domínio nesse formato — ver documento `04-agent-module.md`.

## Tools planejadas

| Nome | Endpoint API | Descrição |
|---|---|---|
| `consultar_servicos` | `GET /agent-tools/services` | Lista serviços do estabelecimento |
| `consultar_horarios_disponiveis` | `GET /agent-tools/slots` | Slots livres para um serviço/data |
| `criar_agendamento` | `POST /agent-tools/schedulings` | Novo agendamento |
| `cancelar_agendamento` | `DELETE /agent-tools/schedulings/{id}` | Cancelar |
| `reagendar` | `PATCH /agent-tools/schedulings/{id}/reschedule` | Reagendar |
| `consultar_meus_agendamentos` | `GET /agent-tools/schedulings` | Listar agendamentos do cliente |

## Deployment

Ver documento `09-deployment.md` para detalhes de HTTPS público, reverse proxy e variáveis de ambiente.
