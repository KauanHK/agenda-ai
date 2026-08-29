from app.core.db.session import db
from app.modules.establishments.adapters.db.unit_of_work import EstablishmentsUnitOfWork


def make_unit_of_work() -> EstablishmentsUnitOfWork:
    return EstablishmentsUnitOfWork(session_factory=db.create_session)
