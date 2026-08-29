from app.core.db.session import db
from app.modules.unavailabilities.adapters.db.unit_of_work import (
    UnavailabilitiesUnitOfWork,
)


def make_unit_of_work() -> UnavailabilitiesUnitOfWork:
    return UnavailabilitiesUnitOfWork(session_factory=db.create_session)
