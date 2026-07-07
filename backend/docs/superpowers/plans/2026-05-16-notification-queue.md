# Notification Queue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a Celery-based WhatsApp notification queue that auto-creates `SchedulingNotification` records on scheduling creation and dispatches them via Evolution API at the scheduled time.

**Architecture:** On scheduling creation, one `SchedulingNotification` is inserted per active template linked to the service, with `scheduled_at = starts_at - timedelta(minutes=template.minutes_before)`. A Celery Beat task polls every 30 seconds for due pending notifications and dispatches individual send tasks. Each send task fetches the notification with `SELECT FOR UPDATE SKIP LOCKED`, renders the template content, calls Evolution API, and updates status to `sent` or `failed` (no retry).

**Tech Stack:** Celery 5 + Redis, SQLAlchemy 2.0 async, httpx, Evolution API (WhatsApp), pytest-asyncio

---

## File Map

| Action | Path |
|--------|------|
| Create | `app/integrations/evolution.py` |
| Create | `app/worker/notifications.py` |
| Create | `app/modules/scheduling_notifications/application/create.py` |
| Modify | `app/modules/messaging_templates/infra/repository.py` |
| Modify | `app/modules/scheduling_notifications/infra/repository.py` |
| Modify | `app/modules/schedulings/application/create.py` |
| Modify | `app/celery_app.py` |
| Modify | `app/worker/__init__.py` |
| Create | `tests/integrations/__init__.py` |
| Create | `tests/integrations/test_evolution.py` |
| Create | `tests/modules/messaging_templates/infra/__init__.py` |
| Create | `tests/modules/messaging_templates/infra/test_repository.py` |
| Create | `tests/modules/scheduling_notifications/__init__.py` |
| Create | `tests/modules/scheduling_notifications/infra/__init__.py` |
| Create | `tests/modules/scheduling_notifications/infra/test_repository.py` |
| Create | `tests/modules/scheduling_notifications/application/__init__.py` |
| Create | `tests/modules/scheduling_notifications/application/test_create.py` |
| Create | `tests/worker/__init__.py` |
| Create | `tests/worker/test_notifications.py` |

---

## Task 1: Evolution API Client

**Files:**
- Create: `app/integrations/evolution.py`
- Create: `tests/integrations/__init__.py`
- Create: `tests/integrations/test_evolution.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/integrations/test_evolution.py
from unittest.mock import MagicMock, patch

import pytest

from app.integrations.evolution import EvolutionAPIError, send_text


def test_send_text_success():
    mock_response = MagicMock()
    mock_response.is_success = True
    with patch("app.integrations.evolution.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response
        send_text("5548999999999", "Olá mundo")
        mock_client.return_value.__enter__.return_value.post.assert_called_once_with(
            f"http://fake/message/sendText/fake-instance",
            json={"number": "5548999999999", "text": "Olá mundo"},
            headers={"apikey": "fake-key"},
        )


def test_send_text_raises_on_non_2xx():
    mock_response = MagicMock()
    mock_response.is_success = False
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    with patch("app.integrations.evolution.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response
        with pytest.raises(EvolutionAPIError, match="500"):
            send_text("5548999999999", "Olá mundo")
```

> Note: the test above checks `f"http://fake/message/sendText/fake-instance"` — update this to match your actual settings mock approach. Since Settings requires env vars, run tests with the existing test pattern (no env file needed for unit tests that patch httpx). The tests for the integration layer don't call `settings` at module load time — `send_text` calls it at call time. Patch `app.integrations.evolution.settings` to avoid needing env vars.

Revised tests that patch settings:

```python
# tests/integrations/test_evolution.py
from unittest.mock import MagicMock, patch

import pytest

from app.integrations.evolution import EvolutionAPIError, send_text


def _mock_settings():
    s = MagicMock()
    s.EVOLUTION_URL = "http://evo"
    s.EVOLUTION_INSTANCE = "inst"
    s.EVOLUTION_APIKEY = "key"
    return s


def test_send_text_success():
    mock_response = MagicMock()
    mock_response.is_success = True
    with (
        patch("app.integrations.evolution.settings", _mock_settings()),
        patch("app.integrations.evolution.httpx.Client") as mock_client,
    ):
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response
        send_text("5548999999999", "Olá mundo")
        mock_client.return_value.__enter__.return_value.post.assert_called_once_with(
            "http://evo/message/sendText/inst",
            json={"number": "5548999999999", "text": "Olá mundo"},
            headers={"apikey": "key"},
        )


def test_send_text_raises_on_non_2xx():
    mock_response = MagicMock()
    mock_response.is_success = False
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    with (
        patch("app.integrations.evolution.settings", _mock_settings()),
        patch("app.integrations.evolution.httpx.Client") as mock_client,
    ):
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response
        with pytest.raises(EvolutionAPIError, match="500"):
            send_text("5548999999999", "Olá mundo")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /path/to/project && uv run pytest tests/integrations/test_evolution.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.integrations.evolution'`

