"""add order cart table

Revision ID: a89cac7ecb0b
Revises: 92b51207e018
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

Adds order_cart_items table for session-based shopping cart.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a89cac7ecb0b'
down_revision = '92b51207e018'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add order_cart_items table for order planning cart.
    """
    op.create_table(
        'order_cart_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=False),  # User ID or session ID
        sa.Column('item_id', sa.String(255), nullable=False),  # ⚠️ CRITICAL: matches forecasting engine
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_cost', sa.Numeric(10, 2), nullable=False),
        sa.Column('total_price', sa.Numeric(12, 2), nullable=False),
        sa.Column('packaging_unit', sa.String(50), nullable=True),
        sa.Column('packaging_qty', sa.Integer(), nullable=True),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['client_id'], ['clients.client_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('client_id', 'session_id', 'item_id', 'supplier_id', name='uq_cart_client_session_item_supplier'),
    )
    op.create_index('idx_cart_client_session', 'order_cart_items', ['client_id', 'session_id'])
    op.create_index('idx_cart_item', 'order_cart_items', ['item_id'])


def downgrade():
    op.drop_index('idx_cart_item', table_name='order_cart_items')
    op.drop_index('idx_cart_client_session', table_name='order_cart_items')
    op.drop_table('order_cart_items')
