"""Testes de `Settings`: defaults e a exigência da API key do provider."""

import pytest
from pydantic import ValidationError

from src.settings import Settings

_SECRETS = {
    "AGENDABOT_SERVICE_KEY": "svc-key",
    "TELEGRAM_BOT_TOKEN": "tg-token",
    "TELEGRAM_WEBHOOK_SECRET": "hook-secret",
}


def _set(monkeypatch: pytest.MonkeyPatch, **env: str) -> None:
    for name in (*_SECRETS, "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "LLM_PROVIDER"):
        monkeypatch.delenv(name, raising=False)
    for name, value in {**_SECRETS, **env}.items():
        monkeypatch.setenv(name, value)


def test_defaults_valem_quando_so_os_segredos_estao_definidos(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set(monkeypatch, ANTHROPIC_API_KEY="sk-ant")

    settings = Settings(_env_file=None)

    assert settings.llm_provider == "anthropic"
    assert settings.llm_model == "claude-sonnet-5"
    assert settings.llm_temperature == pytest.approx(0.3)
    assert str(settings.establishment_id) == "01a04f5b-0e84-7530-be67-63f08e7b2269"
    assert settings.redis_url.endswith("/1")
    assert settings.agendabot_service_key.get_secret_value() == "svc-key"


def test_provider_selecionado_sem_a_sua_key_falha_no_boot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set(monkeypatch, LLM_PROVIDER="anthropic")  # sem ANTHROPIC_API_KEY

    with pytest.raises(ValidationError, match="ANTHROPIC_API_KEY"):
        Settings(_env_file=None)


def test_openai_como_provider_exige_a_openai_key(monkeypatch: pytest.MonkeyPatch) -> None:
    _set(monkeypatch, LLM_PROVIDER="openai", OPENAI_API_KEY="sk-openai")

    settings = Settings(_env_file=None)

    assert settings.llm_provider == "openai"
