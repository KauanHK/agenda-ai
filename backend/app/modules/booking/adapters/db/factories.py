from app.core.db.session import db
from app.modules.booking.adapters.db.unit_of_work import BookingUnitOfWork


def make_unit_of_work() -> BookingUnitOfWork:
    return BookingUnitOfWork(session_factory=db.create_session)
