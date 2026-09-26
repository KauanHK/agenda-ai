"""Testes de `build_chat_model`: seleção de provider e exigência da API key."""

import pytest
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq
from pydantic import SecretStr

from app.modules.agent.adapters.llm.factory import build_chat_model
from app.modules.agent.settings import LLMSettings


def test_provider_anthropic_constroi_chat_anthropic_com_os_parametros() -> None:
    settings = LLMSettings(
        provider="anthropic",
        model="claude-sonnet-5",
        temperature=0.3,
        max_tokens=1024,
        anthropic_api_key=SecretStr("sk-ant-test"),
    )

    model = build_chat_model(settings)

    assert isinstance(model, ChatAnthropic)
    assert model.model == "claude-sonnet-5"
    assert model.temperature == pytest.approx(0.3)
    assert model.max_tokens == 1024


def test_provider_groq_constroi_chat_groq_com_os_parametros() -> None:
    settings = LLMSettings(
        provider="groq",
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        max_tokens=1024,
        groq_api_key=SecretStr("gsk-test"),
    )

    model = build_chat_model(settings)

    assert isinstance(model, ChatGroq)
    assert model.model_name == "llama-3.3-70b-versatile"
    assert model.temperature == pytest.approx(0.3)
    assert model.max_tokens == 1024


def test_sem_a_api_key_do_provider_selecionado_levanta_value_error() -> None:
    settings = LLMSettings(provider="anthropic", anthropic_api_key=None)

    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        build_chat_model(settings)


def test_api_key_em_branco_tambem_levanta_value_error() -> None:
    # `.env` com a linha presente mas vazia não passa como credencial.
    settings = LLMSettings(provider="anthropic", anthropic_api_key=SecretStr(""))

    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        build_chat_model(settings)