- [ ] **Step 3: Create `tests/integrations/__init__.py`**

```python
# tests/integrations/__init__.py
```

(empty file)

- [ ] **Step 4: Implement `app/integrations/evolution.py`**

```python
# app/integrations/evolution.py
import httpx

from app.core.settings import settings


class EvolutionAPIError(Exception):
    pass


def send_text(phone: str, text: str) -> None:
    url = f"{settings.EVOLUTION_URL}/message/sendText/{settings.EVOLUTION_INSTANCE}"
    headers = {"apikey": settings.EVOLUTION_APIKEY}
    with httpx.Client(timeout=10) as client:
        response = client.post(url, json={"number": phone, "text": text}, headers=headers)
    if not response.is_success:
        raise EvolutionAPIError(f"{response.status_code}: {response.text}")
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
uv run pytest tests/integrations/test_evolution.py -v
```

Expected: `2 passed`

- [ ] **Step 6: Commit**

```bash
git add app/integrations/evolution.py tests/integrations/__init__.py tests/integrations/test_evolution.py
git commit -m "feat: add Evolution API client with send_text"
```

---

## Task 2: `get_active_templates_for_service` in `MessagingTemplatesRepository`

**Files:**
- Modify: `app/modules/messaging_templates/infra/repository.py`
- Create: `tests/modules/messaging_templates/infra/__init__.py`
- Create: `tests/modules/messaging_templates/infra/test_repository.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/modules/messaging_templates/infra/test_repository.py
import uuid
from unittest.mock import AsyncMock, MagicMock

from app.modules.messaging_templates.domain.model import MessagingTemplate
from app.modules.messaging_templates.infra.repository import MessagingTemplatesRepository


async def test_get_active_templates_for_service_returns_matching():
    service_id = uuid.uuid7()
    template = MagicMock(spec=MessagingTemplate)

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value = [template]
    mock_session.execute.return_value = mock_result

    repo = MessagingTemplatesRepository(mock_session)
    result = await repo.get_active_templates_for_service(service_id)

    assert result == [template]
    mock_session.execute.assert_called_once()


async def test_get_active_templates_for_service_returns_empty_when_none():
    service_id = uuid.uuid7()

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value = []
    mock_session.execute.return_value = mock_result

    repo = MessagingTemplatesRepository(mock_session)
    result = await repo.get_active_templates_for_service(service_id)

    assert result == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/modules/messaging_templates/infra/test_repository.py -v
```

Expected: `AttributeError: 'MessagingTemplatesRepository' object has no attribute 'get_active_templates_for_service'`

- [ ] **Step 3: Add `get_active_templates_for_service` to the repository**

Open `app/modules/messaging_templates/infra/repository.py` and add this method after `get_link_or_none` (before `_construct_select_query`):

```python
async def get_active_templates_for_service(self, service_id: uuid.UUID) -> list[MessagingTemplate]:
    query = (
        select(MessagingTemplate)
        .join(ServiceMessagingTemplate, ServiceMessagingTemplate.template_id == MessagingTemplate.id)
        .where(ServiceMessagingTemplate.service_id == service_id)
        .where(MessagingTemplate.is_active.is_(True))
        .where(MessagingTemplate.deleted_at.is_(None))
        .where(MessagingTemplate.minutes_before.is_not(None))
    )
    result = await self._session.execute(query)
    return list(result.scalars())
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/modules/messaging_templates/infra/test_repository.py -v
```

Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add app/modules/messaging_templates/infra/repository.py \
        tests/modules/messaging_templates/infra/__init__.py \
        tests/modules/messaging_templates/infra/test_repository.py
git commit -m "feat: add get_active_templates_for_service to MessagingTemplatesRepository"
```

---

## Task 3: `get_pending_due` in `SchedulingNotificationsRepository`

**Files:**
- Modify: `app/modules/scheduling_notifications/infra/repository.py`
- Create: `tests/modules/scheduling_notifications/__init__.py`
- Create: `tests/modules/scheduling_notifications/infra/__init__.py`
- Create: `tests/modules/scheduling_notifications/infra/test_repository.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/modules/scheduling_notifications/infra/test_repository.py
import uuid
from unittest.mock import AsyncMock, MagicMock

