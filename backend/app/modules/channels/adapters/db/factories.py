from app.core.db.session import db
from app.modules.channels.adapters.db.unit_of_work import ChannelsUnitOfWork


def make_unit_of_work() -> ChannelsUnitOfWork:
    return ChannelsUnitOfWork(session_factory=db.create_session)
