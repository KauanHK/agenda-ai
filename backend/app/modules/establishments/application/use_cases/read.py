import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.modules.establishments.application.ports.unit_of_work import (
    EstablishmentsUnitOfWorkProtocol,
)
from app.modules.establishments.domain.entities import Establishment
from app.modules.memberships.infra.repository import MembershipRepository


class EstablishmentsReader:
    def __init__(self, uow: EstablishmentsUnitOfWorkProtocol) -> None:
        """
        Inicializa um leitor de estabelecimentos.

        Args:
            uow (EstablishmentsUnitOfWorkProtocol):
                Unit of work de estabelecimentos.
        """

        self._uow = uow

    async def get_by_id(
        self,
        establishment_id: uuid.UUID,
        actor: UserActor,
    ) -> Establishment:
        """
        Obtém um estabelecimento pelo seu id, garantindo que o ator tenha acesso a ele.

        Args:
            establishment_id (uuid.UUID):
                UUID do estabelecimento.
            actor (UserActor):
                Usuário que está executando a ação.
        """

        async with self._uow as uow:
            if not actor.is_member_of(establishment_id):
                memberships_repo = MembershipRepository(uow.session)
                user_establishment = (
                    await memberships_repo.get_by_user_and_establishment_or_none(
                        user_id=actor.user_id,
                        establishment_id=establishment_id,
                    )
                )
                if user_establishment is None:
                    raise NotFoundError("Estabelecimento não encontrado.")

            return await uow.establishments.get_by_id(establishment_id)