from app.modules.scheduling_notifications.domain.model import SchedulingNotification
from app.modules.scheduling_notifications.infra.repository import SchedulingNotificationsRepository


async def test_get_pending_due_returns_due_notifications():
    notification = MagicMock(spec=SchedulingNotification)

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value = [notification]
    mock_session.execute.return_value = mock_result

    repo = SchedulingNotificationsRepository(mock_session)
    result = await repo.get_pending_due(limit=10)

    assert result == [notification]
    mock_session.execute.assert_called_once()


async def test_get_pending_due_returns_empty_when_none_due():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value = []
    mock_session.execute.return_value = mock_result

    repo = SchedulingNotificationsRepository(mock_session)
    result = await repo.get_pending_due()

    assert result == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/modules/scheduling_notifications/infra/test_repository.py -v
```

Expected: `AttributeError: 'SchedulingNotificationsRepository' object has no attribute 'get_pending_due'`

- [ ] **Step 3: Add imports and `get_pending_due` to the repository**

Open `app/modules/scheduling_notifications/infra/repository.py`. Add `datetime` and `UTC` to the imports at the top:

```python
import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginationParams
from app.modules.scheduling_notifications.domain.enums import NotificationStatus
from app.modules.scheduling_notifications.domain.filters import (
    SchedulingNotificationFilters,
)
from app.modules.scheduling_notifications.domain.model import SchedulingNotification
```

Then add this method after `count` (before `_construct_select_query`):

```python
async def get_pending_due(self, limit: int = 100) -> list[SchedulingNotification]:
    now = datetime.now(UTC)
    query = (
        select(SchedulingNotification)
        .where(SchedulingNotification.status == NotificationStatus.pending)
        .where(SchedulingNotification.scheduled_at <= now)
        .limit(limit)
    )
    result = await self._session.execute(query)
    return list(result.scalars())
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/modules/scheduling_notifications/infra/test_repository.py -v
```

Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add app/modules/scheduling_notifications/infra/repository.py \
        tests/modules/scheduling_notifications/__init__.py \
        tests/modules/scheduling_notifications/infra/__init__.py \
        tests/modules/scheduling_notifications/infra/test_repository.py
git commit -m "feat: add get_pending_due to SchedulingNotificationsRepository"
```

---

## Task 4: `SchedulingNotificationsCreator` Use Case

