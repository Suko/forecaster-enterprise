# User Stories

## Overview
This document contains user stories organized by stakeholder persona. The system serves three primary stakeholders: CEO (executive overview), Procurement Manager (operational inventory management), and Marketing Manager (product promotion strategy).

---

## CEO - Executive Overview & Performance

### US-CEO-001: View High-Level Performance Dashboard
**As a** CEO  
**I want to** view high-level performance metrics and KPIs  
**So that** I can assess overall business health at a glance

**Acceptance Criteria:**
- Executive dashboard shows: Total inventory value, Total SKUs, Revenue trends, Forecast accuracy
- Time period selector (daily, weekly, monthly, quarterly, yearly)
- Visual indicators (trending up/down, percentage changes)
- Comparison to previous periods
- Export capability for reports

### US-CEO-002: View Historical Performance Trends
**As a** CEO  
**I want to** see past and current performance data  
**So that** I can track business trends over time

**Acceptance Criteria:**
- Historical charts showing inventory value, stock levels, sales trends
- Date range selector for custom periods
- Compare multiple time periods side-by-side
- Key milestones and events marked on timeline
- Export historical data

### US-CEO-003: Configure High-Level Data Thresholds
**As a** CEO  
**I want to** set high-level data thresholds and targets  
**So that** I can define business goals and monitor performance against them

**Acceptance Criteria:**
- Set target inventory value ranges
- Configure acceptable stockout risk thresholds
- Set forecast accuracy targets (MAPE goals)
- Define overstock/understock thresholds at business level
- View alerts when thresholds are exceeded

### US-CEO-004: View ROI of Forecast Improvements
**As a** CEO  
**I want to** see the financial impact of forecast accuracy improvements  
**So that** I can justify investments in forecasting technology

**Acceptance Criteria:**
- ROI calculator showing potential savings
- Current vs improved forecast accuracy comparison
- Annual savings projections
- Visual charts showing cost reduction
- Scenario planning (best case, target, current)

### US-CEO-005: Monitor Critical Inventory Issues
**As a** CEO  
**I want to** see critical inventory issues requiring attention  
**So that** I can ensure operational risks are managed

**Acceptance Criteria:**
- Alert dashboard for critical issues (high stockout risk, excessive overstock)
- Summary of products needing immediate attention
- Financial impact of issues (potential lost sales, excess inventory cost)
- Trend indicators showing if issues are improving or worsening

---

## Procurement Manager - Operational Inventory Management

### US-PROC-001: View Products Needing Attention
**As a** procurement manager  
**I want to** see products that need immediate attention  
**So that** I can prioritize my ordering activities

**Acceptance Criteria:**
- List of understocked products with stockout risk scores
- List of overstocked products with excess inventory value
- Sortable by risk level, inventory value, or forecasted demand
- Filter by supplier, category, or location
- Visual indicators (red/yellow/green) for urgency

### US-PROC-002: Prevent Stockouts Through Order Planning
**As a** procurement manager  
**I want to** use forecast data to plan orders  
**So that** I can avoid stockouts while maintaining optimal inventory levels

**Acceptance Criteria:**
- Order planning suggestions based on forecasted demand
- Suggested order quantities with lead time consideration
- Stockout risk indicators for each product
- Days of inventory remaining (DIR) clearly displayed
- One-click add to order cart

### US-PROC-003: Avoid Excessive Inventory
**As a** procurement manager  
**I want to** identify overstocked products  
**So that** I can avoid ordering too much inventory

**Acceptance Criteria:**
- List of overstocked products (DIR > 90 days)
- Excess inventory value displayed
- Recommendations to reduce ordering for overstocked items
- Historical trend showing inventory buildup
- Alerts when products become overstocked

### US-PROC-004: View Operational Clarity Dashboard
**As a** procurement manager  
**I want to** see clear operational metrics  
**So that** I can make efficient ordering decisions

**Acceptance Criteria:**
- Dashboard showing: Total SKUs, Understocked count, Overstocked count, Average DIR
- Top 5 understocked and overstocked items
- Supplier performance metrics
- Order status overview (pending, confirmed, shipped)
- Quick access to order planning and recommendations

