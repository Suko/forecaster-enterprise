"""add stock_on_date to ts_demand_daily

Revision ID: 92b51207e018
Revises: 95dfb658e5b7
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

Adds stock_on_date column to track historical stock levels and detect stockouts.
This allows us to see when stockouts occurred (stock_on_date = 0) vs. no demand (units_sold = 0 but stock > 0).
Stock can be synced from external systems (end of day) or manually updated at any time.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '92b51207e018'
down_revision = '95dfb658e5b7'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add stock_on_date column to ts_demand_daily table.

    This column tracks the stock level for each date, allowing us to:
    - Detect stockouts: stock_on_date = 0 AND units_sold = 0 (likely stockout)
    - Track historical inventory levels
    - Analyze stockout impact on sales

    Note: Stock can be:
    - Synced from external systems (typically end of day snapshots)
    - Manually updated by users at any time
    - This is optional (nullable) because:
      - Historical data may not have stock information
      - External systems may not provide daily stock snapshots
      - Can be populated going forward from stock_levels table
    """
    op.add_column(
        'ts_demand_daily',
        sa.Column('stock_on_date', sa.Integer(), nullable=True, comment='Stock level for this date (synced or manually updated, for stockout detection)')
    )

    # Add index for stockout queries (filtering by stock_on_date = 0)
    # Note: Partial index syntax varies by database - using standard index for compatibility
    op.create_index(
        'idx_ts_demand_daily_stock',
        'ts_demand_daily',
        ['client_id', 'item_id', 'stock_on_date'],
        unique=False
    )


def downgrade():
    # Drop index first
    op.drop_index('idx_ts_demand_daily_stock', table_name='ts_demand_daily')

    # Drop column
    op.drop_column('ts_demand_daily', 'stock_on_date')
