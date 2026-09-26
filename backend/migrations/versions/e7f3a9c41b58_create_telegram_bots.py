"""create telegram_bots

Bot do Telegram de cada estabelecimento. O token e o segredo do webhook ficam cifrados
com a `CHANNEL_SECRETS_KEY` (ver `app.core.security.secret_box`).

Revision ID: e7f3a9c41b58
Revises: d2b5c8e17a44
Create Date: 2026-09-26

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e7f3a9c41b58"
down_revision: str | Sequence[str] | None = "d2b5c8e17a44"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "telegram_bots",
        sa.Column("establishment_id", sa.UUID(), nullable=False),
        sa.Column("bot_id", sa.BigInteger(), nullable=False),
        sa.Column("bot_username", sa.String(length=64), nullable=False),
        sa.Column("bot_token_encrypted", sa.Text(), nullable=False),
        sa.Column("webhook_secret_encrypted", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["establishment_id"],
            ["establishments.id"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("establishment_id"),
        sa.UniqueConstraint("bot_id"),
    )


def downgrade() -> None:
    op.drop_table("telegram_bots")
