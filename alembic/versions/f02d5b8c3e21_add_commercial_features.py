"""add commercial features

Revision ID: f02d5b8c3e21
Revises: e91c4a7b2d10
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "f02d5b8c3e21"
down_revision: Union[str, Sequence[str], None] = "e91c4a7b2d10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email_verificado", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("orders", sa.Column("codigo_rastreio", sa.String(100), nullable=True))
    op.add_column("orders", sa.Column("url_rastreio", sa.String(500), nullable=True))
    for name, length in (("temporada", 50), ("versao", 50), ("genero", 30), ("fornecedor", 120)):
        op.add_column("products", sa.Column(name, sa.String(length), nullable=True))
        op.create_index(f"ix_products_{name}", "products", [name])
    op.add_column("products", sa.Column("sku", sa.String(100), nullable=True))
    op.create_index("ix_products_sku", "products", ["sku"], unique=True)
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("event", sa.String(50), nullable=False),
        sa.Column("recipient", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(255), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
    )
    for name in ("channel", "event", "status"):
        op.create_index(f"ix_notifications_{name}", "notifications", [name])
    op.create_table(
        "post_sale_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("request_type", sa.String(20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="REQUESTED"),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    for name in ("order_id", "client_id", "request_type", "status"):
        op.create_index(f"ix_post_sale_requests_{name}", "post_sale_requests", [name])


def downgrade() -> None:
    op.drop_table("post_sale_requests")
    op.drop_table("notifications")
    op.drop_index("ix_products_sku", table_name="products")
    op.drop_column("products", "sku")
    for name in ("fornecedor", "genero", "versao", "temporada"):
        op.drop_index(f"ix_products_{name}", table_name="products")
        op.drop_column("products", name)
    op.drop_column("orders", "url_rastreio")
    op.drop_column("orders", "codigo_rastreio")
    op.drop_column("users", "email_verificado")
