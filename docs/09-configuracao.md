# 09 — Configuração e deploy

## 9.1 Settings

`src/settings.py`, um único `BaseSettings`. Ninguém mais no projeto lê `os.environ`.
A config é dividida em grupos aninhados; no ambiente cada grupo é um prefixo separado
por `__` (`env_nested_delimiter="__"`).

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_nested_delimiter="__", extra="ignore",
    )

    agendabot: AgendaBotSettings
    telegram: TelegramSettings
    redis: RedisSettings
    llm: LLMSettings = LLMSettings()
    conversation: ConversationSettings = ConversationSettings()
    identity: IdentitySettings = IdentitySettings()
    http: HTTPSettings = HTTPSettings()
    observability: ObservabilitySettings = ObservabilitySettings()
```

| Variável | Tipo | Default | Uso |
| --- | --- | --- | --- |
| `AGENDABOT__API_URL` | str | — | base da API |
| `AGENDABOT__MCP_URL` | str | — | endpoint MCP |
| `AGENDABOT__SERVICE_KEY` | `SecretStr` | — | header `X-Service-Key` |
| `AGENDABOT__ESTABLISHMENT_ID` | `UUID` | — | fixo nesta fase |
| `AGENDABOT__ESTABLISHMENT_TIMEZONE` | str | `America/Sao_Paulo` | data/hora do prompt |
| `TELEGRAM__BOT_TOKEN` | `SecretStr` | — | Bot API |
| `TELEGRAM__WEBHOOK_SECRET` | `SecretStr` | — | path secreto do webhook |
| `TELEGRAM__API_ROOT` | str | `https://api.telegram.org` | raiz da Bot API (Local Bot API Server / testes) |
| `REDIS__URL` | str | — | checkpointer + cache |
| `LLM__PROVIDER` | `Literal["anthropic","openai"]` | `anthropic` | provider |
| `LLM__MODEL` | str | `claude-sonnet-5` | modelo |
| `LLM__TEMPERATURE` | float | `0.3` | criatividade baixa: é atendimento |
| `LLM__MAX_TOKENS` | int | `1024` | resposta de chat é curta |
| `LLM__ANTHROPIC_API_KEY` | `SecretStr \| None` | `None` | exigida se provider = anthropic |
| `LLM__OPENAI_API_KEY` | `SecretStr \| None` | `None` | exigida se provider = openai |
| `CONVERSATION__TTL_MINUTES` | int | `1440` | TTL do histórico |
| `CONVERSATION__MAX_HISTORY_MESSAGES` | int | `10` | poda do histórico |
| `CONVERSATION__MAX_AGENT_STEPS` | int | `8` | teto de ciclos do grafo |
| `CONVERSATION__MAX_INPUT_CHARS` | int | `1000` | truncamento da mensagem do cliente |
| `CONVERSATION__SESSION_REFRESH_MARGIN_SECONDS` | int | `60` | margem antes de expirar |
| `IDENTITY__SYNTHETIC_PHONE_PREFIX` | str | `5547999` | identidade da fase 1 |
| `HTTP__TIMEOUT_SECONDS` | float | `10.0` | API do AgendaBot e Telegram |
| `HTTP__MCP_TIMEOUT_SECONDS` | float | `15.0` | carregamento e execução de tools |
| `OBSERVABILITY__LOG_LEVEL` | str | `INFO` | logging |

Um `model_validator` garante que a API key do provider selecionado existe — falhar no
boot é melhor que falhar no primeiro cliente.

## 9.2 Dependências

```toml
[project]
name = "agente-agenda"
requires-python = ">=3.14"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",
    "httpx>=0.27",
    "pydantic>=2.9",
    "pydantic-settings>=2.6",
    "langgraph>=0.2.50",
    "langchain-core>=0.3",
    "langchain-mcp-adapters>=0.1",
    "langgraph-checkpoint-redis>=0.0.6",
    "redis>=5.2",
]

[project.optional-dependencies]
anthropic = ["langchain-anthropic>=0.3"]
openai = ["langchain-openai>=0.2"]

[dependency-groups]
dev = ["pytest>=8", "pytest-asyncio>=0.24", "respx>=0.21", "fakeredis>=2.26",
       "ruff>=0.8", "mypy>=1.13"]
```

Gerenciador: `uv`, como no `agenda2`. Python 3.14+ (o `.python-version` fixa `3.14`).

## 9.3 Composition root

`src/container.py` — um dataclass com as dependências já montadas e uma função que o
constrói. Nenhuma instância global, nenhum singleton implícito.

```python
@dataclass(frozen=True, slots=True)
class Container:
    """As dependências prontas da aplicação."""

    handle_incoming_message: HandleIncomingMessage
    reset_conversation: ResetConversation
    parse_update: Callable[[dict[str, Any]], IncomingMessage | None]


async def build_container(settings: Settings) -> tuple[Container, AsyncExitStack]:
    """Constrói as dependências e devolve o stack que as fecha."""
```

O `AsyncExitStack` guarda o que precisa ser fechado (clientes HTTP, Redis, saver) e é
fechado no shutdown do lifespan. Ordem de construção: settings → Redis → checkpointer →
LLM → grafo → adapters HTTP → use cases.

O FastAPI acessa o container por `request.app.state.container`, exposto via uma
dependência tipada em `interfaces/http/dependencies.py`.

## 9.4 Execução local

```bash
uv sync --extra anthropic
cp .env.example .env      # preencher as chaves
docker compose up -d redis
uv run uvicorn src.main:app --reload --port 8080
```

Webhook em desenvolvimento: túnel HTTPS (`cloudflared tunnel --url http://localhost:8080`)
e registro no Telegram:

```bash
curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
  -d "url=https://<tunel>/webhook/telegram/$TELEGRAM_WEBHOOK_SECRET" \
  -d "secret_token=$TELEGRAM_WEBHOOK_SECRET"
```

Um script `scripts/set_webhook.py` faz isso lendo o `.env`, e `scripts/delete_webhook.py`
desfaz.

## 9.5 Deploy

- `Dockerfile` multi-stage com `uv`, sobre `ghcr.io/astral-sh/uv:python3.14-bookworm-slim`,
  venv resolvido do `uv.lock` (`uv sync --locked --no-dev --extra anthropic`), runtime
  não-root (`appuser`, uid 1000), `EXPOSE 8080`. Um `.dockerignore` mantém `scripts/`
  na imagem (o `set_webhook` roda no container durante o deploy) e exclui `docs/`,
  `tests/`, caches e `.env`.
- Um serviço no `docker-compose.yml` + Redis, atrás do mesmo nginx do `agenda2`.
- Healthcheck: `GET /health`.
- Escala horizontal é segura: o estado todo está no Redis e cada update é
  independente. A exceção é a ordem de mensagens de um mesmo chat, que não é garantida
  entre réplicas — aceitável nesta fase (mensagens em rajada são raras em agendamento).
- Logs em JSON no stdout, com `thread_id` em todo registro do turno. O telefone
  sintético e o `session_token` **nunca** são logados.
