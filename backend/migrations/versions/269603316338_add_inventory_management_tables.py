"""add inventory management tables

Revision ID: 269603316338
Revises: 056e67f57114
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '269603316338'
down_revision = '056e67f57114'
branch_labels = None
depends_on = None


def upgrade():
    # ============================================================================
    # PRODUCTS TABLE
    # ============================================================================
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_id', sa.String(255), nullable=False),  # ⚠️ CRITICAL: matches forecasting engine
        sa.Column('sku', sa.String(255), nullable=True),  # Optional alias
        sa.Column('product_name', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100), default='Uncategorized', nullable=False),
        sa.Column('unit_cost', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['client_id'], ['clients.client_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('client_id', 'item_id', name='uq_products_client_item'),
    )
    op.create_index('idx_products_client_item', 'products', ['client_id', 'item_id'])
    op.create_index('idx_products_client', 'products', ['client_id'])

    # ============================================================================
    # LOCATIONS TABLE
    # ============================================================================
    op.create_table(
        'locations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location_id', sa.String(50), nullable=False),  # External ID
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('country', sa.String(100), nullable=True),
        sa.Column('is_synced', sa.Boolean(), default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['client_id'], ['clients.client_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('client_id', 'location_id', name='uq_locations_client_location'),
    )
    op.create_index('idx_locations_client_location', 'locations', ['client_id', 'location_id'])
    op.create_index('idx_locations_client', 'locations', ['client_id'])

    # ============================================================================
    # STOCK_LEVELS TABLE
    # ============================================================================
    op.create_table(
        'stock_levels',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_id', sa.String(255), nullable=False),  # ⚠️ CRITICAL: matches forecasting engine
        sa.Column('location_id', sa.String(50), nullable=False),
        sa.Column('current_stock', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['client_id'], ['clients.client_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('client_id', 'item_id', 'location_id', name='uq_stock_client_item_location'),
    )
    op.create_index('idx_stock_client_item_location', 'stock_levels', ['client_id', 'item_id', 'location_id'])
    op.create_index('idx_stock_client_item', 'stock_levels', ['client_id', 'item_id'])

    # ============================================================================
    # SUPPLIERS TABLE
    # ============================================================================
    op.create_table(
        'suppliers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('external_id', sa.String(100), nullable=True),  # External ID from ERP
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('contact_phone', sa.String(50), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('supplier_type', sa.String(20), default='PO', nullable=False),  # PO or WO
        sa.Column('is_synced', sa.Boolean(), default=False, nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['client_id'], ['clients.client_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('client_id', 'name', name='uq_suppliers_client_name'),
        sa.UniqueConstraint('client_id', 'external_id', name='uq_suppliers_client_external'),
    )
    op.create_index('idx_suppliers_client', 'suppliers', ['client_id'])

    # ============================================================================
    # PRODUCT_SUPPLIER_CONDITIONS TABLE
    # ============================================================================
    op.create_table(
        'product_supplier_conditions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_id', sa.String(255), nullable=False),  # ⚠️ CRITICAL: matches forecasting engine
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('moq', sa.Integer(), default=0, nullable=False),  # Minimum Order Quantity
        sa.Column('lead_time_days', sa.Integer(), default=0, nullable=False),
        sa.Column('supplier_sku', sa.String(100), nullable=True),
        sa.Column('supplier_cost', sa.Numeric(10, 2), nullable=True),
        sa.Column('packaging_unit', sa.String(50), nullable=True),
        sa.Column('packaging_qty', sa.Integer(), nullable=True),
        sa.Column('is_primary', sa.Boolean(), default=False, nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['client_id'], ['clients.client_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('client_id', 'item_id', 'supplier_id', name='uq_product_supplier_client_item_supplier'),
    )
    op.create_index('idx_product_supplier_client_item', 'product_supplier_conditions', ['client_id', 'item_id'])
    op.create_index('idx_product_supplier_supplier', 'product_supplier_conditions', ['supplier_id'])

    # ============================================================================
    # CLIENT_SETTINGS TABLE
    # ============================================================================
    op.create_table(
        'client_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), unique=True, nullable=False),
        sa.Column('safety_buffer_days', sa.Integer(), default=7, nullable=False),
        sa.Column('understocked_threshold', sa.Integer(), default=14, nullable=False),
        sa.Column('overstocked_threshold', sa.Integer(), default=90, nullable=False),
        sa.Column('dead_stock_days', sa.Integer(), default=90, nullable=False),
        sa.Column('recommendation_rules', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['client_id'], ['clients.client_id'], ondelete='CASCADE'),
    )
    op.create_index('idx_client_settings_client', 'client_settings', ['client_id'])

    # ============================================================================
    # INVENTORY_METRICS TABLE
    # ============================================================================
    op.create_table(
        'inventory_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_id', sa.String(255), nullable=False),  # ⚠️ CRITICAL: matches forecasting engine
        sa.Column('location_id', sa.String(50), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('current_stock', sa.Integer(), nullable=False),
        sa.Column('dir', sa.Numeric(10, 2), nullable=True),  # Days of Inventory Remaining
        sa.Column('stockout_risk', sa.Numeric(5, 2), nullable=True),  # Risk score 0-100
        sa.Column('forecasted_demand_30d', sa.Numeric(10, 2), nullable=True),
        sa.Column('inventory_value', sa.Numeric(12, 2), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),  # understocked, overstocked, normal
        sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['client_id'], ['clients.client_id'], ondelete='CASCADE'),
    )
    op.create_index('idx_inventory_metrics_client_item_location_date', 'inventory_metrics', 
                    ['client_id', 'item_id', 'location_id', 'date'])
    op.create_index('idx_inventory_metrics_status', 'inventory_metrics', ['status'])
    op.create_index('idx_inventory_metrics_client_item', 'inventory_metrics', ['client_id', 'item_id'])

    # ============================================================================
    # PURCHASE_ORDERS TABLE
    # ============================================================================
    op.create_table(
        'purchase_orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('po_number', sa.String(50), nullable=False, unique=True),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(20), default='pending', nullable=False),
        sa.Column('order_date', sa.Date(), nullable=False, server_default=sa.func.current_date()),
        sa.Column('expected_delivery_date', sa.Date(), nullable=True),
        sa.Column('total_amount', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('shipping_method', sa.String(50), nullable=True),
        sa.Column('shipping_unit', sa.String(50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['client_id'], ['clients.client_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_purchase_orders_client', 'purchase_orders', ['client_id'])
    op.create_index('idx_purchase_orders_supplier', 'purchase_orders', ['supplier_id'])
    op.create_index('idx_purchase_orders_status', 'purchase_orders', ['status'])

    # ============================================================================
    # PURCHASE_ORDER_ITEMS TABLE
    # ============================================================================
    op.create_table(
        'purchase_order_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('po_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_id', sa.String(255), nullable=False),  # ⚠️ CRITICAL: matches forecasting engine
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_cost', sa.Numeric(10, 2), nullable=False),
        sa.Column('total_price', sa.Numeric(12, 2), nullable=False),
        sa.Column('packaging_unit', sa.String(50), nullable=True),
        sa.Column('packaging_qty', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['po_id'], ['purchase_orders.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_purchase_order_items_po', 'purchase_order_items', ['po_id'])
    op.create_index('idx_purchase_order_items_item', 'purchase_order_items', ['item_id'])


def downgrade():
    # Drop tables in reverse order (respecting foreign key dependencies)
    op.drop_table('purchase_order_items')
    op.drop_table('purchase_orders')
    op.drop_table('inventory_metrics')
    op.drop_table('client_settings')
    op.drop_table('product_supplier_conditions')
    op.drop_table('suppliers')
    op.drop_table('stock_levels')
    op.drop_table('locations')
    op.drop_table('products')
