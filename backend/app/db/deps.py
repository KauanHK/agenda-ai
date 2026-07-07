from app.db.session import db
from app.db.unit_of_work import UnitOfWork


def get_unit_of_work():
    """Dependência para obter uma instância de UnitOfWork."""

    session = db.create_session()
    return UnitOfWork(session)
