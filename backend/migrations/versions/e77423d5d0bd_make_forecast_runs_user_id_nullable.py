"""make_forecast_runs_user_id_nullable

Revision ID: e77423d5d0bd
Revises: 881cd10fab75
Create Date: 2025-12-17 14:46:23.643119

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'e77423d5d0bd'
down_revision: Union[str, None] = '881cd10fab75'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make user_id nullable to allow system-generated forecasts
    # Find the actual foreign key constraint name
    conn = op.get_bind()
    inspector = inspect(conn)
    fk_constraints = inspector.get_foreign_keys('forecast_runs')
    fk_name = None
    for fk in fk_constraints:
        if 'user_id' in fk['constrained_columns']:
            fk_name = fk['name']
            break
    
    # Drop the foreign key constraint if it exists
    if fk_name:
        op.drop_constraint(fk_name, 'forecast_runs', type_='foreignkey')
    
    # Then make the column nullable
    op.alter_column('forecast_runs', 'user_id', nullable=True)
    
    # Recreate the foreign key constraint (allows NULLs)
    op.create_foreign_key(
        'forecast_runs_user_id_fkey',
        'forecast_runs', 'users',
        ['user_id'], ['id']
    )


def downgrade() -> None:
    # Revert to non-nullable (requires data cleanup first)
    # Drop the foreign key constraint
    op.drop_constraint('forecast_runs_user_id_fkey', 'forecast_runs', type_='foreignkey')
    # Make the column non-nullable (will fail if NULL values exist)
    op.alter_column('forecast_runs', 'user_id', nullable=False)
    # Recreate the foreign key constraint
    op.create_foreign_key(
        'forecast_runs_user_id_fkey',
        'forecast_runs', 'users',
        ['user_id'], ['id']
    )

