from typing import Annotated

from fastapi import Depends

from app.api.deps import UnitOfWorkDep
from app.modules.services.application.activate import ServicesActivator
from app.modules.services.application.create import ServicesCreator
from app.modules.services.application.delete import ServicesDeleter
from app.modules.services.application.read import ServicesReader
from app.modules.services.application.update import ServicesUpdater
from app.modules.services.domain.schemas import ServicesQueryParams


def get_services_creator(uow: UnitOfWorkDep) -> ServicesCreator:
    """Dependência para criar um serviço."""
    return ServicesCreator(uow=uow)


def get_services_reader(uow: UnitOfWorkDep) -> ServicesReader:
    """Dependência para ler serviços."""
    return ServicesReader(uow=uow)


def get_services_updater(uow: UnitOfWorkDep) -> ServicesUpdater:
    """Dependência para atualizar serviços."""
    return ServicesUpdater(uow=uow)


def get_services_activator(uow: UnitOfWorkDep) -> ServicesActivator:
    """Dependência para ativar serviços."""
    return ServicesActivator(uow=uow)


def get_services_deleter(uow: UnitOfWorkDep) -> ServicesDeleter:
    """Dependência para deletar um serviço."""
    return ServicesDeleter(uow=uow)


def get_services_query_params(
    query_params: Annotated[ServicesQueryParams, Depends()],
) -> ServicesQueryParams:
    """Dependência para os parâmetros de consulta de serviços."""

    return query_params


ServicesCreatorDep = Annotated[
    ServicesCreator,
    Depends(get_services_creator),
]

ServicesReaderDep = Annotated[
    ServicesReader,
    Depends(get_services_reader),
]

ServicesUpdaterDep = Annotated[
    ServicesUpdater,
    Depends(get_services_updater),
]

ServicesActivatorDep = Annotated[
    ServicesActivator,
    Depends(get_services_activator),
]

ServicesDeleterDep = Annotated[
    ServicesDeleter,
    Depends(get_services_deleter),
]

ServicesQueryParamsDep = Annotated[
    ServicesQueryParams,
    Depends(get_services_query_params),
]
