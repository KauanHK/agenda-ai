"""Cache do token de sessão no Redis.

Chave: `agente:session:{sha256(phone)}` — o telefone nunca vai em claro na chave.
Ao contrário do checkpointer, uma falha de Redis aqui degrada performance, não
funcionalidade: `get` devolve `None`, `put` não levanta, e ambos logam em
`warning`. O `BookingSessionProvider` apenas reemite o token.
"""

import hashlib
import json
import logging
import uuid
from collections.abc import Callable
from datetime import datetime

from redis.asyncio import Redis
from redis.exceptions import RedisError

from src.domain.entities import BookingSession

logger = logging.getLogger(__name__)

_KEY_PREFIX = "agente:session:"
_MIN_TTL_SECONDS = 1


class RedisSessionTokenCache:
    """Guarda a sessão emitida no Redis. Implementa `SessionTokenCacheProtocol`."""

    def __init__(
        self,
        client: Redis,
        *,
        clock: Callable[[], datetime],
        refresh_margin_seconds: int,
    ) -> None:
        self._client = client
        self._clock = clock
        self._refresh_margin_seconds = refresh_margin_seconds

    async def get(self, phone: str) -> BookingSession | None:
        """Devolve a sessão cacheada para o telefone, ou `None` em miss/falha."""
        try:
            raw = await self._client.get(_key_for(phone))
        except RedisError:
            logger.warning("Cache de sessão indisponível na leitura", exc_info=True)
            return None
        if raw is None:
            return None
        return _decode(raw, phone)

    async def put(self, session: BookingSession) -> None:
        """Guarda a sessão com um TTL que expira antes do token real."""
        try:
            await self._client.set(
                _key_for(session.phone),
                _encode(session),
                ex=self._ttl_seconds(session),
            )
        except RedisError:
            logger.warning("Cache de sessão indisponível na escrita", exc_info=True)

    def _ttl_seconds(self, session: BookingSession) -> int:
        """Vida da entrada: até `refresh_margin_seconds` antes da expiração."""
        remaining = (session.expires_at - self._clock()).total_seconds()
        return max(_MIN_TTL_SECONDS, int(remaining - self._refresh_margin_seconds))


def _key_for(phone: str) -> str:
    return f"{_KEY_PREFIX}{hashlib.sha256(phone.encode()).hexdigest()}"


def _encode(session: BookingSession) -> str:
    return json.dumps(
        {
            "token": session.token,
            "client_id": str(session.client_id),
            "client_name": session.client_name,
            "expires_at": session.expires_at.isoformat(),
            "is_new_client": session.is_new_client,
        }
    )


def _decode(raw: bytes | str, phone: str) -> BookingSession:
    data = json.loads(raw)
    return BookingSession(
        token=data["token"],
        phone=phone,
        client_id=uuid.UUID(data["client_id"]),
        client_name=data["client_name"],
        expires_at=datetime.fromisoformat(data["expires_at"]),
        is_new_client=data["is_new_client"],
    )
