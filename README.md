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

Requer Python 3.12+ e [`uv`](https://docs.astral.sh/uv/).
