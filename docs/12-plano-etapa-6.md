# 12 — Plano da Etapa 6 (Robustez)

Detalha a [Etapa 6 do roadmap](11-roadmap.md) em implementações pequenas, **uma PR por
implementação**. A referência de padrões de CI, Dockerfile e compose é o projeto
`brand_open/notas-fiscais` (monorepo FastAPI + `uv`, deploy por SSH numa VPS com
imagens no GHCR).

## Objetivo da etapa

Deixar o agente pronto para produção: imagem reproduzível, stack de deploy, CI que
barra regressão, logs utilizáveis e uma revisão da resiliência de rede. Critério de
pronto do roadmap: *"sobe em produção atrás do nginx, com healthcheck verde"*.

## Decisões desta rodada

| Tema | Decisão |
| --- | --- |
| Composes | Dois arquivos: `docker-compose.yml` (produção, só imagem do GHCR) + `docker-compose.override.yml` (local, carregado automático, com `build` e portas). Sem homologação. |
| Deploy/CD | Completo: build+push da imagem no GHCR e **deploy automático** por SSH na `main`, com workflow de `rollback` manual. Sem ambiente de homologação. |
| `/health` | `GET /health` continua *liveness* burro (200 sempre). Novo `GET /health/ready` faz `PING` no Redis e responde `503` se ele estiver fora. |
| Proxy | `nginx` **próprio** no compose (`nginx:alpine` + `nginx/nginx.conf` versionado → `api:8080`), na rede Docker `web` externa. |
| Logging | JSON no stdout com `thread_id` no turno (conforme `docs/09`), formatter próprio, sem dependência nova. |

## Desvios das specs existentes (a corrigir nas PRs)

- **`docs/09` diz `python:3.12-slim` e `requires-python = ">=3.12"`.** O `pyproject.toml`
  real exige `>=3.14` e o `.python-version` é `3.14`. O Dockerfile usa a imagem `uv`
  com Python 3.14; a PR do Dockerfile alinha o texto de `docs/09`.
- **`docs/09` diz "atrás do mesmo nginx do `agenda2`".** Aqui o compose sobe um `nginx`
  próprio na rede `web` externa (decisão acima). A PR dos composes atualiza `docs/09`.
- **Sem homologação** — `docs/09` não previa, então não há o que remover; apenas não se
  cria `docker-compose.homolog.yml`.

## Pré-requisitos de infraestrutura (fora do código, uma vez)

- Repositório publicado no GitHub com Actions habilitado; pacote GHCR
  `ghcr.io/<owner>/agente-agenda` (o push cria na primeira execução).
- Secrets do repositório: `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY` e, se o registro do
  webhook for automatizado, `PUBLIC_BASE_URL` (ex.: `https://agente.exemplo`).
- Na VPS: diretório `/opt/agente-agenda/`, `.env` preenchido (nunca versionado), rede
  Docker externa `web` (`docker network create web`) e o proxy de borda terminando TLS
  do domínio e roteando para o container `nginx` pela rede `web`.

---

## PR 1 — Teste de arquitetura

**Objetivo:** travar a tabela de "Regras de dependência" de `docs/01-arquitetura.md`.

**Arquivos:** `tests/test_dependencies.py`.

**Conteúdo:**
- Percorre `src/**/*.py` com `ast`, extrai os `import` / `from ... import`, classifica
  cada módulo por camada (`domain`, `application.ports`, `application.use_cases`,
  `infrastructure`, `interfaces`, raiz: `container`/`main`/`settings`).
- Verifica:
  - `domain` → só stdlib;
  - `application.ports` → `domain` + stdlib + `typing`;
  - `application.use_cases` → `domain` + `application.ports` + stdlib;
  - `infrastructure.*` → `domain` + `application.ports` + libs externas (nunca
    `interfaces` nem `container`);
  - `interfaces.*` → `application` + `container` + `fastapi` + stdlib;
  - `container` / `main` → livre.
- Checagem explícita do princípio 3 do doc 01: `httpx`, `redis`, `telegram`,
  `langgraph`, `langchain*` proibidos em `domain` e `application`.

**Pronto quando:** `uv run pytest tests/test_dependencies.py` passa no código atual;
um import proibido introduzido de propósito faz o teste falhar apontando o módulo.

**Depende de:** nada.

---

## PR 2 — `Dockerfile` + `.dockerignore`

**Objetivo:** imagem de runtime reproduzível, não-root, a partir do lock.

**Arquivos:** `Dockerfile`, `.dockerignore`, ajuste de texto em `docs/09-configuracao.md`.

