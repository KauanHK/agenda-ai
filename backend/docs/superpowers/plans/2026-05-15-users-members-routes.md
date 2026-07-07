# Users/Members Routes Separation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Separar rotas de usuários em dois escopos claros: gerenciamento global (`/users/...`) e gerenciamento de membros por estabelecimento (`/establishments/{id}/members/...`), adicionando `membership.is_active` e os endpoints activate/deactivate no escopo de estabelecimento.

**Architecture:** Adicionar `is_active` ao modelo `Membership` com migration. Criar `MembershipActivator` no módulo memberships seguindo o padrão já existente em `UsersActivator`. Adicionar `GET /{id}/members/{user_id}` e os dois endpoints de activate/deactivate ao memberships router. Remover a rota misplaced `GET /users/establishments/{establishment_id}/members` do users router.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async, Pydantic v2, Alembic, pytest-asyncio

---

## File Map

| Arquivo | Ação | Responsabilidade |
|---------|------|-----------------|
| `app/modules/memberships/domain/model.py` | Modificar | Adicionar campo `is_active` |
| `app/modules/memberships/domain/schemas.py` | Modificar | Adicionar `is_active` ao `MembershipRead` |
| `app/modules/memberships/domain/expanded.py` | Modificar | Adicionar `is_active` ao `MembershipReadExpanded` |
| `app/modules/memberships/infra/repository.py` | Modificar | Adicionar `get_by_user_and_establishment_expanded` |
| `app/modules/memberships/application/read.py` | Modificar | Adicionar `get_by_user_and_establishment` |
| `app/modules/memberships/application/activate.py` | Criar | `MembershipActivator` use case |
| `app/modules/memberships/api/deps.py` | Modificar | Adicionar `MembershipActivatorDep` |
| `app/modules/memberships/api/router.py` | Modificar | Adicionar 3 novos endpoints |
| `app/modules/users/api/router.py` | Modificar | Remover rota misplaced |
| `tests/modules/memberships/__init__.py` | Criar | Pacote de testes |
| `tests/modules/memberships/application/__init__.py` | Criar | Pacote de testes |
| `tests/modules/memberships/application/test_activate.py` | Criar | Testes do `MembershipActivator` |

---

## Task 1: Adicionar `is_active` ao modelo, schemas e gerar migration

**Files:**
- Modify: `app/modules/memberships/domain/model.py`
- Modify: `app/modules/memberships/domain/schemas.py`
- Modify: `app/modules/memberships/domain/expanded.py`

- [ ] **Step 1: Adicionar campo `is_active` ao modelo `Membership`**

Em `app/modules/memberships/domain/model.py`, adicionar o campo após `role`:

```python
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.modules.users.domain.enums import UserRole


class Membership(Base):
    __tablename__ = "user_establishments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid7,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    establishment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("establishments.id", ondelete="CASCADE"),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )

    user = relationship("User", back_populates="memberships")
    establishment = relationship("Establishment", back_populates="memberships")

    __table_args__ = (
        UniqueConstraint("user_id", "establishment_id", name="uq_user_establishment"),
    )
```

- [ ] **Step 2: Adicionar `is_active` ao `MembershipRead`**

Em `app/modules/memberships/domain/schemas.py`:

```python
from pydantic import UUID7, EmailStr

from app.modules.clients.domain.schemas import Phone
from app.modules.common.domain.schemas import BaseSchema
from app.modules.establishments.domain.schemas import Name
from app.modules.users.domain.enums import UserRole
from app.modules.users.domain.schemas import Password


class MembershipUpdate(BaseSchema):
    role: UserRole


class MembershipRead(BaseSchema):
    user_id: UUID7
    establishment_id: UUID7
    role: UserRole
    is_active: bool


class MembershipInviteExisting(BaseSchema):
    user_id: UUID7
    role: UserRole


class MembershipInviteNew(BaseSchema):
    name: Name
    email: EmailStr
    phone: Phone | None = None
    password: Password
    role: UserRole


MembershipInvitePayload = MembershipInviteExisting | MembershipInviteNew
```

