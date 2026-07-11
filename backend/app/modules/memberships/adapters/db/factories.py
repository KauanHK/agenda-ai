from app.core.db.session import db
from app.modules.memberships.adapters.db.unit_of_work import MembershipsUnitOfWork


def make_unit_of_work() -> MembershipsUnitOfWork:
    return MembershipsUnitOfWork(session_factory=db.create_session)
