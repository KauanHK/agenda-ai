# 01 — Arquitetura

## Princípios

1. **Uma responsabilidade por função.** Toda função faz uma coisa e o nome dela diz
   qual. Se a docstring precisa de um "e", provavelmente são duas funções.
2. **Dependências apontam para dentro.** `interfaces` → `application` → `domain`.
   `infrastructure` implementa portas de `application` e é injetada de fora.
3. **`domain` e `application` não importam biblioteca de terceiro de I/O.** Nada de
   `httpx`, `redis`, `telegram`, `langgraph` ou `langchain` nessas camadas.
4. **Composição num único lugar.** Só o *composition root* (`main.py` / `container.py`)
   conhece as classes concretas; ninguém mais instancia infraestrutura.
5. **Erros de fora viram erros do domínio na fronteira.** Um `httpx.HTTPStatusError`
   nunca sobe além do adapter que o produziu.

## Camadas

```
┌───────────────────────────────────────────────────────────────┐
│ interfaces/   webhook do Telegram, healthcheck                │
│               traduz HTTP ↔ comando de use case               │
├───────────────────────────────────────────────────────────────┤
│ application/  use cases + portas (Protocol)                   │
│               orquestra, não conhece tecnologia               │
├───────────────────────────────────────────────────────────────┤
│ domain/       entidades e erros do agente                     │
│               puro, sem I/O                                   │
├───────────────────────────────────────────────────────────────┤
│ infrastructure/ MCP, LLM, LangGraph, Redis, Telegram          │
│                 implementa as portas                          │
└───────────────────────────────────────────────────────────────┘
```

> O LangGraph vive em `infrastructure`, não em `application`. O grafo é *um detalhe de
> implementação* da porta `AgentRunnerProtocol`: trocar LangGraph por outra orquestração
> não deve tocar em nenhum use case.

## Estrutura de pastas

```
agente-agenda/
├── docs/                             # estas specs
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── src/
│   ├── main.py                       # entrypoint uvicorn
│   ├── container.py                  # composition root: monta as dependências
│   ├── settings.py                   # pydantic-settings
│   ├── logging_config.py             # logging estruturado JSON (só stdlib)
│   │
│   ├── domain/
│   │   ├── entities.py               # Contact, IncomingMessage, AgentAnswer, ...
│   │   └── exceptions.py             # AgentError e subclasses
│   │
│   ├── application/
│   │   ├── ports/
│   │   │   ├── agent_runner.py       # AgentRunnerProtocol
│   │   │   ├── booking_session.py    # BookingSessionIssuerProtocol
│   │   │   ├── session_cache.py      # SessionTokenCacheProtocol
│   │   │   ├── tool_provider.py      # BookingToolProviderProtocol
│   │   │   ├── phone_resolver.py     # PhoneResolverProtocol
│   │   │   └── messenger.py          # OutboundMessengerProtocol
│   │   └── use_cases/
│   │       ├── handle_incoming_message.py
│   │       ├── open_booking_session.py
│   │       └── reset_conversation.py
│   │
│   ├── infrastructure/
│   │   ├── booking/
│   │   │   └── session_issuer.py     # CustomerSessionIssuer no próprio processo
│   │   ├── mcp_client/
│   │   │   └── tool_provider.py      # langchain-mcp-adapters → tools autenticadas
│   │   ├── llm/
│   │   │   └── factory.py            # build_chat_model() por provider
│   │   ├── agent/
│   │   │   ├── state.py              # ConversationState (TypedDict)
│   │   │   ├── prompts.py            # system prompt
│   │   │   ├── nodes/
│   │   │   │   ├── call_model.py
│   │   │   │   └── call_tools.py
│   │   │   ├── graph.py              # build_graph(): monta e compila
│   │   │   └── runner.py             # LangGraphAgentRunner (implementa a porta)
│   │   ├── redis/
│   │   │   ├── client.py
│   │   │   ├── checkpointer.py       # AsyncRedisSaver
│   │   │   └── session_cache.py      # cache do session_token
│   │   ├── identity/
│   │   │   └── synthetic_phone.py    # chat_id → telefone determinístico
│   │   └── telegram/
│   │       ├── client.py             # sendMessage / sendChatAction
│   │       ├── update_parser.py      # payload cru → IncomingMessage
│   │       ├── formatting.py         # texto do LLM → MarkdownV2 seguro
│   │       └── webhook_registry.py   # setWebhook / getWebhookInfo
│   │
│   └── interfaces/
│       └── http/
│           ├── app.py                # create_app(): FastAPI + lifespan
│           ├── dependencies.py       # injeta o container nos endpoints
│           └── routes/
│               ├── admin.py          # /admin/telegram/webhook (Bearer)
│               ├── health.py
│               └── telegram.py       # POST /webhook/telegram/{secret}
└── tests/
    ├── domain/
    ├── application/
    ├── infrastructure/
    └── interfaces/
```

## Regras de dependência (verificáveis)

| Módulo | Pode importar |
| --- | --- |
| `domain` | só stdlib |
| `application.ports` | `domain` + stdlib + `typing` |
| `application.use_cases` | `domain`, `application.ports` |
| `infrastructure.*` | `domain`, `application.ports`, libs externas |
| `interfaces.*` | `domain` (só para traduzir erros em HTTP), `application`, `container`, `fastapi` |
| `container` | tudo |
| `logging_config` | só stdlib (importável por qualquer camada) |

Um teste de arquitetura (`tests/modules/agent/test_dependencies.py`) percorre os imports com `ast` e
falha se a tabela acima for violada.

## Fronteiras de erro

| Origem | Adapter que traduz | Erro de domínio |
| --- | --- | --- |
| HTTP do AgendaBot | `session_issuer.py` | `BookingSessionError` |
| Tool MCP | `tool_provider.py` / nó de tools | devolvido ao LLM como texto, não levanta |
| Redis fora | `redis/*` | `ConversationStateError` |
| API do Telegram | `telegram/client.py` | `DeliveryError` |
| `setWebhook` / `getWebhookInfo` | `telegram/webhook_registry.py` | `WebhookRegistrationError` (→ `502` em `routes/admin.py`) |
| LLM | `agent/runner.py` | `AgentUnavailableError` |