**Conteúdo:**
- Multi-stage sobre `ghcr.io/astral-sh/uv:python3.14-bookworm-slim`:
  - *builder*: `ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never`,
    `COPY pyproject.toml uv.lock`, `RUN uv sync --locked --no-dev --extra anthropic`.
  - *runtime*: `ENV PATH=/app/.venv/bin:$PATH PYTHONUNBUFFERED=1
    PYTHONDONTWRITEBYTECODE=1`, copia `/app/.venv` do builder, `COPY . .`, cria
    `appuser` uid 1000, `USER appuser`, `EXPOSE 8080`,
    `CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]`.
  - `build-essential` só se algum wheel faltar no primeiro build.
- `.dockerignore`: `.git`, `.venv`, `__pycache__/`, `*.py[cod]`, `.mypy_cache`,
  `.pytest_cache`, `.ruff_cache`, `.env`, `.env.*` (com `!.env.example`), `docs/`,
  `tests/`, `*.md`, `.github/`, `.vscode/`. **Mantém `scripts/`** (o `set_webhook`
  roda dentro do container no deploy).

**Pronto quando:** `docker build -t agente-agenda .` conclui; `docker run --rm
agente-agenda id` mostra uid 1000; `docker run --rm agente-agenda` falha rápido
reclamando das settings (esperado, sem `.env`).

**Depende de:** nada.

---

## PR 3 — CI (`.github/workflows/ci.yml`)

**Objetivo:** gate de qualidade em toda PR para `main`.

**Arquivos:** `.github/workflows/ci.yml`.

**Conteúdo (padrão `notas-fiscais/ci.yml`, adaptado a um único app Python):**
- Gatilhos: `pull_request: [main]` e `push: [main]`.
- `concurrency: ci-${{ github.ref }}`, `cancel-in-progress: true`.
- Job `checks`:
  - `actions/checkout@v4`;
  - `astral-sh/setup-uv@v5` com `enable-cache: true`, `cache-dependency-glob: uv.lock`;
  - `uv sync --locked --extra anthropic`;
  - `uv run ruff check .`;
  - `uv run ruff format --check .`;
  - `uv run mypy` — **bloqueante** (diferente de `notas-fiscais`, que usa
    `continue-on-error`; aqui as specs exigem `mypy --strict` verde);
  - `uv run pytest -q` — sem serviço de Redis: a suíte usa `fakeredis` e os fakes.
- Job `image`: `docker/setup-buildx-action@v3` + `docker/build-push-action@v6` com
  `context: .`, `push: false`, `cache-from: type=gha`, `cache-to: type=gha,mode=max`.

**Pronto quando:** uma PR de teste mostra os dois jobs verdes.

**Depende de:** PR 1 (entra na suíte) e PR 2 (job `image`).

---

## PR 4 — Logging estruturado

**Objetivo:** log em JSON no stdout, com `thread_id` em todo registro do turno.

**Arquivos:** `src/logging_config.py` (novo), `src/main.py`, `src/interfaces/http/app.py`,
`src/infrastructure/telegram/webhook_handler.py` (início do turno), testes.

**Conteúdo:**
- `configure_logging(level: str) -> None`: `logging.basicConfig(..., force=True)` com
  um `logging.Formatter` que serializa cada record numa linha JSON: `ts` (ISO-8601
  UTC), `level`, `logger`, `msg`, `thread_id` (quando houver) e os campos passados via
  `extra`. Formatter próprio (~30 linhas), **sem dependência nova**.
- `thread_id`: `ContextVar[str | None]` em `src/logging_config.py` + um
  `logging.Filter` que o injeta no record. O handler do webhook (ou o use case) faz
  `token = _thread_id_var.set(ref.thread_id)` e `reset` no `finally`.
- Chamar `configure_logging` em `create_app` (cobre `TestClient` e `uvicorn --reload`)
  e manter em `main.py` para o boot anterior à app.
- Auditar os `logger.*` existentes: telefone sintético e `session_token` **nunca**
  entram (hoje já não entram — adicionar nota e um teste no caminho crítico).

**Pronto quando:** a linha emitida é JSON válido; `thread_id` presente com o ContextVar
setado e ausente sem ele; o nível respeita `OBSERVABILITY__LOG_LEVEL`.

**Depende de:** nada.

---

## PR 5 — `/health/ready`

**Objetivo:** separar *liveness* de *readiness* sem acoplar o healthcheck do container
ao Redis.

**Arquivos:** `src/container.py`, `src/interfaces/http/routes/health.py`,
`tests/interfaces/test_app.py` (o `_FakeContainer` ganha `check_readiness`), testes de
health, `README` e `docs/09`.

**Conteúdo:**
- `Container` ganha `check_readiness: Callable[[], Awaitable[dict[str, str]]]` — uma
  closure em `_wire` sobre o `redis_client`, que faz
  `await asyncio.wait_for(redis_client.ping(), timeout=2.0)` e devolve
  `{"redis": "ok"}` ou sinaliza `{"redis": "down"}`. Mantém `infrastructure` fora de
  `interfaces`.
