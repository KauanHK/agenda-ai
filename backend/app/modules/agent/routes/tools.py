import uuid
from datetime import date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps.db import UnitOfWorkDep
from app.core.exceptions import AppError
from app.core.pagination import PaginatedResponse, PaginationParams
from app.modules.agent.actors import ClientAgentActor
from app.modules.agent.application.create import AgentSchedulingsCreator
from app.modules.agent.application.delete import AgentSchedulingsCanceller
from app.modules.agent.application.escalation import OwnerNotifier
from app.modules.agent.application.read import AgentSchedulingsReader
from app.modules.agent.application.slots import AgentSlotsReader
from app.modules.agent.application.update import AgentSchedulingsRescheduler
from app.modules.agent.dependencies import get_session_actor
from app.modules.agent.errors import to_envelope
from app.modules.clients.infra.repository import ClientsRepository
from app.modules.establishments.infra.repository import EstablishmentsRepository
from app.modules.services.api.deps import ServicesReaderDep
from app.modules.services.domain.filters import ServiceFilters
from app.modules.services.domain.schemas import ServiceRead
from app.modules.services.infra.repository import ServicesRepository

router = APIRouter()

SessionActorDep = Annotated[ClientAgentActor, Depends(get_session_actor)]


class CreateSchedulingRequest(BaseModel):
    service_id: uuid.UUID
    scheduled_at: datetime


class RescheduleAgentRequest(BaseModel):
    new_scheduled_at: datetime


class EscalationRequest(BaseModel):
    motivo: Literal["COMPLAINT", "MAX_ATTEMPTS", "AGGRESSIVE", "OUT_OF_SCOPE"]
    resumo: str


@router.get("/services")
async def list_services(
    actor: SessionActorDep,
    reader: ServicesReaderDep,
) -> PaginatedResponse[ServiceRead]:

    return await reader.paginate(
        pagination=pagination,
        filters=ServiceFilters(q=q, is_active=is_active),
    )

    try:
        async with uow:
            repo = uow.repository(ServicesRepository)
            services = await repo.list(
                pagination=PaginationParams(page=1, size=100),
                filters=ServiceFilters(
                    establishment_id=str(actor.establishment_id), is_active=True
                ),
            )
        return {
            "success": True,
            "data": [
                {
                    "service_id": str(s.id),
                    "name": s.name,
                    "description": s.description,
                    "duration_minutes": s.duration_minutes,
                    "price": str(s.price),
                }
                for s in services
            ],
        }
    except AppError as exc:
        return to_envelope(exc)


@router.get("/slots")
async def list_slots(
    service_id: uuid.UUID,
    date: date,
    actor: SessionActorDep,
    uow: UnitOfWorkDep,
) -> dict:
    try:
        reader = AgentSlotsReader(uow)
        slots = await reader.list(
            service_id=service_id,
            target_date=date,
            establishment_id=actor.establishment_id,
        )
        return {"success": True, "data": slots}
    except AppError as exc:
        return to_envelope(exc)


@router.post("/schedulings")
async def create_scheduling(
    payload: CreateSchedulingRequest,
    actor: SessionActorDep,
    uow: UnitOfWorkDep,
) -> dict:
    try:
        creator = AgentSchedulingsCreator(uow)
        result = await creator.create(
            actor=actor,
            service_id=payload.service_id,
            starts_at=payload.scheduled_at,
        )
        return {"success": True, "data": result}
    except AppError as exc:
        return to_envelope(exc)


@router.get("/schedulings")
async def list_schedulings(
    actor: SessionActorDep,
    uow: UnitOfWorkDep,
) -> dict:
    try:
        reader = AgentSchedulingsReader(uow)
        schedulings = await reader.list(actor)
        return {"success": True, "data": schedulings}
    except AppError as exc:
        return to_envelope(exc)


@router.delete("/schedulings/{scheduling_id}")
async def cancel_scheduling(
    scheduling_id: uuid.UUID,
    actor: SessionActorDep,
    uow: UnitOfWorkDep,
) -> dict:
    try:
        canceller = AgentSchedulingsCanceller(uow)
        result = await canceller.cancel(actor=actor, scheduling_id=scheduling_id)
        return {"success": True, "data": result}
    except AppError as exc:
        return to_envelope(exc)


@router.patch("/schedulings/{scheduling_id}/reschedule")
async def reschedule_scheduling(
    scheduling_id: uuid.UUID,
    payload: RescheduleAgentRequest,
    actor: SessionActorDep,
    uow: UnitOfWorkDep,
) -> dict:
    try:
        rescheduler = AgentSchedulingsRescheduler(uow)
        result = await rescheduler.reschedule(
            actor=actor,
            scheduling_id=scheduling_id,
            new_starts_at=payload.new_scheduled_at,
        )
        return {"success": True, "data": result}
    except AppError as exc:
        return to_envelope(exc)


@router.post("/escalations")
async def create_escalation(
    payload: EscalationRequest,
    actor: SessionActorDep,
    uow: UnitOfWorkDep,
) -> dict:
    try:
        async with uow:
            clients_repo = uow.repository(ClientsRepository)
            establishments_repo = uow.repository(EstablishmentsRepository)

            client = await clients_repo.get_by_id(actor.client_id)
            establishment = await establishments_repo.get_by_id(actor.establishment_id)

        owner_phone = getattr(establishment, "owner_phone", None)
        notifier = OwnerNotifier()
        await notifier.notify(
            owner_phone=owner_phone,
            client_name=client.name,
            client_phone=actor.phone,
            motivo=payload.motivo,
            resumo=payload.resumo,
        )
        return {"success": True, "data": {"escalated": True}}
    except AppError as exc:
        return to_envelope(exc)
