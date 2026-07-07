# 10 — Checklist de implementação

Ordem sugerida. Cada fase pode ser testada antes de prosseguir.

## Fase 1 — Fundação na API existente

- [ ] Adicionar dependências ao `agendabot-api`: `openai`, `pyjwt`, `redis[hiredis]`
- [ ] Criar variáveis de ambiente listadas em `04-agent-module.md` e `09-deployment.md`
- [ ] Criar módulo vazio `app/modules/agent/` com estrutura de pastas
- [ ] Implementar `actors.py` com `ClientAgentActor`
- [ ] Implementar `tokens.py` (issue + decode) com testes unitários
- [ ] Implementar `dependencies.py` com `get_session_actor` e `verify_evolution_webhook`

**Critério de aceite:** testes unitários de geração e validação de token passam, incluindo casos de expiração e assinatura inválida.

## Fase 2 — Histórico e contexto

- [ ] Implementar `history.py` (ConversationHistory) com testes de integração contra Redis
- [ ] Implementar `context.py` (AgentContext + loaders) com testes que carregam dados reais
- [ ] Adicionar template do system prompt em `prompts/system_prompt.md` (revisado conforme `06-system-prompt.md`)
- [ ] Implementar `prompts.py` (build_system_prompt) com teste de injeção de variáveis

**Critério de aceite:** dado um phone e establishment_id, o sistema carrega contexto completo e gera o system prompt corretamente.

## Fase 3 — Rotas de tools na API

- [ ] Criar `routes/tools.py` com endpoints:
  - [ ] `GET /agent-tools/services`
  - [ ] `GET /agent-tools/slots`
  - [ ] `POST /agent-tools/schedulings`
  - [ ] `DELETE /agent-tools/schedulings/{id}`
  - [ ] `PATCH /agent-tools/schedulings/{id}/reschedule`
  - [ ] `GET /agent-tools/schedulings` (do cliente)
  - [ ] `POST /agent-tools/escalations`
- [ ] Implementar `errors.py` com tradução de exceções de domínio para envelope
- [ ] Registrar router no `app/main.py`
- [ ] Testes de integração validando que `client_id` e `establishment_id` nunca vêm do payload — sempre do token

**Critério de aceite:** todos os endpoints respondem corretamente quando chamados com token válido e retornam envelope padronizado para erros de domínio.

## Fase 4 — MCP server

- [ ] Criar repositório `agendabot-mcp` com `pyproject.toml`
- [ ] Implementar `config.py`, `http_client.py`, `auth.py`
- [ ] Implementar `server.py` e `main.py`
- [ ] Implementar cada arquivo de tools (`scheduling.py`, `availability.py`, `services.py`, `escalation.py`)
- [ ] Adicionar `Dockerfile` e `docker-compose.yml`
- [ ] Subir localmente e testar com `curl` que cada tool roteia corretamente para a API com o token

**Critério de aceite:** chamando o MCP server com headers válidos, cada tool executa o use case correto na API e retorna o envelope.

## Fase 5 — Runner e integração com OpenAI

- [ ] Implementar `runner.py` (AgentRunner) usando OpenAI Responses API
- [ ] Configurar `tools=[{"type": "mcp", ...}]` apontando para o MCP server local
- [ ] Implementar router de webhook `app/modules/agent/router.py`
- [ ] Testar end-to-end localmente:
  - [ ] Enviar POST simulando webhook da Evolution
  - [ ] Verificar que o agente raciocina, chama tools, e retorna resposta
- [ ] Validar histórico persistido no Redis

**Critério de aceite:** conversa completa de agendamento funciona de ponta a ponta em ambiente local.

## Fase 6 — Integração com Evolution

- [ ] Configurar instância Evolution de teste para apontar webhook para servidor local (ngrok ou similar)
- [ ] Implementar parsing real do payload da Evolution
- [ ] Implementar idempotência via Redis
- [ ] Testar com WhatsApp real:
  - [ ] Saudação inicial
  - [ ] Consulta de serviços
  - [ ] Criação de agendamento
  - [ ] Cancelamento
  - [ ] Reagendamento
  - [ ] Escalada (provocar reclamação)
- [ ] Validar que mensagens não-texto são respondidas adequadamente

**Critério de aceite:** os 6 fluxos acima funcionam via WhatsApp real.

## Fase 7 — Deploy de staging

- [ ] Provisionar `mcp.agendabot.com.br` com HTTPS válido
- [ ] Configurar reverse proxy
- [ ] Deploy do MCP server em staging
- [ ] Deploy da API atualizada em staging
- [ ] Configurar instância Evolution de staging com webhook apontando para staging
- [ ] Rodar testes da Fase 6 em staging

**Critério de aceite:** ambiente staging funcional com integração ponta a ponta.

## Fase 8 — Produção

- [ ] Configurar `mcp.agendabot.com.br` produção
- [ ] Deploy do MCP server em produção
- [ ] Deploy da API em produção
- [ ] Configurar webhook do estabelecimento piloto para o endpoint do agente
- [ ] Monitorar primeiras 50 conversas reais
- [ ] Coletar feedback e iterar no system prompt

**Critério de aceite:** primeiro estabelecimento usando em produção com aprovação do dono.

## Critérios transversais (válidos em todas as fases)

- [ ] Logs estruturados com `session_id` em todas as operações do agente
- [ ] Erros 5xx reportados ao Sentry com contexto
- [ ] Nenhum endpoint do agente aceita `client_id` ou `establishment_id` no body
- [ ] Token de sessão expira em 30 minutos
- [ ] Histórico Redis expira em 30 minutos
- [ ] Nenhuma chamada à OpenAI sem system prompt
- [ ] Nenhuma tool call ao MCP sem header `X-MCP-Key`

## Pontos de atenção para revisitar pós-MVP

- Cache de prompt da OpenAI (quando disponível para o modelo escolhido)
- Métrica de custo por estabelecimento
- Buffer de debounce para mensagens em rajada
- Detecção de mensagens duplicadas mais robusta
- Tabela `agent_conversations` para histórico permanente (auditoria, métricas)
- Rate limiting por telefone
- Botão no painel para o dono visualizar/intervir em conversas ativas
- Multi-idioma (quando expandir além do Brasil)
- Canal interno para staff (mencionado em `01-overview.md` como escopo futuro)
