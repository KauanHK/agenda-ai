import dataclasses
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt

from app.core.exceptions import UnauthorizedError
from app.core.security.access_tokens import (
    TokenIdentity,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)
from app.core.security.jwt import decode_token
from app.core.security.passwords import hash_password, verify_password
from app.core.settings import settings


@pytest.fixture
def identity() -> TokenIdentity:
    return TokenIdentity(subject=uuid.uuid4())


@pytest.fixture
def expired_token() -> str:
    now = datetime.now(tz=UTC)
    claims = {
        "sub": str(uuid.uuid4()),
        "type": "access",
        "iat": now - timedelta(hours=2),
        "exp": now - timedelta(hours=1),
    }
    return jwt.encode(claims, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def test_hash_password_returns_string():
    result = hash_password("minhasenha")
    assert isinstance(result, str)


def test_hash_password_is_not_plaintext():
    result = hash_password("minhasenha")
    assert result != "minhasenha"


def test_hash_password_same_input_produces_different_hashes():
    hash1 = hash_password("minhasenha")
    hash2 = hash_password("minhasenha")
    assert hash1 != hash2


def test_verify_password_correct():
    password = "minhasenha"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True


def test_verify_password_wrong_password():
    hashed = hash_password("minhasenha")
    assert verify_password("senhaerrada", hashed) is False


def test_create_access_token_returns_string(identity):
    token = create_access_token(identity)
    assert isinstance(token, str)


def test_create_access_token_claims(identity):
    token = create_access_token(identity)
    payload = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )

    assert payload["sub"] == str(identity.subject)
    assert payload["type"] == "access"


def test_create_access_token_expiry(identity):
    before = datetime.now(tz=UTC).replace(microsecond=0)
    token = create_access_token(identity)
    after = datetime.now(tz=UTC).replace(microsecond=0)

    payload = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )
    exp = datetime.fromtimestamp(payload["exp"], tz=UTC)

    expected_min = before + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES_MIN)
    expected_max = after + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES_MIN)

    assert expected_min <= exp <= expected_max


def test_create_refresh_token_returns_string(identity):
    token = create_refresh_token(identity)
    assert isinstance(token, str)


def test_create_refresh_token_claims(identity):
    token = create_refresh_token(identity)
    payload = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )

    assert payload["sub"] == str(identity.subject)
    assert payload["type"] == "refresh"


def test_create_refresh_token_expiry(identity):
    before = datetime.now(tz=UTC).replace(microsecond=0)
    token = create_refresh_token(identity)
    after = datetime.now(tz=UTC).replace(microsecond=0)

    payload = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )
    exp = datetime.fromtimestamp(payload["exp"], tz=UTC)

    expected_min = before + timedelta(days=settings.REFRESH_TOKEN_EXPIRES_DAYS)
    expected_max = after + timedelta(days=settings.REFRESH_TOKEN_EXPIRES_DAYS)

    assert expected_min <= exp <= expected_max


def test_access_and_refresh_tokens_are_different(identity):
    access = create_access_token(identity)
    refresh = create_refresh_token(identity)
    assert access != refresh


def test_decode_token_valid(identity):
    token = create_access_token(identity)
    claims = decode_token(token)

    assert claims["sub"] == str(identity.subject)
    assert claims["type"] == "access"


def test_decode_token_expired_raises_unauthorized(expired_token):
    with pytest.raises(UnauthorizedError, match=r"Token expired\."):
        decode_token(expired_token)


def test_decode_token_invalid_string_raises_unauthorized():
    with pytest.raises(UnauthorizedError, match=r"Invalid token\."):
        decode_token("token.invalido.aqui")


def test_decode_token_wrong_secret(identity):
    claims = {
        "sub": str(identity.subject),
        "type": "access",
        "iat": datetime.now(tz=UTC),
        "exp": datetime.now(tz=UTC) + timedelta(minutes=30),
    }
    token_wrong_secret = jwt.encode(
        claims, "wrong-secret", algorithm=settings.JWT_ALGORITHM
    )

    with pytest.raises(UnauthorizedError, match=r"Invalid token\."):
        decode_token(token_wrong_secret)


def test_decode_token_tampered_payload(identity):
    token = create_access_token(identity)
    header, payload, signature = token.split(".")
    tampered = f"{header}.AAAA{payload}.{signature}"

    with pytest.raises(UnauthorizedError):
        decode_token(tampered)


def test_token_identity_is_frozen():
    identity = TokenIdentity(subject=uuid.uuid4())
    with pytest.raises(dataclasses.FrozenInstanceError):
        identity.subject = uuid.uuid4()  # type: ignore


def test_token_identity_equality():
    subject = uuid.uuid4()
    a = TokenIdentity(subject=subject)
    b = TokenIdentity(subject=subject)
    assert a == b


def test_decode_access_token_valid(identity):
    token = create_access_token(identity)
    claims = decode_access_token(token)

    assert claims["sub"] == str(identity.subject)
    assert claims["type"] == "access"


def test_decode_access_token_rejects_refresh_type(identity):
    token = create_refresh_token(identity)
    with pytest.raises(UnauthorizedError, match="Invalid token type"):
        decode_access_token(token)


def test_decode_access_token_expired_raises_unauthorized(expired_token):
    with pytest.raises(UnauthorizedError, match=r"Token expired\."):
        decode_access_token(expired_token)


def test_decode_access_token_invalid_string_raises_unauthorized():
    with pytest.raises(UnauthorizedError, match=r"Invalid token\."):
        decode_access_token("token.invalido.aqui")


def test_decode_refresh_token_valid(identity):
    token = create_refresh_token(identity)
    claims = decode_refresh_token(token)

    assert claims["sub"] == str(identity.subject)
    assert claims["type"] == "refresh"


def test_decode_refresh_token_rejects_access_type(identity):
    token = create_access_token(identity)
    with pytest.raises(UnauthorizedError, match="Invalid token type"):
        decode_refresh_token(token)


def test_decode_refresh_token_expired_raises_unauthorized(expired_token):
    with pytest.raises(UnauthorizedError, match=r"Token expired\."):
        decode_refresh_token(expired_token)


def test_decode_refresh_token_invalid_string_raises_unauthorized():
    with pytest.raises(UnauthorizedError, match=r"Invalid token\."):
        decode_refresh_token("token.invalido.aqui")
