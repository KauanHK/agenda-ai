"""Testes de `RedisSessionTokenCache` contra um Redis falso (fakeredis)."""

import uuid
from datetime import UTC, datetime, timedelta

from fakeredis import FakeAsyncRedis
from redis.exceptions import RedisError

from src.domain.entities import BookingSession
from src.infrastructure.redis.session_cache import RedisSessionTokenCache

_NOW = datetime(2026, 8, 29, 12, 0, tzinfo=UTC)
_PHONE = "5547999123456"


def _session(
    *,
    token: str = "jwt",
    expires_at: datetime = _NOW + timedelta(minutes=10),
) -> BookingSession:
    return BookingSession(
        token=token,
        phone=_PHONE,
        client_id=uuid.UUID("01a04f64-0000-7000-8000-000000000000"),
        client_name="Kauan",
        expires_at=expires_at,
        is_new_client=True,
    )


def _cache(client: object) -> RedisSessionTokenCache:
    return RedisSessionTokenCache(
        client,  # type: ignore[arg-type]
        clock=lambda: _NOW,
        refresh_margin_seconds=60,
    )


async def test_round_trip_preserva_a_sessao() -> None:
    cache = _cache(FakeAsyncRedis())
    session = _session()

    await cache.put(session)

    assert await cache.get(_PHONE) == session


async def test_miss_devolve_none() -> None:
    assert await _cache(FakeAsyncRedis()).get("desconhecido") is None


async def test_a_chave_nao_expoe_o_telefone() -> None:
    redis = FakeAsyncRedis()
    await _cache(redis).put(_session())

    keys = [key.decode() for key in await redis.keys("*")]

    assert keys
    assert all(_PHONE not in key for key in keys)
    assert all(key.startswith("agente:session:") for key in keys)


async def test_ttl_expira_antes_do_token_menos_a_margem() -> None:
    redis = FakeAsyncRedis()
    await _cache(redis).put(_session(expires_at=_NOW + timedelta(minutes=10)))

    [key] = await redis.keys("*")

    assert 0 < await redis.ttl(key) <= 600 - 60


async def test_ttl_minimo_de_um_segundo_para_sessao_no_limite() -> None:
    redis = FakeAsyncRedis()
    await _cache(redis).put(_session(expires_at=_NOW + timedelta(seconds=5)))

    [key] = await redis.keys("*")

    assert await redis.ttl(key) == 1


class _BoomRedis:
    async def get(self, name: object) -> object:
        raise RedisError("redis fora")

    async def set(self, *args: object, **kwargs: object) -> object:
        raise RedisError("redis fora")


async def test_get_engole_falha_de_redis() -> None:
    assert await _cache(_BoomRedis()).get(_PHONE) is None


async def test_put_engole_falha_de_redis() -> None:
    await _cache(_BoomRedis()).put(_session())  # não levanta
