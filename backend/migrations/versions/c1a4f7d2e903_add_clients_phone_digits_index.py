"""add clients phone digits index

Índice funcional sobre os dígitos do telefone. A identificação do cliente no canal
automático compara `regexp_replace(phone, '\\D', '', 'g')`, porque a coluna guarda o
número no formato em que foi digitado — sem o índice, cada mensagem recebida faria um
seq scan em `clients`.

Revision ID: c1a4f7d2e903
Revises: b0021778e045
Create Date: 2026-08-29

"""

from collections.abc import Sequence

from alembic import op

revision: str = "c1a4f7d2e903"
down_revision: str | Sequence[str] | None = "b0021778e045"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INDEX_NAME = "idx_clients_establishment_phone_digits"


def upgrade() -> None:
    op.execute(
        f"""
        CREATE INDEX {INDEX_NAME}
        ON clients (establishment_id, regexp_replace(phone, '\\D', '', 'g'))
        """
    )


def downgrade() -> None:
    op.execute(f"DROP INDEX IF EXISTS {INDEX_NAME}")
