from app.core.db.session import db
from app.modules.auth.adapters.db.unit_of_work import AuthUnitOfWork


def make_unit_of_work() -> AuthUnitOfWork:
    return AuthUnitOfWork(session_factory=db.create_session)
