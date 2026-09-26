"""Testes de `Settings`: grupos aninhados, delimitador e a exigência da API key."""

import pytest
from pydantic import ValidationError

from app.modules.agent.settings import Settings

_ESTABLISHMENT_ID = "01a04f5b-0e84-7530-be67-63f08e7b2269"

# Tudo que não tem default e precisa vir do ambiente.
_REQUIRED = {
    "AGENT_AGENDABOT__API_URL": "https://agenda.escaleia.cloud",
    "AGENT_AGENDABOT__MCP_URL": "https://agenda.escaleia.cloud/mcp",
    "AGENT_AGENDABOT__SERVICE_KEY": "svc-key",
    "AGENT_AGENDABOT__ESTABLISHMENT_ID": _ESTABLISHMENT_ID,
    "AGENT_TELEGRAM__BOT_TOKEN": "tg-token",
    "AGENT_TELEGRAM__WEBHOOK_SECRET": "hook-secret",
    "AGENT_TELEGRAM__ADMIN_TOKEN": "admin-token",
    "AGENT_REDIS__URL": "redis://localhost:6379/1",
}

_MANAGED = (
    *_REQUIRED,
    "AGENT_LLM__ANTHROPIC_API_KEY",
    "AGENT_LLM__OPENAI_API_KEY",
    "AGENT_LLM__PROVIDER",
)


def _set(monkeypatch: pytest.MonkeyPatch, **env: str) -> None:
    for name in _MANAGED:
        monkeypatch.delenv(name, raising=False)
    for name, value in {**_REQUIRED, **env}.items():
        monkeypatch.setenv(name, value)


def test_defaults_valem_quando_so_os_obrigatorios_estao_definidos(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set(monkeypatch, AGENT_LLM__ANTHROPIC_API_KEY="sk-ant")

    settings = Settings(_env_file=None)

    assert settings.llm.provider == "anthropic"
    assert settings.llm.model == "claude-sonnet-5"
    assert settings.llm.temperature == pytest.approx(0.3)
    assert str(settings.agendabot.establishment_id) == _ESTABLISHMENT_ID
    assert settings.agendabot.service_key.get_secret_value() == "svc-key"
    assert settings.telegram.bot_token.get_secret_value() == "tg-token"
    assert settings.conversation.max_history_turns == 10
    assert settings.http.timeout_seconds == pytest.approx(10.0)
    assert settings.http.connect_timeout_seconds == pytest.approx(5.0)
    assert settings.http.telegram_read_timeout_seconds == pytest.approx(5.0)


def test_grupos_leem_o_prefixo_com_delimitador(monkeypatch: pytest.MonkeyPatch) -> None:
    _set(
        monkeypatch,
        AGENT_LLM__ANTHROPIC_API_KEY="sk-ant",
        AGENT_AGENDABOT__API_URL="https://exemplo.test",
        AGENT_CONVERSATION__MAX_HISTORY_TURNS="7",
    )

    settings = Settings(_env_file=None)

    assert settings.agendabot.api_url == "https://exemplo.test"
    assert settings.conversation.max_history_turns == 7


def test_variaveis_obrigatorias_ausentes_falham_no_boot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in _MANAGED:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("AGENT_LLM__ANTHROPIC_API_KEY", "sk-ant")

    with pytest.raises(ValidationError, match="redis"):
        Settings(_env_file=None)


def test_provider_selecionado_sem_a_sua_key_falha_no_boot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set(monkeypatch, AGENT_LLM__PROVIDER="anthropic")  # sem AGENT_LLM__ANTHROPIC_API_KEY

    with pytest.raises(ValidationError, match="AGENT_LLM__ANTHROPIC_API_KEY"):
        Settings(_env_file=None)


def test_openai_como_provider_exige_a_openai_key(monkeypatch: pytest.MonkeyPatch) -> None:
    _set(monkeypatch, AGENT_LLM__PROVIDER="openai", AGENT_LLM__OPENAI_API_KEY="sk-openai")

    settings = Settings(_env_file=None)

    assert settings.llm.provider == "openai"


def test_groq_como_provider_exige_a_groq_key(monkeypatch: pytest.MonkeyPatch) -> None:
    _set(monkeypatch, AGENT_LLM__PROVIDER="groq", AGENT_LLM__GROQ_API_KEY="gsk-test")

    settings = Settings(_env_file=None)

    assert settings.llm.provider == "groq"
    assert settings.llm.selected_api_key is not None
    assert settings.llm.selected_api_key.get_secret_value() == "gsk-test"


def test_groq_como_provider_sem_a_groq_key_falha_no_boot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set(monkeypatch, AGENT_LLM__PROVIDER="groq")  # sem AGENT_LLM__GROQ_API_KEY

    with pytest.raises(ValidationError, match="AGENT_LLM__GROQ_API_KEY"):
        Settings(_env_file=None)
