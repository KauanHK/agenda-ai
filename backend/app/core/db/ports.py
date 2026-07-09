import uuid
from typing import Protocol

from app.core.pagination.params import Page, PageParams
from app.core.types import BaseCreateCommand, BaseUpdateCommand, DataclassInstance


class ReadRepositoryProtocol[EntityT](Protocol):
    """
    Contrato de leitura comum a todos os repositórios. Define apenas as operações de
    consulta por ID, permitindo que use cases que só leem dados dependam de uma
    interface mínima (ISP).
    """

    async def get_by_id_or_none(self, id_: uuid.UUID) -> EntityT | None: ...
    async def get_by_id(self, id_: uuid.UUID) -> EntityT: ...


class BaseRepositoryProtocol[
    EntityT,
    FiltersT: DataclassInstance,
    CreateCommandT: BaseCreateCommand,
    UpdateCommandT: BaseUpdateCommand,
](ReadRepositoryProtocol[EntityT], Protocol):
    """
    Contrato completo de CRUD + paginação comum a todos os repositórios.

    É satisfeito estruturalmente por `app.core.db.repository.BaseRepository`, sem que
    este precise herdar do protocolo. Os módulos especializam os parâmetros genéricos
    com seus próprios tipos de entidade, filtros e comandos, e adicionam apenas os
    métodos específicos do domínio.
    """

    async def create(self, create_command: CreateCommandT) -> EntityT: ...
    async def update(
        self,
        id_: uuid.UUID,
        update_command: UpdateCommandT,
    ) -> EntityT: ...
    async def delete(self, id_: uuid.UUID) -> None: ...
    async def list_all(
        self,
        filters: FiltersT | None = None,
    ) -> list[EntityT]: ...
    async def paginate(
        self,
        page_params: PageParams,
        filters: FiltersT | None = None,
    ) -> Page[EntityT]: ...
