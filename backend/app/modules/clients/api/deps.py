from typing import Annotated

from fastapi import Depends

from app.api.deps import UnitOfWorkDep
from app.modules.clients.application.activate import ClientsActivator
from app.modules.clients.application.create import ClientsCreator
from app.modules.clients.application.delete import ClientsDeleter
from app.modules.clients.application.read import ClientsReader
from app.modules.clients.application.update import ClientsUpdater


def get_clients_creator(uow: UnitOfWorkDep) -> ClientsCreator:
    """Dependência para criar um cliente."""
    return ClientsCreator(uow=uow)


def get_clients_reader(uow: UnitOfWorkDep) -> ClientsReader:
    """Dependência para ler clientes."""
    return ClientsReader(uow=uow)


def get_clients_updater(uow: UnitOfWorkDep) -> ClientsUpdater:
    """Dependência para atualizar um cliente."""
    return ClientsUpdater(uow=uow)


def get_clients_activator(uow: UnitOfWorkDep) -> ClientsActivator:
    """Dependência para ativar um cliente."""
    return ClientsActivator(uow=uow)


def get_clients_deleter(uow: UnitOfWorkDep) -> ClientsDeleter:
    """Dependência para deletar um cliente."""
    return ClientsDeleter(uow=uow)


ClientsCreatorDep = Annotated[ClientsCreator, Depends(get_clients_creator)]
ClientsReaderDep = Annotated[ClientsReader, Depends(get_clients_reader)]
ClientsUpdaterDep = Annotated[ClientsUpdater, Depends(get_clients_updater)]
ClientsActivatorDep = Annotated[ClientsActivator, Depends(get_clients_activator)]
ClientsDeleterDep = Annotated[ClientsDeleter, Depends(get_clients_deleter)]
