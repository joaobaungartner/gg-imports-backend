"""add order stock reservations

Revision ID: e91c4a7b2d10
Revises: d8b2c4e5f6a7
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e91c4a7b2d10"
down_revision: Union[str, Sequence[str], None] = "d8b2c4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column("estoque_reservado", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "orders", sa.Column("reserva_expira_em", sa.DateTime(), nullable=True)
    )
    op.create_index(
        "ix_orders_estoque_reservado", "orders", ["estoque_reservado"]
    )
    op.create_index(
        "ix_orders_reserva_expira_em", "orders", ["reserva_expira_em"]
    )


def downgrade() -> None:
    op.drop_index("ix_orders_reserva_expira_em", table_name="orders")
    op.drop_index("ix_orders_estoque_reservado", table_name="orders")
    op.drop_column("orders", "reserva_expira_em")
    op.drop_column("orders", "estoque_reservado")
