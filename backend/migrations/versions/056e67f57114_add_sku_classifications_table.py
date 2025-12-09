"""add_sku_classifications_table

Revision ID: 056e67f57114
Revises: 38c1879adfce
Create Date: 2025-12-08 21:11:24.963111

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '056e67f57114'
down_revision: Union[str, None] = '38c1879adfce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create sku_classifications table
    op.create_table(
        'sku_classifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_id', sa.String(255), nullable=False),
        
        # ABC-XYZ Classification
        sa.Column('abc_class', sa.String(1), nullable=False),
        sa.Column('xyz_class', sa.String(1), nullable=False),
        
        # Demand Pattern
        sa.Column('demand_pattern', sa.String(50), nullable=False),
        
        # Metrics
        sa.Column('coefficient_of_variation', sa.Numeric(10, 4), nullable=False),
        sa.Column('average_demand_interval', sa.Numeric(10, 4), nullable=False),
        sa.Column('revenue_contribution', sa.Numeric(10, 4)),
        
        # Forecasting
        sa.Column('forecastability_score', sa.Numeric(5, 4), nullable=False),
        sa.Column('recommended_method', sa.String(50), nullable=False),
        sa.Column('expected_mape_min', sa.Numeric(5, 2)),
        sa.Column('expected_mape_max', sa.Numeric(5, 2)),
        
        # Metadata
        sa.Column('classification_date', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('history_days_used', sa.Integer()),
        sa.Column('classification_metadata', postgresql.JSONB(), nullable=True),
    )
    
    # Create indexes
    op.create_index('idx_sku_classifications_client_id', 'sku_classifications', ['client_id'])
    op.create_index('idx_sku_classifications_item_id', 'sku_classifications', ['item_id'])
    
    # Create unique constraint on (client_id, item_id)
    op.create_unique_constraint(
        'uq_sku_classifications_client_item',
        'sku_classifications',
        ['client_id', 'item_id']
    )


def downgrade() -> None:
    op.drop_table('sku_classifications')

