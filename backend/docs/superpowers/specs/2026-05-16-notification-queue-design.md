# Notification Queue — Design Spec

**Date:** 2026-05-16  
**Branch:** feat/schedulings  
**Status:** Approved

---

## Context

The system already has:
- `SchedulingNotification` ORM model with all required fields (`scheduled_at`, `status`, `attempts`, `last_error`, `content_at_send`, `sent_at`)
- Celery configured with Redis broker/backend (`app/celery_app.py`)
- Evolution API credentials in settings (`EVOLUTION_URL`, `EVOLUTION_INSTANCE`, `EVOLUTION_APIKEY`)
- `MessagingTemplate` with `minutes_before` and types `CONFIRMATION`, `REMINDER`, `CANCELLATION`
- `ServiceMessagingTemplate` linking services to templates (one template per type per service)
- Manual cancellation route already implemented (`SchedulingNotificationsCanceller`)

---

## Architecture

Three independent stages:

### 1. Notification creation (triggered on scheduling creation)

Inside `SchedulingsCreator.create()`, after persisting the scheduling (same UoW):

1. Call `SchedulingNotificationsCreator.create_for_scheduling(scheduling, uow)`
2. Fetch all active `ServiceMessagingTemplate` records for the service
3. For each linked template: insert a `SchedulingNotification` with:
   - `scheduled_at = scheduling.starts_at - timedelta(minutes=template.minutes_before)`
   - `status = pending`
   - `template_id = template.id`
   - `establishment_id = scheduling.establishment_id`
   - `scheduling_id = scheduling.id`

### 2. Celery Beat dispatcher (every 30 seconds)

Task `beat_dispatch_notifications`:
- Queries `scheduling_notifications` where `status = pending AND scheduled_at <= now()`
- Uses `SELECT FOR UPDATE SKIP LOCKED LIMIT 100` to prevent duplicate dispatch across multiple beat instances
- For each result, dispatches `send_notification.delay(notification_id)`
- The worker re-checks `status == pending` at the start of each task as a guard against race conditions

### 3. Celery Worker — send task

Task `send_notification(notification_id: str)`:
1. Fetch notification from DB (sync session)
2. Skip if status is not `pending` (guard against race conditions)
3. Fetch scheduling, client, service, template
4. Render message content using `str.format_map`:
   - `{cliente}` → `client.name`
   - `{servico}` → `service.name`
   - `{data}` → `scheduling.starts_at` in `America/Sao_Paulo`, formatted as `DD/MM/YYYY`
   - `{hora}` → `scheduling.starts_at` in `America/Sao_Paulo`, formatted as `HH:MM`
5. Save `content_at_send` (snapshot before sending)
6. Call Evolution API:
   ```
   POST {EVOLUTION_URL}/message/sendText/{EVOLUTION_INSTANCE}
   Headers: { "apikey": "{EVOLUTION_APIKEY}" }
   Body: { "number": "{client.phone}", "text": "{rendered_content}" }
   ```
7. On success: `status = sent`, `sent_at = now()`, `attempts += 1`
8. On failure (any exception or non-2xx response): `status = failed`, `last_error = str(error)`, `attempts += 1`, `last_attempt_at = now()`

**No retry.** A failed notification stays `failed`.

---

## Cancellation

Manual cancellation is already implemented via the existing API route. The beat task filters only `pending` notifications, so `cancelled` and `failed` records are never re-processed.

When a scheduling is cancelled (future concern, not in scope of this spec), pending notifications for that scheduling should be cancelled — but this is deferred.

---

## Components

### New files

| File | Purpose |
|------|---------|
| `app/integrations/evolution.py` | HTTP client for Evolution API (`send_text(phone, message) -> None`) |
| `app/worker/notifications.py` | Celery tasks: `beat_dispatch_notifications` and `send_notification` |
| `app/modules/scheduling_notifications/application/create.py` | Use case: creates notifications from service templates |

### Modified files

| File | Change |
|------|--------|
| `app/worker/__init__.py` | Import `app.worker.notifications` so Celery discovers tasks |
| `app/celery_app.py` | Add `beat_schedule` entry for `beat_dispatch_notifications` (30s interval) |
| `app/modules/schedulings/application/create.py` | Call `SchedulingNotificationsCreator` after creating the scheduling |
| `app/modules/scheduling_notifications/infra/repository.py` | Add `get_pending_due(limit)` with `FOR UPDATE SKIP LOCKED` (sync) |
| `app/modules/messaging_templates/infra/repository.py` | Add `get_active_templates_for_service(service_id)` |

**No new migrations** — `SchedulingNotification` model already has all required fields.

---

## Implementation Notes

### Sync vs async in Celery

Celery tasks run outside the asyncio event loop. The worker uses a **synchronous** SQLAlchemy engine (same DB URL, `postgresql+psycopg2` driver) separate from the async engine used by FastAPI. The beat task and send task both use `with engine.begin() as conn` for sync access.

### Race condition protection

The beat task uses `SELECT ... FOR UPDATE SKIP LOCKED` scoped to a short transaction. Notifications are fetched and their IDs passed to individual worker tasks. Each worker task re-checks `status == pending` at the start before doing anything (guard clause).

### Phone number format

Evolution API accepts numbers in international format without `+` (e.g., `5548999999999`). The `client.phone` field is expected to already be stored in this format.

### Template rendering safety

`str.format_map()` is used with a controlled dict — unknown placeholders in the template content will raise `KeyError`. The send task wraps rendering in a try/except and marks the notification as `failed` with a descriptive `last_error` if rendering fails.
