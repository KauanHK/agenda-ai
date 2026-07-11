import uuid

from fastapi import APIRouter

from app.api.deps.auth import ActorDep
from app.core.pagination.dependencies import PageParamsDep
from app.core.pagination.schemas import PaginatedResponse
from app.core.roles import UserRole
from app.modules.auth.adapters.http.dependencies import UsersCreatorDep
from app.modules.users.adapters.http.dependencies import (
    UsersActivatorDep,
    UsersDeleterDep,
    UsersReaderDep,
    UsersUpdaterDep,
)
from app.modules.users.adapters.http.expanded import UserReadExpanded
from app.modules.users.adapters.http.schemas import UserCreate, UserRead, UserUpdate
from app.modules.users.application.dtos.commands import (
    CreateUserCommand,
    UpdateUserCommand,
)
from app.modules.users.application.dtos.filters import UserFilters

router = APIRouter()


@router.get("/me", response_model=UserRead)
async def get_me(
    reader: UsersReaderDep,
    actor: ActorDep,
) -> UserRead:
    user = await reader.get_by_id(actor.user_id, actor)
    return UserRead.model_validate(user.to_dict())


@router.patch("/me", response_model=UserRead)
async def update_me(
    data: UserUpdate,
    updater: UsersUpdaterDep,
    actor: ActorDep,
) -> UserRead:
    command = UpdateUserCommand(**data.model_dump(exclude_unset=True))
    user = await updater.update_me(command, actor)
    return UserRead.model_validate(user.to_dict())


@router.get("")
async def list_users(
    page_params: PageParamsDep,
    reader: UsersReaderDep,
    actor: ActorDep,
    q: str | None = None,
    role: UserRole | None = None,
    is_active: bool | None = None,
) -> PaginatedResponse[UserRead]:
    page = await reader.paginate(
        page_params=page_params,
        actor=actor,
        filters=UserFilters(q=q, is_active=is_active),
    )
    return PaginatedResponse[UserRead](
        data=[UserRead.model_validate(u.to_dict()) for u in page.items],
        total=page.total,
        page=page.page,
        size=page.page_size,
    )


@router.get("/{user_id}", response_model=UserReadExpanded)
async def get_user(
    user_id: uuid.UUID,
    reader: UsersReaderDep,
    actor: ActorDep,
) -> UserReadExpanded:
    user = await reader.get_by_id(user_id, actor)
    return UserReadExpanded.model_validate(user.to_dict())


@router.post("", response_model=UserRead, status_code=201)
async def create_user(
    data: UserCreate,
    creator: UsersCreatorDep,
    actor: ActorDep,
) -> UserRead:
    """Cria um novo usuário. Restrito a establishment_admin e global_admin."""

    command = CreateUserCommand(**data.model_dump(exclude_unset=True))
    user = await creator.create(command, actor)
    return UserRead.model_validate(user.to_dict())


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    updater: UsersUpdaterDep,
    actor: ActorDep,
) -> UserRead:
    command = UpdateUserCommand(**data.model_dump(exclude_unset=True))
    user = await updater.update(user_id, command, actor)
    return UserRead.model_validate(user.to_dict())


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: uuid.UUID,
    deleter: UsersDeleterDep,
    actor: ActorDep,
) -> None:
    await deleter.delete(user_id, actor)


@router.post("/{user_id}/activate", response_model=UserRead)
async def activate_user(
    user_id: uuid.UUID,
    activator: UsersActivatorDep,
    actor: ActorDep,
) -> UserRead:
    user = await activator.activate(user_id, actor)
    return UserRead.model_validate(user.to_dict())


@router.post("/{user_id}/deactivate", response_model=UserRead)
async def deactivate_user(
    user_id: uuid.UUID,
    activator: UsersActivatorDep,
    actor: ActorDep,
) -> UserRead:
    user = await activator.deactivate(user_id, actor)
    return UserRead.model_validate(user.to_dict())
