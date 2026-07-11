from typing import Annotated

from fastapi import Depends

from app.modules.auth.adapters.db.factories import make_unit_of_work
from app.modules.auth.adapters.db.unit_of_work import AuthUnitOfWork
from app.modules.auth.application.use_cases.create import UsersCreator
from app.modules.auth.application.use_cases.login import AuthLogin
from app.modules.auth.application.use_cases.refresh import AuthRefresh

AuthUnitOfWorkDep = Annotated[AuthUnitOfWork, Depends(make_unit_of_work)]


def get_auth_login(uow: AuthUnitOfWorkDep) -> AuthLogin:
    """
    Factory de dependência para o serviço de login.

    Args:
        uow (AuthUnitOfWork):
            A unidade de trabalho de autenticação.
    Returns:
        AuthLogin:
            A instância do serviço de login.
    """

    return AuthLogin(uow=uow)


def get_auth_refresh(uow: AuthUnitOfWorkDep) -> AuthRefresh:
    """
    Factory de dependência para o serviço de atualização de tokens.

    Args:
        uow (AuthUnitOfWork):
            A unidade de trabalho de autenticação.
    Returns:
        AuthRefresh:
            A instância do serviço de atualização de tokens.
    """

    return AuthRefresh(uow=uow)


def get_auth_creator(uow: AuthUnitOfWorkDep) -> UsersCreator:
    """
    Factory de dependência para o serviço de criação de usuários.

    Args:
        uow (AuthUnitOfWork):
            A unidade de trabalho de autenticação.
    Returns:
        UsersCreator:
            A instância do serviço de criação de usuários.
    """

    return UsersCreator(uow=uow)


AuthLoginDep = Annotated[AuthLogin, Depends(get_auth_login)]
AuthRefreshDep = Annotated[AuthRefresh, Depends(get_auth_refresh)]
UsersCreatorDep = Annotated[UsersCreator, Depends(get_auth_creator)]