### US-PROC-005: Create Purchase Orders Efficiently
**As a** procurement manager  
**I want to** create purchase orders from order planning suggestions  
**So that** I can quickly place orders with suppliers

**Acceptance Criteria:**
- Order planning cart with suggested items
- Group items by supplier automatically
- Adjust quantities before creating order
- Review order summary (items, quantities, costs, totals)
- Create order with one click
- Order appears in orders list with "pending" status

### US-PROC-006: Manage Purchase Orders
**As a** procurement manager  
**I want to** track purchase orders through their lifecycle  
**So that** I can ensure timely delivery

**Acceptance Criteria:**
- View all orders with status, supplier, date, total value
- Filter by status (pending, confirmed, shipped, received, cancelled)
- Filter by supplier
- Update order status as orders progress
- View order details (items, quantities, costs, shipping info)
- Track expected delivery dates

### US-PROC-007: View Supplier Information
**As a** procurement manager  
**I want to** view supplier details and catalogs  
**So that** I can make informed ordering decisions

**Acceptance Criteria:**
- View supplier list with contact information
- View all products from a specific supplier
- See supplier-specific pricing, MOQ, and lead times
- View order history with supplier
- Supplier performance metrics (on-time delivery, etc.)

### US-PROC-008: Identify Dead Stock
**As a** procurement manager  
**I want to** identify dead stock (slow-moving or obsolete inventory)  
**So that** I can take action to reduce inventory holding costs

**Acceptance Criteria:**
- List of products with no sales in last X days (configurable)
- Products with declining sales trends
- Inventory value of dead stock
- Recommendations for dead stock (promote, discount, liquidate)
- Filter by category, supplier, or location
- Export dead stock report

### US-PROC-009: View AI-Powered Recommendations
**As a** procurement manager  
**I want to** see AI-generated recommendations for inventory actions  
**So that** I can make data-driven decisions

**Acceptance Criteria:**
- Recommendations categorized by action (REORDER, REDUCE_ORDER, etc.)
- Each recommendation shows SKU, reason, priority, suggested action
- Add recommendations directly to order planning cart
- Ignore recommendations that aren't relevant
- Recommendations already in cart are hidden

### US-PROC-010: Search and Filter Products
**As a** procurement manager  
**I want to** search and filter products efficiently  
**So that** I can find specific items quickly

**Acceptance Criteria:**
- Search by SKU, name, or category
- Filter by supplier, category, location, stock status (understocked/overstocked/normal)
- Sort by DIR, inventory value, stockout risk
- Pagination for large product lists
- Export filtered results

### US-PROC-011: Edit Product Information
**As a** procurement manager  
**I want to** update product details relevant to ordering  
**So that** I can maintain accurate procurement data

**Acceptance Criteria:**
- Edit unit cost, MOQ, lead time, supplier
- Bulk update multiple products
- Changes saved and reflected immediately
- Validation prevents invalid data entry
- Audit trail of changes

### US-PROC-012: Refresh Inventory Metrics
**As a** procurement manager  
**I want to** manually refresh DIR calculations  
**So that** I can get updated metrics after data changes

**Acceptance Criteria:**
- "Refresh DIRs" button available
- System recalculates all DIR values
- Loading state shown during calculation
- Updated values reflected in all views
- Notification when refresh completes

---

## Marketing Manager - Product Promotion Strategy

### US-MKT-001: Identify Products to Promote
**As a** marketing manager  
**I want to** see which products are good candidates for promotion  
**So that** I can increase sales of well-stocked items

**Acceptance Criteria:**
- List of products with sufficient inventory (DIR > 30 days)
- Products with declining sales that need boost
- Products not currently in active campaigns
- Sortable by inventory level, sales trend, margin
- Filter by category, supplier, or location

### US-MKT-002: View Products Below Marketing Threshold
**As a** marketing manager  
**I want to** see products that are below the marketing threshold  
**So that** I can identify products that need marketing support

**Acceptance Criteria:**
- List of products with low sales or declining trends
- Products with no active marketing campaigns
- Threshold configurable (e.g., sales below X units, declining trend)
- Visual indicators showing how far below threshold
- Recommendations for marketing actions

