import uuid
from datetime import time, timedelta
from unittest.mock import AsyncMock

import pytest

from app.modules.booking.application.use_cases.availability import (
    AvailabilityCalculator,
)
from app.modules.booking.domain.exceptions import (
    ClosedOnWeekdayError,
    EstablishmentUnavailableError,
    NoProfessionalAvailableError,
    NoProfessionalsError,
    OutsideOperatingHoursError,
    PastDateTimeError,
    ServiceUnavailableError,
)
from app.modules.schedulings.domain.exceptions import SchedulingOverlapClientError
from app.modules.services.domain.model import Service
from tests.modules.booking.application.use_cases.conftest import (
    NOW,
    TARGET_DATE,
    FakeBookingUnitOfWork,
    make_operating_hour,
    make_scheduling,
    make_service,
    make_unavailability,
    utc,
)


class TestGetBookableService:
    async def test_retorna_o_servico_do_estabelecimento(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        service: Service,
    ) -> None:
        result = await AvailabilityCalculator(uow).get_bookable_service(
            establishment_id, service.id
        )

        assert result is service

    async def test_rejeita_servico_inexistente(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        services_repo: AsyncMock,
    ) -> None:
        services_repo.get_by_id_or_none.return_value = None

        with pytest.raises(ServiceUnavailableError):
            await AvailabilityCalculator(uow).get_bookable_service(
                establishment_id, uuid.uuid7()
            )

    async def test_rejeita_servico_inativo(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        services_repo: AsyncMock,
    ) -> None:
        services_repo.get_by_id_or_none.return_value = make_service(
            establishment_id, is_active=False
        )

        with pytest.raises(ServiceUnavailableError):
            await AvailabilityCalculator(uow).get_bookable_service(
                establishment_id, uuid.uuid7()
            )

    async def test_rejeita_servico_de_outro_estabelecimento(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        services_repo: AsyncMock,
    ) -> None:
        services_repo.get_by_id_or_none.return_value = make_service(uuid.uuid7())

        with pytest.raises(ServiceUnavailableError):
            await AvailabilityCalculator(uow).get_bookable_service(
                establishment_id, uuid.uuid7()
            )