- [ ] **Step 3: Adicionar `is_active` ao `MembershipReadExpanded`**

Em `app/modules/memberships/domain/expanded.py`:

```python
from app.modules.common.domain.schemas import BaseSchema
from app.modules.establishments.domain.schemas import EstablishmentRead
from app.modules.users.domain.enums import UserRole
from app.modules.users.domain.schemas import UserRead


class MembershipReadExpanded(BaseSchema):
    role: UserRole
    is_active: bool
    user: UserRead
    establishment: EstablishmentRead
```

- [ ] **Step 4: Gerar a migration**

```bash
uv run alembic revision --autogenerate -m "add is_active to memberships"
```

Verificar o arquivo gerado em `migrations/versions/` — deve conter um `op.add_column` com a coluna `is_active` e `server_default="true"`.

- [ ] **Step 5: Aplicar a migration**

```bash
uv run alembic upgrade head
```

Esperado: sem erros.

- [ ] **Step 6: Commit**

```bash
git add app/modules/memberships/domain/model.py \
        app/modules/memberships/domain/schemas.py \
        app/modules/memberships/domain/expanded.py \
        migrations/versions/
git commit -m "feat: add is_active field to Membership model and schemas"
```

---

## Task 2: Adicionar `get_by_user_and_establishment_expanded` ao repository

**Files:**
- Modify: `app/modules/memberships/infra/repository.py`

- [ ] **Step 1: Atualizar o repository**

Em `app/modules/memberships/infra/repository.py`, adicionar import de `selectinload` e o novo método:

```python
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginationParams
from app.modules.memberships.domain.model import Membership
from app.modules.users.domain.enums import UserRole


class MembershipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, membership: Membership) -> Membership:
        self._session.add(membership)
        await self._session.flush()
        await self._session.refresh(membership)
        return membership

    async def delete(self, membership: Membership) -> None:
        await self._session.delete(membership)

    async def update(self, membership: Membership) -> Membership:
        membership = await self._session.merge(membership)
        await self._session.refresh(membership)
        return membership

    async def get_by_user_and_establishment_or_none(
        self,
        user_id: uuid.UUID,
        establishment_id: uuid.UUID,
    ) -> Membership | None:
        result = await self._session.execute(
            select(Membership)
            .where(Membership.user_id == user_id)
            .where(Membership.establishment_id == establishment_id)
        )
        return result.scalars().one_or_none()

    async def get_by_user_and_establishment(
        self,
        user_id: uuid.UUID,
        establishment_id: uuid.UUID,
    ) -> Membership:
        membership = await self.get_by_user_and_establishment_or_none(
            user_id=user_id, establishment_id=establishment_id
        )
        if membership is None:
            raise NotFoundError("Membership não encontrada.")
        return membership

    async def get_by_user_and_establishment_expanded(
        self,
        user_id: uuid.UUID,
        establishment_id: uuid.UUID,
    ) -> Membership:
        result = await self._session.execute(
            select(Membership)
            .where(Membership.user_id == user_id)
            .where(Membership.establishment_id == establishment_id)
            .options(
                selectinload(Membership.user),
                selectinload(Membership.establishment),
            )
        )
        membership = result.scalars().one_or_none()
        if membership is None:
            raise NotFoundError("Membership não encontrada.")
        return membership

    async def list_by_user(self, user_id: uuid.UUID) -> list[Membership]:
        result = await self._session.execute(
            select(Membership).where(Membership.user_id == user_id)
        )
        return list(result.scalars().all())

    async def list_by_establishment(
        self,
        establishment_id: uuid.UUID,
        pagination: PaginationParams,
    ) -> list[Membership]:
        result = await self._session.execute(
            select(Membership)
            .where(Membership.establishment_id == establishment_id)
            .limit(pagination.size)
            .offset(pagination.offset)
        )
        return list(result.scalars().all())

    async def count_by_establishment(self, establishment_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(Membership)
            .where(Membership.establishment_id == establishment_id)
        )
        return result.scalar_one()

    async def count_admins_in_establishment(self, establishment_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(Membership)
            .where(Membership.establishment_id == establishment_id)
            .where(Membership.role == UserRole.ESTABLISHMENT_ADMIN)
        )
        return result.scalar_one()
```

