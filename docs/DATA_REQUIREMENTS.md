# Data Requirements Guide

**Last Updated:** 2025-01-27  
**Audience:** Business Stakeholders & Decision Makers  
**Purpose:** Understand what data and systems you need to connect vs. what we manage for you

---

## Executive Summary

This document explains from a **business perspective**:
- **What data sources you need to connect** (required for forecasting)
- **What business processes need to be in place** (data availability)
- **What we can manage for you** (entered in our system)
- **What's optional** (improves accuracy but not required)

---

## 1. What You Need to Connect (Required)

These are the **minimum requirements** from your business systems. Without access to these, the forecasting system cannot work.

### 1.1 Sales Transaction Data (CRITICAL)

**What You Need:**
- Access to your sales/transaction system (POS, e-commerce platform, ERP)
- Historical sales data showing: **what products sold, when, where, and how many**

**Business Requirements:**
- **Minimum:** 30 days (3 weeks) of sales history
- **Recommended:** 2 years of history for better accuracy
- **Daily granularity:** We need day-by-day sales, not just monthly totals
- **Location tracking:** If you have multiple warehouses/stores, we need sales broken down by location

**What This Enables:**
- Demand forecasting (predicting future sales)
- Inventory recommendations
- Stockout risk assessment

**If You Don't Have This:**
- System cannot generate forecasts
- Cannot provide inventory recommendations

---

### 1.2 Product Catalog (CRITICAL)

**What You Need:**
- Access to your product master data (product catalog, SKU list)
- At minimum: Product identifiers (SKU codes) and product names

**Business Requirements:**
- Product identifiers must match what's in your sales data
- Product names for display (can be in any language)
- Product categories (if available - helps with grouping and analysis)
- Product costs (if available - enables inventory value calculations)

**What This Enables:**
- Links sales data to products
- Inventory value calculations
- Product-level recommendations

**If You Don't Have This:**
- Cannot link sales to products
- Cannot generate product-specific forecasts

---

### 1.3 Warehouse/Store Locations (CRITICAL)

**What You Need:**
- List of your warehouses, stores, or distribution centers
- Location identifiers that match your sales data

**Business Requirements:**
- If you have multiple locations: We need location identifiers in your sales data
- If you have a single location: We can use a default location identifier
- Location names for display

**What This Enables:**
- Multi-location inventory tracking
- Location-specific forecasts
- Location-level stock recommendations

**If You Don't Have This:**
- Cannot track inventory by location
- Cannot provide location-specific recommendations

---

### 1.4 Current Inventory Levels (CRITICAL)

**What You Need:**
- Access to your inventory management system
- Current stock levels per product and location

**Business Requirements:**
- Real-time or daily updated inventory counts
- Stock levels per product and location (if multi-location)
- Must be synced regularly (daily recommended)

**What This Enables:**
- Days of Inventory Remaining (DIR) calculations
- Stockout risk assessment
- Urgent reorder recommendations

**If You Don't Have This:**
- Cannot calculate how many days of stock you have left
- Cannot assess stockout risk
- Cannot provide urgent reorder alerts

---

## 2. What's Optional (Improves Accuracy)

These are **not required** but significantly improve forecast accuracy and enable additional features.

### 2.1 Enhanced Sales Context

**What Helps (If Available):**
- **Promotion data:** When promotions were active (helps system understand promotion-driven demand spikes)
- **Holiday calendar:** Which days were holidays (improves seasonal pattern recognition)
- **Revenue data:** Sales revenue in addition to units (enables revenue forecasting)
- **Marketing spend:** Marketing campaign data (helps understand marketing impact on demand)

**Business Impact:**
- More accurate forecasts (especially during promotions and holidays)
- Better understanding of demand patterns
- Revenue forecasting capabilities

**If You Don't Have This:**
- System still works, but forecasts may be less accurate during promotions/holidays
- Revenue forecasting unavailable

---

### 2.2 Supplier Information

**What Helps (If Available):**
- Supplier master data from your ERP (supplier names, contact info)
- Product-supplier relationships (which products come from which suppliers)

**Best Case:** Synced from your ERP system  
**Fallback:** Can be entered manually in our system

**Business Impact:**
- Enables automated purchase order recommendations
- Links products to suppliers for procurement workflows

**If You Don't Have This:**
- System still works for forecasting
- You'll need to enter supplier relationships manually for purchase order features

