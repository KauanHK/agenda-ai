import uuid
from dataclasses import dataclass

from app.core.roles import UserRole


@dataclass(frozen=True, slots=True)
class Membership:
    establishment_id: uuid.UUID
    role: str


@dataclass(frozen=True, slots=True)
class UserActor:
    user_id: uuid.UUID
    is_global_admin: bool
    memberships: tuple[Membership, ...]

    def has_role_in(
        self,
        establishment_id: uuid.UUID,
        roles: set[UserRole],
    ) -> bool:
        """
        Verifica se o ator tem um dos papéis especificados em um estabelecimento.

        Args:
            establishment_id (uuid.UUID): O ID do estabelecimento a ser verificado.
            roles (set[UserRole]): Um conjunto de papéis a serem verificados.

        Returns:
            bool:
                True se o ator tiver um dos papéis
                no estabelecimento, False caso contrário.
        """

        return any(
            m.establishment_id == establishment_id and m.role in roles
            for m in self.memberships
        )

    def is_member_of(
        self,
        establishment_id: uuid.UUID,
    ) -> bool:
        """
        Verifica se o ator é membro de um estabelecimento.

        Args:
            establishment_id (uuid.UUID):
                O ID do estabelecimento a ser verificado.

        Returns:
            bool: True se o ator for membro do estabelecimento, False caso contrário.
        """

        return self.is_global_admin or any(
            m.establishment_id == establishment_id for m in self.memberships
        )
