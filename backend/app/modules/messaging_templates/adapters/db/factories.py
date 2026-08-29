from app.core.db.session import db
from app.modules.messaging_templates.adapters.db.unit_of_work import (
    MessagingTemplatesUnitOfWork,
)


def make_unit_of_work() -> MessagingTemplatesUnitOfWork:
    return MessagingTemplatesUnitOfWork(session_factory=db.create_session)
