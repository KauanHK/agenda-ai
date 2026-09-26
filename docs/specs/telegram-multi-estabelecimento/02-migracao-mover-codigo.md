# 02 — Mover o agente para o backend

**Repositório:** agenda2 · **Depende de:** 01 · **Estimativa:** ~30 linhas novas; o resto é
código movido

## Objetivo

Trazer o código, os testes e a documentação do `agente-agenda` para
`backend/app/modules/agent/`, **sem mudar comportamento**. Ao final, a suíte do agente roda
na suíte do backend e o agente sobe localmente como processo próprio. Esta PR ainda não
coloca o serviço em produção; isso é a spec 03.

## Princípio da PR

É uma PR de mover código. Só entram:
- `git mv` com a nova estrutura de pastas;
- reescrita mecânica de imports;
- os ajustes mínimos listados em "Código novo".

Nada de refatoração, renome de símbolo ou reformatação. O revisor confere com
`git diff -M --stat` (arquivos movidos com similaridade alta) e com o script de reescrita
de imports, que vai na descrição da PR.

## Mapeamento

| Origem (`agente-agenda`) | Destino (`backend/`) |
|---|---|
| `src/domain/` | `app/modules/agent/domain/` |
| `src/application/` | `app/modules/agent/application/` |
| `src/infrastructure/agendabot/` | `app/modules/agent/adapters/agendabot/` |
| `src/infrastructure/agent/` | `app/modules/agent/adapters/langgraph/` |
| `src/infrastructure/{identity,llm,redis,telegram}/` | `app/modules/agent/adapters/{identity,llm,redis,telegram}/` |
| `src/interfaces/http/` | `app/modules/agent/adapters/http/` |
| `src/container.py`, `settings.py`, `logging_config.py` | `app/modules/agent/` |
| `src/main.py` | `app/main_agent.py` |
| `scripts/*.py` | `scripts/agent/*.py` (`python -m scripts.agent.repl`) |
| `tests/<camada>/`, `tests/fakes/`, `tests/conftest.py` | `tests/modules/agent/<camada correspondente>/`, `.../fakes/`, `.../conftest.py` |
| `docs/` | `docs/agente/`, **substituindo** os arquivos atuais, que estão desatualizados (propõem repositório separado e orquestrador de WhatsApp) |

A estrutura segue a convenção hexagonal do backend (`domain/`, `application/`,
`adapters/`). `infrastructure/agent/` virou `adapters/langgraph/` para não repetir
"agent" dentro do módulo `agent`.

A reescrita de imports troca `src.` → `app.modules.agent.` (com as renomeações de pasta
acima) e `tests.fakes` → `tests.modules.agent.fakes`. O teste de arquitetura do agente
(`tests/test_dependencies.py`, que proíbe `domain` de importar infraestrutura) passa a
verificar os caminhos novos.

## Código novo

- **Settings do agente** (`app/modules/agent/settings.py`):
  - Continua sendo uma classe separada (`AgentSettings`); a API e o worker não precisam
    de chave de LLM.
  - Passa a ler o `.env` único da raiz. `app/core/settings.py` expõe o caminho como
    `ENV_FILE` (hoje `_ENV_FILE`, privado).
  - Ganha `env_prefix="AGENT_"`, para as variáveis do agente não colidirem com as do
    backend no mesmo arquivo (hoje existem `REDIS_URL` e `REDIS__URL`, por exemplo).
- **Variáveis renomeadas** (só o prefixo, que é mecânico):

  | Antes | Depois |
  |---|---|
  | `AGENDABOT__*` | `AGENT_AGENDABOT__*` |
  | `TELEGRAM__*` | `AGENT_TELEGRAM__*` |
  | `LLM__*` | `AGENT_LLM__*` |
  | `REDIS__URL` | `AGENT_REDIS__URL` |
  | `CONVERSATION__*`, `IDENTITY__*`, `HTTP__*`, `OBSERVABILITY__*` | `AGENT_` + o mesmo nome |

- **`.env.example` da raiz** ganha a seção "Agente de IA" com essas variáveis, os mesmos
  defaults e os mesmos comentários do `.env.example` do agente.
- **`backend/pyproject.toml`:**
  - Novo extra `agent` com as dependências de runtime do agente (`langgraph`,
    `langchain-core`, `langchain-mcp-adapters`, `langgraph-checkpoint-redis`, `redis`,
    `langchain-anthropic`, `langchain-openai`, `langchain-groq`).
  - O grupo `dev` ganha `respx` e `fakeredis`.
  - O `Dockerfile` já usa `--all-extras`, então não muda.
  - `ruff`: se o código movido acusar `RUF001`–`RUF003` (acentos e travessões em
    pt-BR), essas regras entram no `ignore` global, como já estavam no agente.
- **Testes:** cada diretório novo em `tests/modules/agent/` ganha `__init__.py`. O
  backend importa os testes como pacote, e há nomes repetidos (`test_settings.py`,
  `test_app.py`). O `conftest.py` do agente (isolamento do logging do root) fica
  restrito a `tests/modules/agent/`. Os testes de settings passam a usar o prefixo.
- **CI** (`.github/workflows/ci.yml`, que ainda não existe no agenda2), em `pull_request`
  e em `push` na `main`, rodando em `backend/`: `uv sync --frozen --all-extras --dev`,
  `ruff check .`, `mypy app/modules/agent` e `pytest`.
  - O `mypy` fica restrito ao módulo porque o resto do backend tem ~17 erros antigos
    tolerados; o agente já passa em `strict`.
  - Hoje a suíte do backend passa inteira sem banco (577 testes).
- **README do backend:** seção "Agente" com os comandos (`uvicorn app.main_agent:app`,
  `python -m scripts.agent.repl --memory`, `python -m scripts.agent.smoke_mcp`).

## Fora de escopo

- Serviço no compose, nginx e deploy (spec 03).
- Qualquer mudança de comportamento, incluindo a emissão de sessão, que continua por HTTP
  até a spec 04.
- Reformatar o código movido para `line-length = 88`. O `ruff check` do backend ignora
  `E501`; se for fazer, vai numa PR só de formatação.
- Arquivar o repositório `agente-agenda` (spec 03, depois da virada).

## Critérios de aceite

- `pytest` do backend verde, com os ~184 testes do agente somados aos 577.
- `ruff check .` limpo e `mypy app/modules/agent` limpo.
- `uv run python -m scripts.agent.repl --memory` conversa localmente com o `.env` da
  raiz.
- `git diff -M --stat` mostra os arquivos do agente como renomeados.

## Deploy

Sem efeito em produção: nenhum serviço novo, só dependências a mais na imagem. O agente
continua rodando no stack antigo.
