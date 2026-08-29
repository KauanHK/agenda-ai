"""
Dependência de acesso a dados das tools.

A unidade de trabalho é entregue fechada: cada use case a abre no seu `async with`,
delimitando a transação. A dependência existe para que a construção (e o ponto de
override em testes) fique num lugar só.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from app.modules.booking.adapters.db.factories import make_unit_of_work
from app.modules.booking.adapters.db.unit_of_work import BookingUnitOfWork


@asynccontextmanager
async def get_booking_uow() -> AsyncIterator[BookingUnitOfWork]:
    """Fornece a unidade de trabalho do agendamento para uma tool call."""

    yield make_unit_of_work()
