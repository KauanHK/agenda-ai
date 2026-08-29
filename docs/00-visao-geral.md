# 00 — Visão geral

## O que é

`agente-agenda` é um agente de IA conversacional que atende clientes finais pelo
Telegram e realiza agendamentos consumindo o **MCP server do AgendaBot**
(`https://agenda.escaleia.cloud/mcp`).

O agente é um processo separado do backend do AgendaBot. Ele não tem banco de dados de
negócio, não conhece as regras de agenda e não fala com o Postgres do AgendaBot: toda
capacidade de negócio chega até ele como *tool* MCP.

## Responsabilidades

| É responsabilidade do agente | **Não** é responsabilidade do agente |
| --- | --- |
| Receber mensagens do Telegram | Validar expediente, feriados, bloqueios |
| Manter o histórico da conversa | Escolher qual profissional atende |
| Decidir qual tool chamar e com quais argumentos | Persistir agendamentos |
| Traduzir `error_code` do MCP em linguagem natural | Cobrar, notificar, lembrar |
| Enviar a resposta de volta ao Telegram | Autenticar o cliente (o backend faz isso pelo telefone) |

## Fluxo de uma mensagem

```
Telegram → webhook (FastAPI)
  → HandleIncomingMessage (use case)
      → resolve telefone a partir do chat            (PhoneResolver)
      → obtém session_token do AgendaBot             (SessionIssuer, cache Redis)
      → carrega as tools MCP autenticadas            (ToolProvider)
      → roda o grafo LangGraph com o histórico       (AgentRunner + checkpointer Redis)
          ↳ o grafo faz N chamadas de tool via MCP
      → devolve o texto final                        (OutboundMessenger → Telegram)
```

## Decisões tomadas

| Tema | Decisão |
| --- | --- |
| Orquestração | LangGraph (`StateGraph` com ciclo agente ↔ tools) |
| LLM | **configurável por env** — porta abstrata, provider escolhido em runtime |
| Entrada do Telegram | **webhook** HTTP servido por FastAPI |
| Estado da conversa | **Redis** (`langgraph-checkpoint-redis`) |
| Identidade | telefone **sintético determinístico** derivado do `chat_id` (fase 1) |
| `establishment_id` | **fixo** por env: `01a04f5b-0e84-7530-be67-63f08e7b2269` |
| Idioma | pt-BR em todo o produto: código, docstrings, prompts e mensagens |

## Fora de escopo nesta fase

- WhatsApp / Evolution API (o Telegram vem primeiro).
- Multi-estabelecimento (um `establishment_id` fixo por deploy).
- Escalonamento para atendente humano.
- Painel ou API de observabilidade próprios.
- Áudio, imagem e anexos — só texto.

## Índice das specs

| # | Documento | Assunto |
| --- | --- | --- |
| 01 | [`01-arquitetura.md`](01-arquitetura.md) | Camadas, estrutura de pastas, regras de dependência |
| 02 | [`02-dominio.md`](02-dominio.md) | Entidades e erros do agente |
| 03 | [`03-portas.md`](03-portas.md) | Contratos (protocols) da camada de aplicação |
| 04 | [`04-use-cases.md`](04-use-cases.md) | Casos de uso e suas responsabilidades |
| 05 | [`05-integracao-mcp.md`](05-integracao-mcp.md) | Sessão, token, tools e catálogo de erros |
| 06 | [`06-agente-langgraph.md`](06-agente-langgraph.md) | Grafo, estado, nós e system prompt |
| 07 | [`07-canal-telegram.md`](07-canal-telegram.md) | Webhook, parsing de update, envio de resposta |
| 08 | [`08-estado-redis.md`](08-estado-redis.md) | Checkpointer, cache de token, chaves e TTLs |
| 09 | [`09-configuracao.md`](09-configuracao.md) | Settings, `.env`, dependências, deploy |
| 10 | [`10-testes.md`](10-testes.md) | Estratégia de testes por camada |
| 11 | [`11-roadmap.md`](11-roadmap.md) | Ordem de implementação em etapas |
