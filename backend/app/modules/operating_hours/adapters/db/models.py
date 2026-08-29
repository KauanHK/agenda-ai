import uuid
from datetime import time

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base


class OperatingHour(Base):
    __tablename__ = "operating_hours"

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

    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time(timezone=False), nullable=False)
    end_time: Mapped[time] = mapped_column(Time(timezone=False), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "weekday >= 0 AND weekday <= 6",
            name="ck_operating_hours_weekday_range",
        ),
        CheckConstraint(
            "start_time < end_time",
            name="ck_operating_hours_time_range",
        ),
        Index("idx_operating_hours_establishment", "establishment_id"),
    )
