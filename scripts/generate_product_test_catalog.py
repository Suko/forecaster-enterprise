#!/usr/bin/env python3
"""
Generate Product Test Catalog

Creates a comprehensive document listing all products with their data characteristics
to help identify which products to use for different types of testing scenarios.
"""
import asyncio
import sys
from pathlib import Path
from datetime import date
from collections import defaultdict

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from models.database import get_async_session_local


async def generate_catalog(client_id: str, output_file: str = None):
    """Generate product test catalog"""
    
    async_session = get_async_session_local()
    
    async with async_session() as db:
        # Get comprehensive product analysis
        query = text("""
            SELECT 
                item_id,
                COUNT(*) as total_days,
                COUNT(CASE WHEN stock_on_date = 0 THEN 1 END) as zero_stock_days,
                COUNT(CASE WHEN stock_on_date > 0 THEN 1 END) as in_stock_days,
                ROUND(AVG(units_sold), 2) as avg_daily_sales,
                ROUND(STDDEV(units_sold), 2) as sales_stddev,
                ROUND(MIN(units_sold), 2) as min_sales,
                ROUND(MAX(units_sold), 2) as max_sales,
                ROUND(AVG(stock_on_date), 2) as avg_stock,
                ROUND(MIN(stock_on_date), 2) as min_stock,
                ROUND(MAX(stock_on_date), 2) as max_stock,
                MIN(date_local) as first_date,
                MAX(date_local) as last_date
            FROM ts_demand_daily
            WHERE client_id = :client_id
            GROUP BY item_id
            ORDER BY item_id
        """)
        
        result = await db.execute(query, {"client_id": client_id})
        rows = result.all()
        
        # Categorize products
        products = []
        categories = defaultdict(list)
        
        for row in rows:
            zero_stock_pct = (row.zero_stock_days / row.total_days * 100) if row.total_days > 0 else 0
            cv = (row.sales_stddev / row.avg_daily_sales * 100) if row.avg_daily_sales > 0 else 0
            
            product = {
                'item_id': row.item_id,
                'total_days': row.total_days,
                'zero_stock_days': row.zero_stock_days,
                'zero_stock_pct': zero_stock_pct,
                'avg_sales': row.avg_daily_sales,
                'sales_stddev': row.sales_stddev or 0,
                'cv': cv,
                'min_sales': row.min_sales,
                'max_sales': row.max_sales,
                'avg_stock': row.avg_stock,
                'min_stock': row.min_stock,
                'max_stock': row.max_stock,
                'first_date': row.first_date,
                'last_date': row.last_date,
                'categories': []
            }
            
            # Categorize by stockout rate
            if zero_stock_pct >= 30:
                product['categories'].append('high_stockout')
                categories['high_stockout'].append(product)
            elif zero_stock_pct >= 10:
                product['categories'].append('moderate_stockout')
                categories['moderate_stockout'].append(product)
            elif zero_stock_pct > 0:
                product['categories'].append('low_stockout')
                categories['low_stockout'].append(product)
            else:
                product['categories'].append('no_stockout')
                categories['no_stockout'].append(product)
            
            # Categorize by demand variability
            if cv > 50:
                product['categories'].append('high_variability')
                categories['high_variability'].append(product)
            elif cv < 20 and row.avg_daily_sales > 0:
                product['categories'].append('stable_demand')
                categories['stable_demand'].append(product)
            
            # Categorize by sales volume
            if row.avg_daily_sales >= 10:
                product['categories'].append('high_volume')
                categories['high_volume'].append(product)
            elif row.avg_daily_sales >= 5:
                product['categories'].append('medium_volume')
                categories['medium_volume'].append(product)
            elif row.avg_daily_sales > 0:
                product['categories'].append('low_volume')
                categories['low_volume'].append(product)
            else:
                product['categories'].append('zero_sales')
                categories['zero_sales'].append(product)
            
            # Categorize by stock levels
            if row.avg_stock >= 100:
                product['categories'].append('high_stock')
                categories['high_stock'].append(product)
            elif row.avg_stock < 10:
                product['categories'].append('low_stock')
                categories['low_stock'].append(product)
            
            products.append(product)
        
        # Generate markdown document
        md_content = generate_markdown(client_id, products, categories)
        
        if output_file:
            output_path = Path(output_file)
            output_path.write_text(md_content)
            print(f"✅ Catalog written to: {output_file}")
        else:
            print(md_content)
        
        return products, categories


