"""make_forecast_runs_user_id_nullable

Revision ID: e77423d5d0bd
Revises: 881cd10fab75
Create Date: 2025-12-17 14:46:23.643119

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e77423d5d0bd'
down_revision: Union[str, None] = '881cd10fab75'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make user_id nullable to allow system-generated forecasts
    op.alter_column('forecast_runs', 'user_id', nullable=True)


def downgrade() -> None:
    # Revert to non-nullable (requires data cleanup first)
    op.alter_column('forecast_runs', 'user_id', nullable=False)

