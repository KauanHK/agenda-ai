# 01 — Visão geral

## Objetivo

Implementar um agente conversacional via WhatsApp para clientes do AgendaBot, capaz de consultar serviços, verificar horários, criar, cancelar e reagendar atendimentos através de linguagem natural.

## Decisões de arquitetura

### Modelo e provedor
- **LLM:** OpenAI GPT-5-nano
- **Integração de tools:** MCP server consumido via Responses API
- **Loop de tool calling:** gerenciado pela OpenAI durante a inferência

### Topologia
- **Repositórios separados:** `agendabot-api` (existente) e `agendabot-mcp` (novo)
- **Comunicação MCP → API:** HTTP via httpx assíncrono
- **MCP server público via HTTPS** — requisito da OpenAI para alcançar o servidor durante a inferência

### Canal
- **Escopo atual:** apenas clientes via WhatsApp
- **Canal interno (staff):** fora do escopo, mas o design contempla extensão futura
- **Evolution API:** uma instância por estabelecimento, integração futura no backend fora do escopo atual

### Identidade e autorização
- **Cliente identificado pelo número de telefone** no recebimento do webhook
- **`establishment_id` resolvido pela URL do webhook** — nunca pelo conteúdo da mensagem ou pelo LLM
- **Token de sessão assinado** carrega contexto verificado para o MCP server e a API
- **Parâmetros sensíveis (client_id, establishment_id) nunca são gerados pelo LLM** — vêm do token

### Persistência de conversa
- **Redis** (já existe no stack do worker Celery)
- **TTL:** 30 minutos de inatividade
- **Chave:** `chat:{phone}:{establishment_id}`

### Escalada
- **Critérios:** reclamações, mais de 2 tentativas sem resolver, linguagem agressiva, solicitações fora do escopo
- **Ação atual:** notifica o dono do estabelecimento e continua a conversa

## Fluxo end-to-end

```
1. Cliente envia mensagem no WhatsApp
2. Evolution API → POST /agent/{establishment_id}/message (FastAPI)
3. FastAPI valida HMAC do webhook
4. FastAPI resolve client_id pelo telefone (cria se não existe)
5. FastAPI carrega histórico do Redis
6. FastAPI gera session_token assinado com {client_id, establishment_id, exp}
7. FastAPI chama OpenAI Responses API com:
   - system prompt (com contexto injetado)
   - histórico
   - mcp_servers=[{url, headers: {X-Session-Token: token}}]
8. OpenAI raciocina e chama tools no MCP server (com o header)
9. MCP server repassa header em cada chamada à FastAPI
10. FastAPI valida token, extrai contexto confiável, executa use case
11. Resposta final chega na FastAPI
12. FastAPI persiste histórico atualizado no Redis
13. FastAPI envia resposta via Evolution API ao cliente
```

## Stack consolidada

| Camada | Tecnologia |
|---|---|
| Backend (existente) | Python + FastAPI |
| Banco | PostgreSQL via SQLAlchemy |
| Workers | Celery |
| Cache/sessões | Redis |
| LLM | OpenAI GPT-5-nano |
| Tool server | FastMCP (Python) |
| WhatsApp | Evolution API |
| Token signing | JWT (HS256) com secret dedicado |

## Premissas

- Sistema base (módulos `clients`, `services`, `schedulings`, `establishments`, etc.) já está implementado.
- Evolution API já está integrada para envio de mensagens transacionais — o cliente existente será reutilizado.
- Redis já está provisionado para o worker Celery — será reutilizado.
- Use cases atuais (`CreateScheduling`, `GetAvailableSlots`, etc.) já existem e seguem o padrão de classes.

## O que NÃO está coberto neste plano

- Canal interno para staff (mencionado apenas como decisão de design futura)
- Métricas e observabilidade do agente (logs estruturados, custo por conversa)
- Testes de carga
- Multi-idioma (assume português brasileiro)
