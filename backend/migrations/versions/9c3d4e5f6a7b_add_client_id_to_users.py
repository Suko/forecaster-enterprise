"""add client_id to users

Revision ID: 9c3d4e5f6a7b
Revises: 9b2f3c4d5e6a
Create Date: 2025-12-06 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9c3d4e5f6a7b'
down_revision = '9b2f3c4d5e6a'
branch_labels = None
depends_on = None


def upgrade():
    # Add client_id column to users table
    # Note: For existing users, this will be nullable initially
    # You'll need to backfill client_id for existing users
    op.add_column('users', sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Create index for client_id
    op.create_index('idx_users_client_id', 'users', ['client_id'])

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_users_client_id',
        'users', 'clients',
        ['client_id'], ['client_id'],
        ondelete='RESTRICT'
    )

    # Note: For production, you should backfill client_id for existing users
    # before making it NOT NULL. For now, we keep it nullable for migration safety.


def downgrade():
    op.drop_constraint('fk_users_client_id', 'users', type_='foreignkey')
    op.drop_index('idx_users_client_id', table_name='users')
    op.drop_column('users', 'client_id')

