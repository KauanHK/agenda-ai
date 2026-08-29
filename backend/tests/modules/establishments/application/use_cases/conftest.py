import uuid
from datetime import UTC, datetime
from types import TracebackType
from typing import Self
from unittest.mock import AsyncMock

import pytest

from app.modules.establishments.domain.entities import Establishment
from app.modules.establishments.domain.enums import DocumentType


class FakeEstablishmentsUnitOfWork:
    """Fake de `EstablishmentsUnitOfWorkProtocol` para testar os use cases isoladamente."""

    def __init__(self, establishments: AsyncMock) -> None:
        self.establishments = establishments
        self.session = AsyncMock()
        self.entered = False
        self.exited = False

    async def __aenter__(self) -> Self:
        self.entered = True
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.exited = True
        return None


def make_establishment(**overrides) -> Establishment:
    now = datetime.now(UTC)
    defaults = dict(  # noqa: C408
        id=uuid.uuid7(),
        name="Clínica Teste",
        document="11222333000181",
        document_type=DocumentType.CNPJ,
        timezone="America/Sao_Paulo",
        street="Rua das Flores",
        number="123",
        complement="",
        neighborhood="Centro",
        city="São Paulo",
        state="SP",
        zip_code="01310100",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return Establishment(**defaults)


@pytest.fixture
def establishment() -> Establishment:
    return make_establishment()


@pytest.fixture
def establishments_repo(establishment: Establishment) -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_id.return_value = establishment
    repo.create.return_value = establishment
    repo.update.return_value = establishment
    return repo


@pytest.fixture
def uow(establishments_repo: AsyncMock) -> FakeEstablishmentsUnitOfWork:
    return FakeEstablishmentsUnitOfWork(establishments=establishments_repo)
