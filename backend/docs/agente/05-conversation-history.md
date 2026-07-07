# 05 — Histórico de conversa

## Princípio

Cada conversa tem um identificador único (`session_id = phone:establishment_id`) e um histórico de mensagens persistido no Redis com TTL.

## Por que Redis

- Já está provisionado no stack (worker Celery)
- TTL nativo elimina lógica de expiração manual
- Acesso assíncrono via `redis.asyncio`
- Sem necessidade de query — sempre lookup direto por chave

## Estrutura da chave

```
chat:{phone}:{establishment_id}
```

Exemplo:
```
chat:+5547999999999:c7e8d1a2-...
```

## Formato do valor

JSON serializado contendo uma lista de mensagens no formato da OpenAI:

```json
[
  {"role": "user", "content": "Quero marcar amanhã"},
  {"role": "assistant", "content": "Claro! Para qual serviço?"},
  {"role": "user", "content": "Corte de cabelo"}
]
```

> Mensagens de tool call/result não são persistidas no histórico — apenas turnos `user` e `assistant`. Isso mantém o histórico limpo e dentro do limite de tokens.

## Implementação

`app/modules/agent/history.py`:

```python
import json
from redis.asyncio import Redis

class ConversationHistory:
    def __init__(self, redis: Redis, ttl_seconds: int = 1800):
        self.redis = redis
        self.ttl = ttl_seconds  # 30 minutos

    def _key(self, session_id: str) -> str:
        return f"chat:{session_id}"

    async def load(self, session_id: str) -> list[dict]:
        raw = await self.redis.get(self._key(session_id))
        if not raw:
            return []
        return json.loads(raw)

    async def save(
        self,
        session_id: str,
        history: list[dict],
    ) -> None:
        # Trim para evitar que cresça indefinidamente
        trimmed = history[-40:]  # últimos 40 turnos
        await self.redis.setex(
            self._key(session_id),
            self.ttl,
            json.dumps(trimmed, ensure_ascii=False),
        )

    async def clear(self, session_id: str) -> None:
        await self.redis.delete(self._key(session_id))
```

## Limite de turnos

O `trimmed = history[-40:]` mantém apenas os últimos 40 turnos (20 pares user+assistant). Razões:

- GPT-5-nano tem janela limitada
- Conversas de agendamento raramente passam de 10-15 turnos
- Mensagens muito antigas raramente são relevantes para o turno atual

Se for ajustar, considere o trade-off entre custo de tokens e qualidade de contexto.

## Reset de sessão

O TTL de 30 minutos significa que após 30 minutos de inatividade, a conversa começa do zero. Isso é desejável para WhatsApp — um cliente que volta no dia seguinte não deveria ter contexto de uma conversa antiga sobre outro agendamento.

Se quiser permitir reset manual (cliente diz "esquece tudo"), implementar como tool ou como detecção de palavra-chave no router antes de chamar o agente.

## Considerações sobre concorrência

Se o mesmo cliente enviar duas mensagens em sequência muito rápida, há risco de race condition no save (a segunda mensagem sobrescreve o save da primeira sem incluí-la).

Mitigação simples: usar `WATCH/MULTI/EXEC` do Redis ou um lock distribuído com TTL curto (5s) por session_id. Para o volume inicial, provavelmente não é necessário — registrar como ponto de atenção para escala.

## Variáveis de ambiente

```
REDIS_URL=redis://localhost:6379/0
AGENT_HISTORY_TTL_SECONDS=1800
AGENT_HISTORY_MAX_TURNS=40
```
