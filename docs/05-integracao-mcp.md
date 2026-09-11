# 05 — Integração com o AgendaBot

Duas integrações distintas com o mesmo host: a **API HTTP** (emite a sessão) e o
**MCP server** (executa as tools). São arquivos separados porque mudam por motivos
diferentes.

## 5.1 Emissão da sessão

`POST https://agenda.escaleia.cloud/api/agent/{establishment_id}/sessions`

Headers:

```
X-Service-Key: <AGENDABOT_SERVICE_KEY>
Content-Type: application/json
```

Body:

```json
{ "phone": "554792277579", "name": "Kauan" }
```

Resposta `201`:

```json
{
  "session_token": "<jwt>",
  "expires_in_minutes": 10,
  "client": { "id": "01a04f64-...", "name": "Kauan" },
  "is_new_client": true
}
```

`expires_at` é calculado no adapter: `now + expires_in_minutes`. O agente **nunca**
confia num token além disso.

### Mapeamento de erro

| Status | Erro de domínio | Observação |
| --- | --- | --- |
| 403 | `ClientBlockedError` | cliente inativo no estabelecimento |
| 404 | `BookingSessionError` | estabelecimento inexistente ou inativo |
| 401 | `BookingSessionError` | `X-Service-Key` errada — falha de configuração |
| 409 / 422 | `BookingSessionError` | telefone inválido, corrida na criação |
| 5xx / timeout | `BookingSessionError` | com retry (abaixo) |

Retry só nos casos idempotentes-seguros — falha de conexão, timeout
(`connect` / `read` / `write` / `pool`) e `5xx`: até 3 tentativas, backoff
exponencial a partir de 200 ms. `4xx` nunca é repetido. Repetir a emissão é
seguro: o AgendaBot resolve o cliente pelo telefone e não duplica cadastro. O
`connect` usa `HTTP__CONNECT_TIMEOUT_SECONDS`; o resto, `HTTP__TIMEOUT_SECONDS`.
Quadro completo em [`09-configuracao.md`](09-configuracao.md#96-política-de-retry-e-timeout-por-adapter).

O `X-Service-Key` só existe dentro de `infrastructure/agendabot/` — nunca é logado,
nunca entra em mensagem de erro, nunca chega ao LLM.

## 5.2 Carregamento das tools

`POST https://agenda.escaleia.cloud/mcp` (Streamable HTTP), autenticado com
`Authorization: Bearer <session_token>`.

O servidor valida o token num `TokenVerifier`: um token inválido derruba a **conexão**
com 401, antes de qualquer tool rodar. Consequência prática: o token não pode expirar
no meio do turno, e a conexão não pode ser reaproveitada entre clientes.

Implementação com `langchain-mcp-adapters`:

```python
async def tools_for(self, session_token: str) -> Sequence[BaseTool]:
    """Abre uma conexão MCP autenticada e devolve as tools carregadas."""

    client = MultiServerMCPClient(
        {
            "agendabot": {
                "url": self._url,
                "transport": "streamable_http",
                "headers": {"Authorization": f"Bearer {session_token}"},
            }
        }
    )
    return await client.get_tools()
```

Regras:

- **Uma conexão por turno, por cliente.** Nunca cachear tools entre contatos: o token
  é a identidade, e reusar tools de outra sessão agendaria para o cliente errado.
- O *schema* das tools é cacheável, o *cliente* não. Otimização deixada para depois,
  e só se medir.
- Timeout total do carregamento: `HTTP__MCP_TIMEOUT_SECONDS` (default 15 s), via
  `asyncio.timeout`. **Sem retry**: o handshake do protocolo MCP não é
  comprovadamente idempotente e o custo de falhar aqui é só uma resposta em
  linguagem natural. Qualquer falha (timeout, `401`, servidor fora) vira
  `BookingSessionError`.

## 5.3 Contrato das tools

O agente não redeclara as tools: elas chegam do servidor com nome, descrição e schema.
As descrições vêm em pt-BR e já instruem o fluxo — o system prompt não precisa repetir
o que cada tool faz.

| Tool | Args | Devolve |
| --- | --- | --- |
| `list_services` | — | `[{service_id, name, description, duration_minutes, price}]` |
| `list_available_slots` | `service_id: uuid`, `day: date (AAAA-MM-DD)` | `[{starts_at, ends_at}]` |
| `create_scheduling` | `service_id: uuid`, `starts_at: datetime ISO` | `{scheduling_id, starts_at, ends_at, status, service_id, service_name}` |
| `list_my_schedulings` | — | lista do mesmo formato acima |
| `cancel_scheduling` | `scheduling_id: uuid` | idem |
| `reschedule_scheduling` | `scheduling_id: uuid`, `new_starts_at: datetime ISO` | idem |

Nenhuma tool aceita `client_id` ou `establishment_id`: os dois vêm do token. O LLM não
tem como preenchê-los, e o prompt não deve mencioná-los.

## 5.4 Envelope de resposta

Toda tool responde em um dos dois formatos:

```json
{ "success": true, "data": ... }
{ "success": false, "error_code": "...", "message": "...", "details": {} }
```

O `message` do erro já está em pt-BR e adequado a ser parafraseado ao cliente. O
agente **não** faz `try/except` em cima disso: o envelope de erro é entregue ao LLM
como resultado da tool, e ele decide o próximo passo.

### Catálogo de `error_code`

| `error_code` | Significado | Comportamento esperado do agente |
| --- | --- | --- |
| `service_unavailable` | serviço inexistente/indisponível | reconsultar `list_services` |
| `scheduling_not_found` | agendamento inexistente | reconsultar `list_my_schedulings` |
| `past_datetime` | horário já passou | pedir outro horário, conferindo a data atual |
| `closed_on_weekday` | fechado nesse dia da semana | propor outro dia |
| `outside_operating_hours` | fora do expediente | oferecer horários de `list_available_slots` |
| `establishment_unavailable` | bloqueio na agenda | propor outro horário |
| `no_professional_available` | vaga tomada nesse horário | reconsultar slots e oferecer os atuais |
| `no_professionals` | sem profissionais cadastrados | avisar que não há atendimento |
| `scheduling_not_changeable` | agendamento não alterável | explicar e sugerir falar com o estabelecimento |
| `validation_error` | argumento malformado | corrigir o argumento e repetir |
| `internal_error` | falha inesperada no backend | pedir para tentar de novo em instantes |

Esse catálogo é replicado no system prompt de forma condensada (ver
[`06-agente-langgraph.md`](06-agente-langgraph.md)).
