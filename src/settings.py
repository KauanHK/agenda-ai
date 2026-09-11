"""Configuração do agente, carregada uma única vez do ambiente.

Este é o único módulo do projeto que lê variáveis de ambiente. Todo o resto recebe
os valores já prontos, por injeção.

A configuração é dividida em grupos aninhados (`agendabot`, `telegram`, `llm`, ...).
No ambiente, cada grupo é um prefixo separado por `__`: a chave do serviço do
AgendaBot é `AGENDABOT__SERVICE_KEY`, o token do bot é `TELEGRAM__BOT_TOKEN`, e assim
por diante.
"""

from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgendaBotSettings(BaseModel):
    """Acesso à API e ao MCP do AgendaBot. Prefixo `AGENDABOT__`."""

    api_url: str
    mcp_url: str
    service_key: SecretStr
    establishment_id: UUID
    establishment_timezone: str = "America/Sao_Paulo"


class TelegramSettings(BaseModel):
    """Credenciais e endpoint do canal Telegram. Prefixo `TELEGRAM__`."""

    bot_token: SecretStr
    webhook_secret: SecretStr
    api_root: str = "https://api.telegram.org"


class LLMSettings(BaseModel):
    """Provider e parâmetros do modelo de linguagem. Prefixo `LLM__`."""

    provider: Literal["anthropic", "openai"] = "anthropic"
    model: str = "claude-sonnet-5"
    temperature: float = 0.3
    max_tokens: int = 1024
    anthropic_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None

    @property
    def selected_api_key(self) -> SecretStr | None:
        """A API key do provider atualmente selecionado."""
        return {
            "anthropic": self.anthropic_api_key,
            "openai": self.openai_api_key,
        }[self.provider]


class RedisSettings(BaseModel):
    """Redis usado pelo checkpointer e pelo cache. Prefixo `REDIS__`."""

    url: str


class ConversationSettings(BaseModel):
    """Limites da conversa e do ciclo do agente. Prefixo `CONVERSATION__`."""

    ttl_minutes: int = 1440
    max_history_messages: int = 10
    max_agent_steps: int = 8
    max_input_chars: int = 1000
    session_refresh_margin_seconds: int = 60


class IdentitySettings(BaseModel):
    """Identidade sintética da fase 1. Prefixo `IDENTITY__`."""

    synthetic_phone_prefix: str = "5547999"


class HTTPSettings(BaseModel):
    """Timeouts de HTTP e MCP. Prefixo `HTTP__`.

    `connect_timeout_seconds` é comum aos dois adapters — abrir a conexão TCP+TLS
    não deveria passar disso. Os tetos de leitura/escrita são separados por
    adapter: o AgendaBot faz trabalho no backend ao emitir a sessão (`timeout_seconds`,
    mais folgado); o Telegram responde `sendMessage` rápido ou não responde
    (`telegram_read_timeout_seconds`, curto). Ver a tabela em `docs/09`.
    """

    timeout_seconds: float = 10.0
    connect_timeout_seconds: float = 5.0
    telegram_read_timeout_seconds: float = 5.0
    mcp_timeout_seconds: float = 15.0


class ObservabilitySettings(BaseModel):
    """Observabilidade. Prefixo `OBSERVABILITY__`."""

    log_level: str = "INFO"


class Settings(BaseSettings):
    """Configuração do agente, carregada do ambiente (ou de um arquivo `.env`)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )

    agendabot: AgendaBotSettings
    telegram: TelegramSettings
    redis: RedisSettings
    llm: LLMSettings = LLMSettings()
    conversation: ConversationSettings = ConversationSettings()
    identity: IdentitySettings = IdentitySettings()
    http: HTTPSettings = HTTPSettings()
    observability: ObservabilitySettings = ObservabilitySettings()

    @model_validator(mode="after")
    def _require_selected_provider_key(self) -> Self:
        """Falha no boot se a API key do provider escolhido não foi fornecida.

        Falhar aqui é melhor que falhar no primeiro cliente.
        """
        if self.llm.selected_api_key is None:
            raise ValueError(
                f"LLM__PROVIDER={self.llm.provider!r} exige a variável "
                f"LLM__{self.llm.provider.upper()}_API_KEY."
            )
        return self