- `GET /health` — inalterado (`{"status": "ok"}`, sem tocar em nada).
- `GET /health/ready` — chama `request.app.state.container.check_readiness()`; `200`
  com o relatório ou `503` com `{"redis": "down"}`.

**Pronto quando:** teste de `interfaces` com container fake — `ready` `200`; Redis fora
→ `503`; `/health` continua sem dependências.

**Depende de:** nada (mas convém entrar antes da PR 6, para o compose já referenciar os
dois endpoints).

---

## PR 6 — Composes + `nginx/nginx.conf`

**Objetivo:** stack de produção e stack local.

**Arquivos:** `docker-compose.yml`, `docker-compose.override.yml`, `nginx/nginx.conf`,
`.env.example` (bloco do compose), `.dockerignore` (+ `docker-compose*.yml`, `nginx/`),
`README`, `docs/09`.

**Conteúdo:**
- `docker-compose.yml` (produção — só imagem do GHCR, sem `build`):
  - âncora `x-logging` json-file (`max-size: 10m`, `max-file: 3`);
  - `nginx`: `nginx:1.27-alpine`, `restart: unless-stopped`, bind-mount
    `./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro`, redes `web` + `backend`,
    `depends_on: [api]`;
  - `api`: `image: ghcr.io/${GITHUB_REPOSITORY:-<owner>/agente-agenda}:latest`,
    `container_name: agente-agenda-api`, `restart: unless-stopped`, `env_file: ./.env`,
    `depends_on: {redis: {condition: service_healthy}}`, rede `backend`, `healthcheck`
    via `python -c "import socket; socket.create_connection(('127.0.0.1', 8080),
    timeout=3).close()"` (`start_period: 20s`);
  - `redis`: `redis:7-alpine`, `command: redis-server --appendonly yes`, volume
    `redisdata:/data`, `healthcheck: redis-cli ping`, rede `backend`,
    `stop_grace_period: 30s`;
  - `networks`: `backend: {internal: true}`, `web: {external: true, name: web}`;
  - `volumes`: `redisdata`.
- `docker-compose.override.yml` (local, carregado automático):
  - `api`: `build: {context: ., dockerfile: Dockerfile}`, `image: agente-agenda:dev`;
  - `nginx`: `ports: ["8080:80"]`;
  - `redis`: `ports: ["6379:6379"]`;
  - `networks`: `web: {external: false, name: agente-agenda_web}`.
- `nginx/nginx.conf`: `resolver 127.0.0.11 valid=10s ipv6=off;` e um `location /` que
  faz `proxy_pass` para `http://$upstream:8080$request_uri` com `$upstream` em variável
  (adia a resolução de DNS) e os headers `Host` / `X-Real-IP` / `X-Forwarded-For` /
  `X-Forwarded-Proto`.
- `.env.example`: acrescenta `GITHUB_REPOSITORY=<owner>/agente-agenda` e uma nota de que
  no compose `REDIS__URL=redis://redis:6379/1`.

**Pronto quando:** `docker compose up --build` local serve `GET /health` →
`{"status":"ok"}` e `GET /health/ready` verde com Redis de pé; `docker compose -f
docker-compose.yml config` valida a stack de produção sem o override.

**Depende de:** PR 2 (Dockerfile); PR 5 (para `/health/ready` já existir).

---

## PR 7 — Deploy + rollback

**Objetivo:** publicar a imagem e subir a stack na `main`; reverter sob demanda.

**Arquivos:** `.github/workflows/deploy.yml`, `.github/workflows/rollback.yml`,
`docs/09` (seção de deploy).

**Conteúdo (padrão `notas-fiscais/deploy.yml` + `rollback.yml`, sem homologação):**
- `deploy.yml`: `on: push: [main]`, `concurrency: deploy-production`.
  `env: IMAGE: ghcr.io/${{ github.repository }}`.
  - Job `build` (`permissions: {contents: read, packages: write}`): buildx,
    `docker/login-action@v3` no `ghcr.io`, `docker/build-push-action@v6` `push: true`,
    tags `:latest` e `:sha-${{ github.sha }}`, cache gha.
  - Job `deploy` (`needs: build`):
    - `appleboy/scp-action@v1` copia `docker-compose.yml` e `nginx/nginx.conf` para
      `/opt/agente-agenda`;
    - `appleboy/ssh-action@v1`: `docker login ghcr.io`;
      `docker tag $IMAGE:latest $IMAGE:rollback || true`;
      `docker pull $IMAGE:sha-<sha>` → `docker tag ... $IMAGE:latest`;
      `docker compose up -d --remove-orphans --wait --wait-timeout 180`;
      `docker compose exec -T nginx nginx -t && docker compose exec -T nginx nginx -s reload`;
      limpeza das tags `sha-*` antigas + `docker image prune -f`.
    - **Registro do webhook:** `docker compose exec -T api python -m scripts.set_webhook
      "$PUBLIC_BASE_URL"` — idempotente, só surte efeito se a URL mudou. Pode ficar
      manual no primeiro deploy; se automatizado, `PUBLIC_BASE_URL` vem de secret.
