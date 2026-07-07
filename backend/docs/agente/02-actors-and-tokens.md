# 02 — Actors e tokens de sessão

## ClientAgentActor

Conceito específico do agente, distinto do `Actor` existente do painel.

**Localização:** `app/modules/agent/actors.py`

```python
import uuid
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class ClientAgentActor:
    client_id: uuid.UUID
    establishment_id: uuid.UUID
    phone: str
```

**Por que separado do `Actor`:** o `Actor` representa um usuário autenticado do painel com múltiplos memberships. O `ClientAgentActor` representa um cliente em uma sessão de WhatsApp em um único estabelecimento. São identidades fundamentalmente diferentes.

**Extensão futura (canal interno):** ao implementar staff, criar `StaffAgentActor` no mesmo arquivo, com `user_id`, `establishment_id` e `role`. O `AgentRunner` aceitará `ClientAgentActor | StaffAgentActor`.

## Token de sessão

JWT assinado pela FastAPI no momento do recebimento do webhook, repassado para o MCP server via header e validado em cada tool call.

### Payload

```python
{
    "type": "client",
    "client_id": "uuid-string",
    "establishment_id": "uuid-string",
    "phone": "+5547999999999",
    "exp": 1234567890,  # now + 30 min
    "iat": 1234567890,
}
```

### Características

- **Algoritmo:** HS256
- **Secret:** dedicado, separado do JWT do painel (`AGENT_SESSION_SECRET` no `.env`)
- **TTL:** 30 minutos
- **Regeração:** a cada mensagem recebida, sem custo adicional (lookup já está sendo feito)
- **Não persistido:** vive apenas em memória durante a chamada à OpenAI

### Por que secret separado

Comprometer o secret do agente não compromete sessões do painel, e vice-versa. Token do agente tem propósito, TTL e escopo diferentes do JWT do painel.

## Geração

**Localização:** `app/modules/agent/tokens.py`

```python
import jwt
from datetime import datetime, timedelta
from app.modules.agent.actors import ClientAgentActor

TTL_MINUTES = 30

def issue_session_token(actor: ClientAgentActor, secret: str) -> str:
    now = datetime.utcnow()
    payload = {
        "type": "client",
        "client_id": str(actor.client_id),
        "establishment_id": str(actor.establishment_id),
        "phone": actor.phone,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=TTL_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm="HS256")
```

## Validação

Implementada como dependência FastAPI, aplicada às rotas consumidas pelo MCP server.

**Localização:** `app/modules/agent/dependencies.py`

```python
from typing import Annotated
from fastapi import Header, HTTPException
import jwt
from app.modules.agent.actors import ClientAgentActor
from app.core.config import settings

def get_session_actor(
    x_session_token: Annotated[str, Header()],
) -> ClientAgentActor:
    try:
        payload = jwt.decode(
            x_session_token,
            settings.AGENT_SESSION_SECRET,
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Session token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid session token")

    if payload.get("type") != "client":
        raise HTTPException(403, "Token type not allowed for this scope")

    return ClientAgentActor(
        client_id=UUID(payload["client_id"]),
        establishment_id=UUID(payload["establishment_id"]),
        phone=payload["phone"],
    )
```

## Princípio de segurança crítico

**Os endpoints consumidos pelo MCP server NUNCA devem aceitar `client_id` ou `establishment_id` como parâmetros.** Esses valores vêm exclusivamente do token validado.

Exemplo: a rota `POST /agent-tools/schedulings` recebe apenas `service_id` e `scheduled_at` no body — `client_id` e `establishment_id` vêm de `Depends(get_session_actor)`.

Isso elimina prompt injection como vetor de ataque: ainda que o LLM gerasse parâmetros maliciosos, eles seriam ignorados.

## Variáveis de ambiente

```
AGENT_SESSION_SECRET=<gerar com `openssl rand -hex 32`>
AGENT_SESSION_TTL_MINUTES=30
```
