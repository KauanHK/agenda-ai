# agente-agenda

Agente de IA conversacional que atende clientes pelo Telegram e realiza agendamentos
consumindo o MCP server do AgendaBot (`https://agenda.escaleia.cloud/mcp`).

As especificações estão em [`docs/`](docs/) — comece por
[`docs/00-visao-geral.md`](docs/00-visao-geral.md). A ordem de implementação está em
[`docs/11-roadmap.md`](docs/11-roadmap.md).

## Desenvolvimento

```bash
uv sync --extra anthropic
cp .env.example .env        # preencha as chaves
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
```

Requer Python 3.14+ e [`uv`](https://docs.astral.sh/uv/).

## Servidor

Com um Redis de pé em `REDIS__URL`:

```bash
uv run uvicorn src.main:app --reload --port 8080
```

`GET /health` responde `{"status": "ok"}` enquanto o processo está de pé
(*liveness*, usado pelo healthcheck do container). `GET /health/ready` é
*readiness*: dá `PING` no Redis e responde `200` com `{"redis": "ok"}` ou `503`
com `{"redis": "down"}`. O webhook do Telegram fica em
`POST /webhook/telegram/{TELEGRAM__WEBHOOK_SECRET}`. As rotas administrativas
`POST`/`GET /admin/telegram/webhook` (Bearer `TELEGRAM__ADMIN_TOKEN`) registram e
consultam o webhook direto na Bot API — ver `docs/09`.

Para subir a stack completa (nginx + api + redis) via Docker — em dev a imagem é
construída localmente e o nginx expõe a porta `8080`:

```bash
docker compose up --build
```

Em desenvolvimento, exponha a porta com um túnel HTTPS e registre o webhook:

```bash
uv run python -m scripts.set_webhook https://<seu-tunel>
uv run python -m scripts.delete_webhook   # desfaz
```

## Smoke tests manuais

Rodam contra o ambiente real, lendo o `.env`; não fazem parte da suíte.

```bash
uv run python -m scripts.smoke_mcp     # emite a sessão e lista as tools do MCP
uv run python -m scripts.repl          # conversa com o agente no terminal
uv run python -m scripts.repl --memory # sem Redis (checkpointer e cache em memória)
```
