"""Configuração do agente, carregada uma única vez do ambiente.

Este é o único módulo do projeto que lê variáveis de ambiente. Todo o resto recebe
os valores já prontos, por injeção.
"""

from typing import Literal, Self
from uuid import UUID

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuração do agente, carregada do ambiente (ou de um arquivo `.env`)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # AgendaBot
    agendabot_api_url: str
    agendabot_mcp_url: str
    agendabot_service_key: SecretStr
    establishment_id: UUID
    establishment_timezone: str = "America/Sao_Paulo"

    # Telegram
    telegram_bot_token: SecretStr
    telegram_webhook_secret: SecretStr

    # LLM
    llm_provider: Literal["anthropic", "openai"] = "anthropic"
    llm_model: str = "claude-sonnet-5"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 1024
    anthropic_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None

    # Redis
    redis_url: str

    # Conversa e limites do agente
    conversation_ttl_minutes: int = 1440
    max_history_messages: int = 10
    max_agent_steps: int = 8
    max_input_chars: int = 1000
    session_refresh_margin_seconds: int = 60

    # Identidade (fase 1)
    synthetic_phone_prefix: str = "5547999"

    # HTTP / MCP
    http_timeout_seconds: float = 10.0
    mcp_timeout_seconds: float = 15.0

    # Observabilidade
    log_level: str = "INFO"

    @model_validator(mode="after")
    def _require_selected_provider_key(self) -> Self:
        """Falha no boot se a API key do provider escolhido não foi fornecida.

        Falhar aqui é melhor que falhar no primeiro cliente.
        """
        provider_keys: dict[str, SecretStr | None] = {
            "anthropic": self.anthropic_api_key,
            "openai": self.openai_api_key,
        }
        if provider_keys[self.llm_provider] is None:
            raise ValueError(
                f"LLM_PROVIDER={self.llm_provider!r} exige a variável "
                f"{self.llm_provider.upper()}_API_KEY."
            )
        return self
