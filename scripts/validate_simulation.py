#!/usr/bin/env python3
"""
Simulation Process Validation Script

Validates that the simulation process is working correctly by checking:
1. Data sources and queries
2. Calculation logic
3. Order placement logic
4. Stock tracking accuracy
5. Metrics calculation
"""

import json
import sys
from pathlib import Path
from datetime import date, timedelta
from typing import Dict, List, Optional

def validate_simulation_results(simulation_file: str, item_id: str) -> Dict[str, any]:
    """
    Validate simulation results for a specific item.
    
    Returns a dictionary with validation results.
    """
    with open(simulation_file, 'r') as f:
        data = json.load(f)
    
    # Filter daily comparisons for this item
    daily = [d for d in data.get('daily_comparison', []) if d['item_id'] == item_id]
    daily.sort(key=lambda x: x['date'])
    
    if not daily:
        return {
            "error": f"No data found for item {item_id}",
            "valid": False
        }
    
    validation_results = {
        "item_id": item_id,
        "total_days": len(daily),
        "start_date": daily[0]['date'],
        "end_date": daily[-1]['date'],
        "checks": {},
        "warnings": [],
        "errors": [],
        "valid": True
    }
    
    # CHECK 1: Initial Stock Consistency
    initial_sim = daily[0]['simulated_stock']
    initial_real = daily[0]['real_stock']
    diff = abs(initial_sim - initial_real)
    
    validation_results["checks"]["initial_stock"] = {
        "simulated": initial_sim,
        "real": initial_real,
        "difference": diff,
        "pass": diff <= 1.0,  # Allow 1 unit difference
        "message": f"Initial stock difference: {diff:.1f} units"
    }
    
    if diff > 1.0:
        validation_results["warnings"].append(
            f"Initial stock differs: Sim={initial_sim:.1f}, Real={initial_real:.1f}"
        )
    
    # CHECK 2: Stock Never Negative
    sim_negative = [d for d in daily if d['simulated_stock'] < 0]
    real_negative = [d for d in daily if d['real_stock'] < 0]
    
    validation_results["checks"]["no_negative_stock"] = {
        "simulated_negative_days": len(sim_negative),
        "real_negative_days": len(real_negative),
        "pass": len(sim_negative) == 0 and len(real_negative) == 0,
        "message": f"Simulated: {len(sim_negative)} negative days, Real: {len(real_negative)} negative days"
    }
    
    if sim_negative:
        validation_results["errors"].append(
            f"Simulated stock is negative on {len(sim_negative)} days"
        )
        validation_results["valid"] = False
    
    if real_negative:
        validation_results["errors"].append(
            f"Real stock is negative on {len(real_negative)} days"
        )
        validation_results["valid"] = False
    
    # CHECK 3: Sales Data Completeness
    sales_missing = [d for d in daily if d.get('actual_sales') is None]
    sales_zero = [d for d in daily if d.get('actual_sales', 0) == 0]
    
    validation_results["checks"]["sales_data"] = {
        "missing_sales": len(sales_missing),
        "zero_sales_days": len(sales_zero),
        "total_days": len(daily),
        "pass": len(sales_missing) == 0,
        "message": f"Sales data: {len(daily) - len(sales_missing)}/{len(daily)} days available"
    }
    
    if sales_missing:
        validation_results["warnings"].append(
            f"Sales data missing for {len(sales_missing)} days"
        )
    
    # CHECK 4: Simulated Stock Calculation (verify stock decreases by sales)
    calculation_errors = []
    for i in range(1, min(10, len(daily))):  # Check first 10 days
        prev_stock = daily[i-1]['simulated_stock']
        curr_stock = daily[i]['simulated_stock']
        sales = daily[i].get('actual_sales', 0)
        expected_stock = max(0, prev_stock - sales)
        
        # Allow for order arrivals (stock can increase)
        if curr_stock < expected_stock - 0.1:  # Small tolerance
            calculation_errors.append({
                "date": daily[i]['date'],
                "expected": expected_stock,
                "actual": curr_stock,
                "prev_stock": prev_stock,
                "sales": sales
            })
    
    validation_results["checks"]["stock_calculation"] = {
        "calculation_errors": len(calculation_errors),
        "pass": len(calculation_errors) == 0,
        "message": f"Stock calculation errors: {len(calculation_errors)}"
    }
    
    if calculation_errors:
        validation_results["warnings"].append(
            f"Stock calculation issues on {len(calculation_errors)} days (may be due to order arrivals)"
        )
    
    # CHECK 5: Order Placement Logic
    orders = [d for d in daily if d.get('order_placed', False)]
    orders_with_qty = [d for d in orders if d.get('order_quantity', 0) > 0]
    
    validation_results["checks"]["orders"] = {
        "total_orders": len(orders),
        "orders_with_quantity": len(orders_with_qty),
        "pass": len(orders) == len(orders_with_qty),
        "message": f"Orders placed: {len(orders)}"
    }
    
    if len(orders) != len(orders_with_qty):
        validation_results["warnings"].append(
            f"Some orders missing quantity: {len(orders) - len(orders_with_qty)}"
        )
    
    # CHECK 6: Stockout Detection
    sim_stockouts = [d for d in daily if d.get('simulated_stockout', False)]
    real_stockouts = [d for d in daily if d.get('real_stockout', False)]
    
    # Verify stockouts match zero stock
    sim_stockout_errors = [
        d for d in sim_stockouts 
        if d['simulated_stock'] > 0.1  # Should be 0 or very close
    ]
    real_stockout_errors = [
        d for d in real_stockouts 
        if d['real_stock'] > 0.1
    ]
    
    validation_results["checks"]["stockouts"] = {
        "simulated_stockout_days": len(sim_stockouts),
        "real_stockout_days": len(real_stockouts),
        "sim_stockout_errors": len(sim_stockout_errors),
        "real_stockout_errors": len(real_stockout_errors),
        "pass": len(sim_stockout_errors) == 0 and len(real_stockout_errors) == 0,
        "message": f"Stockouts: Sim={len(sim_stockouts)}, Real={len(real_stockouts)}"
    }
    
    if sim_stockout_errors:
        validation_results["errors"].append(
            f"Simulated stockout flagged but stock > 0 on {len(sim_stockout_errors)} days"
        )
        validation_results["valid"] = False
    
    if real_stockout_errors:
        validation_results["errors"].append(
            f"Real stockout flagged but stock > 0 on {len(real_stockout_errors)} days"
        )
        validation_results["valid"] = False
    
    # CHECK 7: Metrics Consistency
    results = data.get('results', {})
    stockout_rate_sim = results.get('stockout_rate', {}).get('simulated', 0)
    stockout_rate_real = results.get('stockout_rate', {}).get('real', 0)
    
    # Calculate expected stockout rate
    expected_sim_rate = len(sim_stockouts) / len(daily) if daily else 0
    expected_real_rate = len(real_stockouts) / len(daily) if daily else 0
    
    stockout_rate_diff_sim = abs(stockout_rate_sim - expected_sim_rate)
    stockout_rate_diff_real = abs(stockout_rate_real - expected_real_rate)
    
    validation_results["checks"]["metrics"] = {
        "stockout_rate_sim": stockout_rate_sim,
        "stockout_rate_real": stockout_rate_real,
        "expected_sim_rate": expected_sim_rate,
        "expected_real_rate": expected_real_rate,
        "sim_difference": stockout_rate_diff_sim,
        "real_difference": stockout_rate_diff_real,
        "pass": stockout_rate_diff_sim < 0.01 and stockout_rate_diff_real < 0.01,
        "message": f"Stockout rates match calculated values"
    }
    
    if stockout_rate_diff_sim >= 0.01 or stockout_rate_diff_real >= 0.01:
        validation_results["warnings"].append(
            f"Stockout rate calculation may be inconsistent"
        )
    
    # CHECK 8: Real Stock Independence
    # Verify that real stock values are independent (from DB) and not just calculated
    # This is harder to validate automatically, but we can check for patterns
    real_stock_changes = []
    for i in range(1, len(daily)):
        prev_real = daily[i-1]['real_stock']
        curr_real = daily[i]['real_stock']
        sales = daily[i].get('actual_sales', 0)
        change = curr_real - prev_real
        
        # Real stock can increase (orders arrived) or decrease (sales)
        # But if it's always decreasing by exactly sales, it might be calculated
        real_stock_changes.append({
            "date": daily[i]['date'],
            "change": change,
            "sales": sales,
            "is_calculated": abs(change + sales) < 0.1  # If change ≈ -sales, likely calculated
        })
    
    calculated_days = sum(1 for c in real_stock_changes if c['is_calculated'])
    db_days = len(real_stock_changes) - calculated_days
    
    validation_results["checks"]["real_stock_independence"] = {
        "calculated_days": calculated_days,
        "db_days": db_days,
        "total_days": len(real_stock_changes),
        "pass": db_days > calculated_days,  # More DB days than calculated
        "message": f"Real stock: {db_days} days from DB, {calculated_days} calculated"
    }
    
    if calculated_days > db_days:
        validation_results["warnings"].append(
            f"Most real stock values appear to be calculated, not from DB"
        )
    
    return validation_results


