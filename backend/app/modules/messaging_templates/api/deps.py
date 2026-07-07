from typing import Annotated

from fastapi import Depends

from app.api.deps import UnitOfWorkDep
from app.modules.messaging_templates.application.activate import (
    MessagingTemplatesActivator,
)
from app.modules.messaging_templates.application.create import MessagingTemplatesCreator
from app.modules.messaging_templates.application.delete import MessagingTemplatesDeleter
from app.modules.messaging_templates.application.link_service import (
    MessagingTemplatesServiceLinker,
)
from app.modules.messaging_templates.application.read import MessagingTemplatesReader
from app.modules.messaging_templates.application.update import MessagingTemplatesUpdater


def get_messaging_templates_creator(uow: UnitOfWorkDep) -> MessagingTemplatesCreator:
    return MessagingTemplatesCreator(uow=uow)


def get_messaging_templates_reader(uow: UnitOfWorkDep) -> MessagingTemplatesReader:
    return MessagingTemplatesReader(uow=uow)


def get_messaging_templates_updater(uow: UnitOfWorkDep) -> MessagingTemplatesUpdater:
    return MessagingTemplatesUpdater(uow=uow)


def get_messaging_templates_deleter(uow: UnitOfWorkDep) -> MessagingTemplatesDeleter:
    return MessagingTemplatesDeleter(uow=uow)


def get_messaging_templates_activator(uow: UnitOfWorkDep) -> MessagingTemplatesActivator:
    return MessagingTemplatesActivator(uow=uow)


def get_messaging_templates_service_linker(uow: UnitOfWorkDep) -> MessagingTemplatesServiceLinker:
    return MessagingTemplatesServiceLinker(uow=uow)


MessagingTemplatesCreatorDep = Annotated[MessagingTemplatesCreator, Depends(get_messaging_templates_creator)]
MessagingTemplatesReaderDep = Annotated[MessagingTemplatesReader, Depends(get_messaging_templates_reader)]
MessagingTemplatesUpdaterDep = Annotated[MessagingTemplatesUpdater, Depends(get_messaging_templates_updater)]
MessagingTemplatesDeleterDep = Annotated[MessagingTemplatesDeleter, Depends(get_messaging_templates_deleter)]
MessagingTemplatesActivatorDep = Annotated[MessagingTemplatesActivator, Depends(get_messaging_templates_activator)]
MessagingTemplatesLinkerDep = Annotated[MessagingTemplatesServiceLinker, Depends(get_messaging_templates_service_linker)]
