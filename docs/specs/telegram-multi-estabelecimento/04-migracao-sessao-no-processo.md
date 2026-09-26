# 04 — Sessão emitida no próprio processo

**Repositório:** agenda2 · **Depende de:** 03 · **Estimativa:** ~70 linhas

## Objetivo

O agente passa a emitir o token de sessão do cliente chamando `CustomerSessionIssuer`
diretamente, com o banco, em vez de `POST /api/agent/{id}/sessions` com `X-Service-Key`.
Com isso, o endpoint e a chave de serviço deixam de ter consumidor e saem.

## Contexto

- O endpoint existia para um "orquestrador do WhatsApp" externo. Hoje o único consumidor
  é o agente (verificado com grep no agenda2: frontend, compose e `.env.example`).
- Um endpoint que troca telefone por identidade, protegido só por uma chave compartilhada,
  é uma superfície de ataque que já não se justifica.
- O MCP continua público em `/mcp` e continua sendo a fronteira: o agente chama as tools
  com o token de sessão, como antes.

## Mudanças

### Agente

- **`adapters/booking/session_issuer.py` → `InProcessSessionIssuer`**, que implementa
  `BookingSessionIssuerProtocol`:
  - Chama `CustomerSessionIssuer(make_unit_of_work()).issue(...)` e monta o
    `BookingSession`, com `expires_at = clock() + MCP_SESSION_TOKEN_EXPIRES_MINUTES`
    (a mesma conta que o router faz hoje).
  - Traduz erros para o domínio do agente:

    | Erro do backend | Vira |
    |---|---|
    | `ForbiddenError` (cliente inativo) | `ClientBlockedError` |
    | `ValueError` (telefone inválido) | `InvalidPhoneError` |
    | `ConflictError` (cliente criado ao mesmo tempo por duas mensagens) | **uma** nova tentativa; se falhar de novo, `BookingSessionError` |
    | `NotFoundError` (estabelecimento inexistente ou inativo), `SQLAlchemyError`, `OSError` | `BookingSessionError` |

  - Nenhuma exceção de banco passa daqui para cima.
- **Container:** o lifespan abre e fecha o pool do banco (`db.init()` e `db.close()` no
  `AsyncExitStack`), como o `app/mcp/server.py` já faz.
- **Removidos:**
  - `adapters/agendabot/http_client.py` e `session_issuer.py`, com os testes;
  - as settings `agendabot.api_url` e `agendabot.service_key`.
- **Renomeado:** `adapters/agendabot/` (agora só com `tool_provider.py`) vira
  `adapters/mcp_client/`.
- **Scripts:** `scripts/agent/smoke_mcp.py` e `repl.py` usam o emissor novo.

### Backend

- **Removidos:**
  - `app/modules/booking/adapters/http/router.py`, `schemas.py` e `dependencies.py`
    (`require_service_key`, `ServiceKeyDep`, `BookingUnitOfWorkDep`, se não tiver outro
    uso), com os testes;
  - o `include_router` de `/agent` em `app/api/router.py`;
  - `AGENT_SERVICE_KEY` de `app/core/settings.py`.
- Docstrings que citam o endpoint (`app/mcp/auth.py`, `booking/.../sessions.py`) passam a
  citar o agente.

### Configuração

- `.env.example`: saem `AGENT_SERVICE_KEY`, `AGENT_AGENDABOT__API_URL` e
  `AGENT_AGENDABOT__SERVICE_KEY`.

## Testes

- `InProcessSessionIssuer` com um `CustomerSessionIssuer` falso (ou um UoW falso),
  cobrindo:
  - sucesso: token, `client_id`, nome e `is_new_client` repassados; `expires_at`
    calculado pelo relógio injetado;
  - cada linha da tabela de erros;
  - `ConflictError` seguido de sucesso: uma nova tentativa e retorna a sessão.
- O teste de API do router removido sai junto. `CustomerSessionIssuer` continua coberto
  pelos testes que já existem.

## Critérios de aceite

- `rg "X-Service-Key|AGENT_SERVICE_KEY|/agent/\{"` não encontra nada no código.
- `smoke_mcp` emite a sessão e lista as tools contra o ambiente local.
- Em produção, o bot marca um horário de ponta a ponta.

## Deploy

1. Deploy normal.
2. Depois de confirmar o bot, remover da VPS `AGENT_SERVICE_KEY`,
   `AGENT_AGENDABOT__API_URL` e `AGENT_AGENDABOT__SERVICE_KEY`.