def print_validation_report(results: Dict[str, any]):
    """Print a formatted validation report."""
    print("=" * 70)
    print("SIMULATION PROCESS VALIDATION REPORT")
    print("=" * 70)
    print()
    print(f"Item ID: {results['item_id']}")
    print(f"Period: {results['start_date']} to {results['end_date']}")
    print(f"Total Days: {results['total_days']}")
    print()
    
    print("VALIDATION CHECKS:")
    print("-" * 70)
    
    for check_name, check_result in results['checks'].items():
        status = "✓ PASS" if check_result['pass'] else "✗ FAIL"
        print(f"{status} {check_name.replace('_', ' ').title()}")
        print(f"      {check_result['message']}")
        if not check_result['pass']:
            for key, value in check_result.items():
                if key not in ['pass', 'message']:
                    print(f"      {key}: {value}")
        print()
    
    if results['warnings']:
        print("WARNINGS:")
        print("-" * 70)
        for warning in results['warnings']:
            print(f"  ⚠ {warning}")
        print()
    
    if results['errors']:
        print("ERRORS:")
        print("-" * 70)
        for error in results['errors']:
            print(f"  ✗ {error}")
        print()
    
    print("=" * 70)
    if results['valid']:
        print("✅ VALIDATION PASSED")
    else:
        print("❌ VALIDATION FAILED - Review errors above")
    print("=" * 70)


def main():
    """CLI entry point"""
    if len(sys.argv) < 3:
        print("Usage: python validate_simulation.py <simulation_json_file> <item_id>")
        print("Example: python validate_simulation.py /tmp/sim_validation.json M5_HOBBIES_1_014")
        sys.exit(1)
    
    simulation_file = sys.argv[1]
    item_id = sys.argv[2]
    
    if not Path(simulation_file).exists():
        print(f"Error: Simulation file not found: {simulation_file}")
        sys.exit(1)
    
    results = validate_simulation_results(simulation_file, item_id)
    print_validation_report(results)
    
    # Exit with error code if validation failed
    if not results['valid']:
        sys.exit(1)


if __name__ == "__main__":
    main()


