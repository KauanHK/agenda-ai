import pytest
from cryptography.fernet import Fernet
from pydantic import ValidationError

from app.core.security.secret_box import SecretBoxKeyError, decrypt, encrypt
from app.core.settings import Settings, settings


def test_encrypt_then_decrypt_returns_original():
    assert decrypt(encrypt("123456:ABC-token")) == "123456:ABC-token"


def test_ciphertext_does_not_contain_plaintext():
    ciphertext = encrypt("123456:ABC-token")

    assert "123456:ABC-token" not in ciphertext


def test_decrypt_with_another_key_raises_configuration_error(monkeypatch):
    ciphertext = encrypt("123456:ABC-token")
    monkeypatch.setattr(settings, "CHANNEL_SECRETS_KEY", Fernet.generate_key().decode())

    with pytest.raises(SecretBoxKeyError, match="CHANNEL_SECRETS_KEY"):
        decrypt(ciphertext)


def test_settings_rejects_invalid_key():
    with pytest.raises(ValidationError, match="CHANNEL_SECRETS_KEY"):
        Settings(CHANNEL_SECRETS_KEY="troque-me")