### US-MKT-003: View Product Campaign Status
**As a** marketing manager  
**I want to** see which products are in active campaigns  
**So that** I can understand campaign coverage and identify gaps

**Acceptance Criteria:**
- View products with active campaigns
- View products without campaigns
- See campaign names and details for each product
- Filter and search products by campaign status
- Coverage metrics (percentage of products in campaigns)

### US-MKT-004: Create Marketing Campaigns
**As a** marketing manager  
**I want to** create marketing campaigns for products  
**So that** I can drive sales and clear inventory

**Acceptance Criteria:**
- Create campaign with name, type, status, dates, budget
- Add products to campaign
- Set campaign parameters (discount, target audience, channels)
- View inventory levels for selected products
- Save as draft or activate immediately

### US-MKT-005: View Marketing Campaigns
**As a** marketing manager  
**I want to** view all marketing campaigns  
**So that** I can track campaign performance and status

**Acceptance Criteria:**
- Campaign list with name, type, status, dates, budget
- Filter by status (planned, active, completed, cancelled)
- Filter by type (email, google_ads, facebook, promotion, launch, seasonal)
- View campaign details including products and performance metrics
- Sort by date, budget, or status

### US-MKT-006: Edit Marketing Campaigns
**As a** marketing manager  
**I want to** edit existing campaigns  
**So that** I can update campaign details and parameters

**Acceptance Criteria:**
- Edit campaign name, dates, budget, status
- Add/remove products from campaign
- Update campaign parameters (discount, channels, etc.)
- Changes saved and reflected immediately
- View campaign performance metrics

### US-MKT-007: Delete Marketing Campaigns
**As a** marketing manager  
**I want to** delete campaigns  
**So that** I can remove cancelled or obsolete campaigns

**Acceptance Criteria:**
- Delete button on campaign detail page
- Confirmation dialog before deletion
- Campaign removed from list after deletion
- Products removed from campaign become available for other campaigns

### US-MKT-008: View Products with Excess Inventory
**As a** marketing manager  
**I want to** see products with excess inventory  
**So that** I can create campaigns to clear overstock

**Acceptance Criteria:**
- List of overstocked products (DIR > 90 days)
- Excess inventory value and quantity
- Products not in active campaigns highlighted
- Recommendations for promotion types (discount, bundle, etc.)
- Historical sales data to inform campaign strategy

### US-MKT-009: Avoid Promoting Low-Stock Products
**As a** marketing manager  
**I want to** see which products have low stock  
**So that** I can avoid promoting products that might stock out

**Acceptance Criteria:**
- Warning indicators for products with low stock (DIR < lead time + 7 days)
- Products excluded from "promote" recommendations if stock is too low
- Alert when trying to add low-stock product to campaign
- View stockout risk score for each product
- Recommendations to wait until stock is replenished

### US-MKT-010: View Campaign Performance Impact
**As a** marketing manager  
**I want to** see how campaigns affect product sales and inventory  
**So that** I can measure campaign effectiveness

**Acceptance Criteria:**
- Sales trends before, during, and after campaigns
- Inventory level changes during campaigns
- Campaign ROI metrics
- Compare products with and without campaigns
- Export campaign performance reports

---

## Shared Features - All Stakeholders

### US-SHARED-001: Navigate Between Features
**As a** user  
**I want to** easily navigate between different features  
**So that** I can access all functionality efficiently

**Acceptance Criteria:**
- Sidebar navigation with main features
- Active page clearly highlighted
- Breadcrumbs for deep navigation
- Keyboard shortcuts for common actions
- Responsive design for mobile/tablet

### US-SHARED-002: View Product Details
**As a** user  
**I want to** view detailed information about a product  
**So that** I can make informed decisions

**Acceptance Criteria:**
- Navigate to product detail page
- View full product information (SKU, name, category, supplier, stock, cost, DIR)
- See product history and trends
- View associated campaigns
- View order history
- Edit product from detail page (if permissions allow)

### US-SHARED-003: Generate Forecasts with Covariates
**As a** user  
**I want to** generate forecasts using covariates (promotions, holidays, stockouts)  
**So that** I can create accurate demand predictions

