"""Construção do chat model do provider configurado.

Um `match` sobre o provider, um construtor por branch, `ValueError` no default.
O import do pacote do provider fica dentro do branch: faltar a dependência do
provider que não está em uso não pode quebrar o boot.
"""

from langchain_core.language_models import BaseChatModel

from src.settings import LLMSettings


def build_chat_model(settings: LLMSettings) -> BaseChatModel:
    """Constrói o chat model a partir das configurações do LLM."""
    api_key = settings.selected_api_key
    if api_key is None or not api_key.get_secret_value():
        raise ValueError(
            f"LLM__{settings.provider.upper()}_API_KEY não foi fornecida para o provider "
            "selecionado."
        )

    match settings.provider:
        case "anthropic":
            from langchain_anthropic import ChatAnthropic

            return ChatAnthropic(
                model=settings.model,
                anthropic_api_key=api_key,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
            )
        case "openai":
            from langchain_openai import ChatOpenAI

            openai_model: BaseChatModel = ChatOpenAI(
                model=settings.model,
                api_key=api_key,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
            )
            return openai_model
        case _:  # pragma: no cover — o Literal fecha o conjunto; ramo defensivo.
            raise ValueError(f"Provider de LLM não suportado: {settings.provider!r}")
