"""add_audit_metadata_to_forecast_runs

Revision ID: 38c1879adfce
Revises: 63bc2efb58b6
Create Date: 2025-12-08 16:40:21.777368

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '38c1879adfce'
down_revision: Union[str, None] = '63bc2efb58b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add audit_metadata column to forecast_runs table
    # Stores data flow audit trail: IN -> Model -> OUT -> Comparison
    op.add_column(
        'forecast_runs',
        sa.Column('audit_metadata', postgresql.JSONB(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('forecast_runs', 'audit_metadata')

