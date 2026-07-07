import uuid

from fastapi import APIRouter

from app.api.deps import ActorDep, PaginationParamsDep
from app.core.pagination import PaginatedResponse
from app.modules.auth.api.deps import UsersCreatorDep
from app.modules.users.api.deps import (
    UsersActivatorDep,
    UsersDeleterDep,
    UsersReaderDep,
    UsersUpdaterDep,
)
from app.modules.users.domain.enums import UserRole
from app.modules.users.domain.expanded import UserReadExpanded
from app.modules.users.domain.filters import UserFilters
from app.modules.users.domain.schemas import (
    UserCreate,
    UserRead,
    UserUpdate,
)

router = APIRouter()


@router.get("/me", response_model=UserRead)
async def get_me(
    reader: UsersReaderDep,
    actor: ActorDep,
) -> UserRead:
    return await reader.get_by_id(actor.user_id, actor)


@router.patch("/me", response_model=UserRead)
async def update_me(
    data: UserUpdate,
    updater: UsersUpdaterDep,
    actor: ActorDep,
) -> UserRead:
    return await updater.update_me(data, actor)


@router.get("")
async def list_users(
    pagination: PaginationParamsDep,
    reader: UsersReaderDep,
    actor: ActorDep,
    q: str | None = None,
    role: UserRole | None = None,
    is_active: bool | None = None,
) -> PaginatedResponse[UserRead]:

    return await reader.paginate(
        pagination=pagination,
        actor=actor,
        filters=UserFilters(q=q, is_active=is_active),
    )


@router.get("/{user_id}", response_model=UserReadExpanded)
async def get_user(
    user_id: uuid.UUID,
    reader: UsersReaderDep,
    actor: ActorDep,
) -> UserReadExpanded:
    return await reader.get_by_id(user_id, actor)


@router.post("", response_model=UserRead, status_code=201)
async def create_user(
    data: UserCreate,
    creator: UsersCreatorDep,
    actor: ActorDep,
) -> UserRead:
    """Cria um novo usuário. Restrito a establishment_admin e global_admin."""

    return await creator.create(data, actor)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    updater: UsersUpdaterDep,
    actor: ActorDep,
) -> UserRead:
    return await updater.update(user_id, data, actor)


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
    return await activator.activate(user_id, actor)


@router.post("/{user_id}/deactivate", response_model=UserRead)
async def deactivate_user(
    user_id: uuid.UUID,
    activator: UsersActivatorDep,
    actor: ActorDep,
) -> UserRead:
    return await activator.deactivate(user_id, actor)
