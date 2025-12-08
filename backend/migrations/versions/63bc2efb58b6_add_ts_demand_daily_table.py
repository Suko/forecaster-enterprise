"""add ts_demand_daily table

Revision ID: 63bc2efb58b6
Revises: 9c3d4e5f6a7b
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '63bc2efb58b6'
down_revision = '9c3d4e5f6a7b'
branch_labels = None
depends_on = None


def upgrade():
    # Create ts_demand_daily table (simplified MVP version)
    # Full schema will be added in Phase 2
    op.create_table(
        'ts_demand_daily',
        sa.Column('item_id', sa.String(255), nullable=False),
        sa.Column('date_local', sa.Date(), nullable=False),
        sa.Column('units_sold', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('promotion_flag', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('holiday_flag', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('is_weekend', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('marketing_spend', sa.Numeric(18, 2), nullable=True, server_default='0'),
        sa.PrimaryKeyConstraint('item_id', 'date_local', 'client_id'),
        sa.ForeignKeyConstraint(['client_id'], ['clients.client_id'], ondelete='CASCADE'),
    )
    
    # Create indexes for common queries
    op.create_index('idx_ts_demand_daily_client_item', 'ts_demand_daily', ['client_id', 'item_id'])
    op.create_index('idx_ts_demand_daily_date', 'ts_demand_daily', ['date_local'])
    op.create_index('idx_ts_demand_daily_client_date', 'ts_demand_daily', ['client_id', 'date_local'])


def downgrade():
    op.drop_index('idx_ts_demand_daily_client_date', table_name='ts_demand_daily')
    op.drop_index('idx_ts_demand_daily_date', table_name='ts_demand_daily')
    op.drop_index('idx_ts_demand_daily_client_item', table_name='ts_demand_daily')
    op.drop_table('ts_demand_daily')
