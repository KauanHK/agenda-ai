"""Identidade da fase 1: telefone sintético determinístico a partir do canal."""

import hashlib

from src.domain.entities import Channel

_SUFFIX_DIGITS = 6


class SyntheticPhoneResolver:
    """Deriva um telefone determinístico do id do usuário no canal.

    Não há identidade real ainda: cada `channel_user_id` mapeia sempre para o
    mesmo número, montado a partir de um prefixo fixo e de um sufixo derivado por
    hash SHA-256. Implementa `PhoneResolverProtocol`; trocar isto por
    `request_contact` é trocar só este adapter.
    """

    def __init__(self, prefix: str) -> None:
        self._prefix = prefix

    def resolve(self, channel: Channel, channel_user_id: str) -> str:
        """Devolve o telefone canônico do contato, em E.164 sem o `+`."""
        seed = f"{channel.value}:{channel_user_id}".encode()
        digest = hashlib.sha256(seed).digest()
        suffix = int.from_bytes(digest, "big") % 10**_SUFFIX_DIGITS
        return f"{self._prefix}{suffix:0{_SUFFIX_DIGITS}d}"
