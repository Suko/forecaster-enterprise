"""
Validate Forecast Results Script

Validates a forecast run to ensure:
1. Forecast run exists and is completed
2. Forecast results are stored correctly
3. Metrics calculations are correct
4. Data integrity checks

Usage:
    cd backend
    uv run python scripts/validate_forecast_results.py <forecast_run_id>
    
Or validate the latest forecast:
    uv run python scripts/validate_forecast_results.py
"""
import asyncio
import sys
from pathlib import Path
from uuid import UUID
from decimal import Decimal
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import get_async_session_local
from models.client import Client
from models.forecast import ForecastRun, ForecastResult
from services.metrics_service import MetricsService
from forecasting.services.forecast_service import ForecastService
from forecasting.services.data_validator import DataValidator


async def validate_forecast_run(
    db: AsyncSession,
    forecast_run_id: UUID,
    client_id: UUID
) -> dict:
    """Validate a forecast run and its results"""
    validation_report = {
        "forecast_run_id": str(forecast_run_id),
        "client_id": str(client_id),
        "checks": {},
        "errors": [],
        "warnings": [],
        "summary": {}
    }
    
    # Check 1: Forecast run exists and is completed
    print("🔍 Check 1: Forecast Run Status...")
    forecast_run_result = await db.execute(
        select(ForecastRun).where(
            ForecastRun.forecast_run_id == forecast_run_id,
            ForecastRun.client_id == client_id
        )
    )
    forecast_run = forecast_run_result.scalar_one_or_none()
    
    if not forecast_run:
        validation_report["errors"].append(f"Forecast run {forecast_run_id} not found")
        validation_report["checks"]["forecast_run_exists"] = False
        return validation_report
    
    validation_report["checks"]["forecast_run_exists"] = True
    validation_report["checks"]["forecast_run_status"] = forecast_run.status
    
    if forecast_run.status != "completed":
        validation_report["errors"].append(
            f"Forecast run status is '{forecast_run.status}', expected 'completed'"
        )
        if forecast_run.error_message:
            validation_report["errors"].append(f"Error message: {forecast_run.error_message}")
    
    print(f"   ✅ Forecast run found: {forecast_run.status}")
    if forecast_run.recommended_method:
        print(f"   📊 Method: {forecast_run.recommended_method}")
    
    # Check 2: Forecast results exist
    print("\n🔍 Check 2: Forecast Results Storage...")
    results_count = await db.execute(
        select(func.count(ForecastResult.result_id)).where(
            ForecastResult.forecast_run_id == forecast_run_id
        )
    )
    total_results = results_count.scalar()
    
    validation_report["checks"]["total_results"] = total_results
    
    if total_results == 0:
        validation_report["errors"].append("No forecast results found for this run")
        return validation_report
    
    print(f"   ✅ Found {total_results} forecast results")
    
    # Check 3: Get unique items and validate structure
    print("\n🔍 Check 3: Forecast Results Structure...")
    items_result = await db.execute(
        select(
            ForecastResult.item_id,
            func.count(ForecastResult.result_id).label("count"),
            func.min(ForecastResult.date).label("min_date"),
            func.max(ForecastResult.date).label("max_date")
        )
        .where(ForecastResult.forecast_run_id == forecast_run_id)
        .group_by(ForecastResult.item_id)
    )
    items_data = items_result.fetchall()
    
    validation_report["checks"]["items_forecasted"] = len(items_data)
    validation_report["summary"]["items"] = []
    
    for item_id, count, min_date, max_date in items_data:
        item_summary = {
            "item_id": item_id,
            "prediction_count": count,
            "date_range": f"{min_date} to {max_date}"
        }
        validation_report["summary"]["items"].append(item_summary)
        print(f"   📦 {item_id}: {count} predictions ({min_date} to {max_date})")
    
    # Check 4: Validate prediction data quality
    print("\n🔍 Check 4: Prediction Data Quality...")
    predictions_result = await db.execute(
        select(ForecastResult).where(
            ForecastResult.forecast_run_id == forecast_run_id
        ).limit(100)  # Sample for validation
    )
    predictions = predictions_result.scalars().all()
    
    issues = []
    for pred in predictions:
        if pred.point_forecast is None:
            issues.append(f"Null point_forecast for {pred.item_id} on {pred.date}")
        elif pred.point_forecast < 0:
            issues.append(f"Negative forecast for {pred.item_id} on {pred.date}: {pred.point_forecast}")
        if pred.date is None:
            issues.append(f"Null date for prediction {pred.result_id}")
    
    if issues:
        validation_report["warnings"].extend(issues[:10])  # Limit to first 10
        print(f"   ⚠️  Found {len(issues)} data quality issues (showing first 10)")
        for issue in issues[:5]:
            print(f"      - {issue}")
    else:
        print("   ✅ All predictions have valid data")
    
    validation_report["checks"]["data_quality_issues"] = len(issues)
    
    # Check 5: Validate metrics calculations
    print("\n🔍 Check 5: Metrics Calculations...")
    forecast_service = ForecastService(db)
    metrics_service = MetricsService(db)
    
    metrics_validation = []
    for item_id, _, _, _ in items_data[:5]:  # Test first 5 items
        # Get forecast results for this item
        item_results = await forecast_service.get_forecast_results(
            forecast_run_id=str(forecast_run_id)
        )
        
        if item_id not in item_results or not item_results[item_id]:
            metrics_validation.append({
                "item_id": item_id,
                "status": "error",
                "message": "No forecast results found"
            })
            continue
        
        # Calculate forecasted demand 30d
        predictions = item_results[item_id]
        total_forecast = sum(p["point_forecast"] for p in predictions)
        forecasted_demand_30d = Decimal(str(total_forecast))
        
        # Calculate metrics with forecast
        try:
            metrics = await metrics_service.compute_product_metrics(
                client_id=client_id,
                item_id=item_id,
                forecasted_demand_30d=forecasted_demand_30d
            )
            
            # Validate metrics
            metrics_valid = True
            issues = []
            
            if metrics.get("dir") is not None:
                if metrics["dir"] < 0:
                    issues.append("DIR is negative")
                    metrics_valid = False
            
            if metrics.get("stockout_risk") is not None:
                risk = float(metrics["stockout_risk"])
                if risk < 0 or risk > 1:
                    issues.append(f"Stockout risk out of range: {risk} (expected 0-1)")
                    metrics_valid = False
            
            if metrics.get("inventory_value") is not None:
                if metrics["inventory_value"] < 0:
                    issues.append("Inventory value is negative")
                    metrics_valid = False
            
            metrics_validation.append({
                "item_id": item_id,
                "status": "valid" if metrics_valid else "error",
                "dir": float(metrics.get("dir")) if metrics.get("dir") else None,
                "stockout_risk": float(metrics.get("stockout_risk")) if metrics.get("stockout_risk") else None,
                "forecasted_demand_30d": float(forecasted_demand_30d),
                "issues": issues
            })
            
            status_icon = "✅" if metrics_valid else "❌"
            print(f"   {status_icon} {item_id}: DIR={metrics.get('dir')}, Risk={metrics.get('stockout_risk')}")
            if issues:
                for issue in issues:
                    print(f"      ⚠️  {issue}")
        
        except Exception as e:
            metrics_validation.append({
                "item_id": item_id,
                "status": "error",
                "message": str(e)
            })
            print(f"   ❌ {item_id}: Error calculating metrics - {str(e)}")
    
    validation_report["checks"]["metrics_validation"] = metrics_validation
    
    # Summary
    validation_report["summary"]["total_checks"] = len(validation_report["checks"])
    validation_report["summary"]["total_errors"] = len(validation_report["errors"])
    validation_report["summary"]["total_warnings"] = len(validation_report["warnings"])
    validation_report["summary"]["is_valid"] = (
        len(validation_report["errors"]) == 0 and
        forecast_run.status == "completed"
    )
    
    return validation_report


