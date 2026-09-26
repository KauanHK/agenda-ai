# Backend

## Agente

Agente de IA que atende clientes pelo Telegram e agenda pelo MCP. Mora em
`app/modules/agent/` e roda como processo próprio (`app.main_agent`), com a mesma
imagem da API. A documentação está em [`docs/agente/`](docs/agente/), começando por
[`00-visao-geral.md`](docs/agente/00-visao-geral.md).

A configuração vem do `.env` da raiz, nas variáveis `AGENT_*` (ver a seção "Agente de
IA" do `.env.example`).

```bash
uv sync --all-extras

# servidor (precisa de um Redis em AGENT_REDIS__URL)
uv run uvicorn app.main_agent:app --reload --port 8002

# conversa com o agente no terminal, sem Telegram
uv run python -m scripts.agent.repl --establishment-id <uuid>
uv run python -m scripts.agent.repl --establishment-id <uuid> --memory   # sem Redis

# emite uma sessão e lista as tools do MCP
uv run python -m scripts.agent.smoke_mcp --establishment-id <uuid>
```

Os scripts rodam contra o ambiente real e não fazem parte da suíte. O estabelecimento
precisa ter um bot conectado (o fuso vem do diretório de canais).

O webhook de cada bot é registrado pelo backend ao conectar o bot
(`PUT /api/establishments/{id}/channels/telegram`), em
`{TELEGRAM_WEBHOOK_BASE_URL}/webhook/telegram/{establishment_id}`.
