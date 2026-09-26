# 03 — Subir o agente no stack do agenda2

**Repositório:** agenda2 · **Depende de:** 02 · **Estimativa:** ~0 linhas de regra (só infra)

## Objetivo

Colocar o agente em produção como serviço do `docker-compose.yml` do agenda2, com a mesma
imagem do backend, e desligar o stack do `agente-agenda`. O comportamento continua o
mesmo: um bot, um estabelecimento.

## Mudanças

### `docker-compose.yml` (produção)

- **Serviço `agent`:** usa o `<<: *backend`, com `container_name: agenda-bot-agent` e
  - comando `uv run --no-sync uvicorn app.main_agent:app --host 0.0.0.0 --port 8002
    --proxy-headers --forwarded-allow-ips='*'`;
  - redes `backend` e `egress` (precisa chegar ao provedor de LLM e à Bot API);
  - healthcheck em `http://localhost:8002/health`;
  - `depends_on` `agent-redis` e `mcp` saudáveis.
- **Serviço `agent-redis`:** `redis:8-alpine`, `--appendonly yes`, volume `agentredis`,
  rede `backend`, healthcheck com `redis-cli ping`.
  - Fica separado do Redis do Celery porque o checkpointer do LangGraph exige Redis 8
    (motor de busca e JSON embutidos, índices só no DB 0) e persistência, enquanto o do
    Celery é Redis 7, sem persistência e com senha.
  - Unificar os dois fica fora de escopo.
- **`nginx`** passa a depender de `agent`.

### `nginx.conf`

- `location /webhook/` → `http://agenda-bot-agent:8002`, com os mesmos `proxy_set_header`
  das outras rotas.
- **Só** `/webhook/` fica público. `/health` e `/admin/telegram/webhook` do agente
  continuam só na rede interna; os scripts rodam com `docker compose exec`.

### `docker-compose.local.yml` e `nginx.local.conf`

- Mesmos dois serviços. `agent` publica `8002` para um túnel HTTPS local (ngrok ou
  similar) e o `nginx` local ganha a mesma rota `/webhook/`.

### `.env.example`

- `AGENT_AGENDABOT__MCP_URL=http://mcp:8001/mcp`: o MCP é chamado pela rede interna, sem
  passar pelo domínio público.
- `AGENT_REDIS__URL=redis://agent-redis:6379/0`.
- `AGENT_AGENDABOT__API_URL` continua com a URL pública até a spec 04 remover a variável.
  Não dá para usar `http://api:8000`: a API roda com `--root-path /api` e o caminho
  `/api/agent/...` não bate por dentro.

### `deploy.yml`

- Nada muda. É a mesma imagem de backend, e o `docker-compose.yml` e o `nginx.conf` já
  são copiados para a VPS.

## Passo a passo da virada (no PR, como checklist)

1. **Na VPS**, copiar as variáveis do `.env` do agente antigo para `/opt/agenda-bot/.env`
   com o prefixo `AGENT_`, ajustando `AGENT_AGENDABOT__MCP_URL` e `AGENT_REDIS__URL`.
2. Merge. O deploy sobe `agent` e `agent-redis`. Nesse momento os dois agentes estão de
   pé, mas o Telegram ainda entrega no antigo.
3. `docker compose exec agent uv run --no-sync python -m scripts.agent.set_webhook
   https://agenda.escaleia.cloud`: o Telegram passa a entregar no host novo, com o
   mesmo segredo e o mesmo caminho `/webhook/telegram/{segredo}`.
4. Mandar uma mensagem ao bot e confirmar a resposta e o log do `agenda-bot-agent`.
5. Desligar o stack antigo (`docker compose down` no diretório do `agente-agenda`).
6. No GitHub: desabilitar os workflows de deploy e rollback do `agente-agenda` e arquivar
   o repositório, com um README apontando para `backend/app/modules/agent/`.

**Rollback:** subir o stack antigo de novo e rodar o `set_webhook` dele apontando para o
host antigo.

**Efeito conhecido:** o histórico das conversas não migra, porque o Redis é novo. O TTL
já é de 24h e expirar não é erro.

## Critérios de aceite

- `docker compose -f docker-compose.local.yml up --build` sobe `agent` saudável, e um
  `curl -X POST localhost:8080/webhook/telegram/<segredo>` com um update de exemplo
  responde `{"ok": true}`.
- Por fora, `GET https://<host>/health` **não** chega ao agente (rota do frontend) e
  `/admin/...` não é exposto.
- Em produção, depois do checklist, o bot responde pelo host novo e o stack antigo está
  parado.
