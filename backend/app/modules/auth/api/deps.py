from typing import Annotated

from fastapi import Depends

from app.api.deps import UnitOfWorkDep
from app.modules.auth.application.create import UsersCreator
from app.modules.auth.application.login import AuthLogin
from app.modules.auth.application.refresh import AuthRefresh


def get_auth_login(uow: UnitOfWorkDep) -> AuthLogin:
    """
    Factory de dependência para o serviço de login.

    Args:
        uow (UnitOfWork):
            A unidade de trabalho para acessar os repositórios.
    Returns:
        AuthLogin:
            A instância do serviço de login.
    """

    return AuthLogin(uow=uow)


def get_auth_refresh(uow: UnitOfWorkDep) -> AuthRefresh:
    """
    Factory de dependência para o serviço de atualização de tokens.

    Args:
        uow (UnitOfWork):
            A unidade de trabalho para acessar os repositórios.
    Returns:
        AuthRefresh:
            A instância do serviço de atualização de tokens.
    """

    return AuthRefresh(uow=uow)


def get_auth_creator(uow: UnitOfWorkDep) -> UsersCreator:
    """
    Factory de dependência para o serviço de criação de usuários.

    Args:
        uow (UnitOfWork):
            A unidade de trabalho para acessar os repositórios.
    Returns:
        UsersCreator:
            A instância do serviço de criação de usuários.
    """

    return UsersCreator(uow=uow)


AuthLoginDep = Annotated[AuthLogin, Depends(get_auth_login)]
AuthRefreshDep = Annotated[AuthRefresh, Depends(get_auth_refresh)]
UsersCreatorDep = Annotated[UsersCreator, Depends(get_auth_creator)]