**Acceptance Criteria:**
- Select dataset/client
- Filter by store, SKU, category, supplier
- Configure forecast horizon (days)
- Toggle covariates (promotions, holidays, weekends, stockouts)
- View forecast chart with historical data and predictions
- See forecast metrics (MAPE, RMSE, etc.)

### US-SHARED-004: View Forecast Charts
**As a** user  
**I want to** visualize forecasts with historical data  
**So that** I can understand forecast accuracy and trends

**Acceptance Criteria:**
- Interactive chart showing historical sales and forecast
- Toggle visibility of promotions, holidays, weekends, stockouts
- Show/hide rolling average
- Adjustable rolling window size
- Cutoff date clearly marked (train/test split)
- Zoom and pan capabilities

### US-SHARED-005: Query Data Using Natural Language
**As a** user  
**I want to** ask questions about my data in natural language  
**So that** I can get insights without writing SQL

**Acceptance Criteria:**
- Chat interface with message history
- Type questions in natural language
- Receive answers with text and/or tables
- Predefined prompt suggestions available
- Support for questions about: inventory, sales, products, campaigns

### US-SHARED-006: Upload Data Files
**As a** user  
**I want to** upload data files  
**So that** I can import new data into the system

**Acceptance Criteria:**
- Upload CSV or other supported formats
- File validation before upload
- Progress indicator during upload
- Success/error messages
- View upload history

### US-SHARED-007: Select Active Client/Dataset
**As a** user  
**I want to** select which client's data to work with  
**So that** I can switch between different clients

**Acceptance Criteria:**
- Client selector in UI
- Active client clearly indicated
- All views update when client changes
- Client-specific data loaded automatically

### US-SHARED-008: Configure System Settings
**As a** administrator  
**I want to** configure system settings  
**So that** I can customize system behavior

**Acceptance Criteria:**
- Access settings page
- Configure inventory thresholds (understocked, overstocked)
- Set default forecast parameters
- Configure notification preferences
- Save settings with validation

---

## Priority Classification

### High Priority (P0) - Critical for Operations

**CEO:**
- US-CEO-001: View High-Level Performance Dashboard
- US-CEO-002: View Historical Performance Trends

**Procurement Manager:**
- US-PROC-001: View Products Needing Attention
- US-PROC-002: Prevent Stockouts Through Order Planning
- US-PROC-003: Avoid Excessive Inventory
- US-PROC-005: Create Purchase Orders Efficiently

**Marketing Manager:**
- US-MKT-001: Identify Products to Promote
- US-MKT-002: View Products Below Marketing Threshold
- US-MKT-004: Create Marketing Campaigns

### Medium Priority (P1) - Important for Efficiency

**CEO:**
- US-CEO-003: Configure High-Level Data Thresholds
- US-CEO-004: View ROI of Forecast Improvements

**Procurement Manager:**
- US-PROC-004: View Operational Clarity Dashboard
- US-PROC-006: Manage Purchase Orders
- US-PROC-008: Identify Dead Stock
- US-PROC-009: View AI-Powered Recommendations

**Marketing Manager:**
- US-MKT-003: View Product Campaign Status
- US-MKT-005: View Marketing Campaigns
- US-MKT-008: View Products with Excess Inventory

### Low Priority (P2) - Nice to Have

**CEO:**
- US-CEO-005: Monitor Critical Inventory Issues

**Procurement Manager:**
- US-PROC-007: View Supplier Information
- US-PROC-010: Search and Filter Products
- US-PROC-011: Edit Product Information
- US-PROC-012: Refresh Inventory Metrics

**Marketing Manager:**
- US-MKT-006: Edit Marketing Campaigns
- US-MKT-007: Delete Marketing Campaigns
- US-MKT-009: Avoid Promoting Low-Stock Products
- US-MKT-010: View Campaign Performance Impact

---

## Notes
- User stories are based on the existing UI structure in `/old/ecommerce-agent/frontend`
- Stories are organized by stakeholder persona to reflect different user needs
- Dead stock management is assigned to Procurement Manager as it relates to inventory optimization
- Products below marketing threshold are assigned to Marketing Manager for campaign planning
- Some features may be experimental or in development
- Integration with backend APIs is assumed for all stories