- [ ] **Step 2: Commit**

```bash
git add app/modules/memberships/infra/repository.py
git commit -m "feat: add get_by_user_and_establishment_expanded to MembershipRepository"
```

---

## Task 3: Adicionar `get_by_user_and_establishment` ao `MembershipsReader`

**Files:**
- Modify: `app/modules/memberships/application/read.py`

- [ ] **Step 1: Adicionar método ao reader**

Em `app/modules/memberships/application/read.py`:

```python
import uuid

from app.core.actor import Actor
from app.core.exceptions import ForbiddenError
from app.core.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
)
from app.db.unit_of_work import UnitOfWork
from app.modules.memberships.domain.expanded import MembershipReadExpanded
from app.modules.memberships.domain.schemas import MembershipRead
from app.modules.memberships.infra.repository import MembershipRepository


class MembershipsReader:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def get_by_user_and_establishment(
        self,
        user_id: uuid.UUID,
        establishment_id: uuid.UUID,
        actor: Actor,
    ) -> MembershipReadExpanded:
        async with self._uow:
            repo = self._uow.repository(MembershipRepository)

            if not actor.is_global_admin:
                caller = await repo.get_by_user_and_establishment_or_none(
                    actor.user_id, establishment_id
                )
                if caller is None:
                    raise ForbiddenError("Acesso negado ao estabelecimento.")

            membership = await repo.get_by_user_and_establishment_expanded(
                user_id=user_id,
                establishment_id=establishment_id,
            )
            return MembershipReadExpanded.model_validate(membership)

    async def paginate(
        self,
        establishment_id: uuid.UUID,
        actor: Actor,
        pagination: PaginationParams,
    ) -> PaginatedResponse[MembershipRead]:
        async with self._uow:
            repo = self._uow.repository(MembershipRepository)

            if not actor.is_global_admin:
                caller = await repo.get_by_user_and_establishment_or_none(
                    actor.user_id, establishment_id
                )
                if caller is None:
                    raise ForbiddenError("Acesso negado ao estabelecimento.")

            items = await repo.list_by_establishment(establishment_id, pagination)
            total = await repo.count_by_establishment(establishment_id)

            return build_paginated_response(
                items=[MembershipRead.model_validate(m) for m in items],
                total=total,
                params=pagination,
            )

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        actor: Actor,
    ) -> list[MembershipRead]:
        if not actor.is_global_admin and actor.user_id != user_id:
            raise ForbiddenError("Acesso negado.")

        async with self._uow:
            repo = self._uow.repository(MembershipRepository)
            memberships = await repo.list_by_user(user_id)
            return [MembershipRead.model_validate(m) for m in memberships]
```

- [ ] **Step 2: Commit**

```bash
git add app/modules/memberships/application/read.py
git commit -m "feat: add get_by_user_and_establishment to MembershipsReader"
```

---

## Task 4: Criar `MembershipActivator` (TDD)

**Files:**
- Create: `tests/modules/memberships/__init__.py`
- Create: `tests/modules/memberships/application/__init__.py`
- Create: `tests/modules/memberships/application/test_activate.py`
- Create: `app/modules/memberships/application/activate.py`

- [ ] **Step 1: Criar pacotes de teste**

```bash
touch tests/modules/memberships/__init__.py
touch tests/modules/memberships/application/__init__.py
```

- [ ] **Step 2: Escrever os testes (falharão)**

Criar `tests/modules/memberships/application/test_activate.py`:

