"""add_checkout_fields_to_orders

Revision ID: b3f8a2c91d04
Revises: 8ea458253ada
Create Date: 2026-07-04 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b3f8a2c91d04"
down_revision: Union[str, Sequence[str], None] = "8ea458253ada"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("orders", "client_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("orders", "endereco_id", existing_type=sa.Integer(), nullable=True)

    op.add_column("orders", sa.Column("customer_name", sa.String(length=255), nullable=True))
    op.add_column("orders", sa.Column("customer_email", sa.String(length=255), nullable=True))
    op.add_column("orders", sa.Column("customer_phone", sa.String(length=20), nullable=True))
    op.add_column("orders", sa.Column("customer_cpf", sa.String(length=11), nullable=True))
    op.add_column("orders", sa.Column("shipping_cep", sa.String(length=8), nullable=True))
    op.add_column("orders", sa.Column("shipping_street", sa.String(length=255), nullable=True))
    op.add_column("orders", sa.Column("shipping_number", sa.String(length=20), nullable=True))
    op.add_column("orders", sa.Column("shipping_complement", sa.String(length=255), nullable=True))
    op.add_column("orders", sa.Column("shipping_neighborhood", sa.String(length=100), nullable=True))
    op.add_column("orders", sa.Column("shipping_city", sa.String(length=100), nullable=True))
    op.add_column("orders", sa.Column("shipping_state", sa.String(length=2), nullable=True))
    op.add_column("orders", sa.Column("shipping_method", sa.String(length=50), nullable=True))
    op.add_column("orders", sa.Column("payment_method", sa.String(length=20), nullable=True))
    op.add_column(
        "orders",
        sa.Column("subtotal", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0"),
    )
    op.add_column(
        "orders",
        sa.Column("frete", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0"),
    )

    op.add_column("order_items", sa.Column("nome_produto", sa.String(length=255), nullable=True))
    op.add_column("order_items", sa.Column("imagem_url", sa.String(length=500), nullable=True))
    op.add_column("order_items", sa.Column("tamanho", sa.String(length=20), nullable=True))

    op.execute(
        """
        UPDATE orders SET status = 'PENDING_PAYMENT' WHERE status = 'PENDING';
        UPDATE orders SET status = 'PREPARING' WHERE status = 'PROCESSING';
        UPDATE orders SET status = 'PENDING_PAYMENT' WHERE status = 'CONFIRMED';
        """
    )


def downgrade() -> None:
    op.drop_column("order_items", "tamanho")
    op.drop_column("order_items", "imagem_url")
    op.drop_column("order_items", "nome_produto")

    op.drop_column("orders", "frete")
    op.drop_column("orders", "subtotal")
    op.drop_column("orders", "payment_method")
    op.drop_column("orders", "shipping_method")
    op.drop_column("orders", "shipping_state")
    op.drop_column("orders", "shipping_city")
    op.drop_column("orders", "shipping_neighborhood")
    op.drop_column("orders", "shipping_complement")
    op.drop_column("orders", "shipping_number")
    op.drop_column("orders", "shipping_street")
    op.drop_column("orders", "shipping_cep")
    op.drop_column("orders", "customer_cpf")
    op.drop_column("orders", "customer_phone")
    op.drop_column("orders", "customer_email")
    op.drop_column("orders", "customer_name")

    op.alter_column("orders", "endereco_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column("orders", "client_id", existing_type=sa.Integer(), nullable=False)
