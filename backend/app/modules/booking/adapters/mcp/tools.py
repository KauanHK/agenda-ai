"""
Tools MCP do agendamento.

As docstrings destas funções são o que o modelo lê para decidir quando chamar cada
tool — são parte do contrato, não comentário interno.

Nenhuma tool recebe `client_id` ou `establishment_id`: os dois vêm do token de sessão,
via `get_customer_actor`. Os parâmetros injetados por `Depends` não aparecem no schema
que o modelo enxerga, então ele nem tem como tentar preenchê-los.
"""

import uuid
from datetime import date, datetime
from typing import Any

from fastmcp import FastMCP
from fastmcp.dependencies import Depends

from app.core.actors.customer import CustomerActor
from app.mcp.deps.actors import get_customer_actor
from app.mcp.deps.unit_of_work import get_booking_uow
from app.mcp.envelope import enveloped
from app.modules.booking.adapters.db.unit_of_work import BookingUnitOfWork
from app.modules.booking.application.use_cases.cancel import BookingCanceller
from app.modules.booking.application.use_cases.create import BookingCreator
from app.modules.booking.application.use_cases.read import BookingReader
from app.modules.booking.application.use_cases.reschedule import BookingRescheduler
from app.modules.booking.domain.entities import CustomerScheduling, Slot


def _scheduling_to_dict(scheduling: CustomerScheduling) -> dict[str, Any]:
    return {
        "scheduling_id": str(scheduling.id),
        "starts_at": scheduling.starts_at.isoformat(),
        "ends_at": scheduling.ends_at.isoformat(),
        "status": scheduling.status.value,
        "service_id": str(scheduling.service_id),
        "service_name": scheduling.service_name,
    }


def _slot_to_dict(slot: Slot) -> dict[str, Any]:
    # `user_id` fica de fora de propósito: qual profissional atende é decisão do
    # sistema, e expor isso ao modelo só abriria espaço para ele prometer algo.
    return {
        "starts_at": slot.starts_at.isoformat(),
        "ends_at": slot.ends_at.isoformat(),
    }


def register_tools(mcp: FastMCP) -> None:
    """Registra as tools de agendamento no servidor MCP."""

    @mcp.tool
    @enveloped
    async def list_services(
        actor: CustomerActor = Depends(get_customer_actor),
        uow: BookingUnitOfWork = Depends(get_booking_uow),
    ) -> list[dict[str, Any]]:
        """
        Lista os serviços que o estabelecimento oferece, com duração e preço.

        Use no início da conversa, para apresentar as opções ao cliente, e sempre que
        precisar do `service_id` de um serviço que o cliente mencionou pelo nome.
        """

        services = await BookingReader(uow).list_services(actor)
        return [
            {
                "service_id": str(service.id),
                "name": service.name,
                "description": service.description,
                "duration_minutes": service.duration_minutes,
                "price": str(service.price),
            }
            for service in services
        ]

    @mcp.tool
    @enveloped
    async def list_available_slots(
        service_id: uuid.UUID,
        day: date,
        actor: CustomerActor = Depends(get_customer_actor),
        uow: BookingUnitOfWork = Depends(get_booking_uow),
    ) -> list[dict[str, Any]]:
        """
        Lista os horários livres para um serviço em um dia específico.

        Os horários já vêm no fuso do estabelecimento e consideram o expediente, os
        bloqueios da agenda e os compromissos que o próprio cliente já tem.

        Sempre consulte antes de marcar: só ofereça ao cliente horários que apareceram
        aqui. Uma lista vazia significa que não há vaga nesse dia — proponha outro.

        Args:
            service_id: O identificador do serviço, obtido em `list_services`.
            day: O dia desejado, no formato AAAA-MM-DD.
        """

        slots = await BookingReader(uow).list_slots(
            actor=actor,
            service_id=service_id,
            target_date=day,
        )
        return [_slot_to_dict(slot) for slot in slots]

    @mcp.tool
    @enveloped
    async def create_scheduling(
        service_id: uuid.UUID,
        starts_at: datetime,
        actor: CustomerActor = Depends(get_customer_actor),
        uow: BookingUnitOfWork = Depends(get_booking_uow),
    ) -> dict[str, Any]:
        """
        Marca um agendamento para o cliente.

        Use somente depois de confirmar com o cliente o serviço e o horário exatos, e
        de ter visto esse horário em `list_available_slots`.

        Args:
            service_id: O identificador do serviço, obtido em `list_services`.
            starts_at:
                O início do atendimento, no formato ISO 8601. Sem fuso, é entendido
                como horário local do estabelecimento.
        """

        scheduling = await BookingCreator(uow).create(
            actor=actor,
            service_id=service_id,
            starts_at=starts_at,
        )
        return _scheduling_to_dict(scheduling)

    @mcp.tool
    @enveloped
    async def list_my_schedulings(
        actor: CustomerActor = Depends(get_customer_actor),
        uow: BookingUnitOfWork = Depends(get_booking_uow),
    ) -> list[dict[str, Any]]:
        """
        Lista os agendamentos futuros do cliente que ainda estão valendo.

        Use quando o cliente perguntar sobre os compromissos dele, e para obter o
        `scheduling_id` necessário para cancelar ou reagendar.
        """

        schedulings = await BookingReader(uow).list_schedulings(actor)
        return [_scheduling_to_dict(scheduling) for scheduling in schedulings]

    @mcp.tool
    @enveloped
    async def cancel_scheduling(
        scheduling_id: uuid.UUID,
        actor: CustomerActor = Depends(get_customer_actor),
        uow: BookingUnitOfWork = Depends(get_booking_uow),
    ) -> dict[str, Any]:
        """
        Cancela um agendamento do cliente.

        Confirme com o cliente antes de chamar — a operação não tem volta.

        Args:
            scheduling_id:
                O identificador do agendamento, obtido em `list_my_schedulings`.
        """

        scheduling = await BookingCanceller(uow).cancel(
            actor=actor,
            scheduling_id=scheduling_id,
        )
        return _scheduling_to_dict(scheduling)

    @mcp.tool
    @enveloped
    async def reschedule_scheduling(
        scheduling_id: uuid.UUID,
        new_starts_at: datetime,
        actor: CustomerActor = Depends(get_customer_actor),
        uow: BookingUnitOfWork = Depends(get_booking_uow),
    ) -> dict[str, Any]:
        """
        Move um agendamento do cliente para outro horário.

        Prefira reagendar a cancelar e marcar de novo. Confira antes em
        `list_available_slots` que o horário novo está livre.

        Args:
            scheduling_id:
                O identificador do agendamento, obtido em `list_my_schedulings`.
            new_starts_at:
                O novo início, no formato ISO 8601. Sem fuso, é entendido como
                horário local do estabelecimento.
        """

        scheduling = await BookingRescheduler(uow).reschedule(
            actor=actor,
            scheduling_id=scheduling_id,
            new_starts_at=new_starts_at,
        )
        return _scheduling_to_dict(scheduling)
