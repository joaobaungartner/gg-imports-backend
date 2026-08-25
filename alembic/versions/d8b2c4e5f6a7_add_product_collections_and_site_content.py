"""add_product_collections_and_site_content

Revision ID: d8b2c4e5f6a7
Revises: c7a91e4f2b8d
Create Date: 2026-07-16 16:10:00.000000

"""
from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d8b2c4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "c7a91e4f2b8d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

HOW_TO_BUY_DEFAULT = {
    "title": "Como comprar",
    "subtitle": "Do clique ao envio: um processo direto, com suporte quando você precisar.",
    "eyebrow": "Passo a passo",
    "steps": [
        {
            "title": "Escolha sua camisa",
            "description": (
                "Navegue pelo catálogo, filtre por categoria e escolha o modelo, "
                "o tipo e o tamanho certos."
            ),
        },
        {
            "title": "Confira medidas",
            "description": (
                "Use a tabela de medidas e compare com uma peça do seu guarda-roupa. "
                "Em dúvida, fale conosco."
            ),
        },
        {
            "title": "Finalize o pedido",
            "description": (
                "Revise o carrinho, informe entrega ou retirada e confirme o pagamento "
                "(incluindo Pix quando aplicável)."
            ),
        },
        {
            "title": "Acompanhe e receba",
            "description": (
                "Guarde o número do pedido. Acompanhe o status na conta ou pela "
                "página de rastreamento."
            ),
        },
    ],
}


def upgrade() -> None:
    op.create_table(
        "product_collections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(
        op.f("ix_product_collections_id"),
        "product_collections",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_product_collections_slug"),
        "product_collections",
        ["slug"],
        unique=True,
    )

    op.create_table(
        "product_collection_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("collection_id", sa.Integer(), nullable=False),
        sa.Column("group_key", sa.String(length=512), nullable=False),
        sa.ForeignKeyConstraint(
            ["collection_id"],
            ["product_collections.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "collection_id",
            "group_key",
            name="uq_collection_group_key",
        ),
    )
    op.create_index(
        op.f("ix_product_collection_items_id"),
        "product_collection_items",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_product_collection_items_collection_id"),
        "product_collection_items",
        ["collection_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_product_collection_items_group_key"),
        "product_collection_items",
        ["group_key"],
        unique=False,
    )

    op.create_table(
        "site_contents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=50), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index(op.f("ix_site_contents_id"), "site_contents", ["id"], unique=False)
    op.create_index(op.f("ix_site_contents_key"), "site_contents", ["key"], unique=True)

    collections = sa.table(
        "product_collections",
        sa.column("slug", sa.String),
        sa.column("name", sa.String),
    )
    op.bulk_insert(
        collections,
        [
            {"slug": "promotions", "name": "Promoções"},
            {"slug": "launches", "name": "Lançamentos"},
        ],
    )

    site_contents = sa.table(
        "site_contents",
        sa.column("key", sa.String),
        sa.column("payload", postgresql.JSONB),
        sa.column("updated_at", sa.DateTime),
    )
    op.bulk_insert(
        site_contents,
        [
            {
                "key": "how_to_buy",
                "payload": HOW_TO_BUY_DEFAULT,
                "updated_at": datetime.utcnow(),
            }
        ],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_site_contents_key"), table_name="site_contents")
    op.drop_index(op.f("ix_site_contents_id"), table_name="site_contents")
    op.drop_table("site_contents")

    op.drop_index(
        op.f("ix_product_collection_items_group_key"),
        table_name="product_collection_items",
    )
    op.drop_index(
        op.f("ix_product_collection_items_collection_id"),
        table_name="product_collection_items",
    )
    op.drop_index(
        op.f("ix_product_collection_items_id"),
        table_name="product_collection_items",
    )
    op.drop_table("product_collection_items")

    op.drop_index(op.f("ix_product_collections_slug"), table_name="product_collections")
    op.drop_index(op.f("ix_product_collections_id"), table_name="product_collections")
    op.drop_table("product_collections")
