"""add clients table

Revision ID: 9b2f3c4d5e6a
Revises: 8a8ce391936a
Create Date: 2025-12-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9b2f3c4d5e6a'
down_revision = '8a8ce391936a'
branch_labels = None
depends_on = None


def upgrade():
    # Create clients table
    op.create_table(
        'clients',
        sa.Column('client_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('timezone', sa.String(50), nullable=False, server_default='UTC'),
        sa.Column('currency', sa.String(3), nullable=False, server_default='EUR'),
        sa.Column('settings', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create indexes
    op.create_index('idx_clients_name', 'clients', ['name'])
    op.create_index('idx_clients_active', 'clients', ['is_active'], postgresql_where=sa.text('is_active = true'))


def downgrade():
    op.drop_index('idx_clients_active', table_name='clients')
    op.drop_index('idx_clients_name', table_name='clients')
    op.drop_table('clients')

