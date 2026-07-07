# 07 — Integração com Evolution API

## Premissa

A Evolution API já está integrada ao backend para envio de mensagens transacionais. Este documento cobre o que muda especificamente para suportar o agente conversacional.

## Configuração de instâncias

Uma instância Evolution por estabelecimento. Cada instância tem o webhook configurado para apontar para:

```
https://api.agendabot.com.br/agent/{establishment_id}/message
```

O `{establishment_id}` resolve o estabelecimento sem depender do conteúdo da mensagem. Configurar via Evolution API ao provisionar um estabelecimento — provavelmente já existe lógica para criar instâncias.

## Eventos relevantes

Filtrar para receber apenas mensagens de texto recebidas:

- Evento: `messages.upsert`
- Direção: `fromMe: false`
- Tipo: `conversation` ou `extendedTextMessage`

Outras mensagens (status, reações, imagens) são ignoradas no MVP.

## Validação do webhook

A Evolution API permite configurar um secret enviado no header dos webhooks. Validar antes de processar.

`app/modules/agent/dependencies.py`:

```python
import hmac
from fastapi import Request, HTTPException, Depends
from app.core.config import settings

async def verify_evolution_webhook(request: Request) -> None:
    provided = request.headers.get("apikey", "")
    expected = settings.EVOLUTION_WEBHOOK_SECRET

    if not hmac.compare_digest(provided, expected):
        raise HTTPException(401, "Invalid webhook signature")
```

Aplicar como dependência na rota:

```python
@router.post(
    "/{establishment_id}/message",
    dependencies=[Depends(verify_evolution_webhook)],
)
```

## Parsing do payload

A Evolution API envia uma estrutura aninhada. Extrair telefone e texto de forma resiliente — diferentes tipos de mensagem têm o texto em campos diferentes.

```python
def extract_message(payload: dict) -> tuple[str, str] | None:
    """Retorna (phone, text) ou None se não for processável."""
    data = payload.get("data", {})

    # Ignorar mensagens próprias
    if data.get("key", {}).get("fromMe", False):
        return None

    # Extrair telefone (remover @s.whatsapp.net etc)
    remote_jid = data.get("key", {}).get("remoteJid", "")
    phone = remote_jid.split("@")[0]
    if not phone:
        return None

    # Extrair texto
    message = data.get("message", {})
    text = (
        message.get("conversation")
        or message.get("extendedTextMessage", {}).get("text")
    )
    if not text:
        return None

    return phone, text
```

## Envio de resposta

Reutilizar o cliente Evolution já existente no projeto. O método de envio aceita o `establishment_id` para resolver qual instância usar.

Pseudo-código (adaptar ao cliente real):

```python
await evolution_client.send_text(
    establishment_id=establishment_id,
    to=phone,  # com ou sem @s.whatsapp.net dependendo do cliente
    text=reply,
)
```

## Tratamento de mensagens não suportadas

Para imagens, áudios e outras mídias no MVP:

```python
if not extracted:
    await evolution_client.send_text(
        establishment_id=establishment_id,
        to=phone,
        text="Por enquanto consigo entender só mensagens de texto 😅 Pode me escrever o que precisa?",
    )
    return {"status": "ignored"}
```

## Idempotência

A Evolution API pode reentregar webhooks em caso de falha. Para evitar processar a mesma mensagem duas vezes:

- Cada evento tem um `data.key.id` único
- Usar Redis com TTL curto para marcar mensagens já processadas:

```python
async def is_duplicate(message_id: str, redis) -> bool:
    key = f"processed:{message_id}"
    # SET com NX (only if not exists) e EX (TTL)
    result = await redis.set(key, "1", nx=True, ex=300)  # 5 min
    return result is None  # None = já existia
```

## Ordem de processamento

Se o cliente enviar várias mensagens em rajada, o ideal é aguardar um pequeno debounce antes de chamar o LLM, juntando as mensagens. Isso evita respostas fragmentadas.

Implementação simples no MVP: processar mensagem por mensagem. A latência da OpenAI já cria um "buffer" natural — quando a segunda mensagem chega, a primeira normalmente ainda está sendo processada.

Otimização futura: buffer de N segundos no Redis antes de chamar o LLM.

## Rate limiting

Adicionar rate limit por telefone para evitar abuse — ex: máximo 30 mensagens/hora por número. Implementar como middleware ou dependência usando Redis.

## Variáveis de ambiente

```
EVOLUTION_WEBHOOK_SECRET=<configurado na Evolution API>
EVOLUTION_API_URL=https://evolution.agendabot.com.br
EVOLUTION_API_KEY=<chave global da Evolution>
```
