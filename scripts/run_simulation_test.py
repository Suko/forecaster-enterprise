#!/usr/bin/env python3
"""
Run Simulation Test

Quick script to run a simulation test for a specific product.
"""
import asyncio
import sys
import json
from pathlib import Path
from datetime import date, timedelta

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy.ext.asyncio import AsyncSession
from models.database import get_async_session_local
from schemas.simulation import SimulationRequest, SimulationConfig
from services.simulation_service import SimulationService


async def run_test(item_id: str, start_date: date, end_date: date, client_id: str):
    """Run simulation test"""
    
    print("=" * 80)
    print(f"SIMULATION TEST: {item_id}")
    print("=" * 80)
    print(f"Date Range: {start_date} to {end_date}")
    print(f"Total Days: {(end_date - start_date).days + 1}")
    print(f"Client ID: {client_id}")
    print()
    
    async_session = get_async_session_local()
    
    async with async_session() as db:
        # Create simulation request
        config = SimulationConfig(
            auto_place_orders=True,
            lead_time_buffer_days=0,
            min_order_quantity=1,
            service_level=0.95
        )
        
        request = SimulationRequest(
            client_id=client_id,
            start_date=start_date,
            end_date=end_date,
            item_ids=[item_id],
            simulation_config=config
        )
        
        print("🚀 Starting simulation...")
        print()
        
        # Run simulation
        service = SimulationService(db)
        result = await service.run_simulation(request)
        
        if result.status == "failed":
            print(f"❌ Simulation failed: {result.error_message}")
            return
        
        print("✅ Simulation completed!")
        print()
        
        # Display results
        print("=" * 80)
        print("RESULTS SUMMARY")
        print("=" * 80)
        print()
        
        # Overall metrics
        metrics = result.results
        print("📊 OVERALL METRICS")
        print("-" * 80)
        print(f"Total Days:              {result.total_days}")
        print(f"Items Simulated:         {len(result.item_level_results)}")
        print()
        
        # Stockout metrics
        stockout_rates = metrics.stockout_rate
        print("📉 STOCKOUT RATES")
        print("-" * 80)
        print(f"Simulated Stockout Rate: {stockout_rates.get('simulated', 0) * 100:.2f}%")
        print(f"Real Stockout Rate:      {stockout_rates.get('real', 0) * 100:.2f}%")
        if stockout_rates.get('real', 0) > 0:
            reduction = ((stockout_rates.get('real', 0) - stockout_rates.get('simulated', 0)) / 
                        stockout_rates.get('real', 0) * 100)
            print(f"Reduction:                {reduction:.1f}%")
        print()
        
        # Service level
        service_levels = metrics.service_level
        print("✅ SERVICE LEVELS")
        print("-" * 80)
        print(f"Simulated Service Level: {service_levels.get('simulated', 0) * 100:.2f}%")
        print(f"Real Service Level:      {service_levels.get('real', 0) * 100:.2f}%")
        improvement = (service_levels.get('simulated', 0) - service_levels.get('real', 0)) * 100
        print(f"Improvement:              {improvement:+.2f}%")
        print()
        
        # Inventory value
        inventory_values = metrics.inventory_value
        print("💰 INVENTORY VALUES")
        print("-" * 80)
        sim_val = float(inventory_values.get('simulated', 0))
        real_val = float(inventory_values.get('real', 0))
        print(f"Simulated Avg Value:     ${sim_val:,.2f}")
        print(f"Real Avg Value:           ${real_val:,.2f}")
        if real_val > 0:
            diff = sim_val - real_val
            diff_pct = (diff / real_val * 100)
            print(f"Difference:               ${diff:+,.2f} ({diff_pct:+.1f}%)")
        print()
        
        # Item-level results
        if result.item_level_results:
            print("📦 ITEM-LEVEL RESULTS")
            print("-" * 80)
            for item_result in result.item_level_results:
                print(f"Item: {item_result.item_id}")
                print(f"  Simulated Stockout Rate: {item_result.stockout_rate.get('simulated', 0) * 100:.2f}%")
                print(f"  Real Stockout Rate:      {item_result.stockout_rate.get('real', 0) * 100:.2f}%")
                print(f"  Simulated Service Level: {item_result.service_level.get('simulated', 0) * 100:.2f}%")
                print(f"  Real Service Level:      {item_result.service_level.get('real', 0) * 100:.2f}%")
                print(f"  Orders Placed:           {item_result.total_orders_placed}")
                print()
        
        # Sales Metrics
        if metrics.sales_metrics:
            print("💰 SALES METRICS")
            print("-" * 80)
            sales = metrics.sales_metrics
            actual = float(sales.get("actual_sales", 0))
            potential = float(sales.get("potential_sales", 0))
            lost = float(sales.get("lost_sales", 0))
            additional = float(sales.get("additional_sales_opportunity", 0))
            
            print(f"Actual Sales:             {actual:,.2f} units")
            print(f"Potential Sales:           {potential:,.2f} units")
            print(f"Lost Sales (Stockouts):    {lost:,.2f} units")
            print(f"Additional Sales Opportunity: {additional:,.2f} units")
            if actual > 0:
                increase_pct = (additional / actual) * 100
                print(f"Potential Sales Increase:  {increase_pct:.1f}%")
            print()
        
        # Improvements
        if result.improvements:
            print("📈 IMPROVEMENTS")
            print("-" * 80)
            improvements = result.improvements
            print(f"Stockout Reduction:        {improvements.stockout_reduction * 100:.1f}%")
            print(f"Service Level Improvement: {improvements.service_level_improvement * 100:+.1f}%")
            print(f"Inventory Value Change:    ${float(improvements.cost_savings):+,.2f}")
            print()
        
        # Save results to file
        output_file = f"simulation_results_{item_id}_{start_date}_{end_date}.json"
        output_path = Path(__file__).parent / output_file
        
        result_dict = {
            "simulation_id": result.simulation_id,
            "status": result.status,
            "start_date": str(result.start_date),
            "end_date": str(result.end_date),
            "total_days": result.total_days,
            "item_id": item_id,
            "results": {
                "stockout_rate": stockout_rates,
                "service_level": service_levels,
                "inventory_value": inventory_values
            },
            "item_level_results": [
                {
                    "item_id": r.item_id,
                    "simulated_stockout_rate": r.stockout_rate.get("simulated", 0) * 100,
                    "real_stockout_rate": r.stockout_rate.get("real", 0) * 100,
                    "simulated_service_level": r.service_level.get("simulated", 0) * 100,
                    "real_service_level": r.service_level.get("real", 0) * 100,
                    "total_orders_placed": r.total_orders_placed
                }
                for r in result.item_level_results
            ],
            "improvements": {
                "stockout_reduction": improvements.stockout_reduction * 100 if improvements else None,
                "service_level_improvement": improvements.service_level_improvement * 100 if improvements else None,
                "cost_savings": float(improvements.cost_savings) if improvements else None,
                "inventory_reduction": improvements.inventory_reduction * 100 if improvements else None
            } if result.improvements else None
        }
        
        output_path.write_text(json.dumps(result_dict, indent=2, default=str))
        print(f"💾 Results saved to: {output_file}")
        print()
        
        print("=" * 80)
        print("✅ Test Complete!")
        print("=" * 80)


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run simulation test")
    parser.add_argument("--item-id", default="M5_HOUSEHOLD_1_410", help="Item ID to test")
    parser.add_argument("--start-date", default="2023-01-11", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", default="2024-01-11", help="End date (YYYY-MM-DD)")
    parser.add_argument("--client-id", default="56b5ffb9-c0a3-49c4-acb2-cd0438da3f64", help="Client ID")
    
    args = parser.parse_args()
    
    start_date = date.fromisoformat(args.start_date)
    end_date = date.fromisoformat(args.end_date)
    
    await run_test(args.item_id, start_date, end_date, args.client_id)


if __name__ == "__main__":
    asyncio.run(main())

