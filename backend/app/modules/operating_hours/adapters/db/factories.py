from app.core.db.session import db
from app.modules.operating_hours.adapters.db.unit_of_work import (
    OperatingHoursUnitOfWork,
)


def make_unit_of_work() -> OperatingHoursUnitOfWork:
    return OperatingHoursUnitOfWork(session_factory=db.create_session)
