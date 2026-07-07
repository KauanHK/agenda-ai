from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
    )

    DATABASE_URL: str | None = None
    POSTGRES_HOST: str | None = None
    POSTGRES_PORT: int | None = None
    POSTGRES_DB: str | None = None
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None

    JWT_SECRET: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRES_MIN: int
    REFRESH_TOKEN_EXPIRES_DAYS: int
    MCP_SESSION_TOKEN_EXPIRES_MINUTES: int

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    FRONTEND_URL: str
    GOOGLE_OAUTH_FRONTEND_PATH: str

    REDIS_URL: str
    REDIS_PASSWORD: str

    EVOLUTION_URL: str
    EVOLUTION_INSTANCE: str
    EVOLUTION_APIKEY: str

    AGENT_SESSION_SECRET: str

    @property
    def sqlalchemy_database_uri(self) -> str:
        """
        Constrói a URI de conexão do SQLAlchemy com base nas configurações fornecidas.
        """

        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            "postgresql+asyncpg://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()  # type: ignore[call-arg]
