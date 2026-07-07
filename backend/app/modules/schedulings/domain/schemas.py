from datetime import datetime

from pydantic import UUID7

from app.modules.clients.domain.schemas import ClientRead
from app.modules.common.domain.schemas import (
    BaseSchema,
    EstablishmentScoped,
    TimestampMixin,
)
from app.modules.schedulings.domain.enums import (
    CancelledByType,
    ChangedBySource,
    SchedulingSource,
    SchedulingStatus,
)
from app.modules.services.domain.schemas import ServiceRead
from app.modules.users.domain.schemas import UserRead


class UserRef(BaseSchema):
    id: UUID7
    name: str


class ClientRef(BaseSchema):
    id: UUID7
    name: str
    phone: str


class ServiceRef(BaseSchema):
    id: UUID7
    name: str
    duration_minutes: int


class SchedulingRead(BaseSchema, EstablishmentScoped, TimestampMixin):
    id: UUID7
    status: SchedulingStatus
    source: SchedulingSource
    starts_at: datetime
    ends_at: datetime
    cancelled_by_type: CancelledByType | None = None
    cancelled_by_user_id: UUID7 | None = None

    client: ClientRef
    service: ServiceRef
    user: UserRef


class SchedulingExpandedRead(BaseSchema, EstablishmentScoped, TimestampMixin):
    id: UUID7
    status: SchedulingStatus
    source: SchedulingSource
    starts_at: datetime
    ends_at: datetime
    cancelled_by_type: CancelledByType | None = None
    cancelled_by_user_id: UUID7 | None = None

    client: ClientRead
    service: ServiceRead
    user: UserRead


class SchedulingCreate(BaseSchema):
    user_id: UUID7
    client_id: UUID7
    service_id: UUID7
    starts_at: datetime


class CancelSchedulingRequest(BaseSchema):
    cancelled_by_type: CancelledByType
    cancelled_by_user_id: UUID7 | None = None


class RescheduleRequest(BaseSchema):
    starts_at: datetime


class SchedulingStatusLogRead(BaseSchema):
    id: UUID7
    scheduling_id: UUID7
    from_status: SchedulingStatus | None = None
    to_status: SchedulingStatus
    changed_by_source: ChangedBySource
    changed_by_user_id: UUID7 | None = None
    note: str | None = None
    changed_at: datetime