def generate_markdown(client_id: str, products: list, categories: dict) -> str:
    """Generate markdown catalog"""
    
    md = f"""# Product Test Catalog

**Client ID:** `{client_id}`  
**Generated:** {date.today()}  
**Total Products:** {len(products)}

---

## 📋 Quick Reference by Category

### Stockout Categories

#### High Stockout Rate (≥30% zero stock days)
**Use for:** Testing stockout scenarios, reorder point validation, emergency ordering

| Item ID | Zero Stock % | Avg Sales | Avg Stock | Date Range |
|---------|--------------|-----------|-----------|------------|
"""
    
    for p in sorted(categories.get('high_stockout', []), key=lambda x: x['zero_stock_pct'], reverse=True)[:20]:
        md += f"| `{p['item_id']}` | {p['zero_stock_pct']:.1f}% | {p['avg_sales']:.2f} | {p['avg_stock']:.2f} | {p['first_date']} to {p['last_date']} |\n"
    
    md += f"""
**Total:** {len(categories.get('high_stockout', []))} products

#### Moderate Stockout Rate (10-30% zero stock days)
**Use for:** Testing normal inventory management, occasional stockouts

| Item ID | Zero Stock % | Avg Sales | Avg Stock | Date Range |
|---------|--------------|-----------|-----------|------------|
"""
    
    for p in sorted(categories.get('moderate_stockout', []), key=lambda x: x['zero_stock_pct'], reverse=True)[:20]:
        md += f"| `{p['item_id']}` | {p['zero_stock_pct']:.1f}% | {p['avg_sales']:.2f} | {p['avg_stock']:.2f} | {p['first_date']} to {p['last_date']} |\n"
    
    md += f"""
**Total:** {len(categories.get('moderate_stockout', []))} products

#### Low Stockout Rate (<10% zero stock days)
**Use for:** Testing well-managed inventory, minimal stockout scenarios

**Total:** {len(categories.get('low_stockout', []))} products

#### No Stockout (0% zero stock days)
**Use for:** Testing perfect inventory management, baseline comparisons

**Total:** {len(categories.get('no_stockout', []))} products

---

### Demand Variability Categories

#### High Variability (CV > 50%)
**Use for:** Testing forecast accuracy with volatile demand, seasonal patterns

| Item ID | CV % | Avg Sales | Std Dev | Date Range |
|---------|------|-----------|---------|------------|
"""
    
    for p in sorted(categories.get('high_variability', []), key=lambda x: x['cv'], reverse=True)[:20]:
        md += f"| `{p['item_id']}` | {p['cv']:.1f}% | {p['avg_sales']:.2f} | {p['sales_stddev']:.2f} | {p['first_date']} to {p['last_date']} |\n"
    
    md += f"""
**Total:** {len(categories.get('high_variability', []))} products

#### Stable Demand (CV < 20%)
**Use for:** Testing with predictable demand, baseline scenarios

| Item ID | CV % | Avg Sales | Std Dev | Date Range |
|---------|------|-----------|---------|------------|
"""
    
    for p in sorted(categories.get('stable_demand', []), key=lambda x: x['cv'])[:20]:
        md += f"| `{p['item_id']}` | {p['cv']:.1f}% | {p['avg_sales']:.2f} | {p['sales_stddev']:.2f} | {p['first_date']} to {p['last_date']} |\n"
    
    md += f"""
**Total:** {len(categories.get('stable_demand', []))} products

---

### Sales Volume Categories

#### High Volume (≥10 units/day average)
**Use for:** Testing high-traffic products, bulk ordering scenarios

**Total:** {len(categories.get('high_volume', []))} products

#### Medium Volume (5-10 units/day average)
**Use for:** Testing typical products, standard scenarios

**Total:** {len(categories.get('medium_volume', []))} products

#### Low Volume (<5 units/day average)
**Use for:** Testing slow-moving products, niche items

**Total:** {len(categories.get('low_volume', []))} products

---

## 📊 Complete Product List

| Item ID | Zero Stock % | Avg Sales | CV % | Avg Stock | Categories | Date Range |
|---------|--------------|-----------|------|-----------|------------|------------|
"""
    
    for p in sorted(products, key=lambda x: x['item_id']):
        cats = ', '.join(p['categories'][:3])  # Show first 3 categories
        md += f"| `{p['item_id']}` | {p['zero_stock_pct']:.1f}% | {p['avg_sales']:.2f} | {p['cv']:.1f}% | {p['avg_stock']:.2f} | {cats} | {p['first_date']} to {p['last_date']} |\n"
    
    md += f"""
---

## 🎯 Recommended Test Products by Scenario

### Scenario 1: High Stockout Testing
**Products to use:**
"""
    
    high_stockout = sorted(categories.get('high_stockout', []), key=lambda x: x['zero_stock_pct'], reverse=True)[:5]
    for p in high_stockout:
        md += f"- `{p['item_id']}` - {p['zero_stock_pct']:.1f}% zero stock days, avg sales: {p['avg_sales']:.2f}\n"
    
    md += """
### Scenario 2: Stable Demand Testing
**Products to use:**
"""
    
    stable = sorted(categories.get('stable_demand', []), key=lambda x: x['cv'])[:5]
    for p in stable:
        md += f"- `{p['item_id']}` - CV: {p['cv']:.1f}%, avg sales: {p['avg_sales']:.2f}\n"
    
    md += """
### Scenario 3: High Variability Testing
**Products to use:**
"""
    
    high_var = sorted(categories.get('high_variability', []), key=lambda x: x['cv'], reverse=True)[:5]
    for p in high_var:
        md += f"- `{p['item_id']}` - CV: {p['cv']:.1f}%, avg sales: {p['avg_sales']:.2f}\n"
    
    md += """
### Scenario 4: Perfect Inventory Management
**Products to use:**
"""
    
    no_stockout = categories.get('no_stockout', [])[:5]
    for p in no_stockout:
        md += f"- `{p['item_id']}` - 0% zero stock, avg sales: {p['avg_sales']:.2f}, avg stock: {p['avg_stock']:.2f}\n"
    
    md += """
### Scenario 5: High Volume Products
**Products to use:**
"""
    
    high_vol = sorted(categories.get('high_volume', []), key=lambda x: x['avg_sales'], reverse=True)[:5]
    for p in high_vol:
        md += f"- `{p['item_id']}` - Avg sales: {p['avg_sales']:.2f}/day, avg stock: {p['avg_stock']:.2f}\n"
    
    md += f"""
---

## 📈 Category Statistics

| Category | Count | Description |
|----------|-------|-------------|
| High Stockout | {len(categories.get('high_stockout', []))} | ≥30% zero stock days |
| Moderate Stockout | {len(categories.get('moderate_stockout', []))} | 10-30% zero stock days |
| Low Stockout | {len(categories.get('low_stockout', []))} | <10% zero stock days |
| No Stockout | {len(categories.get('no_stockout', []))} | 0% zero stock days |
| High Variability | {len(categories.get('high_variability', []))} | CV > 50% |
| Stable Demand | {len(categories.get('stable_demand', []))} | CV < 20% |
| High Volume | {len(categories.get('high_volume', []))} | ≥10 units/day |
| Medium Volume | {len(categories.get('medium_volume', []))} | 5-10 units/day |
| Low Volume | {len(categories.get('low_volume', []))} | <5 units/day |

---

## 📝 Notes

- **CV (Coefficient of Variation)**: Standard deviation / mean × 100. Higher CV = more variable demand.
- **Zero Stock %**: Percentage of days where `stock_on_date = 0`
- **Date Range**: First and last date with data for this product
- Products can belong to multiple categories

---

**Last Updated:** {date.today()}
"""
    
    return md


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate product test catalog")
    parser.add_argument("--client-id", required=True, help="Client ID to analyze")
    parser.add_argument("--output", help="Output file path (default: stdout)")
    
    args = parser.parse_args()
    
    await generate_catalog(args.client_id, args.output)


if __name__ == "__main__":
    asyncio.run(main())

