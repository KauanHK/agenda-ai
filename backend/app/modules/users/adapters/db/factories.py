from app.core.db.session import db
from app.modules.users.adapters.db.unit_of_work import UsersUnitOfWork


def make_unit_of_work() -> UsersUnitOfWork:
    return UsersUnitOfWork(session_factory=db.create_session)
