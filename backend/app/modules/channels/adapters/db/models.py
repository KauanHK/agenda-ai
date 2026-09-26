import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base


class TelegramBot(Base):
    __tablename__ = "telegram_bots"

    # PK no estabelecimento: no máximo um bot por estabelecimento.
    establishment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("establishments.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )

    # Id numérico do `getMe`. Único: um bot pertence a no máximo um estabelecimento,
    # senão o segundo `setWebhook` tomaria o bot do primeiro sem aviso.
    bot_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    bot_username: Mapped[str] = mapped_column(String(64), nullable=False)

    # Cifrados com `app.core.security.secret_box`.
    bot_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    webhook_secret_encrypted: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
