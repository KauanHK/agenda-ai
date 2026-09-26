"""Testes de `parse_update`: o que vira `IncomingMessage` e o que vira `None`."""

import uuid
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.modules.agent.adapters.telegram.update_parser import parse_update
from app.modules.agent.domain.entities import Channel, Establishment
from tests.modules.agent.fakes.phone_resolver import FakePhoneResolver

_SENDER = {"id": 123456, "is_bot": False, "first_name": "Kauan", "last_name": "Kaestner"}
_CHAT = {"id": 123456, "type": "private"}
_ESTABLISHMENT = Establishment(
    id=uuid.UUID("01a04f64-0000-7000-8000-00000000e001"),
    timezone=ZoneInfo("America/Sao_Paulo"),
)


def _update(
    *,
    sender: dict[str, Any] | None = None,
    chat: dict[str, Any] | None = None,
    text: str | None = "quero marcar um horário",
) -> dict[str, Any]:
    message: dict[str, Any] = {
        "message_id": 55,
        "date": 1_756_558_800,
        "chat": chat or _CHAT,
        "from": sender or _SENDER,
    }
    if text is not None:
        message["text"] = text
    return {"update_id": 1, "message": message}


def _parse(payload: dict[str, Any], *, max_chars: int = 1000) -> Any:
    return parse_update(
        payload,
        FakePhoneResolver("5547999111222"),
        establishment=_ESTABLISHMENT,
        max_chars=max_chars,
    )


def test_mensagem_de_texto_privada_vira_incoming_message() -> None:
    result = _parse(_update())

    assert result is not None
    assert result.establishment == _ESTABLISHMENT
    assert result.contact.channel is Channel.TELEGRAM
    assert result.contact.channel_user_id == "123456"
    assert result.contact.display_name == "Kauan Kaestner"
    assert result.contact.phone == "5547999111222"
    assert result.text == "quero marcar um horário"
    assert result.channel_message_id == "55"
    assert result.received_at == datetime.fromtimestamp(1_756_558_800, tz=UTC)


def test_so_first_name_ainda_da_display_name() -> None:
    result = _parse(_update(sender={"id": 1, "is_bot": False, "first_name": "Ana"}))

    assert result is not None
    assert result.contact.display_name == "Ana"


def test_sem_nome_nenhum_display_name_fica_none() -> None:
    result = _parse(_update(sender={"id": 1, "is_bot": False}))

    assert result is not None
    assert result.contact.display_name is None


def test_trunca_texto_acima_do_limite() -> None:
    result = _parse(_update(text="a" * 5000), max_chars=1000)

    assert result is not None
    assert len(result.text) == 1000


def test_update_sem_message_vira_none() -> None:
    assert _parse({"update_id": 1, "edited_message": {"text": "oi"}}) is None


def test_mensagem_sem_texto_vira_none() -> None:
    assert _parse(_update(text=None)) is None


def test_mensagem_de_bot_vira_none() -> None:
    assert _parse(_update(sender={"id": 9, "is_bot": True, "first_name": "Bot"})) is None


def test_conversa_de_grupo_vira_none() -> None:
    assert _parse(_update(chat={"id": -100, "type": "group"})) is None
