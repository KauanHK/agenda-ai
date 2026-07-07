# 08 — Escalada para humano

## Comportamento atual definido

- **Critérios de escalada:** reclamações, mais de 2 tentativas sem resolver, linguagem agressiva, solicitações fora do escopo
- **Ação:** notificar o dono do estabelecimento e **continuar a conversa**
- **Não há transferência** — o agente continua respondendo após escalar

## Implementação

### Tool dedicada

A forma mais limpa de detectar escalada é dar ao LLM uma tool que ele chama explicitamente quando uma das condições é atendida. Isso é mais robusto do que tentar inferir do texto da resposta.

`mcp_server/tools/escalation.py` (no MCP server):

```python
from fastmcp import Context
from src.auth import verify_request_origin
from src.http_client import http_client

def register_tools(mcp):
    @mcp.tool()
    async def escalar_para_humano(
        ctx: Context,
        motivo: str,
        resumo: str,
    ) -> dict:
        """
        Notifica o dono do estabelecimento sobre uma situação que precisa de atenção humana.
        Use em casos de: reclamação, 2+ tentativas sem resolver, linguagem agressiva,
        ou solicitação fora do escopo (descontos, alterações de preço, etc).

        motivo: COMPLAINT | MAX_ATTEMPTS | AGGRESSIVE | OUT_OF_SCOPE
        resumo: descrição curta da situação para o dono entender o contexto
        """
        token = verify_request_origin(ctx)
        response = await http_client.post(
            "/agent-tools/escalations",
            json={"motivo": motivo, "resumo": resumo},
            headers={"X-Session-Token": token},
        )
        return response.json()
```

### Endpoint na FastAPI

`app/modules/agent/routes/tools.py` (continuação):

```python
@router.post("/escalations")
async def create_escalation(
    payload: EscalationRequest,
    actor: Annotated[ClientAgentActor, Depends(get_session_actor)],
    uow=Depends(get_uow),
    notifier=Depends(get_owner_notifier),
):
    async with uow:
        client = await uow.clients().get_by_id(actor.client_id)
        establishment = await uow.establishments().get_by_id(
            actor.establishment_id
        )

    await notifier.notify_owner(
        establishment=establishment,
        client=client,
        motivo=payload.motivo,
        resumo=payload.resumo,
    )

    # Registrar para métricas/auditoria futura
    async with uow:
        await uow.agent_escalations().create(
            client_id=actor.client_id,
            establishment_id=actor.establishment_id,
            motivo=payload.motivo,
            resumo=payload.resumo,
        )
        await uow.commit()

    return {"success": True, "data": {"escalated": True}}
```

### Notificador

Reutilizar o mesmo cliente Evolution para enviar mensagem ao dono (cujo número está no estabelecimento):

```python
class OwnerNotifier:
    def __init__(self, evolution_client):
        self.evolution = evolution_client

    async def notify_owner(
        self,
        establishment,
        client,
        motivo: str,
        resumo: str,
    ):
        text = (
            f"⚠️ Atenção necessária\n\n"
            f"Cliente: {client.name or client.phone}\n"
            f"Motivo: {self._humanize(motivo)}\n\n"
            f"Resumo: {resumo}"
        )
        await self.evolution.send_text(
            establishment_id=establishment.id,
            to=establishment.owner_phone,
            text=text,
        )

    @staticmethod
    def _humanize(motivo: str) -> str:
        return {
            "COMPLAINT": "Reclamação do cliente",
            "MAX_ATTEMPTS": "Várias tentativas sem resolver",
            "AGGRESSIVE": "Linguagem agressiva do cliente",
            "OUT_OF_SCOPE": "Solicitação fora do escopo do agente",
        }.get(motivo, motivo)
```

## Persistência

Sugere-se criar uma tabela `agent_escalations` para auditoria e métricas:

```sql
CREATE TABLE agent_escalations (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL REFERENCES clients(id),
    establishment_id UUID NOT NULL REFERENCES establishments(id),
    motivo VARCHAR(20) NOT NULL,
    resumo TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

Útil para:

- Identificar estabelecimentos com muitas escaladas (sinal de problema)
- Identificar motivos mais comuns (sinal de gaps no agente)
- Mostrar histórico ao dono no painel

## Ajuste no system prompt

O system prompt já contém as regras de escalada. Adicionar instrução explícita para usar a tool:

> "Quando uma das condições de escalada for atendida, chame a tool `escalar_para_humano` informando o motivo e um resumo curto da situação. Em seguida, continue a conversa naturalmente — o cliente não deve saber que houve uma notificação interna."

## Limite de escaladas por sessão

Para evitar spam ao dono, considerar:

- Máximo 1 escalada por sessão (`session_id`)
- Flag no Redis com mesmo TTL da sessão:

```python
escalated_key = f"escalated:{session_id}"
already = await redis.get(escalated_key)
if already:
    return {"success": True, "data": {"escalated": False, "reason": "already_notified"}}
await redis.setex(escalated_key, 1800, "1")
```

## Considerações futuras

Quando o produto evoluir:

- **Botão "assumir conversa" no painel:** o dono visualiza a conversa em andamento e pode pausar o agente
- **Webhook de status:** o dono marca uma escalada como "resolvida" → feedback para o agente
- **Categorização automática:** classificar reclamações por tipo (serviço, atendimento, preço, etc.)