---

## 3. What We Manage for You (App-Managed)

These are managed entirely within our system. You don't need to provide these from your business systems.

### 3.1 Supplier Ordering Conditions

**What We Manage:**
- Minimum Order Quantities (MOQ) per supplier
- Lead times (how many days it takes to receive orders)
- Supplier-specific pricing (if different from your standard costs)
- Packaging information (units per box, pallet, etc.)
- Primary supplier assignments

**Why We Manage This:**
- These are business rules specific to your procurement process
- Often not stored in ERP systems
- May change frequently based on negotiations
- Varies by supplier and product

**How You Provide:**
- Enter manually in our system
- Import via spreadsheet
- Set defaults per supplier

---

### 3.2 Business Rules & Thresholds

**What We Manage:**
- Safety buffer days (extra days added to lead time for safety)
- Understocked thresholds (when to alert about low stock)
- Overstocked thresholds (when to alert about excess inventory)
- Dead stock rules (when to flag products with no sales)
- Recommendation preferences (which alerts to show to which roles)

**Why We Manage This:**
- These are business-specific rules that vary by company
- May need adjustment based on your risk tolerance
- Different stakeholders may want different alerts

**How You Configure:**
- Settings page in our system
- Per-client configuration
- Can be adjusted anytime

---

## 4. System Integration Requirements

### 4.1 Data Source Options

**What You Need:**
- A data source we can connect to (one of the following):

**Option 1: Data Warehouse (Recommended)**
- BigQuery, Snowflake, Redshift, or similar
- Your sales/inventory data already aggregated here
- Easiest to connect and most reliable

**Option 2: ERP System**
- MetaKocka, SAP, Oracle, or similar
- Direct connection to your operational system
- May require more setup

**Option 3: Database Access**
- Direct database access (PostgreSQL, MySQL, SQL Server)
- Your data stored in a database we can query
- Requires database credentials

**Option 4: API Access**
- REST API to your systems
- Real-time or near-real-time data access
- Requires API credentials

**Option 5: Manual Import (Fallback)**
- Export data from your systems
- Upload to our system manually
- Less automated but works if other options aren't available

---

### 4.2 Data Availability Requirements

**What Must Be Available:**
- **Sales data:** Must be accessible (either in real-time or daily batch)
- **Product data:** Must be accessible (usually changes infrequently)
- **Inventory data:** Must be accessible (preferably daily updates)
- **Location data:** Must be accessible (usually static, changes rarely)

**Data Quality:**
- Data should be reasonably clean (no major gaps or errors)
- Product identifiers should be consistent across systems
- Dates should be accurate (no future dates in history)

**If Data Quality Is Poor:**
- We can help identify and flag issues
- You may need to clean data in your source system first
- Some features may be unavailable until data quality improves

---

## 5. Minimum Viable Setup

### What You Need to Get Started

**Must Have:**
1. ✅ **Sales system** with 30+ days of history
2. ✅ **Product catalog** with SKU identifiers
3. ✅ **Location list** (even if just one location)
4. ✅ **Inventory system** with current stock levels

**Once You Have This:**
- We can connect via ETL
- System generates forecasts
- You get inventory recommendations
- You see stockout risk alerts

**To Unlock Full Features:**
- Add supplier data (for purchase orders)
- Configure supplier conditions (MOQ, lead times)
- Add enhanced sales data (promotions, holidays)
- Configure business rules and thresholds

---

## 6. What Happens During Setup

### 6.1 ETL Connection Setup

**What We Do:**
1. Connect to your data source (BigQuery, ERP, database, etc.)
2. Map your field names to our system
3. Set up daily sync schedule
4. Validate data quality
5. Start syncing data

**What You Provide:**
- Connection credentials (database, API keys, etc.)
- Field mapping (if field names differ)
- Sync schedule preferences

**Timeline:**
- Initial setup: 1-2 business days
- First sync: Usually within 24 hours
- Full historical data: Depends on data volume (typically 1-3 days)

---

### 6.2 Data Validation

**What We Check:**
- Data completeness (all required fields present)
- Data quality (no major gaps or errors)
- Data consistency (product IDs match across tables)
- Historical depth (enough history for forecasting)

**What You Get:**
- Validation report with any issues
- Recommendations for fixing problems
- Data quality score

