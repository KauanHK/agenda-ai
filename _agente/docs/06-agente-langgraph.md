# 06 — O agente (LangGraph)

## Topologia

O ciclo canônico ReAct, escrito à mão em vez de `create_react_agent`: as tools mudam
a cada turno (vêm autenticadas por sessão), e o nó do modelo precisa fazer o `bind`
dentro da execução — não na construção do grafo.

```
        ┌─────────────┐
START ──▶│ call_model  │
        └──────┬──────┘
               │ should_continue
        ┌──────┴───────┐
        ▼              ▼
  ┌───────────┐      END
  │ call_tools│
  └─────┬─────┘
        └──────────▶ call_model
```

O grafo é construído **uma vez** no startup e compilado com o checkpointer Redis. Só
os dados variam por turno, via `config["configurable"]`.

## Estado

`src/infrastructure/agent/state.py`

```python
class ConversationState(TypedDict):
    """O que o checkpointer persiste por thread."""

    messages: Annotated[list[AnyMessage], add_messages]
```

Só `messages`. O que é por turno e não deve ser persistido (tools, nome do cliente,
data atual) viaja em `configurable`, não no estado — persistir um `session_token` de
10 minutos no histórico seria guardar credencial expirada num lugar durável.

```python
class TurnConfig(TypedDict):
    """Injetado em `config["configurable"]` a cada invocação."""

    thread_id: str
    tools: Sequence[BaseTool]
    client_name: str
    now_iso: str          # data e hora atuais no fuso do estabelecimento
    is_new_client: bool
```

## Nós

Cada nó é uma função com uma responsabilidade.

### `call_model`

`src/infrastructure/agent/nodes/call_model.py`

```python
async def call_model(
    state: ConversationState,
    config: RunnableConfig,
) -> dict[str, list[AnyMessage]]:
    """Pede a próxima ação ao LLM, já com as tools da sessão vinculadas."""
```

1. Lê `tools` e o contexto de `config["configurable"]`.
2. Renderiza o prompt em duas partes: `prompts.render_system_prompt()` (estático) e
   `prompts.render_turn_context(context)` (volátil), cada uma numa `SystemMessage`.
3. `model.bind_tools(tools)` e `ainvoke([system, turn_context, *state["messages"]])`.
4. Devolve `{"messages": [resposta]}`.

O modelo em si vem do `container` já construído (`build_chat_model()`), injetado por
`functools.partial` na montagem do grafo. O nó não conhece provider nem env.

### `call_tools`

`src/infrastructure/agent/nodes/call_tools.py`

```python
async def call_tools(
    state: ConversationState,
    config: RunnableConfig,
) -> dict[str, list[ToolMessage]]:
    """Executa as tool calls pedidas pelo modelo e devolve os resultados."""
```

Um `ToolNode` do LangGraph não serve aqui: ele recebe as tools na construção. Este nó
resolve a tool por nome no dicionário vindo de `configurable`.

- Tool calls independentes rodam em paralelo (`asyncio.gather`).
- Uma tool inexistente ou que levanta exceção vira um `ToolMessage` com
  `{"success": false, "error_code": "tool_failed", ...}` — a falha volta para o modelo
  em vez de derrubar o turno.
- Cada `ToolMessage` carrega o `tool_call_id` correspondente.

### `should_continue`

```python
def should_continue(state: ConversationState) -> Literal["call_tools", "__end__"]:
    """Decide se o turno continua em tools ou termina."""
```

Termina quando a última mensagem não tem `tool_calls`.

## Limite de passos

`recursion_limit = MAX_AGENT_STEPS * 2 + 1` (default `MAX_AGENT_STEPS = 8`). Estourar
levanta `GraphRecursionError`, que o runner traduz em `AgentUnavailableError` — o
cliente recebe a frase padrão em vez de um loop infinito de tool calls.

## O runner

`src/infrastructure/agent/runner.py` — a única classe de `infrastructure/agent` que a
aplicação enxerga.

```python
class LangGraphAgentRunner:
    """Implementa `AgentRunnerProtocol` sobre um grafo compilado."""

    async def run(self, *, conversation, user_text, tools, context) -> AgentAnswer:
        """Roda um turno e extrai o texto final da resposta."""
```

Responsabilidades: montar o `config`, invocar o grafo, extrair o texto do último
`AIMessage`, contar as tool calls do turno e traduzir exceções do LangGraph/LLM em
`AgentUnavailableError` / `ConversationStateError`.

Se o último `AIMessage` vier com texto vazio (acontece quando o modelo encerra depois
de uma tool sem comentar), o runner devolve uma frase de fallback em vez de mandar
mensagem vazia ao Telegram — a API do Telegram rejeita texto vazio.

## System prompt

`src/infrastructure/agent/prompts.py`, duas funções — a divisão é para o prompt
caching:

```python
def render_system_prompt() -> str:
    """Parte estática: mesma para todo turno, serve de prefixo cacheável."""

def render_turn_context(context: PromptContext) -> str:
    """Parte volátil: cliente, data/hora, primeiro contato."""
```

`call_model` emite as duas como `SystemMessage`s consecutivas, a estática primeiro.
Quando o caching for ligado, o `cache_control` vai só na estática (forma de
content-block); o contexto do turno fica de fora do bloco cacheável e a estrutura
do prompt não muda.

Estrutura do prompt (pt-BR):

1. **Papel** — atendente do estabelecimento no Telegram; objetivo é resolver o
   agendamento na conversa. *(estático)*
2. **Contexto do turno** — nome do cliente, data e hora atuais com dia da semana e
   fuso, se é o primeiro contato. *(volátil, `render_turn_context`)*
3. **Regras de agenda** *(estático daqui para baixo)*
   - Só ofereça horários que apareceram em `list_available_slots`.
   - Nunca invente serviço, preço, duração ou horário.
   - Confirme serviço **e** horário antes de `create_scheduling`.
   - Confirme com o cliente antes de `cancel_scheduling`.
   - Prefira `reschedule_scheduling` a cancelar e marcar de novo.
   - Resolva datas relativas ("amanhã", "sexta") contra a data atual informada, e
     repita a data absoluta na confirmação.
4. **Erros** — versão condensada do catálogo de `error_code`; use a `message` do
   envelope para explicar em linguagem natural, sem citar o código.
5. **Estilo** — pt-BR informal e direto, mensagens curtas de chat, sem markdown
   pesado, sem emoji em excesso, uma pergunta por vez. Nunca mencionar "tool", "MCP",
   "sistema", `service_id`, `scheduling_id` ou qualquer UUID.
6. **Limites** — não negocia preço, não promete profissional específico, não trata de
   assunto fora de agendamento; nesses casos oriente a falar com o estabelecimento.

O prompt não descreve o que cada tool faz: isso já vem nas descrições publicadas pelo
MCP server, e duplicar cria duas versões para divergir.

## LLM configurável

`src/infrastructure/llm/factory.py`

```python
def build_chat_model(settings: Settings) -> BaseChatModel:
    """Constrói o chat model do provider configurado."""
```

| `LLM_PROVIDER` | Pacote | Default de `LLM_MODEL` |
| --- | --- | --- |
| `anthropic` | `langchain-anthropic` | `claude-sonnet-5` |
| `openai` | `langchain-openai` | `gpt-4.1` |
| `groq` | `langchain-groq` | `llama-3.3-70b-versatile` |

Um `match` sobre o provider, um construtor por branch, `ValueError` no default.
`temperature` e `max_tokens` vêm de settings. Import do pacote dentro do branch, para
que faltar a dependência do provider não usado não quebre o boot.
