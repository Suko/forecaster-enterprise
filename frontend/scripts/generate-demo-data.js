/**
 * Generate Demo Data Files
 * Creates JSON files for static demo deployment
 */

import { writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';

const demoDataDir = join(process.cwd(), 'public', 'demo-data');
mkdirSync(demoDataDir, { recursive: true });

// Generate dashboard data
const dashboardData = {
  metrics: {
    total_inventory_value: "2900000",
    total_skus: 200,
    understocked_count: 23,
    overstocked_count: 95,
    understocked_value: "450000",
    overstocked_value: "1200000",
  },
  top_understocked: [
    { item_id: "M5_HOUSEHOLD_1_334", product_name: "Product M5_HOUSEHOLD_1_334", dir: 1.3, stockout_risk: 0.944 },
    { item_id: "M5_HOBBIES_1_387", product_name: "Product M5_HOBBIES_1_387", dir: 2.3, stockout_risk: 0.894 },
    { item_id: "M5_HOBBIES_1_404", product_name: "Product M5_HOBBIES_1_404", dir: 2.8, stockout_risk: 0.889 },
    { item_id: "M5_HOBBIES_1_209", product_name: "Product M5_HOBBIES_1_209", dir: 2.1, stockout_risk: 0.884 },
    { item_id: "M5_HOUSEHOLD_1_370", product_name: "Product M5_HOUSEHOLD_1_370", dir: 2.7, stockout_risk: 0.857 },
  ],
  top_overstocked: [
    { item_id: "M5_HOUSEHOLD_1_082", product_name: "Product M5_HOUSEHOLD_1_082", dir: 368.7 },
    { item_id: "M5_HOUSEHOLD_1_086", product_name: "Product M5_HOUSEHOLD_1_086", dir: 351.1 },
    { item_id: "M5_HOUSEHOLD_1_048", product_name: "Product M5_HOUSEHOLD_1_048", dir: 251.5 },
    { item_id: "M5_HOUSEHOLD_1_027", product_name: "Product M5_HOUSEHOLD_1_027", dir: 236.3 },
    { item_id: "M5_HOUSEHOLD_1_439", product_name: "Product M5_HOUSEHOLD_1_439", dir: 194.1 },
  ],
};

// Generate products data (200 products)
const categories = ["HOUSEHOLD", "HOBBIES", "FOODS", "ELECTRONICS"];
const products = [];

for (let i = 1; i <= 200; i++) {
  const category = categories[i % categories.length];
  const itemId = `M5_${category}_1_${String(i).padStart(3, '0')}`;
  const dir = i < 10 ? Math.random() * 10 + 1 : i < 30 ? Math.random() * 60 + 10 : Math.random() * 200 + 100;
  const stockoutRisk = dir < 14 ? Math.random() * 0.3 + 0.7 : dir < 30 ? Math.random() * 0.4 + 0.3 : Math.random() * 0.2;
  const status = dir < 14 ? "understocked" : dir > 90 ? "overstocked" : "normal";
  const currentStock = Math.floor(Math.random() * 500 + 50);
  const unitCost = (Math.random() * 50 + 10).toFixed(2);
  const inventoryValue = (currentStock * parseFloat(unitCost)).toFixed(2);
  
  const baseSales = Math.random() * 50 + 10;
  const avg90d = baseSales;
  const avg30d = baseSales + (Math.random() - 0.5) * 10;
  const avg7d = avg30d + (Math.random() - 0.5) * 5;
  
  products.push({
    item_id: itemId,
    product_name: `Product ${itemId}`,
    category: category,
    current_stock: currentStock,
    unit_cost: unitCost,
    safety_buffer_days: 7,
    dir: parseFloat(dir.toFixed(1)),
    stockout_risk: parseFloat(stockoutRisk.toFixed(3)),
    status: status,
    inventory_value: inventoryValue,
    sales_velocity: {
      avg_7d: Math.max(0, parseFloat(avg7d.toFixed(2))),
      avg_30d: Math.max(0, parseFloat(avg30d.toFixed(2))),
      avg_90d: Math.max(0, parseFloat(avg90d.toFixed(2))),
      trend_7d: avg7d > avg30d ? 1 : avg7d < avg30d ? -1 : 0,
      trend_30d: avg30d > avg90d ? 1 : avg30d < avg90d ? -1 : 0,
    },
    suppliers: [
      {
        supplier_id: `SUPPLIER_${i % 5 + 1}`,
        supplier_name: `Supplier ${i % 5 + 1}`,
        moq: Math.floor(Math.random() * 100 + 10),
        lead_time_days: Math.floor(Math.random() * 14 + 3),
        is_primary: true,
      },
      ...(i % 3 === 0 ? [{
        supplier_id: `SUPPLIER_${(i % 5 + 2) % 5 + 1}`,
        supplier_name: `Supplier ${(i % 5 + 2) % 5 + 1}`,
        moq: Math.floor(Math.random() * 100 + 10),
        lead_time_days: Math.floor(Math.random() * 14 + 3),
        is_primary: false,
      }] : []),
    ],
    locations: [
      {
        location_id: "WAREHOUSE_1",
        location_name: "Main Warehouse",
        current_stock: Math.floor(currentStock * 0.7),
      },
      ...(i % 2 === 0 ? [{
        location_id: "STORE_1",
        location_name: "Store Front",
        current_stock: Math.floor(currentStock * 0.3),
      }] : []),
    ],
  });
}

// Generate recommendations
const recommendationTypes = ["REORDER", "URGENT", "REDUCE_ORDER", "DEAD_STOCK", "PROMOTE"];
const priorities = ["high", "medium", "low"];
const recommendations = [];

for (let i = 0; i < 50; i++) {
  const product = products[Math.floor(Math.random() * products.length)];
  const type = recommendationTypes[Math.floor(Math.random() * recommendationTypes.length)];
  const priority = priorities[Math.floor(Math.random() * priorities.length)];
  
  let reason = "";
  let suggestedQuantity = 0;
  
  if (type === "REORDER" || type === "URGENT") {
    suggestedQuantity = Math.floor(product.current_stock * 2);
    reason = `Stockout risk ${(product.stockout_risk * 100).toFixed(1)}%, DIR ${product.dir.toFixed(1)} days`;
  } else if (type === "REDUCE_ORDER") {
    suggestedQuantity = Math.floor(product.current_stock * 0.5);
    reason = `Excess inventory, DIR ${product.dir.toFixed(1)} days`;
  } else if (type === "DEAD_STOCK") {
    reason = `No sales in last 90 days, DIR ${product.dir.toFixed(1)} days`;
  } else {
    reason = `Low sales velocity, consider promotion`;
  }
  
  recommendations.push({
    type,
    priority,
    item_id: product.item_id,
    product_name: product.product_name,
    reason,
    suggested_quantity: type === "REORDER" || type === "URGENT" ? suggestedQuantity : undefined,
    supplier_id: product.suppliers?.[0]?.supplier_id,
    supplier_name: product.suppliers?.[0]?.supplier_name,
  });
}

// Generate cart data (3 items for demo)
const cartItems = [];
let cartTotalValue = 0;

// Add 3 items to cart from different suppliers
for (let i = 0; i < 3; i++) {
  const product = products[Math.floor(Math.random() * products.length)];
  const supplier = product.suppliers?.[0];
  if (!supplier) continue;
  
  const quantity = Math.floor(Math.random() * 50 + 20);
  const unitCost = parseFloat(product.unit_cost);
  const totalPrice = quantity * unitCost;
  cartTotalValue += totalPrice;
  
  cartItems.push({
    id: `cart_${Date.now()}_${i}`,
    session_id: 'demo-session',
    item_id: product.item_id,
    supplier_id: supplier.supplier_id,
    quantity: quantity,
    unit_cost: unitCost.toFixed(2),
    total_price: totalPrice.toFixed(2),
    packaging_unit: null,
    packaging_qty: null,
    notes: null,
    product_name: product.product_name || `Product ${product.item_id}`,
    supplier_name: supplier.supplier_name || 'Unknown Supplier',
    moq: supplier.moq || 0,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  });
}

const cartData = {
  items: cartItems,
  total_items: cartItems.reduce((sum, item) => sum + item.quantity, 0),
  total_value: cartTotalValue.toFixed(2),
};

// Generate trend data (90 days)
const today = new Date();
const inventoryTrend = [];
const salesTrend = [];

const startInventoryValue = 4100000;
const endInventoryValue = 2900000;
const reduction = startInventoryValue - endInventoryValue;

for (let i = 90; i >= 0; i--) {
  const date = new Date(today);
  date.setDate(date.getDate() - i);
  const dateStr = date.toISOString().split('T')[0];
  
  // Inventory value trend (decreasing)
  const progress = (90 - i) / 90;
  const inventoryValue = startInventoryValue - (reduction * progress) + (Math.random() - 0.5) * 50000;
  inventoryTrend.push({
    date: dateStr,
    value: Math.floor(inventoryValue),
  });
  
  // Sales velocity trend (increasing)
  const baseSales = 850 + (progress * 550);
  const salesValue = baseSales + (Math.random() - 0.5) * 50;
  salesTrend.push({
    date: dateStr,
    value: Math.floor(salesValue),
  });
}

const trendsData = {
  inventory_value: inventoryTrend,
  sales_velocity: salesTrend,
};

// Generate forecast data for top 10 products
const forecastsData = {};
const topProducts = products.slice(0, 10);

topProducts.forEach((product, index) => {
  const historical = [];
  const forecast = [];
  
  // Historical data (90 days)
  for (let i = 90; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    historical.push({
      date: date.toISOString().split('T')[0],
      value: Math.floor(Math.random() * 20 + 10),
    });
  }
  
  // Forecast data (30 days)
  for (let i = 1; i <= 30; i++) {
    const date = new Date(today);
    date.setDate(date.getDate() + i);
    const baseValue = 15;
    const value = baseValue + Math.random() * 5;
    forecast.push({
      date: date.toISOString().split('T')[0],
      value: Math.floor(value),
      lower: Math.floor(value * 0.7),
      upper: Math.floor(value * 1.3),
    });
  }
  
  const stockoutDate = new Date(today);
  stockoutDate.setDate(stockoutDate.getDate() + Math.floor(product.dir));
  
  forecastsData[product.item_id] = {
    historical,
    forecast,
    estimated_stockout_date: stockoutDate.toISOString().split('T')[0],
    recommended_reorder_window: {
      start: new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      end: new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },
  };
});

// Generate suppliers data (10 suppliers)
const suppliers = [];
for (let i = 1; i <= 10; i++) {
  const supplierType = i <= 7 ? 'PO' : 'WO';
  const createdAt = new Date(today);
  createdAt.setDate(createdAt.getDate() - Math.floor(Math.random() * 180));
  
  suppliers.push({
    id: `SUPPLIER_${i}`,
    external_id: `EXT_SUP_${i}`,
    name: `Supplier ${i}`,
    contact_email: `supplier${i}@example.com`,
    contact_phone: `+1-555-${String(i).padStart(4, '0')}`,
    address: `${i * 100} Main Street, City, State ${i * 10000}`,
    supplier_type: supplierType,
    default_moq: Math.floor(Math.random() * 100 + 10),
    default_lead_time_days: Math.floor(Math.random() * 14 + 3),
    is_synced: true,
    notes: i % 3 === 0 ? `Notes for supplier ${i}` : null,
    created_at: createdAt.toISOString(),
    updated_at: createdAt.toISOString(),
    default_product_count: Math.floor(Math.random() * 30 + 5),
    effective_moq_avg: Math.floor(Math.random() * 100 + 10),
    effective_moq_min: 10,
    effective_moq_max: 200,
    custom_moq_count: Math.floor(Math.random() * 5),
    effective_lead_time_avg: Math.floor(Math.random() * 14 + 3),
    effective_lead_time_min: 3,
    effective_lead_time_max: 21,
    custom_lead_time_count: Math.floor(Math.random() * 3),
  });
}

// Generate purchase orders data (20 orders)
const purchaseOrdersList = [];
const purchaseOrdersDetail = [];
const statuses = ['pending', 'confirmed', 'shipped', 'received', 'cancelled'];
const statusWeights = [0.3, 0.25, 0.2, 0.15, 0.1]; // More pending/confirmed orders

for (let i = 1; i <= 20; i++) {
  const supplier = suppliers[Math.floor(Math.random() * suppliers.length)];
  const statusIndex = Math.random() < statusWeights[0] ? 0 : 
                     Math.random() < statusWeights[0] + statusWeights[1] ? 1 :
                     Math.random() < statusWeights[0] + statusWeights[1] + statusWeights[2] ? 2 :
                     Math.random() < statusWeights[0] + statusWeights[1] + statusWeights[2] + statusWeights[3] ? 3 : 4;
  const status = statuses[statusIndex];
  
  const orderDate = new Date(today);
  orderDate.setDate(orderDate.getDate() - Math.floor(Math.random() * 60));
  
  const expectedDelivery = new Date(orderDate);
  expectedDelivery.setDate(expectedDelivery.getDate() + supplier.default_lead_time_days + Math.floor(Math.random() * 7));
  
  // Generate order items (2-5 items per order)
  const numItems = Math.floor(Math.random() * 4 + 2);
  const orderItems = [];
  let totalAmount = 0;
  
  for (let j = 0; j < numItems; j++) {
    const product = products[Math.floor(Math.random() * products.length)];
    const quantity = Math.floor(Math.random() * 100 + 20);
    const unitCost = parseFloat(product.unit_cost);
    const totalPrice = quantity * unitCost;
    totalAmount += totalPrice;
    
    orderItems.push({
      id: `PO_${i}_ITEM_${j + 1}`,
      item_id: product.item_id,
      product_name: product.product_name,
      quantity: quantity,
      unit_cost: unitCost.toFixed(2),
      total_price: totalPrice.toFixed(2),
      packaging_unit: j % 2 === 0 ? 'box' : null,
      packaging_qty: j % 2 === 0 ? 12 : null,
    });
  }
  
  const poId = `po_${String(i).padStart(4, '0')}`;
  const poNumber = `PO-2025-${String(i).padStart(4, '0')}`;
  
  // List item (summary)
  purchaseOrdersList.push({
    id: poId,
    po_number: poNumber,
    supplier_id: supplier.id,
    supplier_name: supplier.name,
    status: status,
    order_date: orderDate.toISOString().split('T')[0],
    expected_delivery_date: status !== 'cancelled' ? expectedDelivery.toISOString().split('T')[0] : null,
    total_amount: Math.round(totalAmount * 100) / 100,
    created_at: orderDate.toISOString(),
  });
  
  // Detail item (full)
  purchaseOrdersDetail.push({
    id: poId,
    po_number: poNumber,
    supplier_id: supplier.id,
    supplier_name: supplier.name,
    status: status,
    order_date: orderDate.toISOString().split('T')[0],
    expected_delivery_date: status !== 'cancelled' ? expectedDelivery.toISOString().split('T')[0] : null,
    total_amount: Math.round(totalAmount * 100) / 100,
    shipping_method: i % 3 === 0 ? 'Standard' : i % 3 === 1 ? 'Express' : null,
    shipping_unit: i % 3 === 0 ? 'pallet' : null,
    notes: i % 5 === 0 ? `Notes for order ${poNumber}` : null,
    created_by: 'demo@forecaster-enterprise.com',
    items: orderItems,
    created_at: orderDate.toISOString(),
    updated_at: orderDate.toISOString(),
  });
}

// Write all files
writeFileSync(join(demoDataDir, 'dashboard.json'), JSON.stringify(dashboardData, null, 2));
writeFileSync(join(demoDataDir, 'products.json'), JSON.stringify(products, null, 2));
writeFileSync(join(demoDataDir, 'recommendations.json'), JSON.stringify(recommendations, null, 2));
writeFileSync(join(demoDataDir, 'cart.json'), JSON.stringify(cartData, null, 2));
writeFileSync(join(demoDataDir, 'trends.json'), JSON.stringify(trendsData, null, 2));
writeFileSync(join(demoDataDir, 'forecasts.json'), JSON.stringify(forecastsData, null, 2));
writeFileSync(join(demoDataDir, 'suppliers.json'), JSON.stringify(suppliers, null, 2));
writeFileSync(join(demoDataDir, 'purchase-orders.json'), JSON.stringify(purchaseOrdersList, null, 2));
writeFileSync(join(demoDataDir, 'purchase-orders-detail.json'), JSON.stringify(purchaseOrdersDetail, null, 2));

console.log('✅ Demo data files generated successfully!');
console.log(`📁 Location: ${demoDataDir}`);
console.log(`📊 Files created:`);
console.log('  - dashboard.json');
console.log('  - products.json (200 products)');
console.log('  - recommendations.json (50 recommendations)');
console.log('  - cart.json');
console.log('  - trends.json (90 days)');
console.log('  - forecasts.json (10 products)');
console.log('  - suppliers.json (10 suppliers)');
console.log('  - purchase-orders.json (20 orders)');
console.log('  - purchase-orders-detail.json (20 order details)');