**Files:**
- Create: `app/modules/scheduling_notifications/application/create.py`
- Create: `tests/modules/scheduling_notifications/application/__init__.py`
- Create: `tests/modules/scheduling_notifications/application/test_create.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/modules/scheduling_notifications/application/test_create.py
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from app.db.unit_of_work import UnitOfWork
from app.modules.messaging_templates.domain.enums import TemplateType
from app.modules.messaging_templates.domain.model import MessagingTemplate
from app.modules.messaging_templates.infra.repository import MessagingTemplatesRepository
from app.modules.scheduling_notifications.application.create import (
    SchedulingNotificationsCreator,
)
from app.modules.scheduling_notifications.domain.enums import NotificationStatus
from app.modules.schedulings.domain.enums import SchedulingSource, SchedulingStatus
from app.modules.schedulings.domain.model import Scheduling


def make_template(establishment_id: uuid.UUID, minutes_before: int = 60) -> MessagingTemplate:
    return MessagingTemplate(
        id=uuid.uuid7(),
        establishment_id=establishment_id,
        name="Lembrete",
        content="Olá {cliente}, seu {servico} é em {data} às {hora}",
        type=TemplateType.REMINDER,
        is_active=True,
        minutes_before=minutes_before,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def make_scheduling(
    establishment_id: uuid.UUID,
    service_id: uuid.UUID,
    starts_at: datetime,
) -> Scheduling:
    return Scheduling(
        id=uuid.uuid7(),
        establishment_id=establishment_id,
        user_id=uuid.uuid7(),
        client_id=uuid.uuid7(),
        service_id=service_id,
        status=SchedulingStatus.PENDING,
        source=SchedulingSource.APP,
        starts_at=starts_at,
        ends_at=starts_at + timedelta(minutes=30),
    )


async def test_create_for_scheduling_inserts_one_notification_per_template():
    establishment_id = uuid.uuid7()
    service_id = uuid.uuid7()
    starts_at = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)
    scheduling = make_scheduling(establishment_id, service_id, starts_at)

    template_60 = make_template(establishment_id, minutes_before=60)
    template_1440 = make_template(establishment_id, minutes_before=1440)

    mock_templates_repo = AsyncMock(spec=MessagingTemplatesRepository)
    mock_templates_repo.get_active_templates_for_service.return_value = [
        template_60,
        template_1440,
    ]

    mock_session = AsyncMock()
    mock_uow = MagicMock(spec=UnitOfWork)
    mock_uow.session = mock_session
    mock_uow.repository.return_value = mock_templates_repo

    creator = SchedulingNotificationsCreator(mock_uow)
    notifications = await creator.create_for_scheduling(scheduling)

    assert len(notifications) == 2
    assert mock_session.add.call_count == 2
    mock_session.flush.assert_called_once()
    assert notifications[0].scheduled_at == starts_at - timedelta(minutes=60)
    assert notifications[1].scheduled_at == starts_at - timedelta(minutes=1440)
    assert all(n.status == NotificationStatus.pending for n in notifications)
    assert all(n.scheduling_id == scheduling.id for n in notifications)
    assert all(n.establishment_id == establishment_id for n in notifications)


async def test_create_for_scheduling_creates_nothing_when_no_templates():
    establishment_id = uuid.uuid7()
    service_id = uuid.uuid7()
    starts_at = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)
    scheduling = make_scheduling(establishment_id, service_id, starts_at)

    mock_templates_repo = AsyncMock(spec=MessagingTemplatesRepository)
    mock_templates_repo.get_active_templates_for_service.return_value = []

    mock_session = AsyncMock()
    mock_uow = MagicMock(spec=UnitOfWork)
    mock_uow.session = mock_session
    mock_uow.repository.return_value = mock_templates_repo

    creator = SchedulingNotificationsCreator(mock_uow)
    notifications = await creator.create_for_scheduling(scheduling)

    assert notifications == []
    mock_session.add.assert_not_called()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/modules/scheduling_notifications/application/test_create.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.modules.scheduling_notifications.application.create'`

- [ ] **Step 3: Implement `app/modules/scheduling_notifications/application/create.py`**

```python
# app/modules/scheduling_notifications/application/create.py
import uuid
from datetime import timedelta

from app.db.unit_of_work import UnitOfWork
from app.modules.messaging_templates.infra.repository import MessagingTemplatesRepository
from app.modules.scheduling_notifications.domain.enums import NotificationStatus
from app.modules.scheduling_notifications.domain.model import SchedulingNotification
from app.modules.schedulings.domain.model import Scheduling


class SchedulingNotificationsCreator:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def create_for_scheduling(self, scheduling: Scheduling) -> list[SchedulingNotification]:
        templates_repo = self._uow.repository(MessagingTemplatesRepository)
        templates = await templates_repo.get_active_templates_for_service(scheduling.service_id)

        notifications: list[SchedulingNotification] = []
        for template in templates:
            scheduled_at = scheduling.starts_at - timedelta(minutes=template.minutes_before)  # type: ignore[arg-type]
            notification = SchedulingNotification(
                establishment_id=scheduling.establishment_id,
                scheduling_id=scheduling.id,
                template_id=template.id,
                scheduled_at=scheduled_at,
                status=NotificationStatus.pending,
            )
            self._uow.session.add(notification)
            notifications.append(notification)

        await self._uow.session.flush()
        return notifications
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/modules/scheduling_notifications/application/test_create.py -v
```

Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add app/modules/scheduling_notifications/application/create.py \
        tests/modules/scheduling_notifications/application/__init__.py \
        tests/modules/scheduling_notifications/application/test_create.py
git commit -m "feat: add SchedulingNotificationsCreator use case"
```

---

## Task 5: Celery Tasks

**Files:**
- Create: `app/worker/notifications.py`
- Create: `tests/worker/__init__.py`
- Create: `tests/worker/test_notifications.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/worker/test_notifications.py
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.scheduling_notifications.domain.enums import NotificationStatus
from app.modules.scheduling_notifications.domain.model import SchedulingNotification
from app.modules.scheduling_notifications.infra.repository import (
    SchedulingNotificationsRepository,
)
from app.worker.notifications import _dispatch_pending, _send_notification


