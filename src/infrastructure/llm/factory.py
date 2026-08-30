"""Construção do chat model do provider configurado.

Um registry `_CHAT_MODEL_FACTORIES` mapeia cada provider ao seu construtor;
`ValueError` quando o provider não está no registry. O import do pacote do
provider fica dentro do construtor: faltar a dependência do provider que não
está em uso não pode quebrar o boot.
"""

from collections.abc import Callable

from langchain_core.language_models import BaseChatModel
from pydantic import SecretStr

from src.settings import LLMSettings

type ChatModelFactory = Callable[[LLMSettings, SecretStr], BaseChatModel]


def build_chat_model(settings: LLMSettings) -> BaseChatModel:
    """Constrói o chat model a partir das configurações do LLM."""
    api_key = _require_api_key(settings)

    chat_model_factory = _CHAT_MODEL_FACTORIES.get(settings.provider)
    if chat_model_factory is None:
        raise ValueError(f"Provider de LLM não suportado: {settings.provider!r}")
    return chat_model_factory(settings, api_key)


def _require_api_key(settings: LLMSettings) -> SecretStr:
    """Retorna a API key do provider selecionado ou levanta se estiver ausente."""
    api_key = settings.selected_api_key
    if api_key is None or not api_key.get_secret_value():
        raise ValueError(
            f"LLM__{settings.provider.upper()}_API_KEY não foi fornecida para o provider "
            "selecionado."
        )
    return api_key


def _build_anthropic(settings: LLMSettings, api_key: SecretStr) -> BaseChatModel:
    """Constrói o chat model da Anthropic."""
    from langchain_anthropic import ChatAnthropic

    # O construtor aceita os nomes de campo (populate_by_name), mas o Pyright só
    # reconhece os aliases; o pydantic.mypy valida a chamada de verdade.
    return ChatAnthropic(
        model=settings.model,  # pyright: ignore[reportCallIssue]
        anthropic_api_key=api_key,  # pyright: ignore[reportCallIssue]
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,  # pyright: ignore[reportCallIssue]
    )


def _build_openai(settings: LLMSettings, api_key: SecretStr) -> BaseChatModel:
    """Constrói o chat model da OpenAI."""
    from langchain_openai import ChatOpenAI

    model: BaseChatModel = ChatOpenAI(
        model=settings.model,
        api_key=api_key,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
    )
    return model


_CHAT_MODEL_FACTORIES: dict[str, ChatModelFactory] = {
    "anthropic": _build_anthropic,
    "openai": _build_openai,
}
