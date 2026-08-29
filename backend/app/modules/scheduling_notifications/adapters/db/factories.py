from app.core.db.session import db
from app.modules.scheduling_notifications.adapters.db.unit_of_work import (
    SchedulingNotificationsUnitOfWork,
)


def make_unit_of_work() -> SchedulingNotificationsUnitOfWork:
    return SchedulingNotificationsUnitOfWork(session_factory=db.create_session)
