from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LoginCommand:
    """Comando de aplicação para autenticação de um usuário."""

    username: str
    password: str


@dataclass(frozen=True, slots=True)
class RefreshCommand:
    """Comando de aplicação para renovação de tokens."""

    refresh_token: str
