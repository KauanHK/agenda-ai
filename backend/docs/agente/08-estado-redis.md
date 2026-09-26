# 08 — Estado no Redis

Um Redis, dois usos independentes, prefixos separados.

## 8.1 Checkpointer do LangGraph

Pacote: `langgraph-checkpoint-redis` (`AsyncRedisSaver`).

- Instanciado **uma vez** no lifespan da aplicação e passado ao
  `graph.compile(checkpointer=...)`.
- `thread_id` = `ConversationRef.thread_id` = `telegram:{establishment_id}:{chat_id}`.
- Índices criados no startup (`await saver.asetup()`).

### TTL

O histórico de uma conversa de agendamento não tem valor após alguns dias, e guardar
para sempre transforma o Redis em banco.

- `CONVERSATION_TTL_MINUTES` (default `1440`, 24 h) aplicado via a configuração de TTL
  do próprio saver, renovado a cada escrita.
- Expirar não é erro: a próxima mensagem começa uma conversa nova. O prompt deve
  suportar isso sem estranhar (por isso o contexto de "cliente novo" vem do
  `is_new_client` da sessão, não do histórico).

### Poda do histórico

Uma thread longa estoura a janela de contexto e o custo por turno. Antes de chamar o
modelo, o histórico é limitado aos `MAX_HISTORY_TURNS` (default 10) turnos mais
recentes — um turno é um `HumanMessage` e tudo que o agente produziu em resposta
(tool calls, resultados, resposta final):

```python
def trim_history(messages: list[AnyMessage], limit: int) -> list[AnyMessage]:
    """Mantém os últimos `limit` turnos: cada `HumanMessage` e tudo que vem depois dele."""
```

A unidade é o turno, e não a mensagem, porque um único turno com várias consultas
de agenda gera dez ou mais mensagens; contar mensagens deixaria o modelo ver os
resultados das tools sem a pergunta que os motivou. Cortar no `HumanMessage`
também garante que nenhum `AIMessage` que pediu tools fica separado dos seus
`ToolMessage`.

Pelo mesmo motivo, o "primeiro contato" do contexto do turno só é enviado no
primeiro turno da thread (`is_first_turn`): a sessão fica em cache e continuaria
dizendo `is_new_client` em toda mensagem, e o modelo lê isso como ordem de
cumprimentar de novo.

Função pura, testável isoladamente. A regra que importa: um `AIMessage` com
`tool_calls` nunca fica sem os `ToolMessage` dele, e um `ToolMessage` nunca aparece sem
o `AIMessage` que o pediu — cortar no meio disso faz a API do provider rejeitar a
requisição.

## 8.2 Cache do token de sessão

`app/modules/agent/adapters/redis/session_cache.py`

- Chave: `agente:session:{establishment_id}:{sha256(phone)}` — o telefone não vai em
  claro na chave, e o mesmo telefone em dois estabelecimentos são duas sessões.
- Valor: JSON com `token`, `client_id`, `client_name`, `expires_at`, `is_new_client`.
- TTL: `expires_in_minutes - SESSION_REFRESH_MARGIN_SECONDS` (default 60 s de margem),
  no mínimo 1 s. Assim uma entrada cacheada é sempre utilizável quando lida.
- Miss e falha de Redis são equivalentes para quem chama: devolve `None` e o
  `BookingSessionProvider` emite um token novo. Cache indisponível degrada
  performance, não funcionalidade — por isso o `get`/`put` do cache engolem erro de
  conexão e logam em `warning`.

> Diferente do checkpointer: **ali** uma falha de Redis é `ConversationStateError`, pois
> perder o histórico muda o comportamento do agente de forma visível ao cliente.

## 8.3 Namespaces

| Prefixo | Uso | Dono |
| --- | --- | --- |
| `checkpoint*` | histórico das conversas | `langgraph-checkpoint-redis` |
| `agente:session:*` | tokens de sessão | `session_cache.py` |

Redis DB dedicado (`REDIS_URL` com `/1`, por exemplo) para não dividir keyspace com
outro serviço.
