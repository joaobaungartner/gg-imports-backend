"""add_order_admin_fields_and_status_history

Revision ID: c7a91e4f2b8d
Revises: b3f8a2c91d04
Create Date: 2026-07-14 02:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c7a91e4f2b8d"
down_revision: Union[str, Sequence[str], None] = "b3f8a2c91d04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("orders", sa.Column("admin_notes", sa.String(length=2000), nullable=True))
    op.alter_column(
        "orders",
        "status",
        existing_type=sa.String(length=20),
        type_=sa.String(length=30),
        existing_nullable=False,
    )

    op.create_table(
        "order_status_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("previous_status", sa.String(length=30), nullable=True),
        sa.Column("new_status", sa.String(length=30), nullable=False),
        sa.Column("changed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["changed_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_order_status_history_id"),
        "order_status_history",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_order_status_history_order_id"),
        "order_status_history",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_order_status_history_changed_by_user_id"),
        "order_status_history",
        ["changed_by_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_order_status_history_changed_by_user_id"),
        table_name="order_status_history",
    )
    op.drop_index(
        op.f("ix_order_status_history_order_id"),
        table_name="order_status_history",
    )
    op.drop_index(op.f("ix_order_status_history_id"), table_name="order_status_history")
    op.drop_table("order_status_history")

    op.alter_column(
        "orders",
        "status",
        existing_type=sa.String(length=30),
        type_=sa.String(length=20),
        existing_nullable=False,
    )
    op.drop_column("orders", "admin_notes")
    op.drop_column("orders", "updated_at")