```python
import uuid
from unittest.mock import AsyncMock

import pytest

from app.core.actor import Actor
from app.core.exceptions import ForbiddenError
from app.db.unit_of_work import UnitOfWork
from app.modules.memberships.application.activate import MembershipActivator
from app.modules.memberships.domain.model import Membership
from app.modules.memberships.domain.schemas import MembershipRead
from app.modules.memberships.infra.repository import MembershipRepository
from app.modules.users.domain.enums import UserRole


def make_membership(is_active: bool = True) -> Membership:
    return Membership(
        id=uuid.uuid7(),
        user_id=uuid.uuid7(),
        establishment_id=uuid.uuid7(),
        role=UserRole.ESTABLISHMENT_ADMIN,
        is_active=is_active,
    )


def make_actor(is_global_admin: bool = True) -> Actor:
    return Actor(user_id=uuid.uuid7(), is_global_admin=is_global_admin, memberships=())


@pytest.fixture
def membership() -> Membership:
    return make_membership(is_active=True)


@pytest.fixture
def caller_membership() -> Membership:
    return make_membership(is_active=True)


@pytest.fixture
def mock_repo(membership, caller_membership) -> AsyncMock:
    repo = AsyncMock(spec=MembershipRepository)
    repo.get_by_user_and_establishment_or_none.return_value = caller_membership
    repo.get_by_user_and_establishment.return_value = membership
    repo.update.return_value = membership
    return repo


@pytest.fixture
def mock_uow(mock_repo) -> AsyncMock:
    uow = AsyncMock(spec=UnitOfWork)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = None
    uow.repository.return_value = mock_repo
    return uow


@pytest.fixture
def activator(mock_uow) -> MembershipActivator:
    return MembershipActivator(uow=mock_uow)


async def test_activate_returns_membership_read(activator, membership):
    actor = make_actor(is_global_admin=True)

    result = await activator.activate(
        user_id=membership.user_id,
        establishment_id=membership.establishment_id,
        actor=actor,
    )

    assert isinstance(result, MembershipRead)


async def test_activate_sets_is_active_true(activator, membership):
    membership.is_active = False
    actor = make_actor(is_global_admin=True)

    await activator.activate(
        user_id=membership.user_id,
        establishment_id=membership.establishment_id,
        actor=actor,
    )

    assert membership.is_active is True


async def test_activate_calls_repo_update(activator, mock_repo, membership):
    actor = make_actor(is_global_admin=True)

    await activator.activate(
        user_id=membership.user_id,
        establishment_id=membership.establishment_id,
        actor=actor,
    )

    mock_repo.update.assert_awaited_once_with(membership)


async def test_deactivate_returns_membership_read(activator, membership):
    actor = make_actor(is_global_admin=True)

    result = await activator.deactivate(
        user_id=membership.user_id,
        establishment_id=membership.establishment_id,
        actor=actor,
    )

    assert isinstance(result, MembershipRead)


async def test_deactivate_sets_is_active_false(activator, membership):
    membership.is_active = True
    actor = make_actor(is_global_admin=True)

    await activator.deactivate(
        user_id=membership.user_id,
        establishment_id=membership.establishment_id,
        actor=actor,
    )

    assert membership.is_active is False


async def test_deactivate_calls_repo_update(activator, mock_repo, membership):
    actor = make_actor(is_global_admin=True)

    await activator.deactivate(
        user_id=membership.user_id,
        establishment_id=membership.establishment_id,
        actor=actor,
    )

    mock_repo.update.assert_awaited_once_with(membership)


async def test_activate_raises_forbidden_when_not_establishment_member(
    activator, mock_repo, membership
):
    mock_repo.get_by_user_and_establishment_or_none.return_value = None
    actor = make_actor(is_global_admin=False)

    with pytest.raises(ForbiddenError):
        await activator.activate(
            user_id=membership.user_id,
            establishment_id=membership.establishment_id,
            actor=actor,
        )


async def test_activate_raises_forbidden_when_not_admin_role(
    activator, mock_repo, membership, caller_membership
):
    caller_membership.role = UserRole.EMPLOYEE
    actor = make_actor(is_global_admin=False)

    with pytest.raises(ForbiddenError):
        await activator.activate(
            user_id=membership.user_id,
            establishment_id=membership.establishment_id,
            actor=actor,
        )
```

- [ ] **Step 3: Rodar os testes e confirmar que falham**

