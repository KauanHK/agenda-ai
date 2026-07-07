import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.modules.common.domain.enums import DocumentType


class Establishment(Base):
    __tablename__ = "establishments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid7,
    )

    name: Mapped[str] = mapped_column(
        String(255),
    )

    document: Mapped[str] = mapped_column(String(18), unique=True)

    document_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType))

    timezone: Mapped[str] = mapped_column(
        String(50),
    )

    street: Mapped[str] = mapped_column(
        String(255),
    )

    number: Mapped[str] = mapped_column(
        String(20),
    )

    complement: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
    )

    neighborhood: Mapped[str] = mapped_column(
        String(255),
    )

    city: Mapped[str] = mapped_column(
        String(255),
    )

    state: Mapped[str] = mapped_column(
        String(255),
    )

    zip_code: Mapped[str] = mapped_column(
        String(20),
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
    )

    deleted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    memberships = relationship("Membership", back_populates="establishment")
