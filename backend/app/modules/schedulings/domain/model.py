import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.modules.schedulings.domain.enums import (
    CancelledByType,
    ChangedBySource,
    SchedulingSource,
    SchedulingStatus,
)

if TYPE_CHECKING:
    from app.modules.clients.domain.model import Client
    from app.modules.services.domain.model import Service
    from app.modules.users.adapters.db.models import User


class Scheduling(Base):
    __tablename__ = "schedulings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid7,
    )

    establishment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("establishments.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )

    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )

    status: Mapped[SchedulingStatus] = mapped_column(
        Enum(SchedulingStatus, name="schedulingstatus"),
        nullable=False,
        default=SchedulingStatus.PENDING,
    )

    source: Mapped[SchedulingSource] = mapped_column(
        Enum(SchedulingSource, name="schedulingsource"),
        nullable=False,
    )

    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    cancelled_by_type: Mapped[CancelledByType | None] = mapped_column(
        Enum(CancelledByType, name="cancelledbytype"),
        nullable=True,
    )

    cancelled_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships for expanded read — loaded only when explicitly requested via selectinload
    user: Mapped[User] = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="noload",
    )
    client: Mapped[Client] = relationship(
        "Client",
        foreign_keys=[client_id],
        lazy="noload",
    )
    service: Mapped[Service] = relationship(
        "Service",
        foreign_keys=[service_id],
        lazy="noload",
    )

    __table_args__ = (
        Index("idx_schedulings_establishment", "establishment_id"),
        Index("idx_schedulings_user_id", "user_id"),
        Index("idx_schedulings_client_id", "client_id"),
        Index("idx_schedulings_status", "status"),
        Index("idx_schedulings_starts_at", "starts_at"),
    )


class SchedulingStatusLog(Base):
    __tablename__ = "scheduling_status_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid7,
    )

    scheduling_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schedulings.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )

    from_status: Mapped[SchedulingStatus | None] = mapped_column(
        Enum(SchedulingStatus, name="schedulingstatus"),
        nullable=True,
    )

    to_status: Mapped[SchedulingStatus] = mapped_column(
        Enum(SchedulingStatus, name="schedulingstatus"),
        nullable=False,
    )

    changed_by_source: Mapped[ChangedBySource] = mapped_column(
        Enum(ChangedBySource, name="changedbysource"),
        nullable=False,
    )

    changed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_scheduling_status_logs_scheduling_id", "scheduling_id"),
    )
