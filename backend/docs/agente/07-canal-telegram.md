# 07 — Canal Telegram

Entrada por **webhook**. Nenhuma dependência do `python-telegram-bot`: a API do
Telegram é REST simples e o que precisamos são duas chamadas — usamos `httpx`.

## 7.1 Endpoint

```
POST /webhook/telegram/{establishment_id}
```

Cada estabelecimento tem o seu bot, conectado pelo painel (módulo `channels`), que
registra o webhook nesta URL. O agente não administra webhook nenhum.

| Situação | Resposta |
| --- | --- |
| `establishment_id` não é UUID | `404` |
| O diretório de canais devolve `None` (sem bot, estabelecimento inativo ou inexistente) | `404` |
| Header `X-Telegram-Bot-Api-Secret-Token` ausente ou diferente do segredo do bot (`hmac.compare_digest`) | `404` |
| `ChannelLookupError` (banco fora) | `503`, para o Telegram reenviar |
| Ok | `200 {"ok": true}` na hora |

- **Sempre `404`, nunca `401`/`403`:** um `403` confirmaria que a rota existe para
  aquele id.
- **O header é a autenticação.** O caminho é só um UUID, que não é segredo.
- O id chega como `str` e é convertido à mão: um `uuid.UUID` no caminho faria o
  FastAPI responder `422`.
- O canal é lido do banco a cada update, sem cache (`DbTelegramChannelDirectory`):
  conectar, reconectar ou desconectar vale na hora.
- **Responde `200` imediatamente** e processa em background
  (`asyncio.create_task` guardado em um set no `app.state`, para não ser coletado).
  O Telegram reentrega updates não respondidos em ~poucos segundos; um turno com
  várias tool calls passa disso.
- Erro no processamento em background nunca vira `5xx`: já respondemos.

`GET /health` responde `{"status": "ok"}` sem tocar em Redis nem no AgendaBot.

## 7.2 Parsing do update

`app/modules/agent/adapters/telegram/update_parser.py`

```python
def parse_update(
    payload: Mapping[str, Any],
    establishment: Establishment,
    *,
    phone_resolver: PhoneResolverProtocol,
    max_chars: int = 1000,
) -> IncomingMessage | None:
    """
    Converte um update do Telegram numa mensagem do domínio.

    Devolve `None` para tudo que o agente não trata: updates sem `message`, mensagens
    sem `text`, edições, mensagens de canal/grupo e mensagens de bot.
    """
```

`None` é a resposta correta, não um erro: o Telegram manda muitos tipos de update e
ignorar em silêncio é o comportamento esperado.

A mensagem sai com o `establishment` recebido: o dono do bot que recebeu o update, que
a rota resolveu pelo `establishment_id` do caminho e repassa ao
`TelegramWebhookHandler.handle_update(establishment, payload)`.

Campos usados:

| Domínio | Update |
| --- | --- |
| `channel_user_id` | `message.chat.id` |
| `display_name` | `message.from.first_name` (+ `last_name`) |
| `text` | `message.text` |
| `channel_message_id` | `message.message_id` |
| `received_at` | `message.date` (epoch → UTC) |

Limite: mensagens acima de `MAX_INPUT_CHARS` (default 1000) são truncadas antes de
chegar ao LLM.

## 7.3 Comandos

Tratados **antes** do agente, num roteador dedicado:

| Comando | Ação |
| --- | --- |
| `/start` | `ResetConversation` + mensagem de boas-vindas fixa |
| `/reset` | `ResetConversation` + confirmação |
| qualquer outro `/x` | repassado ao agente como texto normal |

```python
def match_command(text: str) -> str | None:
    """Extrai o nome do comando de uma mensagem, ou `None` se não for comando."""
```

A mensagem de boas-vindas é texto fixo, não gerada pelo LLM: é a primeira impressão e
custa uma chamada de modelo à toa.

## 7.4 Envio

`app/modules/agent/adapters/telegram/client.py`

```python
class TelegramMessenger:
    """Implementa `OutboundMessengerProtocol` sobre a Bot API."""

    async def send_text(self, conversation: ConversationRef, text: str) -> None: ...
    async def signal_typing(self, conversation: ConversationRef) -> None: ...
```

- `sendMessage` com `chat_id` = `conversation.channel_user_id`, pelo bot do
  estabelecimento da conversa: o `TelegramMessenger` resolve o canal no diretório por
  `conversation.establishment_id` e chama `/bot{token}/sendMessage`. O `httpx.AsyncClient`
  só conhece a raiz da Bot API; o token entra por chamada e nunca aparece em erro
  (`from None`) nem em log.
- Bot desconectado no meio do turno (diretório devolve `None`) ou diretório fora →
  `DeliveryError`.
- Textos acima de 4096 caracteres são quebrados em pedaços por parágrafo antes do
  envio (`split_for_telegram`, função pura em `formatting.py`).
- `429` → respeita `retry_after` do corpo e tenta uma vez; outros erros → `DeliveryError`.
- Timeout: `connect` = `AGENT_HTTP__CONNECT_TIMEOUT_SECONDS` (5 s), `read`/`write`/`pool` =
  `AGENT_HTTP__TELEGRAM_READ_TIMEOUT_SECONDS` (5 s) — a Bot API responde rápido.
- Retry de transporte **só** em `ConnectError` / `ConnectTimeout` (uma vez): aí o
  request não saiu e não há risco de mensagem duplicada. Um `ReadTimeout` /
  `WriteTimeout` — o request pode já ter chegado — vira `DeliveryError` sem repetir.
- `signal_typing` chama `sendChatAction` com `action=typing` e engole qualquer falha,
  inclusive a do diretório.

Quadro completo da política em
[`09-configuracao.md`](09-configuracao.md#96-política-de-retry-e-timeout-por-adapter).

### Formatação

`app/modules/agent/adapters/telegram/formatting.py`

```python
def to_telegram_text(raw: str) -> str:
    """Normaliza o texto do LLM para envio seguro ao Telegram."""
```

Decisão: **enviar sem `parse_mode`**. O LLM produz markdown ocasional e MarkdownV2
exige escapar 18 caracteres — um escape errado devolve `400` e o cliente não recebe
nada. A função apenas remove marcações que ficariam feias em texto puro (`**`, `##`) e
colapsa linhas em branco excessivas. Se um dia quisermos negrito, o caminho é HTML
(`parse_mode=HTML`), que tem só 3 caracteres a escapar.

## 7.5 Identidade sintética (fase 1)

`app/modules/agent/adapters/identity/synthetic_phone.py`

```python
class SyntheticPhoneResolver:
    """Deriva um telefone determinístico a partir do id do usuário no canal."""

    def resolve(self, channel: Channel, channel_user_id: str) -> str:
        """Devolve `{SYNTHETIC_PHONE_PREFIX}{9 dígitos derivados do id}`."""
```

- Determinístico: o mesmo usuário do Telegram cai sempre no mesmo cliente do AgendaBot.
- Prefixo dedicado por env (`SYNTHETIC_PHONE_PREFIX`, ex. `5547999`), para que os
  clientes criados por essa via sejam reconhecíveis no painel.
- Os 9 dígitos vêm de um `blake2b(channel_user_id, digest_size=8)` reduzido — não do
  `chat_id` cru, para não expor o id do Telegram como número de telefone.

> **Isto é um placeholder de desenvolvimento.** Cria clientes com telefone inválido no
> banco do AgendaBot; se o backend passar a enviar notificações por WhatsApp, elas vão
> para o vazio. A substituição planejada é o botão `request_contact` do Telegram, que
> entrega o número verificado pelo próprio Telegram — e só troca o adapter desta porta.
