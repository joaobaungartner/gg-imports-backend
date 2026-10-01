"""Separate deleted products from temporarily inactive products."""
from alembic import op
import sqlalchemy as sa

revision = "c82d6a9e410f"
down_revision = "b4e8f1c2d903"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("products", sa.Column("excluido", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    op.drop_column("products", "excluido")
