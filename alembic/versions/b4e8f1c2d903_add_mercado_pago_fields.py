"""add Mercado Pago payment fields

Revision ID: b4e8f1c2d903
Revises: a13e6c9d4f32
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b4e8f1c2d903"
down_revision: Union[str, Sequence[str], None] = "a13e6c9d4f32"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("payments", sa.Column("gateway", sa.String(30), nullable=True))
    op.add_column("payments", sa.Column("idempotency_key", sa.String(64), nullable=True))
    op.add_column("payments", sa.Column("gateway_status", sa.String(40), nullable=True))
    op.add_column("payments", sa.Column("status_detail", sa.String(100), nullable=True))
    op.add_column("payments", sa.Column("payment_method_id", sa.String(50), nullable=True))
    op.add_column("payments", sa.Column("installments", sa.Integer(), nullable=True))
    op.add_column("payments", sa.Column("pix_qr_code", sa.Text(), nullable=True))
    op.add_column("payments", sa.Column("pix_qr_code_base64", sa.Text(), nullable=True))
    op.add_column("payments", sa.Column("pix_ticket_url", sa.String(1000), nullable=True))
    op.add_column("payments", sa.Column("expires_at", sa.DateTime(), nullable=True))
    op.add_column("payments", sa.Column("refunded_amount", sa.Numeric(10, 2), nullable=False, server_default="0"))
    op.add_column("payments", sa.Column("last_reconciled_at", sa.DateTime(), nullable=True))
    op.create_index("ix_payments_idempotency_key", "payments", ["idempotency_key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_payments_idempotency_key", table_name="payments")
    for column in ("last_reconciled_at", "refunded_amount", "expires_at", "pix_ticket_url", "pix_qr_code_base64", "pix_qr_code", "installments", "payment_method_id", "status_detail", "gateway_status", "idempotency_key", "gateway"):
        op.drop_column("payments", column)
