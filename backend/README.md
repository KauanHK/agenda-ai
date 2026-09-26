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
uv run python -m scripts.agent.repl
uv run python -m scripts.agent.repl --memory   # sem Redis (checkpointer e cache em memória)

# emite uma sessão e lista as tools do MCP
uv run python -m scripts.agent.smoke_mcp

# registra/remove o webhook do bot apontando para um túnel HTTPS
uv run python -m scripts.agent.set_webhook https://<seu-tunel>
uv run python -m scripts.agent.delete_webhook
```

Os scripts rodam contra o ambiente real e não fazem parte da suíte.