- `rollback.yml`: `workflow_dispatch` com input `motivo`; ssh: exige `$IMAGE:rollback`,
  `docker tag $IMAGE:rollback $IMAGE:latest`, `docker compose up -d --wait`.
- `docs/09`: descreve secrets e os pré-requisitos manuais na VPS.

**Pronto quando:** um push na `main` publica a imagem no GHCR e sobe a stack com
`--wait` verde; o workflow `Rollback` volta para a imagem anterior.

**Depende de:** PR 2, PR 3, PR 6.

---

## PR 8 — Retry e timeouts revisados

**Objetivo:** política de resiliência de rede coerente e documentada por adapter.

**Arquivos:** `src/infrastructure/agendabot/http_client.py`,
`src/infrastructure/telegram/client.py`, `src/settings.py` (se surgir
`HTTP__CONNECT_TIMEOUT_SECONDS`), `src/infrastructure/agent/runner.py` (confirmar),
`docs/05` / `docs/07` / `docs/09`, testes.

**Auditoria e ajustes:**
- `httpx.Timeout` único → separar `connect` / `read` / `write` / `pool` (read curto no
  Telegram, mais folgado no AgendaBot).
- `session_issuer`: o retry já cobre `ConnectError` + `5xx` com backoff — garantir que
  `ReadTimeout` / `WriteTimeout` / `PoolTimeout` entrem no caminho repetível (hoje um
  `httpx.HTTPError` genérico vira `BookingSessionError` sem retry).
- `telegram/client.py`: hoje trata `429` uma vez; decidir e **documentar** se repete em
  timeout de conexão (`sendMessage` repetido pode duplicar mensagem — provavelmente só
  `ConnectError`, nunca depois do request sair).
- `tool_provider`: timeout ok, sem retry (abrir conexão MCP não é seguramente
  idempotente) — registrar a decisão.
- Redis: `checkpointer` / `session_cache` degradam sem derrubar o turno — cobrir com
  teste; o `runner` converte falha do grafo em `AgentUnavailableError`.
- `recursion_limit` (`MAX_AGENT_STEPS`) → `AgentUnavailableError`, com o teste exigido
  em `docs/10-testes.md`.
- Nova tabela em `docs` — "política de retry/timeout por adapter".

**Pronto quando:** testes de timeout repetível no issuer (`respx`), de timeout no
Telegram e de estouro do limite do grafo passam; a tabela está no doc.

**Depende de:** nada (última porque se beneficia de tudo estável; pode ser antecipada).

---

## Ordem e dependências

```
PR1 (arch test) ─┐
PR2 (Dockerfile) ┼─→ PR3 (CI) ─────────────────────────┐
                 └─→ PR6 (composes) ─→ PR7 (deploy/rollback)
PR4 (logging)       ── independente
PR5 (/health/ready) ── independente, antes da PR6
PR8 (retry/timeouts) ── independente, sugerida por último
```

Sequência de merge sugerida: **PR1 → PR2 → PR3 → PR4 → PR5 → PR6 → PR7 → PR8.**

## Definição de pronto da Etapa 6

- CI verde em toda PR para `main` (ruff, ruff format, `mypy --strict`, pytest,
  `docker build`).
- `tests/test_dependencies.py` guardando a tabela de imports do doc 01.
- Logs em JSON no stdout com `thread_id` no turno; telefone e `session_token` nunca
  logados.
- `docker compose up --build` local serve `/health` e `/health/ready`.
- Push na `main` publica a imagem no GHCR e sobe a stack de produção com `--wait`
  verde, atrás do `nginx` próprio na rede `web`.
- Workflow `Rollback` manual funcional.
- Política de retry/timeout revisada e documentada por adapter.

## Pontos em aberto

- **Owner/nome no GHCR:** assumido `ghcr.io/<owner>/agente-agenda` a partir de
  `github.repository`. Confirmar org e caixa.
- **Domínio de produção e término de TLS** (proxy de borda da VPS) — necessário para o
  `set_webhook` e para o roteamento na rede `web`.
- **`build-essential` no Dockerfile:** só se algum wheel faltar no primeiro build.
- **Persistência do Redis:** `--appendonly` + volume assumido; se o estado da conversa
  for descartável, um Redis sem volume simplifica.
- **`python-json-logger` vs formatter próprio:** inclinação por formatter próprio, zero
  dependência nova.
- **Registro do webhook no deploy:** automático (secret `PUBLIC_BASE_URL`) ou manual no
  primeiro deploy.
