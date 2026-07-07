import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import ForbiddenError
from app.modules.users.domain.enums import UserRole


def assert_can_access(actor: UserActor, establishment_id: uuid.UUID) -> None:
    """Garante que o ator pode acessar o módulo de clientes no estabelecimento."""
    if actor.is_global_admin:
        raise ForbiddenError("global_admin não opera sobre clientes.")
    if not actor.is_member_of(establishment_id):
        raise ForbiddenError("Acesso negado a este estabelecimento.")


def assert_can_write(actor: UserActor, establishment_id: uuid.UUID) -> None:
    """Garante que o ator pode realizar operações de escrita em clientes."""
    assert_can_access(actor, establishment_id)
    if not actor.has_role_in(establishment_id, {UserRole.ESTABLISHMENT_ADMIN}):
        raise ForbiddenError("Apenas establishment_admin pode escrever clientes.")
