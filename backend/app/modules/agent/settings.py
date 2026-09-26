"""Configuração do agente, carregada uma única vez do ambiente.

Este é o único módulo do agente que lê variáveis de ambiente. Todo o resto recebe
os valores já prontos, por injeção.

Lê o mesmo `.env` da raiz que o backend (`app.core.settings.ENV_FILE`). Toda variável
do agente começa com `AGENT_`, para não colidir com as do backend no mesmo arquivo.

A configuração é dividida em grupos aninhados (`agendabot`, `telegram`, `llm`, ...).
No ambiente, cada grupo é um prefixo separado por `__`: a URL do MCP é
`AGENT_AGENDABOT__MCP_URL`, o token do bot é `AGENT_TELEGRAM__BOT_TOKEN`, e assim
por diante.
"""

from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.settings import ENV_FILE


class AgendaBotSettings(BaseModel):
    """Acesso ao MCP do AgendaBot. Prefixo `AGENT_AGENDABOT__`."""

    mcp_url: str
    establishment_id: UUID
    establishment_timezone: str = "America/Sao_Paulo"


class TelegramSettings(BaseModel):
    """Credenciais e endpoint do canal Telegram. Prefixo `AGENT_TELEGRAM__`.

    `admin_token` protege as rotas administrativas (`/admin/telegram/webhook`),
    que registram e consultam o webhook direto na Bot API.
    """

    bot_token: SecretStr
    webhook_secret: SecretStr
    admin_token: SecretStr
    api_root: str = "https://api.telegram.org"


class LLMSettings(BaseModel):
    """Provider e parâmetros do modelo de linguagem. Prefixo `AGENT_LLM__`."""

    provider: Literal["anthropic", "openai", "groq"] = "anthropic"
    model: str = "claude-sonnet-5"
    temperature: float = 0.3
    max_tokens: int = 1024
    anthropic_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None
    groq_api_key: SecretStr | None = None

    @property
    def selected_api_key(self) -> SecretStr | None:
        """A API key do provider atualmente selecionado."""
        return {
            "anthropic": self.anthropic_api_key,
            "openai": self.openai_api_key,
            "groq": self.groq_api_key,
        }[self.provider]


class RedisSettings(BaseModel):
    """Redis usado pelo checkpointer e pelo cache. Prefixo `AGENT_REDIS__`."""

    url: str


class ConversationSettings(BaseModel):
    """Limites da conversa e do ciclo do agente. Prefixo `AGENT_CONVERSATION__`."""

    ttl_minutes: int = 1440
    max_history_turns: int = 10
    max_agent_steps: int = 8
    max_input_chars: int = 1000
    session_refresh_margin_seconds: int = 60


class IdentitySettings(BaseModel):
    """Identidade sintética da fase 1. Prefixo `AGENT_IDENTITY__`."""

    synthetic_phone_prefix: str = "5547999"


class HTTPSettings(BaseModel):
    """Timeouts de HTTP e MCP. Prefixo `AGENT_HTTP__`.

    `connect_timeout_seconds` limita a abertura da conexão TCP+TLS com o Telegram;
    `telegram_read_timeout_seconds` é curto porque a Bot API responde `sendMessage`
    rápido ou não responde. Ver a tabela em `docs/09`.
    """

    connect_timeout_seconds: float = 5.0
    telegram_read_timeout_seconds: float = 5.0
    mcp_timeout_seconds: float = 15.0


class ObservabilitySettings(BaseModel):
    """Observabilidade. Prefixo `AGENT_OBSERVABILITY__`."""

    log_level: str = "INFO"


class Settings(BaseSettings):
    """Configuração do agente, carregada do ambiente (ou de um arquivo `.env`)."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_prefix="AGENT_",
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
                f"AGENT_LLM__PROVIDER={self.llm.provider!r} exige a variável "
                f"AGENT_LLM__{self.llm.provider.upper()}_API_KEY."
            )
        return self
