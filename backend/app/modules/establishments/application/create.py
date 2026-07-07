from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError
from app.db.unit_of_work import UnitOfWork
from app.modules.establishments.domain.model import Establishment
from app.modules.establishments.domain.schemas import (
    EstablishmentCreate,
    EstablishmentRead,
)
from app.modules.establishments.infra.repository import EstablishmentsRepository


class EstablishmentsCreator:
    def __init__(
        self,
        uow: UnitOfWork,
    ) -> None:
        """Inicializa o criador de estabelecimentos."""

        self._uow = uow

    async def create(
        self,
        establishment_create: EstablishmentCreate,
    ) -> EstablishmentRead:
        """
        Cria um novo estabelecimento.

        Args:
            establishment_create (EstablishmentCreate): Os dados para criação do estabelecimento.

        Returns:
            EstablishmentRead: O estabelecimento criado.
        """

        async with self._uow:
            repository = self._uow.repository(EstablishmentsRepository)

            establishment = Establishment(
                **establishment_create.model_dump(exclude_unset=True)
            )

            try:
                establishment = await repository.create(establishment)
            except IntegrityError as e:
                raise ConflictError(
                    "Já existe um estabelecimento com este cpf/cnpj."
                ) from e

            return EstablishmentRead.model_validate(establishment)