def _make_notification(
    status: NotificationStatus = NotificationStatus.pending,
) -> MagicMock:
    n = MagicMock(spec=SchedulingNotification)
    n.id = uuid.uuid7()
    n.status = status
    n.scheduling_id = uuid.uuid7()
    n.template_id = uuid.uuid7()
    n.attempts = 0
    n.content_at_send = None
    n.last_error = None
    n.sent_at = None
    n.last_attempt_at = None
    return n


def _make_scheduling() -> MagicMock:
    s = MagicMock()
    s.client_id = uuid.uuid7()
    s.service_id = uuid.uuid7()
    s.starts_at = datetime(2026, 6, 1, 14, 0, tzinfo=UTC)
    return s


def _make_client(name: str = "João Silva", phone: str = "5548999999999") -> MagicMock:
    c = MagicMock()
    c.name = name
    c.phone = phone
    return c


def _make_service(name: str = "Corte de Cabelo") -> MagicMock:
    s = MagicMock()
    s.name = name
    return s


def _make_template(
    content: str = "Olá {cliente}, seu {servico} é em {data} às {hora}",
) -> MagicMock:
    t = MagicMock()
    t.content = content
    return t


def _mock_session_with_notification(notification: MagicMock) -> AsyncMock:
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = notification
    mock_session.execute.return_value = mock_result
    return mock_session


async def test_send_notification_success():
    notification = _make_notification()
    scheduling = _make_scheduling()
    client = _make_client()
    service = _make_service()
    template = _make_template()

    mock_session = _mock_session_with_notification(notification)
    mock_session.get.side_effect = [scheduling, client, service, template]

    with patch("app.worker.notifications.send_text") as mock_send:
        await _send_notification(notification.id, mock_session)

    assert notification.status == NotificationStatus.sent
    assert notification.sent_at is not None
    assert notification.attempts == 1
    assert notification.content_at_send is not None
    mock_send.assert_called_once_with(
        "5548999999999",
        notification.content_at_send,
    )


async def test_send_notification_marks_failed_on_evolution_api_error():
    from app.integrations.evolution import EvolutionAPIError

    notification = _make_notification()
    scheduling = _make_scheduling()
    client = _make_client()
    service = _make_service()
    template = _make_template()

    mock_session = _mock_session_with_notification(notification)
    mock_session.get.side_effect = [scheduling, client, service, template]

    with patch(
        "app.worker.notifications.send_text",
        side_effect=EvolutionAPIError("500: timeout"),
    ):
        await _send_notification(notification.id, mock_session)

    assert notification.status == NotificationStatus.failed
    assert "timeout" in notification.last_error
    assert notification.attempts == 1
    assert notification.last_attempt_at is not None


async def test_send_notification_skips_when_not_pending():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    with patch("app.worker.notifications.send_text") as mock_send:
        await _send_notification(uuid.uuid7(), mock_session)

    mock_send.assert_not_called()
    mock_session.get.assert_not_called()


async def test_send_notification_marks_failed_on_unknown_template_variable():
    notification = _make_notification()
    scheduling = _make_scheduling()
    client = _make_client()
    service = _make_service()
    template = _make_template(content="Olá {cliente}, sua {variavel_inexistente}")

    mock_session = _mock_session_with_notification(notification)
    mock_session.get.side_effect = [scheduling, client, service, template]

    with patch("app.worker.notifications.send_text") as mock_send:
        await _send_notification(notification.id, mock_session)

    assert notification.status == NotificationStatus.failed
    assert "Variável desconhecida" in notification.last_error
    mock_send.assert_not_called()


async def test_send_notification_renders_template_variables():
    notification = _make_notification()
    scheduling = _make_scheduling()
    scheduling.starts_at = datetime(2026, 6, 1, 14, 30, tzinfo=UTC)
    client = _make_client(name="Maria Souza", phone="5548911111111")
    service = _make_service(name="Manicure")
    template = _make_template(
        content="Olá {cliente}, seu {servico} é em {data} às {hora}"
    )

    mock_session = _mock_session_with_notification(notification)
    mock_session.get.side_effect = [scheduling, client, service, template]

    with patch("app.worker.notifications.send_text") as mock_send:
        await _send_notification(notification.id, mock_session)

    sent_text = mock_send.call_args[0][1]
    assert "Maria Souza" in sent_text
    assert "Manicure" in sent_text
    assert "01/06/2026" in sent_text
    assert "11:30" in sent_text  # UTC 14:30 = BRT 11:30


