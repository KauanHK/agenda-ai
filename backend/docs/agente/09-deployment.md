# 09 — Deployment

## Topologia em produção

```
                    ┌───────────────────────────────────────┐
Cliente WhatsApp ──→│ Evolution API (uma instância por est.)│
                    └──────────────┬────────────────────────┘
                                   │ webhook HTTPS
                                   ▼
                    ┌─────────────────────────────┐
                    │ api.agendabot.com.br        │
                    │ (FastAPI :8000)             │
                    └────┬──────────────────┬─────┘
                         │                  │
                         │ OpenAI Responses │ chama mcp em tool calls
                         │ API              │
                         ▼                  │
                    ┌─────────────┐         │
                    │ OpenAI      │─────────┘ via mcp_servers[].url
                    └─────────────┘
                                            ▼
                              ┌──────────────────────────┐
                              │ mcp.agendabot.com.br     │
                              │ (FastMCP :8001 público)  │
                              └────────────┬─────────────┘
                                           │ HTTP interno
                                           ▼
                              api.agendabot.com.br/agent-tools/*
```

## Requisitos críticos

### MCP server precisa ser público

A OpenAI conecta ao MCP server **durante a inferência** — não há proxy intermediário possível. Isso significa:

- HTTPS obrigatório com certificado válido
- Domínio público apontando para o servidor
- Firewall liberado para entrada na porta do MCP server

### MCP server NÃO precisa ser acessível externamente para qualquer um

Mesmo público, a entrada é protegida pelo `MCP_INCOMING_SECRET` validado no header `X-MCP-Key`. Apenas requests com esse header válido (vindas da OpenAI configurada pela FastAPI) são aceitas.

Considere adicionar allowlist de IPs da OpenAI como camada extra quando essa lista estiver publicamente documentada.

## Reverse proxy

Recomendado: Caddy ou Nginx para terminar HTTPS e rotear para os processos.

Exemplo Caddyfile mínimo:

```
api.agendabot.com.br {
    reverse_proxy localhost:8000
}

mcp.agendabot.com.br {
    reverse_proxy localhost:8001
}
```

Caddy resolve Let's Encrypt automaticamente. Nginx exige `certbot` separado.

## Docker Compose

Mesmo Dockerfile, comandos diferentes. Como decidimos repositórios separados, cada um tem seu próprio compose.

`agendabot-api/docker-compose.yml`:

```yaml
services:
  api:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [redis, postgres]

  worker:
    build: .
    command: celery -A app.worker worker --loglevel=info
    env_file: .env
    depends_on: [redis, postgres]

  redis:
    image: redis:7-alpine
    volumes: [redis_data:/data]

  postgres:
    image: postgres:16-alpine
    volumes: [pg_data:/var/lib/postgresql/data]
    env_file: .env

volumes:
  redis_data:
  pg_data:
```

`agendabot-mcp/docker-compose.yml`:

```yaml
services:
  mcp:
    build: .
    command: uvicorn src.main:app --host 0.0.0.0 --port 8001
    ports: ["8001:8001"]
    env_file: .env
```

## Variáveis de ambiente consolidadas

### agendabot-api/.env

```
# Base
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://redis:6379/0

# Auth painel (existente)
JWT_SECRET=...

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5-nano

# MCP
MCP_SERVER_URL=https://mcp.agendabot.com.br
MCP_OUTGOING_SECRET=<openssl rand -hex 32>

# Agent session
AGENT_SESSION_SECRET=<openssl rand -hex 32>
AGENT_SESSION_TTL_MINUTES=30
AGENT_HISTORY_TTL_SECONDS=1800
AGENT_HISTORY_MAX_TURNS=40

# Evolution
EVOLUTION_API_URL=https://evolution.agendabot.com.br
EVOLUTION_API_KEY=...
EVOLUTION_WEBHOOK_SECRET=...
```

### agendabot-mcp/.env

```
AGENDABOT_API_URL=https://api.agendabot.com.br
MCP_INCOMING_SECRET=<mesmo valor de MCP_OUTGOING_SECRET na api>
HTTP_TIMEOUT_SECONDS=10
```

## Health checks

Ambos os serviços devem expor `/health` para monitoramento.

FastMCP:

```python
@mcp.custom_route("/health")
async def health(request):
    return {"status": "ok"}
```

FastAPI:

```python
@app.get("/health")
async def health():
    return {"status": "ok"}
```

## Logs

Logs estruturados (JSON) em ambos os serviços, com correlação via `session_id`:

- Toda chamada ao LLM: session_id, tokens usados, latência, custo estimado
- Toda tool call: session_id, tool name, latência, success/error
- Toda escalada: session_id, motivo, timestamp

Útil para depuração e otimização futura.

## Monitoramento mínimo recomendado

- Uptime dos dois domínios (Uptime Robot, Better Stack)
- Erros 5xx no Sentry
- Métrica de custo OpenAI por dia
- Métrica de mensagens recebidas vs respondidas (taxa de sucesso)

## Backup

- Postgres: backup diário (já deve existir)
- Redis: dados de conversa são efêmeros (TTL 30 min) — não precisam backup
- MCP server: stateless, sem necessidade de backup

## Estratégia de deploy

Para mudanças no agente que afetam comportamento (system prompt, tools), preferir:

1. Deploy em ambiente staging com instância Evolution separada
2. Testar com número de teste
3. Deploy produção fora de horário comercial do nicho

Para mudanças no MCP server, deploy primeiro o MCP server e depois a API (API depende do MCP estar atualizado). Para mudanças no agente que adicionam tool, o oposto: API primeiro, MCP depois.