**If Issues Found:**
- We'll work with you to resolve them
- Some issues can be fixed automatically
- Others may require changes in your source system

---

## 7. Business Process Requirements

### 7.1 What Needs to Be in Place

**Data Collection:**
- Your sales transactions must be recorded (POS, e-commerce, etc.)
- Your inventory must be tracked (warehouse management system, etc.)
- Data must be accessible (in a database, data warehouse, or via API)

**Data Maintenance:**
- Product catalog should be kept up to date
- New products should be added to your system
- Discontinued products should be marked (if applicable)

**Ongoing Operations:**
- Daily sync requires your systems to be accessible
- Data should be updated regularly (daily recommended)

---

### 7.2 What We Handle

**Forecasting:**
- We run forecasts automatically (weekly or on-demand)
- We handle all forecasting calculations
- You just need to review recommendations

**Recommendations:**
- We generate purchase order recommendations
- We calculate inventory metrics (DIR, stockout risk)
- We flag urgent issues

**You Just Need To:**
- Review recommendations
- Approve purchase orders
- Update supplier conditions as needed
- Adjust thresholds based on business needs

---

## 8. Common Business Questions

### Q: What if we don't track sales by location?
**A:** If you have a single location, we can use a default location identifier. If you have multiple locations but don't track sales by location, we can aggregate all sales to a single location, but you'll lose location-specific forecasting capabilities.

### Q: What if our product catalog changes frequently?
**A:** That's fine. As long as your sales data uses consistent product identifiers, we can sync product catalog updates daily. New products will appear in the system after the next sync.

### Q: What if we don't have 2 years of history?
**A:** Minimum is 30 days (3 weeks). System will work with less history, but forecasts will be less accurate. We recommend at least 3 months for reasonable accuracy, and 2 years for best accuracy.

### Q: What if our inventory system isn't real-time?
**A:** Daily updates are fine. We sync inventory daily, so as long as your system updates at least once per day, that's sufficient.

### Q: What if we use multiple systems (different POS, different warehouses)?
**A:** We can connect to multiple data sources. You'll need to provide access to all systems, and we'll aggregate the data. Alternatively, if you have a data warehouse that already aggregates this data, we can connect to that instead.

### Q: What if our data has gaps (missing days)?
**A:** Small gaps (up to 7 consecutive days) are acceptable. Larger gaps may reduce forecast accuracy. We'll flag data quality issues and work with you to resolve them.

### Q: What if we want to add data manually instead of syncing?
**A:** You can enter products, locations, suppliers, and supplier conditions manually in our system. However, sales and inventory data should be synced for best results (manual entry is too time-consuming for daily data).

### Q: What if we're not ready to connect our systems yet?
**A:** You can start by entering supplier conditions and configuring settings. However, you'll need to connect your data sources to get forecasts and recommendations.

---

## 9. Getting Started Checklist

**Before Setup:**
- [ ] Identify your data sources (sales system, inventory system, product catalog)
- [ ] Ensure you have 30+ days of sales history
- [ ] Verify you have product catalog with SKU identifiers
- [ ] List your warehouse/store locations
- [ ] Confirm inventory system tracks current stock levels
- [ ] Decide on data source connection method (data warehouse, ERP, database, API, or manual)

**During Setup:**
- [ ] Provide connection credentials
- [ ] Review field mappings
- [ ] Approve sync schedule
- [ ] Review data validation report
- [ ] Fix any data quality issues

**After Setup:**
- [ ] Configure supplier conditions (MOQ, lead times)
- [ ] Set business rules and thresholds
- [ ] Review first forecast results
- [ ] Adjust settings based on business needs

---

## 10. Support & Next Steps

**Data Integration Support:**
- Our team will help you identify the best connection method
- We'll assist with ETL setup and configuration
- We'll validate your data and flag any issues

**Business Process Support:**
- We'll help you understand forecast results
- We'll guide you on setting thresholds and rules
- We'll train your team on using recommendations

**Next Steps:**
1. Review this document with your team
2. Identify your data sources and systems
3. Contact us to begin ETL setup
4. We'll handle the technical integration

---

**Document Owner:** Product Team  
**Last Updated:** 2025-01-27  
**Related Docs:** [Data Model](./DATA_MODEL.md) (technical details), [System Contracts](./system/CONTRACTS.md) (technical specifications), [Quick Start](./QUICK_START.md) (setup guide)
