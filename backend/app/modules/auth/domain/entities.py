from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class TokenPair:
    """Par de tokens de acesso e atualização emitido na autenticação."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    def to_dict(self) -> dict[str, Any]:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
        }
