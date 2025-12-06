"""add_forecast_tables

Revision ID: 8a8ce391936a
Revises: 84f50d6e2ed1
Create Date: 2025-12-06 11:13:26.814399

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '8a8ce391936a'
down_revision: Union[str, None] = '84f50d6e2ed1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create forecast_runs table
    op.create_table(
        'forecast_runs',
        sa.Column('forecast_run_id', sa.String(), primary_key=True),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('primary_model', sa.String(50), nullable=False, server_default='chronos-2'),
        sa.Column('prediction_length', sa.Integer(), nullable=False),
        sa.Column('item_ids', postgresql.JSONB),
        sa.Column('recommended_method', sa.String(50)),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )
    op.create_index('idx_forecast_runs_client', 'forecast_runs', ['client_id'])
    op.create_index('idx_forecast_runs_status', 'forecast_runs', ['status'])
    op.create_index('idx_forecast_runs_created', 'forecast_runs', ['created_at'])
    
    # Create forecast_results table
    op.create_table(
        'forecast_results',
        sa.Column('result_id', sa.String(), primary_key=True),
        sa.Column('forecast_run_id', sa.String(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('item_id', sa.String(255), nullable=False),
        sa.Column('method', sa.String(50), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('horizon_day', sa.Integer(), nullable=False),
        sa.Column('point_forecast', sa.Numeric(18, 2), nullable=False),
        sa.Column('p10', sa.Numeric(18, 2)),
        sa.Column('p50', sa.Numeric(18, 2)),
        sa.Column('p90', sa.Numeric(18, 2)),
        sa.Column('actual_value', sa.Numeric(18, 2)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['forecast_run_id'], ['forecast_runs.forecast_run_id']),
        sa.UniqueConstraint('forecast_run_id', 'item_id', 'method', 'date', name='uq_forecast_result'),
    )
    op.create_index('idx_forecast_results_run_item', 'forecast_results', ['forecast_run_id', 'item_id'])
    op.create_index('idx_forecast_results_item_method_date', 'forecast_results', ['item_id', 'method', 'date'])
    op.create_index('idx_forecast_results_method', 'forecast_results', ['method'])


def downgrade() -> None:
    op.drop_table('forecast_results')
    op.drop_table('forecast_runs')
