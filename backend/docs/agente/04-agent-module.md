# 04 — Módulo agent na FastAPI

## Localização

```
app/modules/agent/
├── __init__.py
├── router.py              # webhook + rotas /agent-tools/*
├── runner.py              # AgentRunner
├── context.py             # carregamento de contexto
├── actors.py              # ClientAgentActor
├── tokens.py              # issue_session_token
├── dependencies.py        # get_session_actor
├── history.py             # ConversationHistory (Redis)
├── prompts.py             # build_system_prompt
├── escalation.py          # detecção e ação de escalada
├── errors.py              # tradução de exceções para envelope
└── routes/
    ├── __init__.py
    └── tools.py           # endpoints consumidos pelo MCP server
```

## AgentRunner

Orquestra a chamada à OpenAI. Único ponto de contato com o LLM.

`app/modules/agent/runner.py`:

```python
from openai import AsyncOpenAI
from app.modules.agent.actors import ClientAgentActor
from app.modules.agent.context import AgentContext
from app.modules.agent.history import ConversationHistory
from app.modules.agent.prompts import build_system_prompt
from app.modules.agent.tokens import issue_session_token

class AgentRunner:
    def __init__(
        self,
        openai_client: AsyncOpenAI,
        history: ConversationHistory,
        settings,
    ):
        self.openai = openai_client
        self.history = history
        self.settings = settings

    async def run(
        self,
        actor: ClientAgentActor,
        context: AgentContext,
        message: str,
    ) -> str:
        history = await self.history.load(context.session_id)
        history.append({"role": "user", "content": message})

        token = issue_session_token(
            actor,
            secret=self.settings.AGENT_SESSION_SECRET,
        )

        response = await self.openai.responses.create(
            model=self.settings.OPENAI_MODEL,  # "gpt-5-nano"
            instructions=build_system_prompt(context),
            input=history,
            tools=[{
                "type": "mcp",
                "server_label": "agendabot",
                "server_url": self.settings.MCP_SERVER_URL,
                "headers": {
                    "X-Session-Token": token,
                    "X-MCP-Key": self.settings.MCP_OUTGOING_SECRET,
                },
            }],
        )

        reply = response.output_text
        history.append({"role": "assistant", "content": reply})
        await self.history.save(context.session_id, history)

        return reply
```

> **Atenção:** o nome exato dos campos da OpenAI Responses API (`tools`, `server_url`, etc.) deve ser confirmado na documentação atual ao implementar. Este código é estrutural.

## Carregamento de contexto

`app/modules/agent/context.py`:

```python
from dataclasses import dataclass
from uuid import UUID

@dataclass(frozen=True, slots=True)
class AgentContext:
    establishment_name: str
    establishment_type: str
    establishment_city: str
    client_first_name: str
    session_id: str

async def load_context(
    actor: ClientAgentActor,
    uow,
) -> AgentContext:
    async with uow:
        client = await uow.clients().get_by_id(actor.client_id)
        establishment = await uow.establishments().get_by_id(
            actor.establishment_id
        )

    return AgentContext(
        establishment_name=establishment.name,
        establishment_type=establishment.type or "estabelecimento",
        establishment_city=establishment.city or "",
        client_first_name=(client.name or "").split()[0] or "você",
        session_id=f"{actor.phone}:{actor.establishment_id}",
    )
```

## Resolução de cliente

`app/modules/agent/context.py` (continuação):

```python
async def resolve_or_create_client(
    phone: str,
    establishment_id: UUID,
    uow,
) -> ClientAgentActor:
    async with uow:
        client = await uow.clients().find_by_phone(
            phone=phone,
            establishment_id=establishment_id,
        )
        if not client:
            client = await uow.clients().create(
                phone=phone,
                establishment_id=establishment_id,
                name=None,
            )
            await uow.commit()

    return ClientAgentActor(
        client_id=client.id,
        establishment_id=establishment_id,
        phone=phone,
    )
```

## Router principal

`app/modules/agent/router.py`:

