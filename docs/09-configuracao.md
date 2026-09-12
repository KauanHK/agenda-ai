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
| `TELEGRAM__ADMIN_TOKEN` | `SecretStr` | — | Bearer das rotas `/admin/telegram/webhook` |
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
| `HTTP__TIMEOUT_SECONDS` | float | `10.0` | read/write/pool da API do AgendaBot |
| `HTTP__CONNECT_TIMEOUT_SECONDS` | float | `5.0` | abrir conexão TCP+TLS (AgendaBot e Telegram) |
| `HTTP__TELEGRAM_READ_TIMEOUT_SECONDS` | float | `5.0` | read/write/pool da Bot API do Telegram |
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
desfaz. Com a API de pé, o mesmo registro pode ser feito pela rota administrativa
(seção 9.7).

Como alternativa, a stack inteira (nginx + api + redis) sobe pelo compose, que em
desenvolvimento constrói a imagem local e publica a porta `8080` no nginx:

```bash
cp .env.example .env      # preencher as chaves; REDIS__URL=redis://redis:6379/0
docker compose up --build
```

## 9.5 Deploy

- `Dockerfile` multi-stage com `uv`, sobre `ghcr.io/astral-sh/uv:python3.14-bookworm-slim`,
  venv resolvido do `uv.lock` (`uv sync --locked --no-dev --extra anthropic`), runtime
  não-root (`appuser`, uid 1000), `EXPOSE 8080`. Um `.dockerignore` mantém `scripts/`
  na imagem e exclui `docs/`, `tests/`, caches, `.env`, os `docker-compose*.yml` e
  `nginx/`.
- Dois composes: `docker-compose.yml` (produção — só a imagem do GHCR
  `ghcr.io/${GITHUB_REPOSITORY}:latest`, sem `build`) e `docker-compose.override.yml`
  (carregado automático em dev — acrescenta `build`, as portas e uma rede `web` local).
- Serviços do `docker-compose.yml`: `nginx` (`nginx:1.27-alpine`, `nginx/nginx.conf`
  versionado, encaminha para `api:8080`), `api` e `redis` (`redis:8-alpine`,
  `--appendonly yes`, volume `redisdata`). O `nginx` fica em duas redes: a `web`
  (externa, `docker network create web`, onde o proxy de borda da VPS o alcança e
  termina o TLS) e a `backend` (`internal: true`, só api + redis). **Não** reaproveita
  o nginx do `agenda2`.
- Healthcheck do container `api`: TCP na porta `8080` (`python -c "import socket;
  ..."`), sem tocar no Redis. `GET /health` é o *liveness* burro — `200` sempre,
  sem tocar em dependências.
- *Readiness*: `GET /health/ready` — dá `PING` no Redis (timeout de 2s) e responde
  `200` com `{"redis": "ok"}` ou `503` com `{"redis": "down"}`. É o endpoint que o
  proxy/orquestrador consulta antes de mandar tráfego; o healthcheck do container
  fica fora dele para não derrubar o processo quando só o Redis oscila.
- Escala horizontal é segura: o estado todo está no Redis e cada update é
  independente. A exceção é a ordem de mensagens de um mesmo chat, que não é garantida
  entre réplicas — aceitável nesta fase (mensagens em rajada são raras em agendamento).
- Logs em JSON no stdout, com `thread_id` em todo registro do turno. O telefone
  sintético e o `session_token` **nunca** são logados.

- O deploy **não** registra o webhook do Telegram: o Telegram guarda a URL do lado
  dele, então o registro é um passo único de *bootstrap* (seção 9.7), refeito só se
  o domínio ou o `TELEGRAM__WEBHOOK_SECRET` mudarem.

### 9.5.1 Pipeline de deploy (GitHub Actions)

`.github/workflows/deploy.yml` roda a cada push na `main` (`concurrency:
deploy-production`, um deploy por vez):

1. **Build & Push** — `docker/build-push-action` publica a imagem no GHCR como
   `ghcr.io/<owner>/<repo>:latest` e `:sha-<commit>` (nome em minúsculas — o
   Docker rejeita `KauanHK`), com cache de camadas no GHA.
2. **Deploy** — copia `docker-compose.yml` e `nginx/nginx.conf` para
   `/opt/agente-agenda` na VPS (`scp-action`) e, por SSH: `docker login ghcr.io`,
   guarda a imagem atual como `:rollback`, faz `pull` da `:sha-<commit>`, retagueia
   como `:latest`, `docker compose up -d --remove-orphans --wait --wait-timeout 180`,
   `nginx -t` + `nginx -s reload` (o `nginx.conf` é bind mount, o Compose não recria
   o container) e limpa as tags `sha-*` antigas.

`.github/workflows/rollback.yml` é `workflow_dispatch` (input `motivo`): exige
`:rollback` na VPS, retagueia como `:latest` e sobe a stack com `--wait`. Só guarda
**um** passo atrás — dois rollbacks seguidos não voltam duas versões.

**Secrets do repositório** (Settings → Secrets → Actions):

| Secret | Uso |
| --- | --- |
| `VPS_HOST` | host/IP da VPS |
| `VPS_USER` | usuário SSH (precisa estar no grupo `docker`) |
| `VPS_SSH_KEY` | chave privada (par cuja pública está no `authorized_keys` do usuário) |

