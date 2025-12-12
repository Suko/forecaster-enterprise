"""add product safety buffer override

Revision ID: g2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2025-12-10 13:00:00.000000

Adds safety_buffer_days column to products table.
Allows product-level override of client-wide safety buffer.
NULL means use client default.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'g2b3c4d5e6f7'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add safety_buffer_days to products table.
    NULL means use client default from client_settings.
    """
    op.add_column('products', sa.Column('safety_buffer_days', sa.Integer(), nullable=True))

    # Index for performance
    op.create_index('idx_products_buffer', 'products', ['client_id', 'safety_buffer_days'])


def downgrade():
    op.drop_index('idx_products_buffer', table_name='products')
    op.drop_column('products', 'safety_buffer_days')

