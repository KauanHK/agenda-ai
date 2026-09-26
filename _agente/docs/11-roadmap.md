# 11 — Roadmap de implementação

Ordem pensada para que cada etapa seja verificável sozinha, antes de a próxima começar.

## Etapa 1 — Fundação
`pyproject.toml`, `settings.py`, `.env.example`, layout de pastas, `ruff`/`mypy`,
`domain/entities.py`, `domain/exceptions.py`, e os testes do domínio.
**Pronto quando:** `mypy --strict` e `pytest` passam num projeto que ainda não faz nada.

## Etapa 2 — Sessão no AgendaBot
`http_client.py`, `session_issuer.py`, `SyntheticPhoneResolver`, `session_cache.py`,
`BookingSessionProvider` e o `scripts/smoke_mcp.py` (só a parte da sessão).
**Pronto quando:** o script emite um `session_token` real do estabelecimento fixo.

## Etapa 3 — Tools MCP
`tool_provider.py` com `langchain-mcp-adapters`; `smoke_mcp.py` completo.
**Pronto quando:** o script lista as 6 tools com seus schemas, autenticado.

## Etapa 4 — Grafo
`state.py`, `prompts.py`, os dois nós, `graph.py`, `runner.py`, `llm/factory.py`,
checkpointer Redis, `trim_history`.
**Pronto quando:** um script de REPL no terminal agenda de ponta a ponta, sem Telegram.

## Etapa 5 — Telegram
`update_parser.py`, `client.py`, `formatting.py`, rotas, comandos, `container.py`,
`main.py`, `scripts/set_webhook.py`.
**Pronto quando:** uma conversa real no Telegram marca, consulta, reagenda e cancela.

## Etapa 6 — Robustez
Retry e timeouts revisados, logging estruturado, `Dockerfile`, `docker-compose.yml`,
CI, teste de arquitetura.
**Pronto quando:** sobe em produção atrás do nginx, com healthcheck verde.
**Plano detalhado (uma PR por implementação):** [`12-plano-etapa-6.md`](12-plano-etapa-6.md).

## Depois (não nesta fase)
1. Identidade real via `request_contact` — troca só o adapter da porta.
2. WhatsApp como segundo canal — novo adapter de entrada/saída, mesmo grafo.
3. `establishment_id` por canal, para multi-estabelecimento.
4. Observabilidade do LLM (LangSmith ou equivalente).
5. Debounce de mensagens em rajada, agrupando um turno por cliente.
