"""add admin operations

Revision ID: a13e6c9d4f32
Revises: f02d5b8c3e21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a13e6c9d4f32"
down_revision: Union[str, Sequence[str], None] = "f02d5b8c3e21"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stock_movements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("movement_type", sa.String(30), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("previous_stock", sa.Integer(), nullable=False),
        sa.Column("new_stock", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(500), nullable=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=True),
        sa.Column("changed_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    for name in ("product_id", "movement_type", "order_id", "changed_by_user_id", "created_at"):
        op.create_index(f"ix_stock_movements_{name}", "stock_movements", [name])
    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("admin_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(80), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    for name in ("admin_user_id", "action", "resource_type", "created_at"):
        op.create_index(f"ix_admin_audit_logs_{name}", "admin_audit_logs", [name])


def downgrade() -> None:
    op.drop_table("admin_audit_logs")
    op.drop_table("stock_movements")
