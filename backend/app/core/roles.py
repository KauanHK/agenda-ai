import enum


class UserRole(enum.StrEnum):
    """Papéis de um usuário dentro de um estabelecimento."""

    ESTABLISHMENT_ADMIN = "establishment_admin"
    MEMBER = "member"