O `GITHUB_TOKEN` padrão basta para publicar e puxar do GHCR (`packages: write` no
job de build). Se o pacote ficar privado, o `docker login` da VPS usa esse mesmo
token efêmero a cada deploy.

**Pré-requisitos manuais na VPS** (uma vez):

```bash
sudo mkdir -p /opt/agente-agenda && sudo chown "$USER" /opt/agente-agenda
docker network create web            # rede do proxy de borda que termina o TLS
cp .env.example /opt/agente-agenda/.env   # preencher; REDIS__URL=redis://redis:6379/0
```

O deploy falha cedo se faltar o `.env` ou a rede `web`. Depois do primeiro deploy
verde, registrar o webhook uma vez via `POST /admin/telegram/webhook` (seção 9.7).

## 9.6 Política de retry e timeout por adapter

Cada integração de rede tem uma política própria, ditada pela idempotência da
operação e pelo custo de uma falha. O quadro abaixo é o contrato — mudou o
comportamento de um adapter, atualiza aqui.

| Adapter | Arquivo | `connect` | `read` / `write` / `pool` | Retry | Repete o quê | Falha terminal vira |
| --- | --- | --- | --- | --- | --- | --- |
| Emissão de sessão | `agendabot/session_issuer.py` | `HTTP__CONNECT_TIMEOUT_SECONDS` (5 s) | `HTTP__TIMEOUT_SECONDS` (10 s) | até 3 tentativas, backoff exponencial de 200 ms | `ConnectError`, `TimeoutException` (connect/read/write/pool), `5xx` | `BookingSessionError` (`403` → `ClientBlockedError`; `4xx` nunca repete) |
| Tools MCP | `agendabot/tool_provider.py` | — (timeout total) | `HTTP__MCP_TIMEOUT_SECONDS` (15 s), `asyncio.timeout` | **nenhum** — handshake MCP não é comprovadamente idempotente | — | `BookingSessionError` |
| Envio ao Telegram (`sendMessage`) | `telegram/client.py` | `HTTP__CONNECT_TIMEOUT_SECONDS` (5 s) | `HTTP__TELEGRAM_READ_TIMEOUT_SECONDS` (5 s) | 1 vez **só** em `ConnectError` / `ConnectTimeout`; `429` respeita `retry_after` e tenta 1 vez | falha ao abrir a conexão (request não saiu) | `DeliveryError` |
| `sendChatAction` (digitando) | `telegram/client.py` | idem | idem | nenhum | — | engolido (log em `debug`) |
| `setWebhook` / `getWebhookInfo` | `telegram/webhook_registry.py` | idem | idem | nenhum — operação manual, quem chamou repete | — | `WebhookRegistrationError` (`502` na rota `/admin`) |
| Checkpointer (histórico) | `redis/checkpointer.py` | — | — | nenhum | — | `ConversationStateError` (turno cai de forma visível) |
| Cache de sessão | `redis/session_cache.py` | — | — | nenhum | — | engolido: `get` → `None`, `put` no-op, log em `warning`; o provider reemite |
| Grafo do agente | `agent/runner.py` | — | — | `recursion_limit` = `MAX_AGENT_STEPS * 2 + 1` | os ciclos do próprio grafo | `AgentUnavailableError` (também para qualquer falha do LLM) |

Regra por trás do quadro: só se repete o que é seguramente reentrante. Emitir a
sessão é (o AgendaBot resolve o cliente pelo telefone); `sendMessage` **não** é
depois que o request parte — repetir ali duplicaria a mensagem, então só um erro
de conexão (que garante que nada saiu) é repetível.

## 9.7 Rotas administrativas: webhook do Telegram

O Telegram precisa saber para onde mandar os updates (`setWebhook`), e guarda essa
URL do lado dele. Registrar é, portanto, um passo **único** por ambiente — não faz
parte do deploy. Depois do primeiro deploy (e sempre que o domínio ou o
`TELEGRAM__WEBHOOK_SECRET` mudarem), o operador chama a rota administrativa uma vez.

| Rota | Faz |
| --- | --- |
| `POST /admin/telegram/webhook` | `setWebhook` em `{base_url}/webhook/telegram/{TELEGRAM__WEBHOOK_SECRET}` (com `secret_token`, `allowed_updates: ["message"]`) e devolve o `getWebhookInfo` resultante |
| `GET /admin/telegram/webhook` | `getWebhookInfo`, consultado direto do Telegram |

As duas exigem `Authorization: Bearer <TELEGRAM__ADMIN_TOKEN>` (`401` sem ele, com a
comparação em tempo constante). Nada é persistido pela API: a fonte da verdade é o
Telegram. O segredo do webhook faz parte da URL registrada e volta mascarado (`***`)
nas respostas. `base_url` precisa ser HTTPS (`422` caso contrário) e uma recusa do
Telegram vira `502` com a `description` original.

```bash
curl -X POST https://agente.exemplo/admin/telegram/webhook \
  -H "Authorization: Bearer $TELEGRAM_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"base_url": "https://agente.exemplo"}'
# opcional: "drop_pending_updates": true descarta os updates acumulados na fila

curl https://agente.exemplo/admin/telegram/webhook \
  -H "Authorization: Bearer $TELEGRAM_ADMIN_TOKEN"
```

Em desenvolvimento, `scripts/set_webhook.py` faz o mesmo `setWebhook` sem passar pela
API (usa o mesmo `TelegramWebhookRegistry`), o que serve para túneis efêmeros antes
de a aplicação subir.
