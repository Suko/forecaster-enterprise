"""add supplier defaults for MOQ and lead time

Revision ID: f1a2b3c4d5e6
Revises: a89cac7ecb0b
Create Date: 2025-12-10 13:00:00.000000

Adds default_moq and default_lead_time_days columns to suppliers table.
These defaults are used when creating product-supplier relationships.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'a89cac7ecb0b'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add default_moq and default_lead_time_days to suppliers table.
    """
    op.add_column('suppliers', sa.Column('default_moq', sa.Integer(), default=0, nullable=False, server_default='0'))
    op.add_column('suppliers', sa.Column('default_lead_time_days', sa.Integer(), default=14, nullable=False, server_default='14'))

    # Index for performance
    op.create_index('idx_suppliers_defaults', 'suppliers', ['client_id', 'default_moq', 'default_lead_time_days'])


def downgrade():
    op.drop_index('idx_suppliers_defaults', table_name='suppliers')
    op.drop_column('suppliers', 'default_lead_time_days')
    op.drop_column('suppliers', 'default_moq')

