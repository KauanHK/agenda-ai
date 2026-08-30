"""Conversão de um update cru do Telegram numa `IncomingMessage` do domínio.

`None` é a resposta correta — não um erro — para tudo que o agente não trata: o
Telegram manda muitos tipos de update e ignorar em silêncio é o comportamento
esperado. O webhook responde `200` de qualquer forma.
"""

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from src.application.ports.phone_resolver import PhoneResolverProtocol
from src.domain.entities import Channel, Contact, IncomingMessage

_DEFAULT_MAX_CHARS = 1000


def parse_update(
    payload: Mapping[str, Any],
    phone_resolver: PhoneResolverProtocol,
    *,
    max_chars: int = _DEFAULT_MAX_CHARS,
) -> IncomingMessage | None:
    """Traduz o update numa mensagem do domínio, ou devolve `None` se não se aplica.

    Devolve `None` para: updates sem `message` (edições, callbacks, posts de
    canal), mensagens sem `text`, mensagens de bot e conversas que não são
    privadas (grupo, supergrupo, canal).

    Mensagens acima de `max_chars` são truncadas antes de seguir para o agente.
    """
    message = payload.get("message")
    if not isinstance(message, Mapping):
        return None

    text = message.get("text")
    if not isinstance(text, str):
        return None

    chat = message.get("chat")
    if not isinstance(chat, Mapping) or chat.get("type") != "private":
        return None

    sender = message.get("from")
    if not isinstance(sender, Mapping) or sender.get("is_bot"):
        return None

    channel_user_id = str(chat["id"])
    contact = Contact(
        channel=Channel.TELEGRAM,
        channel_user_id=channel_user_id,
        display_name=_display_name(sender),
        phone=phone_resolver.resolve(Channel.TELEGRAM, channel_user_id),
    )
    return IncomingMessage(
        contact=contact,
        text=text[:max_chars],
        channel_message_id=str(message["message_id"]),
        received_at=datetime.fromtimestamp(message["date"], tz=UTC),
    )


def _display_name(sender: Mapping[str, Any]) -> str | None:
    """Junta `first_name` e `last_name` do remetente, ou `None` se nada veio."""
    parts = [sender.get("first_name"), sender.get("last_name")]
    name = " ".join(part for part in parts if isinstance(part, str) and part)
    return name or None
