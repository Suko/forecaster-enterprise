"""add location_id to ts_demand_daily

Revision ID: 1a2b3c4d5e6f
Revises: 95dfb658e5b7
Create Date: 2025-12-11
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1a2b3c4d5e6f'
down_revision = '95dfb658e5b7'
branch_labels = None
depends_on = None


def upgrade():
    # Check if column already exists
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns('ts_demand_daily')]
    
    if 'location_id' not in columns:
        # 1) Add location_id with a temporary default, then backfill and enforce NOT NULL
        op.add_column(
            'ts_demand_daily',
            sa.Column('location_id', sa.String(length=50), nullable=True, server_default='UNSPECIFIED')
        )
        op.execute(
            "UPDATE ts_demand_daily SET location_id = 'UNSPECIFIED' WHERE location_id IS NULL"
        )
        op.alter_column('ts_demand_daily', 'location_id', nullable=False, server_default=None)

    # 2) Drop existing primary key and recreate including location_id (if needed)
    pk_constraint = inspector.get_pk_constraint('ts_demand_daily')
    pk_columns = pk_constraint.get('constrained_columns', []) if pk_constraint else []
    
    # Check if primary key already includes location_id
    needs_pk_update = 'location_id' not in pk_columns
    
    if needs_pk_update:
        try:
            op.drop_constraint('ts_demand_daily_pkey', 'ts_demand_daily', type_='primary')
        except:
            pass  # Constraint might not exist
        op.create_primary_key(
            'ts_demand_daily_pkey',
            'ts_demand_daily',
            ['client_id', 'item_id', 'location_id', 'date_local']
        )

    # 3) Add composite index to match common query pattern with location (if needed)
    indexes = [idx['name'] for idx in inspector.get_indexes('ts_demand_daily')]
    if 'idx_ts_demand_daily_client_item_location_date' not in indexes:
        op.create_index(
            'idx_ts_demand_daily_client_item_location_date',
            'ts_demand_daily',
            ['client_id', 'item_id', 'location_id', 'date_local'],
            unique=False
        )


def downgrade():
    # Remove new index
    op.drop_index(
        'idx_ts_demand_daily_client_item_location_date',
        table_name='ts_demand_daily'
    )

    # Restore original primary key (client_id, item_id, date_local)
    op.drop_constraint('ts_demand_daily_pkey', 'ts_demand_daily', type_='primary')
    op.create_primary_key(
        'ts_demand_daily_pkey',
        'ts_demand_daily',
        ['client_id', 'item_id', 'date_local']
    )

    # Drop location_id column
    op.drop_column('ts_demand_daily', 'location_id')