class TestFreeSlots:
    async def test_cobre_todos_os_turnos_do_dia(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        service: Service,
    ) -> None:
        """O expediente tem dois turnos; o da tarde não pode ser descartado."""

        slots = await AvailabilityCalculator(uow).free_slots(
            establishment_id=establishment_id,
            service=service,
            target_date=TARGET_DATE,
            now=NOW,
        )

        manha = [s for s in slots if s.starts_at < utc(17)]
        tarde = [s for s in slots if s.starts_at >= utc(17)]
        assert manha, "turno da manhã deveria render horários"
        assert tarde, "turno da tarde deveria render horários"

    async def test_horarios_ficam_dentro_do_expediente(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        service: Service,
    ) -> None:
        """09:00-12:00 local = 12:00-15:00 UTC; 14:00-18:00 local = 17:00-21:00 UTC."""

        slots = await AvailabilityCalculator(uow).free_slots(
            establishment_id=establishment_id,
            service=service,
            target_date=TARGET_DATE,
            now=NOW,
        )

        assert slots
        for slot in slots:
            dentro_da_manha = utc(12) <= slot.starts_at and slot.ends_at <= utc(15)
            dentro_da_tarde = utc(17) <= slot.starts_at and slot.ends_at <= utc(21)
            assert dentro_da_manha or dentro_da_tarde

    async def test_primeiro_horario_e_a_abertura(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        service: Service,
    ) -> None:
        slots = await AvailabilityCalculator(uow).free_slots(
            establishment_id=establishment_id,
            service=service,
            target_date=TARGET_DATE,
            now=NOW,
        )

        assert slots[0].starts_at == utc(12)

    async def test_servico_longo_nao_gera_horario_que_estoura_o_turno(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
    ) -> None:
        # 3h de serviço cabe exatamente uma vez na manhã (9-12) e uma vez à tarde
        # começando às 14 ou 15 (14-18).
        service = make_service(establishment_id, duration_minutes=180)

        slots = await AvailabilityCalculator(uow).free_slots(
            establishment_id=establishment_id,
            service=service,
            target_date=TARGET_DATE,
            now=NOW,
        )

        assert all(slot.ends_at <= utc(15) or slot.ends_at <= utc(21) for slot in slots)
        assert any(slot.starts_at == utc(12) for slot in slots)

    async def test_dia_sem_expediente_nao_tem_horario(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        service: Service,
        operating_hours_repo: AsyncMock,
    ) -> None:
        operating_hours_repo.list_by_establishment.return_value = [
            make_operating_hour(establishment_id, 2, time(9, 0), time(18, 0))
        ]

        slots = await AvailabilityCalculator(uow).free_slots(
            establishment_id=establishment_id,
            service=service,
            target_date=TARGET_DATE,
            now=NOW,
        )

        assert slots == []

    async def test_bloqueio_do_estabelecimento_remove_os_horarios(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        service: Service,
        unavailabilities_repo: AsyncMock,
    ) -> None:
        """A regressão principal: o algoritmo anterior ignorava `unavailabilities`."""

        unavailabilities_repo.list_overlapping.return_value = [
            make_unavailability(establishment_id, utc(12), utc(15))
        ]

        slots = await AvailabilityCalculator(uow).free_slots(
            establishment_id=establishment_id,
            service=service,
            target_date=TARGET_DATE,
            now=NOW,
        )

        assert all(slot.starts_at >= utc(17) for slot in slots)

    async def test_profissional_ocupado_nao_rende_horario(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        professional_id: uuid.UUID,
        service: Service,
        schedulings_repo: AsyncMock,
    ) -> None:
        schedulings_repo.list_overlapping.return_value = [
            make_scheduling(establishment_id, professional_id, utc(12), utc(15))
        ]

        slots = await AvailabilityCalculator(uow).free_slots(
            establishment_id=establishment_id,
            service=service,
            target_date=TARGET_DATE,
            now=NOW,
        )

        assert all(slot.starts_at >= utc(15) for slot in slots)

    async def test_segundo_profissional_cobre_o_horario_do_primeiro(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        professional_id: uuid.UUID,
        service: Service,
        schedulings_repo: AsyncMock,
        memberships_repo: AsyncMock,
    ) -> None:
        from app.core.roles import UserRole
        from app.modules.memberships.domain.entities import Membership

        outro = uuid.uuid7()
        memberships_repo.list_all_by_establishment.return_value = [
            Membership(
                id=uuid.uuid7(),
                user_id=professional_id,
                establishment_id=establishment_id,
                role=UserRole.MEMBER,
                is_active=True,
            ),
            Membership(
                id=uuid.uuid7(),
                user_id=outro,
                establishment_id=establishment_id,
                role=UserRole.MEMBER,
                is_active=True,
            ),
        ]
        schedulings_repo.list_overlapping.return_value = [
            make_scheduling(establishment_id, professional_id, utc(12), utc(15))
        ]

        slots = await AvailabilityCalculator(uow).free_slots(
            establishment_id=establishment_id,
            service=service,
            target_date=TARGET_DATE,
            now=NOW,
        )

        primeiro = slots[0]
        assert primeiro.starts_at == utc(12)
        assert primeiro.user_id == outro

    async def test_compromisso_do_proprio_cliente_some_da_lista(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        client_id: uuid.UUID,
        service: Service,
        schedulings_repo: AsyncMock,
    ) -> None:
        schedulings_repo.list_overlapping.return_value = [
            make_scheduling(
                establishment_id,
                uuid.uuid7(),
                utc(12),
                utc(13),
                client_id=client_id,
            )
        ]

        slots = await AvailabilityCalculator(uow).free_slots(
            establishment_id=establishment_id,
            service=service,
            target_date=TARGET_DATE,
            client_id=client_id,
            now=NOW,
        )

        assert all(slot.starts_at >= utc(13) for slot in slots)

    async def test_nao_oferece_horario_no_passado(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        service: Service,
    ) -> None:
        slots = await AvailabilityCalculator(uow).free_slots(
            establishment_id=establishment_id,
            service=service,
            target_date=TARGET_DATE,
            now=utc(16),
        )

        assert all(slot.starts_at > utc(16) for slot in slots)

    async def test_respeita_o_limite_de_horarios(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        service: Service,
    ) -> None:
        slots = await AvailabilityCalculator(uow).free_slots(
            establishment_id=establishment_id,
            service=service,
            target_date=TARGET_DATE,
            now=NOW,
            limit=3,
        )

        assert len(slots) == 3

    async def test_carrega_a_agenda_do_dia_em_uma_consulta_so(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        service: Service,
        schedulings_repo: AsyncMock,
    ) -> None:
        """O algoritmo anterior fazia uma consulta por (horário x profissional)."""

        await AvailabilityCalculator(uow).free_slots(
            establishment_id=establishment_id,
            service=service,
            target_date=TARGET_DATE,
            now=NOW,
        )

        assert schedulings_repo.list_overlapping.await_count == 1

    async def test_sem_profissionais_cadastrados_falha(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        service: Service,
        memberships_repo: AsyncMock,
    ) -> None:
        memberships_repo.list_all_by_establishment.return_value = []

        with pytest.raises(NoProfessionalsError):
            await AvailabilityCalculator(uow).free_slots(
                establishment_id=establishment_id,
                service=service,
                target_date=TARGET_DATE,
                now=NOW,
            )

    async def test_usa_o_fuso_do_estabelecimento(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        service: Service,
        establishments_repo: AsyncMock,
        establishment,
    ) -> None:
        """Manaus é UTC-4, então a abertura das 09:00 cai às 13:00 UTC."""

        import dataclasses

        establishments_repo.get_by_id.return_value = dataclasses.replace(
            establishment, timezone="America/Manaus"
        )

        slots = await AvailabilityCalculator(uow).free_slots(
            establishment_id=establishment_id,
            service=service,
            target_date=TARGET_DATE,
            now=NOW,
        )

        assert slots[0].starts_at == utc(13)

    async def test_fuso_invalido_cai_no_padrao(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        service: Service,
        establishments_repo: AsyncMock,
        establishment,
    ) -> None:
        import dataclasses

        establishments_repo.get_by_id.return_value = dataclasses.replace(
            establishment, timezone="Nao/Existe"
        )

        slots = await AvailabilityCalculator(uow).free_slots(
            establishment_id=establishment_id,
            service=service,
            target_date=TARGET_DATE,
            now=NOW,
        )

        assert slots[0].starts_at == utc(12)