```bash
uv run pytest tests/modules/memberships/application/test_activate.py -v
```

Esperado: `ImportError` ou `ModuleNotFoundError` em `activate`.

- [ ] **Step 4: Criar `MembershipActivator`**

Criar `app/modules/memberships/application/activate.py`:

```python
import uuid

from app.core.actor import Actor
from app.db.unit_of_work import UnitOfWork
from app.modules.memberships.application._authz import assert_can_manage
from app.modules.memberships.domain.schemas import MembershipRead
from app.modules.memberships.infra.repository import MembershipRepository


class MembershipActivator:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def activate(
        self,
        user_id: uuid.UUID,
        establishment_id: uuid.UUID,
        actor: Actor,
    ) -> MembershipRead:
        return await self._set_active_status(
            user_id=user_id,
            establishment_id=establishment_id,
            is_active=True,
            actor=actor,
        )

    async def deactivate(
        self,
        user_id: uuid.UUID,
        establishment_id: uuid.UUID,
        actor: Actor,
    ) -> MembershipRead:
        return await self._set_active_status(
            user_id=user_id,
            establishment_id=establishment_id,
            is_active=False,
            actor=actor,
        )

    async def _set_active_status(
        self,
        user_id: uuid.UUID,
        establishment_id: uuid.UUID,
        is_active: bool,
        actor: Actor,
    ) -> MembershipRead:
        async with self._uow:
            repo = self._uow.repository(MembershipRepository)

            caller_membership = await repo.get_by_user_and_establishment_or_none(
                user_id=actor.user_id,
                establishment_id=establishment_id,
            )
            assert_can_manage(actor, caller_membership)

            membership = await repo.get_by_user_and_establishment(
                user_id=user_id,
                establishment_id=establishment_id,
            )
            membership.is_active = is_active
            updated = await repo.update(membership)
            return MembershipRead.model_validate(updated)
```

- [ ] **Step 5: Rodar os testes e confirmar que passam**

```bash
uv run pytest tests/modules/memberships/application/test_activate.py -v
```

Esperado: todos os 8 testes `PASSED`.

- [ ] **Step 6: Commit**

```bash
git add tests/modules/memberships/ \
        app/modules/memberships/application/activate.py
git commit -m "feat: add MembershipActivator use case"
```

---

## Task 5: Atualizar deps, router (memberships) e remover rota do users router

**Files:**
- Modify: `app/modules/memberships/api/deps.py`
- Modify: `app/modules/memberships/api/router.py`
- Modify: `app/modules/users/api/router.py`

- [ ] **Step 1: Adicionar `MembershipActivatorDep` aos deps**

Em `app/modules/memberships/api/deps.py`:

```python
from typing import Annotated

from fastapi import Depends

from app.api.deps import UnitOfWorkDep
from app.modules.memberships.application.activate import MembershipActivator
from app.modules.memberships.application.create import MembershipCreator
from app.modules.memberships.application.delete import MembershipDeleter
from app.modules.memberships.application.read import MembershipsReader
from app.modules.memberships.application.update import MembershipUpdater
from app.modules.memberships.infra.repository import MembershipRepository


def get_memberships_repository(uow: UnitOfWorkDep) -> MembershipRepository:
    return uow.repository(MembershipRepository)


def get_membership_creator(uow: UnitOfWorkDep) -> MembershipCreator:
    return MembershipCreator(uow=uow)


def get_membership_reader(uow: UnitOfWorkDep) -> MembershipsReader:
    return MembershipsReader(uow=uow)


def get_membership_deleter(uow: UnitOfWorkDep) -> MembershipDeleter:
    return MembershipDeleter(uow=uow)


def get_membership_updater(uow: UnitOfWorkDep) -> MembershipUpdater:
    return MembershipUpdater(uow=uow)


def get_membership_activator(uow: UnitOfWorkDep) -> MembershipActivator:
    return MembershipActivator(uow=uow)


MembershipRepositoryDep = Annotated[
    MembershipRepository, Depends(get_memberships_repository)
]
MembershipCreatorDep = Annotated[MembershipCreator, Depends(get_membership_creator)]
MembershipReaderDep = Annotated[MembershipsReader, Depends(get_membership_reader)]
MembershipDeleterDep = Annotated[MembershipDeleter, Depends(get_membership_deleter)]
MembershipUpdaterDep = Annotated[MembershipUpdater, Depends(get_membership_updater)]
MembershipActivatorDep = Annotated[MembershipActivator, Depends(get_membership_activator)]
```

