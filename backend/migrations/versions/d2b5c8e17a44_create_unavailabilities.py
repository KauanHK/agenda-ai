"""create unavailabilities

A tabela nunca chegou a ser criada: o model `Unavailability` não estava importado em
`app/db/models.py`, então ficou de fora do metadata quando a revisão inicial foi
gerada — e os endpoints `/establishments/{id}/unavailabilities` falhavam com
`UndefinedTableError`. O import foi corrigido junto com esta revisão.

Revision ID: d2b5c8e17a44
Revises: c1a4f7d2e903
Create Date: 2026-08-29

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d2b5c8e17a44"
down_revision: str | Sequence[str] | None = "c1a4f7d2e903"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "unavailabilities",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("establishment_id", sa.UUID(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=True),
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
        sa.CheckConstraint(
            "ends_at > starts_at", name="ck_unavailabilities_ends_after_starts"
        ),
        sa.ForeignKeyConstraint(
            ["establishment_id"],
            ["establishments.id"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_unavailabilities_establishment_id",
        "unavailabilities",
        ["establishment_id"],
        unique=False,
    )
    op.create_index(
        "idx_unavailabilities_starts_at_ends_at",
        "unavailabilities",
        ["starts_at", "ends_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "idx_unavailabilities_starts_at_ends_at", table_name="unavailabilities"
    )
    op.drop_index(
        "idx_unavailabilities_establishment_id", table_name="unavailabilities"
    )
    op.drop_table("unavailabilities")
