"""add_user_preferences

Revision ID: c9152349e312
Revises: e712f3443d94
Create Date: 2025-12-12 15:47:17.514080

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c9152349e312'
down_revision: Union[str, None] = 'e712f3443d94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add preferences column to users table (JSONB for PostgreSQL)
    op.add_column('users', sa.Column('preferences', postgresql.JSONB(), nullable=True, server_default='{}'))
    
    # Create GIN index for JSONB in PostgreSQL (for faster JSON queries)
    op.create_index('idx_users_preferences', 'users', ['preferences'], postgresql_using='gin')


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_users_preferences', table_name='users', postgresql_using='gin')
    
    # Drop preferences column
    op.drop_column('users', 'preferences')