async def test_dispatch_pending_dispatches_task_per_notification():
    n1 = MagicMock(id=uuid.uuid7())
    n2 = MagicMock(id=uuid.uuid7())

    mock_repo = AsyncMock(spec=SchedulingNotificationsRepository)
    mock_repo.get_pending_due.return_value = [n1, n2]

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    mock_db = MagicMock()
    mock_db.create_session.return_value = mock_session

    with (
        patch("app.worker.notifications.db", mock_db),
        patch(
            "app.worker.notifications.SchedulingNotificationsRepository",
            return_value=mock_repo,
        ),
        patch("app.worker.notifications.send_notification") as mock_send_task,
    ):
        await _dispatch_pending()

    assert mock_send_task.delay.call_count == 2
    mock_send_task.delay.assert_any_call(str(n1.id))
    mock_send_task.delay.assert_any_call(str(n2.id))


async def test_dispatch_pending_does_nothing_when_empty():
    mock_repo = AsyncMock(spec=SchedulingNotificationsRepository)
    mock_repo.get_pending_due.return_value = []

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    mock_db = MagicMock()
    mock_db.create_session.return_value = mock_session

    with (
        patch("app.worker.notifications.db", mock_db),
        patch(
            "app.worker.notifications.SchedulingNotificationsRepository",
            return_value=mock_repo,
        ),
        patch("app.worker.notifications.send_notification") as mock_send_task,
    ):
        await _dispatch_pending()

    mock_send_task.delay.assert_not_called()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/worker/test_notifications.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.worker.notifications'`

- [ ] **Step 3: Implement `app/worker/notifications.py`**

```python
# app/worker/notifications.py
import asyncio
import uuid
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import app.db.models  # noqa: F401 — registers all ORM models for SQLAlchemy
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery
from app.db.session import db
from app.integrations.evolution import EvolutionAPIError, send_text
from app.modules.clients.domain.model import Client
from app.modules.messaging_templates.domain.model import MessagingTemplate
from app.modules.schedulings.domain.model import Scheduling
from app.modules.scheduling_notifications.domain.enums import NotificationStatus
from app.modules.scheduling_notifications.domain.model import SchedulingNotification
from app.modules.scheduling_notifications.infra.repository import (
    SchedulingNotificationsRepository,
)
from app.modules.services.domain.model import Service

_TZ = ZoneInfo("America/Sao_Paulo")


@celery.task(name="beat_dispatch_notifications")
def beat_dispatch_notifications() -> None:
    asyncio.run(_dispatch_pending())


async def _dispatch_pending() -> None:
    db.init()
    async with db.create_session() as session:
        repo = SchedulingNotificationsRepository(session)
        notifications = await repo.get_pending_due(limit=100)
        for notification in notifications:
            send_notification.delay(str(notification.id))


@celery.task(name="send_notification")
def send_notification(notification_id: str) -> None:
    asyncio.run(_run_send(uuid.UUID(notification_id)))


async def _run_send(notification_id: uuid.UUID) -> None:
    db.init()
    async with db.create_session() as session:
        async with session.begin():
            await _send_notification(notification_id, session)


async def _send_notification(notification_id: uuid.UUID, session: AsyncSession) -> None:
    result = await session.execute(
        select(SchedulingNotification)
        .where(SchedulingNotification.id == notification_id)
        .where(SchedulingNotification.status == NotificationStatus.pending)
        .with_for_update(skip_locked=True)
    )
    notification = result.scalar_one_or_none()
    if notification is None:
        return

    scheduling = await session.get(Scheduling, notification.scheduling_id)
    if scheduling is None:
        notification.status = NotificationStatus.failed
        notification.last_error = "Agendamento não encontrado"
        notification.attempts += 1
        notification.last_attempt_at = datetime.now(UTC)
        return

    client = await session.get(Client, scheduling.client_id)
    service = await session.get(Service, scheduling.service_id)
    template = await session.get(MessagingTemplate, notification.template_id)

    if client is None or service is None or template is None:
        notification.status = NotificationStatus.failed
        notification.last_error = "Dados relacionados não encontrados"
        notification.attempts += 1
        notification.last_attempt_at = datetime.now(UTC)
        return

    starts_local = scheduling.starts_at.astimezone(_TZ)
    try:
        rendered = template.content.format_map({
            "cliente": client.name,
            "servico": service.name,
            "data": starts_local.strftime("%d/%m/%Y"),
            "hora": starts_local.strftime("%H:%M"),
        })
    except KeyError as exc:
        notification.status = NotificationStatus.failed
        notification.last_error = f"Variável desconhecida no template: {exc}"
        notification.attempts += 1
        notification.last_attempt_at = datetime.now(UTC)
        return

    notification.content_at_send = rendered
    now = datetime.now(UTC)
    try:
        send_text(client.phone, rendered)
        notification.status = NotificationStatus.sent
        notification.sent_at = now
        notification.attempts += 1
    except EvolutionAPIError as exc:
        notification.status = NotificationStatus.failed
        notification.last_error = str(exc)
        notification.attempts += 1
        notification.last_attempt_at = now
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/worker/test_notifications.py -v
```

