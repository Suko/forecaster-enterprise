"""optimize ts_demand_daily for forecasting

Revision ID: 95dfb658e5b7
Revises: 269603316338
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

Optimizes ts_demand_daily table indexes for forecasting engine query performance.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '95dfb658e5b7'
down_revision = '269603316338'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add composite index optimized for forecasting engine queries.

    Query pattern: WHERE client_id = X AND item_id IN (...) AND date_local BETWEEN ... ORDER BY item_id, date_local
    """
    # Create composite index for common forecasting query pattern
    # This index optimizes: WHERE client_id = X AND item_id IN (...) AND date_local BETWEEN ...
    op.create_index(
        'idx_ts_demand_daily_client_item_date',
        'ts_demand_daily',
        ['client_id', 'item_id', 'date_local'],
        unique=False
    )

    # Note: Existing indexes are kept:
    # - idx_ts_demand_daily_client_item (may be redundant but kept for backward compatibility)
    # - idx_ts_demand_daily_date (useful for date-only queries)
    # - idx_ts_demand_daily_client_date (may be redundant but kept for backward compatibility)


def downgrade():
    # Drop the composite index
    op.drop_index('idx_ts_demand_daily_client_item_date', table_name='ts_demand_daily')
