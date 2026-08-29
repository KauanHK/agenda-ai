from app.core.db.session import db
from app.modules.clients.adapters.db.unit_of_work import ClientsUnitOfWork


def make_unit_of_work() -> ClientsUnitOfWork:
    return ClientsUnitOfWork(session_factory=db.create_session)