Expected: `7 passed`

- [ ] **Step 5: Commit**

```bash
git add app/worker/notifications.py \
        tests/worker/__init__.py \
        tests/worker/test_notifications.py
git commit -m "feat: add Celery tasks for notification dispatch and send"
```

---

## Task 6: Wire Everything Together

**Files:**
- Modify: `app/worker/__init__.py`
- Modify: `app/celery_app.py`
- Modify: `app/modules/schedulings/application/create.py`

- [ ] **Step 1: Update `app/worker/__init__.py`**

Replace the empty file with:

```python
# app/worker/__init__.py
from app.worker import notifications  # noqa: F401
```

- [ ] **Step 2: Add beat schedule to `app/celery_app.py`**

The file currently ends after `task_reject_on_worker_lost=True,`. Add the beat schedule below the existing `celery.conf.update(...)` call:

```python
from celery import Celery

from app.core.settings import settings

celery = Celery(
    main="app",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.worker"],
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

celery.conf.beat_schedule = {
    "dispatch-notifications-every-30s": {
        "task": "beat_dispatch_notifications",
        "schedule": 30.0,
    },
}
```

- [ ] **Step 3: Write a test for the wiring in schedulings create**

```python
# tests/modules/schedulings/application/test_create_notifications.py
# Tests that SchedulingNotificationsCreator is called during scheduling creation.
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

from app.core.actor import Actor, Membership
from app.db.unit_of_work import UnitOfWork
from app.modules.clients.domain.model import Client
from app.modules.memberships.domain.model import Membership as MembershipModel
from app.modules.operating_hours.domain.model import OperatingHour
from app.modules.schedulings.application.create import SchedulingsCreator
from app.modules.schedulings.domain.model import Scheduling
from app.modules.schedulings.domain.schemas import SchedulingCreate
from app.modules.services.domain.model import Service
from app.modules.users.domain.enums import UserRole
from app.modules.users.domain.model import User

_TZ = ZoneInfo("America/Sao_Paulo")


def _make_actor(establishment_id: uuid.UUID) -> Actor:
    return Actor(
        user_id=uuid.uuid7(),
        is_global_admin=False,
        memberships=(
            Membership(establishment_id=establishment_id, role=UserRole.ESTABLISHMENT_ADMIN),
        ),
    )


async def test_create_scheduling_calls_notifications_creator():
    establishment_id = uuid.uuid7()
    actor = _make_actor(establishment_id)
    # Monday noon BRT = Monday 15:00 UTC, safely in the future
    starts_at = datetime(2026, 6, 8, 15, 0, tzinfo=UTC)
    starts_local = starts_at.astimezone(_TZ)

    user = MagicMock(spec=User)
    user.id = actor.user_id
    user.is_active = True

    membership = MagicMock(spec=MembershipModel)

    client = MagicMock(spec=Client)
    client.id = uuid.uuid7()
    client.is_active = True
    client.establishment_id = establishment_id

    service = MagicMock(spec=Service)
    service.id = uuid.uuid7()
    service.is_active = True
    service.establishment_id = establishment_id
    service.duration_minutes = 30

    # OperatingHour must match the weekday and time window of starts_at in BRT
    hour = MagicMock(spec=OperatingHour)
    hour.weekday = starts_local.weekday()
    hour.start_time = datetime(2026, 6, 8, 8, 0).time()   # 08:00 — before 12:00 BRT
    hour.end_time = datetime(2026, 6, 8, 18, 0).time()    # 18:00 — after 12:00 BRT

    scheduling = MagicMock(spec=Scheduling)
    scheduling.id = uuid.uuid7()

    mock_schedulings_repo = AsyncMock()
    mock_schedulings_repo.has_user_overlap.return_value = False
    mock_schedulings_repo.has_client_overlap.return_value = False
    mock_schedulings_repo.create.return_value = scheduling
    mock_schedulings_repo.get_by_id_expanded.return_value = scheduling

    mock_uow = AsyncMock(spec=UnitOfWork)
    mock_uow.__aenter__.return_value = mock_uow
    mock_uow.__aexit__.return_value = None
    mock_uow.session = AsyncMock()

    from app.modules.clients.infra.repository import ClientsRepository
    from app.modules.memberships.infra.repository import MembershipRepository
    from app.modules.operating_hours.infra.repository import OperatingHoursRepository
    from app.modules.schedulings.infra.repository import SchedulingsRepository
    from app.modules.services.infra.repository import ServicesRepository
    from app.modules.users.infra.repository import UsersRepository

    def get_repo(cls):
        mapping = {
            SchedulingsRepository: mock_schedulings_repo,
            UsersRepository: AsyncMock(**{"get_by_id_or_none.return_value": user}),
            ClientsRepository: AsyncMock(**{"get_by_id_or_none.return_value": client}),
            ServicesRepository: AsyncMock(**{"get_by_id_or_none.return_value": service}),
            MembershipRepository: AsyncMock(
                **{"get_by_user_and_establishment_or_none.return_value": membership}
            ),
            OperatingHoursRepository: AsyncMock(
                **{"list_by_establishment.return_value": [hour]}
            ),
        }
        return mapping[cls]

    mock_uow.repository.side_effect = get_repo

    data = SchedulingCreate(
        user_id=actor.user_id,
        client_id=client.id,
        service_id=service.id,
        starts_at=starts_at,
    )

    with (
        patch(
            "app.modules.schedulings.application.create.SchedulingNotificationsCreator"
        ) as mock_creator_cls,
        patch(
            "app.modules.schedulings.domain.schemas.SchedulingExpandedRead.model_validate",
            return_value=MagicMock(),
        ),
    ):
        mock_creator = AsyncMock()
        mock_creator_cls.return_value = mock_creator

        creator = SchedulingsCreator(mock_uow)
        await creator.create(data, actor, establishment_id)

    mock_creator_cls.assert_called_once_with(mock_uow)
    mock_creator.create_for_scheduling.assert_called_once_with(scheduling)
```

