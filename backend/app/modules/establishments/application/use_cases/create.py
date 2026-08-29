from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError
from app.modules.establishments.application.dtos.commands import (
    CreateEstablishmentCommand,
)
from app.modules.establishments.application.ports.unit_of_work import (
    EstablishmentsUnitOfWorkProtocol,
)
from app.modules.establishments.domain.entities import Establishment, NewEstablishment


class EstablishmentsCreator:
    def __init__(self, uow: EstablishmentsUnitOfWorkProtocol) -> None:
        """
        Inicializa um criador de estabelecimentos.

        Args:
            uow (EstablishmentsUnitOfWorkProtocol):
                Unit of work de estabelecimentos.
        """

        self._uow = uow

    async def create(self, data: CreateEstablishmentCommand) -> Establishment:
        """
        Cria um novo estabelecimento.

        Args:
            data (CreateEstablishmentCommand):
                Dados do estabelecimento a ser criado.
        """

        new_establishment = self._build_new_establishment(data)
        async with self._uow as uow:
            try:
                return await uow.establishments.create(
                    create_command=new_establishment
                )
            except IntegrityError as e:
                raise ConflictError(
                    "Já existe um estabelecimento com este cpf/cnpj."
                ) from e

    def _build_new_establishment(
        self, data: CreateEstablishmentCommand
    ) -> NewEstablishment:
        """Converte o comando de aplicação em um comando de domínio."""

        return NewEstablishment(
            name=data.name,
            document=data.document,
            document_type=data.document_type,
            is_active=data.is_active,
            timezone=data.timezone,
            street=data.street,
            number=data.number,
            complement=data.complement,
            neighborhood=data.neighborhood,
            city=data.city,
            state=data.state,
            zip_code=data.zip_code,
        )