async def main():
    """Main validation function"""
    forecast_run_id_str = sys.argv[1] if len(sys.argv) > 1 else None
    
    print("🔍 Forecast Results Validation")
    print("="*80)
    
    # Get database session
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as db:
        # Get first client
        client_result = await db.execute(select(Client).limit(1))
        client = client_result.scalar_one_or_none()
        
        if not client:
            print("❌ No client found in database")
            return
        
        client_id = client.client_id
        print(f"✅ Using client: {client_id}\n")
        
        # Get forecast_run_id
        if forecast_run_id_str:
            try:
                forecast_run_id = UUID(forecast_run_id_str)
            except ValueError:
                print(f"❌ Invalid forecast_run_id: {forecast_run_id_str}")
                return
        else:
            # Get latest forecast run
            print("📋 Finding latest forecast run...")
            latest_run_result = await db.execute(
                select(ForecastRun)
                .where(ForecastRun.client_id == client_id)
                .order_by(ForecastRun.created_at.desc())
                .limit(1)
            )
            latest_run = latest_run_result.scalar_one_or_none()
            
            if not latest_run:
                print("❌ No forecast runs found for this client")
                return
            
            forecast_run_id = latest_run.forecast_run_id
            print(f"✅ Using latest forecast run: {forecast_run_id}\n")
        
        # Run validation
        validation_report = await validate_forecast_run(
            db, forecast_run_id, client_id
        )
        
        # Print summary
        print("\n" + "="*80)
        print("📋 VALIDATION SUMMARY")
        print("="*80)
        
        if validation_report["summary"]["is_valid"]:
            print("✅ Forecast validation PASSED")
        else:
            print("❌ Forecast validation FAILED")
        
        print(f"\n📊 Statistics:")
        print(f"   Items forecasted: {validation_report['checks'].get('items_forecasted', 0)}")
        print(f"   Total predictions: {validation_report['checks'].get('total_results', 0)}")
        print(f"   Data quality issues: {validation_report['checks'].get('data_quality_issues', 0)}")
        print(f"   Errors: {validation_report['summary']['total_errors']}")
        print(f"   Warnings: {validation_report['summary']['total_warnings']}")
        
        if validation_report["errors"]:
            print(f"\n❌ Errors:")
            for error in validation_report["errors"]:
                print(f"   - {error}")
        
        if validation_report["warnings"]:
            print(f"\n⚠️  Warnings (showing first 5):")
            for warning in validation_report["warnings"][:5]:
                print(f"   - {warning}")
        
        print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(main())

