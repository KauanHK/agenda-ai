# 09 — Configuração e deploy

## 9.1 Settings

`src/settings.py`, um único `BaseSettings`. Ninguém mais no projeto lê `os.environ`.

```python
class Settings(BaseSettings):
    """Configuração do agente, carregada do ambiente."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
```

| Variável | Tipo | Default | Uso |
| --- | --- | --- | --- |
| `AGENDABOT_API_URL` | str | `https://agenda.escaleia.cloud` | base da API |
| `AGENDABOT_MCP_URL` | str | `https://agenda.escaleia.cloud/mcp` | endpoint MCP |
| `AGENDABOT_SERVICE_KEY` | `SecretStr` | — | header `X-Service-Key` |
| `ESTABLISHMENT_ID` | `UUID` | `01a04f5b-0e84-7530-be67-63f08e7b2269` | fixo nesta fase |
| `ESTABLISHMENT_TIMEZONE` | str | `America/Sao_Paulo` | data/hora do prompt |
| `TELEGRAM_BOT_TOKEN` | `SecretStr` | — | Bot API |
| `TELEGRAM_WEBHOOK_SECRET` | `SecretStr` | — | path secreto do webhook |
| `LLM_PROVIDER` | `Literal["anthropic","openai"]` | `anthropic` | provider |
| `LLM_MODEL` | str | `claude-sonnet-5` | modelo |
| `LLM_TEMPERATURE` | float | `0.3` | criatividade baixa: é atendimento |
| `LLM_MAX_TOKENS` | int | `1024` | resposta de chat é curta |
| `ANTHROPIC_API_KEY` | `SecretStr \| None` | `None` | exigida se provider = anthropic |
| `OPENAI_API_KEY` | `SecretStr \| None` | `None` | exigida se provider = openai |
| `REDIS_URL` | str | `redis://localhost:6379/1` | checkpointer + cache |
| `CONVERSATION_TTL_MINUTES` | int | `1440` | TTL do histórico |
| `MAX_HISTORY_MESSAGES` | int | `40` | poda do histórico |
| `MAX_AGENT_STEPS` | int | `8` | teto de ciclos do grafo |
| `MAX_INPUT_CHARS` | int | `1000` | truncamento da mensagem do cliente |
| `SESSION_REFRESH_MARGIN_SECONDS` | int | `60` | margem antes de expirar |
| `SYNTHETIC_PHONE_PREFIX` | str | `5547999` | identidade da fase 1 |
| `HTTP_TIMEOUT_SECONDS` | float | `10.0` | API do AgendaBot e Telegram |
| `MCP_TIMEOUT_SECONDS` | float | `15.0` | carregamento e execução de tools |
| `LOG_LEVEL` | str | `INFO` | logging |

Um `model_validator` garante que a API key do provider selecionado existe — falhar no
boot é melhor que falhar no primeiro cliente.

## 9.2 Dependências

```toml
[project]
name = "agente-agenda"
requires-python = ">=3.12"
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

Gerenciador: `uv`, como no `agenda2`. Python 3.12+.

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

- `Dockerfile` multi-stage com `uv`, imagem `python:3.12-slim`, usuário não-root.
- Um serviço no `docker-compose.yml` + Redis, atrás do mesmo nginx do `agenda2`.
- Healthcheck: `GET /health`.
- Escala horizontal é segura: o estado todo está no Redis e cada update é
  independente. A exceção é a ordem de mensagens de um mesmo chat, que não é garantida
  entre réplicas — aceitável nesta fase (mensagens em rajada são raras em agendamento).
- Logs em JSON no stdout, com `thread_id` em todo registro do turno. O telefone
  sintético e o `session_token` **nunca** são logados.