- [ ] **Step 2: Adicionar 3 novos endpoints ao memberships router**

Em `app/modules/memberships/api/router.py`:

```python
import uuid

from fastapi import APIRouter

from app.api.deps import ActorDep, PaginationParamsDep
from app.core.pagination import PaginatedResponse
from app.modules.memberships.api.deps import (
    MembershipActivatorDep,
    MembershipCreatorDep,
    MembershipDeleterDep,
    MembershipReaderDep,
    MembershipUpdaterDep,
)
from app.modules.memberships.domain.expanded import MembershipReadExpanded
from app.modules.memberships.domain.schemas import (
    MembershipInvitePayload,
    MembershipRead,
    MembershipUpdate,
)

router = APIRouter()
user_router = APIRouter()


@router.get(
    "/{establishment_id}/members/", response_model=PaginatedResponse[MembershipRead]
)
async def list_members(
    establishment_id: uuid.UUID,
    pagination: PaginationParamsDep,
    reader: MembershipReaderDep,
    actor: ActorDep,
) -> PaginatedResponse[MembershipRead]:
    return await reader.paginate(
        establishment_id=establishment_id,
        actor=actor,
        pagination=pagination,
    )


@router.post(
    "/{establishment_id}/members/",
    response_model=MembershipReadExpanded,
    status_code=201,
)
async def add_member(
    establishment_id: uuid.UUID,
    body: MembershipInvitePayload,
    creator: MembershipCreatorDep,
    actor: ActorDep,
) -> MembershipReadExpanded:
    return await creator.create(
        establishment_id=establishment_id,
        body=body,
        actor=actor,
    )


@router.get(
    "/{establishment_id}/members/{user_id}",
    response_model=MembershipReadExpanded,
)
async def get_member(
    establishment_id: uuid.UUID,
    user_id: uuid.UUID,
    reader: MembershipReaderDep,
    actor: ActorDep,
) -> MembershipReadExpanded:
    return await reader.get_by_user_and_establishment(
        user_id=user_id,
        establishment_id=establishment_id,
        actor=actor,
    )


@router.patch("/{establishment_id}/members/{user_id}", response_model=MembershipRead)
async def update_member(
    establishment_id: uuid.UUID,
    user_id: uuid.UUID,
    data: MembershipUpdate,
    updater: MembershipUpdaterDep,
    actor: ActorDep,
) -> MembershipRead:
    return await updater.update(
        user_id=user_id,
        establishment_id=establishment_id,
        data=data,
        actor=actor,
    )


@router.delete("/{establishment_id}/members/{user_id}", status_code=204)
async def remove_member(
    establishment_id: uuid.UUID,
    user_id: uuid.UUID,
    deleter: MembershipDeleterDep,
    actor: ActorDep,
) -> None:
    await deleter.delete(
        user_id=user_id,
        establishment_id=establishment_id,
        actor=actor,
    )


@router.post(
    "/{establishment_id}/members/{user_id}/activate",
    response_model=MembershipRead,
)
async def activate_member(
    establishment_id: uuid.UUID,
    user_id: uuid.UUID,
    activator: MembershipActivatorDep,
    actor: ActorDep,
) -> MembershipRead:
    return await activator.activate(
        user_id=user_id,
        establishment_id=establishment_id,
        actor=actor,
    )


@router.post(
    "/{establishment_id}/members/{user_id}/deactivate",
    response_model=MembershipRead,
)
async def deactivate_member(
    establishment_id: uuid.UUID,
    user_id: uuid.UUID,
    activator: MembershipActivatorDep,
    actor: ActorDep,
) -> MembershipRead:
    return await activator.deactivate(
        user_id=user_id,
        establishment_id=establishment_id,
        actor=actor,
    )


@user_router.get("/{user_id}/memberships/", response_model=list[MembershipRead])
async def list_user_memberships(
    user_id: uuid.UUID,
    reader: MembershipReaderDep,
    actor: ActorDep,
) -> list[MembershipRead]:
    return await reader.list_by_user(user_id=user_id, actor=actor)
```