class TestAssignProfessional:
    async def test_devolve_o_profissional_livre(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        client_id: uuid.UUID,
        professional_id: uuid.UUID,
        service: Service,
    ) -> None:
        result = await AvailabilityCalculator(uow).assign_professional(
            establishment_id=establishment_id,
            service=service,
            starts_at=utc(12),
            client_id=client_id,
            now=NOW,
        )

        assert result == professional_id

    async def test_rejeita_horario_no_passado(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        client_id: uuid.UUID,
        service: Service,
    ) -> None:
        with pytest.raises(PastDateTimeError):
            await AvailabilityCalculator(uow).assign_professional(
                establishment_id=establishment_id,
                service=service,
                starts_at=NOW - timedelta(hours=1),
                client_id=client_id,
                now=NOW,
            )

    async def test_rejeita_dia_sem_expediente(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        client_id: uuid.UUID,
        service: Service,
        operating_hours_repo: AsyncMock,
    ) -> None:
        operating_hours_repo.list_by_establishment.return_value = [
            make_operating_hour(establishment_id, 2, time(9, 0), time(18, 0))
        ]

        with pytest.raises(ClosedOnWeekdayError):
            await AvailabilityCalculator(uow).assign_professional(
                establishment_id=establishment_id,
                service=service,
                starts_at=utc(12),
                client_id=client_id,
                now=NOW,
            )

    async def test_rejeita_horario_fora_do_expediente(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        client_id: uuid.UUID,
        service: Service,
    ) -> None:
        """08:00 local (11:00 UTC) é antes da abertura."""

        with pytest.raises(OutsideOperatingHoursError):
            await AvailabilityCalculator(uow).assign_professional(
                establishment_id=establishment_id,
                service=service,
                starts_at=utc(11),
                client_id=client_id,
                now=NOW,
            )

    async def test_rejeita_servico_que_ultrapassa_o_fim_do_turno(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        client_id: uuid.UUID,
    ) -> None:
        """
        Começar 11:30 local com 60 min terminaria 12:30, depois do fechamento da manhã.
        O código anterior só validava o início e deixava passar.
        """

        service = make_service(establishment_id, duration_minutes=60)

        with pytest.raises(OutsideOperatingHoursError):
            await AvailabilityCalculator(uow).assign_professional(
                establishment_id=establishment_id,
                service=service,
                starts_at=utc(14, 30),
                client_id=client_id,
                now=NOW,
            )

    async def test_rejeita_horario_bloqueado(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        client_id: uuid.UUID,
        service: Service,
        unavailabilities_repo: AsyncMock,
    ) -> None:
        unavailabilities_repo.list_overlapping.return_value = [
            make_unavailability(establishment_id, utc(12), utc(15))
        ]

        with pytest.raises(EstablishmentUnavailableError):
            await AvailabilityCalculator(uow).assign_professional(
                establishment_id=establishment_id,
                service=service,
                starts_at=utc(12),
                client_id=client_id,
                now=NOW,
            )

    async def test_rejeita_quando_o_cliente_ja_tem_compromisso(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        client_id: uuid.UUID,
        service: Service,
        schedulings_repo: AsyncMock,
    ) -> None:
        schedulings_repo.list_overlapping.return_value = [
            make_scheduling(
                establishment_id,
                uuid.uuid7(),
                utc(12),
                utc(13),
                client_id=client_id,
            )
        ]

        with pytest.raises(SchedulingOverlapClientError):
            await AvailabilityCalculator(uow).assign_professional(
                establishment_id=establishment_id,
                service=service,
                starts_at=utc(12),
                client_id=client_id,
                now=NOW,
            )

    async def test_rejeita_quando_todos_os_profissionais_estao_ocupados(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        client_id: uuid.UUID,
        professional_id: uuid.UUID,
        service: Service,
        schedulings_repo: AsyncMock,
    ) -> None:
        schedulings_repo.list_overlapping.return_value = [
            make_scheduling(establishment_id, professional_id, utc(12), utc(13))
        ]

        with pytest.raises(NoProfessionalAvailableError):
            await AvailabilityCalculator(uow).assign_professional(
                establishment_id=establishment_id,
                service=service,
                starts_at=utc(12),
                client_id=client_id,
                now=NOW,
            )

    async def test_ignora_o_proprio_agendamento_ao_reagendar(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        client_id: uuid.UUID,
        service: Service,
        schedulings_repo: AsyncMock,
    ) -> None:
        scheduling_id = uuid.uuid7()

        await AvailabilityCalculator(uow).assign_professional(
            establishment_id=establishment_id,
            service=service,
            starts_at=utc(12),
            client_id=client_id,
            now=NOW,
            exclude_scheduling_id=scheduling_id,
        )

        assert (
            schedulings_repo.list_overlapping.await_args.kwargs["exclude_id"]
            == scheduling_id
        )

    async def test_aceita_horario_no_segundo_turno(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        client_id: uuid.UUID,
        professional_id: uuid.UUID,
        service: Service,
    ) -> None:
        result = await AvailabilityCalculator(uow).assign_professional(
            establishment_id=establishment_id,
            service=service,
            starts_at=utc(17),
            client_id=client_id,
            now=NOW,
        )

        assert result == professional_id

    async def test_rejeita_horario_no_intervalo_entre_turnos(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        client_id: uuid.UUID,
        service: Service,
    ) -> None:
        """13:00 local (16:00 UTC) é o almoço, entre os dois turnos."""

        with pytest.raises(OutsideOperatingHoursError):
            await AvailabilityCalculator(uow).assign_professional(
                establishment_id=establishment_id,
                service=service,
                starts_at=utc(16),
                client_id=client_id,
                now=NOW,
            )


class TestOffered:
    async def test_todo_horario_oferecido_pode_ser_marcado(
        self,
        uow: FakeBookingUnitOfWork,
        establishment_id: uuid.UUID,
        client_id: uuid.UUID,
        service: Service,
    ) -> None:
        """
        Invariante central: `free_slots` e `assign_professional` aplicam os mesmos
        critérios, então nenhum horário oferecido ao cliente pode ser recusado na hora
        de gravar.
        """

        calculator = AvailabilityCalculator(uow)
        slots = await calculator.free_slots(
            establishment_id=establishment_id,
            service=service,
            target_date=TARGET_DATE,
            client_id=client_id,
            now=NOW,
        )

        assert slots
        for slot in slots:
            await calculator.assign_professional(
                establishment_id=establishment_id,
                service=service,
                starts_at=slot.starts_at,
                client_id=client_id,
                now=NOW,
            )
