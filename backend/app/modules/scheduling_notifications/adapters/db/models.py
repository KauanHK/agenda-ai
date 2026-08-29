import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base
from app.modules.scheduling_notifications.domain.enums import NotificationStatus


class SchedulingNotification(Base):
    __tablename__ = "scheduling_notifications"

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

    scheduling_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schedulings.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )

    template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messaging_templates.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )

    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, name="notificationstatus"),
        nullable=False,
        default=NotificationStatus.pending,
    )

    content_at_send: Mapped[str | None] = mapped_column(Text, nullable=True)

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    last_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

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

    __table_args__ = (
        Index("idx_scheduling_notifications_establishment", "establishment_id"),
        Index("idx_scheduling_notifications_scheduling", "scheduling_id"),
        Index("idx_scheduling_notifications_status", "status"),
        Index("idx_scheduling_notifications_scheduled_at", "scheduled_at"),
    )
