import uuid

from fastapi import APIRouter

from app.api.deps import ActorDep, PaginationParamsDep
from app.core.pagination import PaginatedResponse
from app.modules.memberships.api.deps import (
    MembershipActivatorDep,
    MembershipCreatorDep,
    MembershipDeleterDep,
    MembershipReaderDep,
    MembershipUpdaterDep,
)
from app.modules.memberships.domain.expanded import MembershipReadExpanded
from app.modules.memberships.domain.schemas import (
    MembershipInvitePayload,
    MembershipRead,
    MembershipUpdate,
)

router = APIRouter()
user_router = APIRouter()


@router.get("", response_model=PaginatedResponse[MembershipRead])
async def list_members(
    establishment_id: uuid.UUID,
    pagination: PaginationParamsDep,
    reader: MembershipReaderDep,
    actor: ActorDep,
) -> PaginatedResponse[MembershipRead]:
    return await reader.paginate(
        establishment_id=establishment_id,
        actor=actor,
        pagination=pagination,
    )


@router.post(
    "",
    response_model=MembershipReadExpanded,
    status_code=201,
)
async def add_member(
    establishment_id: uuid.UUID,
    body: MembershipInvitePayload,
    creator: MembershipCreatorDep,
    actor: ActorDep,
) -> MembershipReadExpanded:
    return await creator.create(
        establishment_id=establishment_id,
        body=body,
        actor=actor,
    )


@router.get(
    "/{user_id}",
    response_model=MembershipReadExpanded,
)
async def get_member(
    establishment_id: uuid.UUID,
    user_id: uuid.UUID,
    reader: MembershipReaderDep,
    actor: ActorDep,
) -> MembershipReadExpanded:
    return await reader.get_by_user_and_establishment(
        user_id=user_id,
        establishment_id=establishment_id,
        actor=actor,
    )


@router.patch("/{user_id}", response_model=MembershipRead)
async def update_member(
    establishment_id: uuid.UUID,
    user_id: uuid.UUID,
    data: MembershipUpdate,
    updater: MembershipUpdaterDep,
    actor: ActorDep,
) -> MembershipRead:
    return await updater.update(
        user_id=user_id,
        establishment_id=establishment_id,
        data=data,
        actor=actor,
    )


@router.delete("/{user_id}", status_code=204)
async def remove_member(
    establishment_id: uuid.UUID,
    user_id: uuid.UUID,
    deleter: MembershipDeleterDep,
    actor: ActorDep,
) -> None:
    await deleter.delete(
        user_id=user_id,
        establishment_id=establishment_id,
        actor=actor,
    )


@router.post(
    "/{user_id}/activate",
    response_model=MembershipRead,
)
async def activate_member(
    establishment_id: uuid.UUID,
    user_id: uuid.UUID,
    activator: MembershipActivatorDep,
    actor: ActorDep,
) -> MembershipRead:
    return await activator.activate(
        user_id=user_id,
        establishment_id=establishment_id,
        actor=actor,
    )


@router.post(
    "/{user_id}/deactivate",
    response_model=MembershipRead,
)
async def deactivate_member(
    establishment_id: uuid.UUID,
    user_id: uuid.UUID,
    activator: MembershipActivatorDep,
    actor: ActorDep,
) -> MembershipRead:
    return await activator.deactivate(
        user_id=user_id,
        establishment_id=establishment_id,
        actor=actor,
    )


@user_router.get("/{user_id}/memberships", response_model=list[MembershipRead])
async def list_user_memberships(
    user_id: uuid.UUID,
    reader: MembershipReaderDep,
    actor: ActorDep,
) -> list[MembershipRead]:
    return await reader.list_by_user(user_id=user_id, actor=actor)
