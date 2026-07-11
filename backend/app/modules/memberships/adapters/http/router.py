import uuid

from fastapi import APIRouter

from app.api.deps.auth import ActorDep
from app.core.pagination.dependencies import PageParamsDep
from app.core.pagination.schemas import PaginatedResponse
from app.modules.memberships.adapters.http.dependencies import (
    MembershipActivatorDep,
    MembershipCreatorDep,
    MembershipDeleterDep,
    MembershipReaderDep,
    MembershipUpdaterDep,
)
from app.modules.memberships.adapters.http.expanded import MembershipReadExpanded
from app.modules.memberships.adapters.http.schemas import (
    MembershipInviteExisting,
    MembershipInvitePayload,
    MembershipRead,
    MembershipUpdate,
)
from app.modules.memberships.application.dtos.commands import (
    InviteExistingMemberCommand,
    InviteMemberCommand,
    InviteNewMemberCommand,
    UpdateMembershipCommand,
)

router = APIRouter()
user_router = APIRouter()


@router.get("", response_model=PaginatedResponse[MembershipRead])
async def list_members(
    establishment_id: uuid.UUID,
    page_params: PageParamsDep,
    reader: MembershipReaderDep,
    actor: ActorDep,
) -> PaginatedResponse[MembershipRead]:
    page = await reader.paginate(
        establishment_id=establishment_id,
        actor=actor,
        page_params=page_params,
    )
    return PaginatedResponse[MembershipRead](
        data=[MembershipRead.model_validate(m.to_dict()) for m in page.items],
        total=page.total,
        page=page.page,
        size=page.page_size,
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
    command: InviteMemberCommand
    if isinstance(body, MembershipInviteExisting):
        command = InviteExistingMemberCommand(user_id=body.user_id, role=body.role)
    else:
        command = InviteNewMemberCommand(
            name=body.name,
            email=body.email,
            password=body.password,
            role=body.role,
            phone=body.phone,
        )

    membership = await creator.create(
        establishment_id=establishment_id,
        data=command,
        actor=actor,
    )
    return MembershipReadExpanded.model_validate(membership.to_dict())


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
    membership = await reader.get_by_user_and_establishment(
        user_id=user_id,
        establishment_id=establishment_id,
        actor=actor,
    )
    return MembershipReadExpanded.model_validate(membership.to_dict())


@router.patch("/{user_id}", response_model=MembershipRead)
async def update_member(
    establishment_id: uuid.UUID,
    user_id: uuid.UUID,
    data: MembershipUpdate,
    updater: MembershipUpdaterDep,
    actor: ActorDep,
) -> MembershipRead:
    membership = await updater.update(
        user_id=user_id,
        establishment_id=establishment_id,
        data=UpdateMembershipCommand(role=data.role),
        actor=actor,
    )
    return MembershipRead.model_validate(membership.to_dict())


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
    membership = await activator.activate(
        user_id=user_id,
        establishment_id=establishment_id,
        actor=actor,
    )
    return MembershipRead.model_validate(membership.to_dict())


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
    membership = await activator.deactivate(
        user_id=user_id,
        establishment_id=establishment_id,
        actor=actor,
    )
    return MembershipRead.model_validate(membership.to_dict())


@user_router.get("/{user_id}/memberships", response_model=list[MembershipRead])
async def list_user_memberships(
    user_id: uuid.UUID,
    reader: MembershipReaderDep,
    actor: ActorDep,
) -> list[MembershipRead]:
    memberships = await reader.list_by_user(user_id=user_id, actor=actor)
    return [MembershipRead.model_validate(m.to_dict()) for m in memberships]