- [ ] **Step 4: Run the test to verify it fails**

```bash
uv run pytest tests/modules/schedulings/application/test_create_notifications.py -v
```

Expected: FAIL (either `ImportError` for missing `SchedulingNotificationsCreator` import in `create.py`, or assertion failure that `create_for_scheduling` was not called).

- [ ] **Step 5: Update `app/modules/schedulings/application/create.py`**

Add the import at the top (after existing imports):

```python
from app.modules.scheduling_notifications.application.create import (
    SchedulingNotificationsCreator,
)
```

Replace the TODO comment block (lines 131-132):

```python
            # TODO: enqueue Celery tasks for SchedulingNotification and Google Calendar sync
```

With:

```python
            notifications_creator = SchedulingNotificationsCreator(self._uow)
            await notifications_creator.create_for_scheduling(scheduling)
```

- [ ] **Step 6: Create `tests/modules/schedulings/__init__.py` and `tests/modules/schedulings/application/__init__.py`**

Both are empty files. Create them so pytest discovers the new test.

- [ ] **Step 7: Run all tests**

```bash
uv run pytest tests/modules/schedulings/application/test_create_notifications.py -v
```

Expected: `1 passed`

Then run the full suite:

```bash
uv run pytest -v
```

Expected: all tests pass.

- [ ] **Step 8: Commit**

```bash
git add app/worker/__init__.py \
        app/celery_app.py \
        app/modules/schedulings/application/create.py \
        tests/modules/schedulings/__init__.py \
        tests/modules/schedulings/application/__init__.py \
        tests/modules/schedulings/application/test_create_notifications.py
git commit -m "feat: wire notification queue — creation, beat dispatch, and send task"
```

---

## Running the Full Stack

After all tasks complete:

```bash
# Start worker
uv run celery -A app.celery_app worker --loglevel=info

# Start beat scheduler (in a separate terminal)
uv run celery -A app.celery_app beat --loglevel=info

# Or combined (dev only, not for production)
uv run celery -A app.celery_app worker --beat --loglevel=info
```

The beat scheduler requires `REDIS_URL` to be set and Redis running. Notifications with `scheduled_at <= now()` and `status = pending` will be dispatched every 30 seconds.