- [ ] **Step 3: Remover rota misplaced do users router**

Em `app/modules/users/api/router.py`, remover o endpoint `get_establishment_members` (linhas 118–135 no arquivo original) e seus imports não mais utilizados (`UsersFiltersDep`).

O arquivo final deve ficar:

```python
import uuid

from fastapi import APIRouter

from app.api.deps import ActorDep, PaginationParamsDep
from app.core.pagination import PaginatedResponse
from app.modules.auth.api.deps import UsersCreatorDep
from app.modules.users.api.deps import (
    UsersActivatorDep,
    UsersDeleterDep,
    UsersReaderDep,
    UsersUpdaterDep,
)
from app.modules.users.domain.enums import UserRole
from app.modules.users.domain.expanded import UserReadExpanded
from app.modules.users.domain.filters import UserFilters
from app.modules.users.domain.schemas import (
    UserCreate,
    UserRead,
    UserUpdate,
)

router = APIRouter()


@router.get("/me", response_model=UserRead)
async def get_me(
    reader: UsersReaderDep,
    actor: ActorDep,
) -> UserRead:
    return await reader.get_by_id(actor.user_id, actor)


@router.patch("/me", response_model=UserRead)
async def update_me(
    data: UserUpdate,
    updater: UsersUpdaterDep,
    actor: ActorDep,
) -> UserRead:
    return await updater.update_me(data, actor)


@router.get("/")
async def list_users(
    pagination: PaginationParamsDep,
    reader: UsersReaderDep,
    actor: ActorDep,
    q: str | None = None,
    role: UserRole | None = None,
    is_active: bool | None = None,
) -> PaginatedResponse[UserRead]:
    return await reader.paginate(
        pagination=pagination,
        actor=actor,
        filters=UserFilters(q=q, is_active=is_active),
    )


@router.get("/{user_id}", response_model=UserReadExpanded)
async def get_user(
    user_id: uuid.UUID,
    reader: UsersReaderDep,
    actor: ActorDep,
) -> UserReadExpanded:
    return await reader.get_by_id(user_id, actor)


@router.post("/", response_model=UserRead, status_code=201)
async def create_user(
    data: UserCreate,
    creator: UsersCreatorDep,
    actor: ActorDep,
) -> UserRead:
    """Cria um novo usuário. Restrito a establishment_admin e global_admin."""
    return await creator.create(data, actor)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    updater: UsersUpdaterDep,
    actor: ActorDep,
) -> UserRead:
    return await updater.update(user_id, data, actor)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: uuid.UUID,
    deleter: UsersDeleterDep,
    actor: ActorDep,
) -> None:
    await deleter.delete(user_id, actor)


@router.post("/{user_id}/activate", response_model=UserRead)
async def activate_user(
    user_id: uuid.UUID,
    activator: UsersActivatorDep,
    actor: ActorDep,
) -> UserRead:
    return await activator.activate(user_id, actor)


@router.post("/{user_id}/deactivate", response_model=UserRead)
async def deactivate_user(
    user_id: uuid.UUID,
    activator: UsersActivatorDep,
    actor: ActorDep,
) -> UserRead:
    return await activator.deactivate(user_id, actor)
```

- [ ] **Step 4: Rodar todos os testes**

```bash
uv run pytest -v
```

Esperado: todos os testes passam.

- [ ] **Step 5: Commit final**

```bash
git add app/modules/memberships/api/deps.py \
        app/modules/memberships/api/router.py \
        app/modules/users/api/router.py
git commit -m "feat: add member activate/deactivate endpoints and remove misplaced users route"
```