```python
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, Request, HTTPException
from app.modules.agent.context import (
    load_context,
    resolve_or_create_client,
)
from app.modules.agent.runner import AgentRunner
from app.modules.agent.dependencies import (
    verify_evolution_webhook,
    get_agent_runner,
    get_uow,
    get_evolution_client,
)

router = APIRouter(prefix="/agent", tags=["agent"])

@router.post(
    "/{establishment_id}/message",
    dependencies=[Depends(verify_evolution_webhook)],
)
async def receive_message(
    establishment_id: UUID,
    payload: dict,
    runner: Annotated[AgentRunner, Depends(get_agent_runner)],
    uow=Depends(get_uow),
    evolution=Depends(get_evolution_client),
):
    # Extrair telefone e texto do payload da Evolution API
    phone = payload["data"]["key"]["remoteJid"]
    message = payload["data"]["message"]["conversation"]

    # Resolver cliente e contexto
    actor = await resolve_or_create_client(
        phone=phone,
        establishment_id=establishment_id,
        uow=uow,
    )
    context = await load_context(actor, uow)

    # Executar agente
    reply = await runner.run(actor, context, message)

    # Enviar resposta via Evolution API
    await evolution.send_text(
        establishment_id=establishment_id,
        to=phone,
        text=reply,
    )

    return {"status": "ok"}
```

## Rotas consumidas pelo MCP server

`app/modules/agent/routes/tools.py`:

```python
from typing import Annotated
from datetime import datetime
from fastapi import APIRouter, Depends
from app.modules.agent.actors import ClientAgentActor
from app.modules.agent.dependencies import get_session_actor
from app.modules.agent.errors import to_envelope
from app.modules.schedulings.use_cases import (
    SchedulingsCreator,
    SchedulingsCanceller,
    SchedulingsReader,
)

router = APIRouter(prefix="/agent-tools", tags=["agent-tools"])

@router.post("/schedulings")
async def create_scheduling(
    payload: CreateSchedulingRequest,
    actor: Annotated[ClientAgentActor, Depends(get_session_actor)],
    uow=Depends(get_uow),
):
    try:
        result = await SchedulingsCreator(uow).execute(
            client_id=actor.client_id,
            establishment_id=actor.establishment_id,
            service_id=payload.service_id,
            scheduled_at=payload.scheduled_at,
        )
        return {
            "success": True,
            "data": {
                "scheduling_id": str(result.id),
                "scheduled_at": result.scheduled_at.isoformat(),
            },
        }
    except DomainError as e:
        return to_envelope(e)
```

**Crítico:** `client_id` e `establishment_id` vêm do `actor` (token validado), não do payload. O LLM nunca consegue passar esses valores.

## Tradução de erros

`app/modules/agent/errors.py`:

```python
from app.core.exceptions import (
    SlotUnavailableError,
    EstablishmentClosedError,
    SchedulingNotFoundError,
    NotEnoughTimeError,
)

ERROR_MAP = {
    SlotUnavailableError: ("SLOT_UNAVAILABLE", "Esse horário já foi reservado"),
    EstablishmentClosedError: ("ESTABLISHMENT_CLOSED", "Estabelecimento fechado nesta data"),
    SchedulingNotFoundError: ("NOT_FOUND", "Agendamento não encontrado"),
    NotEnoughTimeError: ("NOT_ENOUGH_TIME", "Não há tempo suficiente para este serviço no horário escolhido"),
}

def to_envelope(exception: Exception) -> dict:
    error_class = type(exception)
    code, message = ERROR_MAP.get(
        error_class,
        ("INTERNAL_ERROR", "Tive um probleminha aqui, tente novamente"),
    )
    return {
        "success": False,
        "error_code": code,
        "message": message,
        "details": getattr(exception, "details", {}),
    }
```

Adapte a `ERROR_MAP` aos nomes reais das suas exceções de domínio.

## Variáveis de ambiente adicionais

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5-nano
MCP_SERVER_URL=https://mcp.agendabot.com.br
MCP_OUTGOING_SECRET=<openssl rand -hex 32>  # mesmo valor que MCP_INCOMING_SECRET no MCP server
AGENT_SESSION_SECRET=<openssl rand -hex 32>
EVOLUTION_WEBHOOK_SECRET=<configurado na Evolution API>
```
