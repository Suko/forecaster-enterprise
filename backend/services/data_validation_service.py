"""
Data Validation Service

Consolidates existing validation scripts and adds computed metrics validation.
Reuses:
- forecasting/services/data_validator.py for time series validation
- scripts/check_data_completeness.py for date range validation
- scripts/check_inventory_data.py for DIR prerequisites
"""
from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, and_

from models.product import Product
from models.stock import StockLevel
from models.location import Location
from models.settings import ClientSettings
from models.product_supplier import ProductSupplierCondition
from models.forecast import ForecastRun, ForecastResult
from services.metrics_service import MetricsService
from forecasting.services.data_validator import DataValidator
import pandas as pd


class DataValidationService:
    """Service for comprehensive data validation"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.metrics_service = MetricsService(db)

    async def validate_all(
        self,
        client_id: UUID,
        include_computed_metrics: bool = True,
        include_frontend_consistency: bool = True
    ) -> Dict[str, Any]:
        """
        Run comprehensive data validation

        Returns validation report with:
        - Raw data quality checks
        - Data completeness checks
        - Computed metrics validation (if enabled)
        - Frontend-backend consistency checks (if enabled)
        """
        report = {
            "client_id": str(client_id),
            "validation_timestamp": date.today().isoformat(),
            "raw_data_quality": {},
            "data_completeness": {},
            "computed_metrics": {},
            "frontend_consistency": {},
            "forecast_validation": {},
            "summary": {
                "total_errors": 0,
                "total_warnings": 0,
                "total_info": 0,
                "is_valid": True
            }
        }

        # 1. Raw Data Quality Checks
        raw_quality = await self._validate_raw_data_quality(client_id)
        report["raw_data_quality"] = raw_quality
        report["summary"]["total_errors"] += len(raw_quality.get("errors", []))
        report["summary"]["total_warnings"] += len(raw_quality.get("warnings", []))

        # 2. Data Completeness Checks
        completeness = await self._validate_data_completeness(client_id)
        report["data_completeness"] = completeness
        report["summary"]["total_errors"] += len(completeness.get("errors", []))
        report["summary"]["total_warnings"] += len(completeness.get("warnings", []))

        # 3. Computed Metrics Validation
        if include_computed_metrics:
            computed = await self._validate_computed_metrics(client_id)
            report["computed_metrics"] = computed
            report["summary"]["total_errors"] += len(computed.get("errors", []))
            report["summary"]["total_warnings"] += len(computed.get("warnings", []))

        # 4. Frontend-Backend Consistency Checks
        if include_frontend_consistency:
            consistency = await self._validate_frontend_consistency(client_id)
            report["frontend_consistency"] = consistency
            report["summary"]["total_errors"] += len(consistency.get("errors", []))
            report["summary"]["total_warnings"] += len(consistency.get("warnings", []))

        # 5. Forecast Validation
        forecast_validation = await self._validate_forecasts(client_id)
        report["forecast_validation"] = forecast_validation
        report["summary"]["total_errors"] += len(forecast_validation.get("errors", []))
        report["summary"]["total_warnings"] += len(forecast_validation.get("warnings", []))

        # Final validation status
        report["summary"]["is_valid"] = report["summary"]["total_errors"] == 0

        return report

    async def _validate_raw_data_quality(self, client_id: UUID) -> Dict[str, Any]:
        """Validate raw data quality (dates, formats, ranges)"""
        errors = []
        warnings = []
        info = []

        # Check date ranges in ts_demand_daily
        result = await self.db.execute(
            text("""
                SELECT 
                    MIN(date_local) as min_date,
                    MAX(date_local) as max_date,
                    COUNT(DISTINCT date_local) as day_count,
                    COUNT(*) as total_records
                FROM ts_demand_daily
                WHERE client_id = :client_id
            """),
            {"client_id": str(client_id)}
        )
        date_stats = result.fetchone()

        if date_stats and date_stats[0]:
            min_date = date_stats[0]
            max_date = date_stats[1]
            day_count = date_stats[2]
            total_records = date_stats[3]

            # Check minimum history (3 weeks = 21 days)
            if day_count < 21:
                errors.append(f"Insufficient history: {day_count} days (minimum 21 days required)")

            # Check maximum history (2 years = 730 days)
            if day_count > 730:
                warnings.append(f"Very long history: {day_count} days (recommended max: 730 days)")

            # Check for future dates
            today = date.today()
            if max_date > today:
                errors.append(f"Future dates found: latest date is {max_date} (today is {today})")

            info.append(f"Date range: {min_date} to {max_date} ({day_count} days, {total_records} records)")

        # Check for negative values
        result = await self.db.execute(
            text("""
                SELECT COUNT(*) as negative_count
                FROM ts_demand_daily
                WHERE client_id = :client_id
                  AND units_sold < 0
            """),
            {"client_id": str(client_id)}
        )
        negative_count = result.scalar() or 0
        if negative_count > 0:
            errors.append(f"Found {negative_count} records with negative units_sold")

        # Check item_id format (alphanumeric + underscores, 1-255 chars)
        result = await self.db.execute(
            text("""
                SELECT DISTINCT item_id
                FROM ts_demand_daily
                WHERE client_id = :client_id
                  AND (
                    item_id !~ '^[a-zA-Z0-9_]+$'
                    OR LENGTH(item_id) < 1
                    OR LENGTH(item_id) > 255
                  )
                LIMIT 10
            """),
            {"client_id": str(client_id)}
        )
        invalid_item_ids = [row[0] for row in result.fetchall()]
        if invalid_item_ids:
            errors.append(f"Invalid item_id format found: {invalid_item_ids[:5]}")

        # Check location_id format
        result = await self.db.execute(
            text("""
                SELECT DISTINCT location_id
                FROM ts_demand_daily
                WHERE client_id = :client_id
                  AND (
                    location_id IS NULL
                    OR LENGTH(location_id) < 1
                    OR LENGTH(location_id) > 50
                  )
                LIMIT 10
            """),
            {"client_id": str(client_id)}
        )
        invalid_location_ids = [row[0] for row in result.fetchall()]
        if invalid_location_ids:
            errors.append(f"Invalid location_id found: {invalid_location_ids[:5]}")

        return {
            "errors": errors,
            "warnings": warnings,
            "info": info
        }

    async def _validate_data_completeness(self, client_id: UUID) -> Dict[str, Any]:
        """Validate data completeness (orphaned records, missing relationships)"""
        errors = []
        warnings = []
        info = []

        # Check orphaned item_ids in ts_demand_daily (not in products)
        result = await self.db.execute(
            text("""
                SELECT DISTINCT t.item_id
                FROM ts_demand_daily t
                LEFT JOIN products p ON t.item_id = p.item_id AND t.client_id = p.client_id
                WHERE t.client_id = :client_id
                  AND p.id IS NULL
                LIMIT 10
            """),
            {"client_id": str(client_id)}
        )
        orphaned_item_ids = [row[0] for row in result.fetchall()]
        if orphaned_item_ids:
            errors.append(f"Orphaned item_ids in ts_demand_daily (not in products): {orphaned_item_ids[:5]}")

        # Check orphaned location_ids in ts_demand_daily (not in locations)
        result = await self.db.execute(
            text("""
                SELECT DISTINCT t.location_id
                FROM ts_demand_daily t
                LEFT JOIN locations l ON t.location_id = l.location_id AND t.client_id = l.client_id
                WHERE t.client_id = :client_id
                  AND l.id IS NULL
                LIMIT 10
            """),
            {"client_id": str(client_id)}
        )
        orphaned_location_ids = [row[0] for row in result.fetchall()]
        if orphaned_location_ids:
            errors.append(f"Orphaned location_ids in ts_demand_daily (not in locations): {orphaned_location_ids[:5]}")

        # Check products without stock levels
        result = await self.db.execute(
            text("""
                SELECT COUNT(DISTINCT p.item_id) as products_without_stock
                FROM products p
                LEFT JOIN stock_levels s ON p.item_id = s.item_id AND p.client_id = s.client_id
                WHERE p.client_id = :client_id
                  AND s.id IS NULL
            """),
            {"client_id": str(client_id)}
        )
        products_without_stock = result.scalar() or 0
        if products_without_stock > 0:
            warnings.append(f"{products_without_stock} products have no stock levels")

        # Check products with sales but no stock
        result = await self.db.execute(
            text("""
                SELECT COUNT(DISTINCT t.item_id) as products_with_sales_no_stock
                FROM ts_demand_daily t
                LEFT JOIN stock_levels s ON t.item_id = s.item_id AND t.client_id = s.client_id
                WHERE t.client_id = :client_id
                  AND s.id IS NULL
                LIMIT 10
            """),
            {"client_id": str(client_id)}
        )
        products_with_sales_no_stock = result.scalar() or 0
        if products_with_sales_no_stock > 0:
            warnings.append(f"{products_with_sales_no_stock} products have sales data but no stock levels")

        # Check for missing dates (gaps in time series)
        result = await self.db.execute(
            text("""
                WITH date_range AS (
                    SELECT generate_series(
                        MIN(date_local),
                        MAX(date_local),
                        '1 day'::interval
                    )::date as expected_date
                    FROM ts_demand_daily
                    WHERE client_id = :client_id
                ),
                actual_dates AS (
                    SELECT DISTINCT date_local as actual_date
                    FROM ts_demand_daily
                    WHERE client_id = :client_id
                )
                SELECT COUNT(*) as missing_days
                FROM date_range dr
                LEFT JOIN actual_dates ad ON dr.expected_date = ad.actual_date
                WHERE ad.actual_date IS NULL
            """),
            {"client_id": str(client_id)}
        )
        missing_days = result.scalar() or 0
        if missing_days > 0:
            warnings.append(f"Found {missing_days} missing days in time series (gaps)")

        return {
            "errors": errors,
            "warnings": warnings,
            "info": info
        }

    async def _validate_computed_metrics(self, client_id: UUID) -> Dict[str, Any]:
        """Validate computed metrics (DIR, stockout risk, status, inventory value)"""
        errors = []
        warnings = []
        info = []
        sample_validations = []

        # Get sample products for validation
        result = await self.db.execute(
            select(Product).where(Product.client_id == client_id).limit(10)
        )
        sample_products = result.scalars().all()

        if not sample_products:
            errors.append("No products found for computed metrics validation")
            return {
                "errors": errors,
                "warnings": warnings,
                "info": info,
                "sample_validations": []
            }

        # Get client settings
        settings = await self.metrics_service.get_client_settings(client_id)

        for product in sample_products:
            # Get current stock
            result = await self.db.execute(
                select(StockLevel).where(
                    and_(
                        StockLevel.client_id == client_id,
                        StockLevel.item_id == product.item_id
                    )
                )
            )
            stock_levels = result.scalars().all()
            current_stock = sum(sl.current_stock for sl in stock_levels)

            # Calculate metrics using service
            metrics = await self.metrics_service.compute_product_metrics(
                client_id=client_id,
                item_id=product.item_id
            )

            validation = {
                "item_id": product.item_id,
                "current_stock": current_stock,
                "calculated_metrics": {
                    "dir": float(metrics.get("dir")) if metrics.get("dir") else None,
                    "stockout_risk": float(metrics.get("stockout_risk")) if metrics.get("stockout_risk") else None,
                    "status": metrics.get("status"),
                    "inventory_value": float(metrics.get("inventory_value")) if metrics.get("inventory_value") else None
                },
                "validation_errors": [],
                "validation_warnings": []
            }

            # Validate DIR
            dir_value = metrics.get("dir")
            if current_stock > 0:
                if dir_value is None:
                    validation["validation_warnings"].append("DIR is None but stock > 0 (likely no sales data)")
                elif dir_value < 0:
                    validation["validation_errors"].append(f"DIR is negative: {dir_value}")
            elif current_stock == 0:
                if dir_value is not None and dir_value != 0:
                    validation["validation_warnings"].append(f"Stock is 0 but DIR is {dir_value} (should be 0 or None)")

            # Validate stockout risk (0-1 decimal range)
            risk = metrics.get("stockout_risk")
            if risk is not None:
                if risk < 0 or risk > 1:
                    validation["validation_errors"].append(f"Stockout risk out of range: {risk} (should be 0-1)")
                if current_stock == 0 and risk != 1:
                    validation["validation_errors"].append(f"Stock is 0 but risk is {risk} (should be 1.0)")
            elif current_stock == 0:
                validation["validation_warnings"].append("Stock is 0 but risk is None (should be 1.0)")

            # Validate status
            status = metrics.get("status")
            expected_status = None
            if current_stock <= 0:
                expected_status = "out_of_stock"
            elif dir_value is None:
                expected_status = "unknown"
            elif dir_value < settings.understocked_threshold:
                expected_status = "understocked"
            elif dir_value > settings.overstocked_threshold:
                expected_status = "overstocked"
            else:
                expected_status = "normal"

            if status != expected_status:
                validation["validation_errors"].append(
                    f"Status mismatch: got '{status}', expected '{expected_status}' "
                    f"(DIR={dir_value}, threshold={settings.understocked_threshold}-{settings.overstocked_threshold})"
                )

            # Validate inventory value
            inv_value = metrics.get("inventory_value")
            expected_value = Decimal(current_stock) * product.unit_cost if product.unit_cost else None
            if inv_value is not None and expected_value is not None:
                if abs(float(inv_value) - float(expected_value)) > 0.01:  # Allow small rounding differences
                    validation["validation_errors"].append(
                        f"Inventory value mismatch: got {inv_value}, expected {expected_value} "
                        f"(stock={current_stock}, cost={product.unit_cost})"
                    )

            if validation["validation_errors"]:
                errors.extend([f"{product.item_id}: {e}" for e in validation["validation_errors"]])
            if validation["validation_warnings"]:
                warnings.extend([f"{product.item_id}: {w}" for w in validation["validation_warnings"]])

            sample_validations.append(validation)

        return {
            "errors": errors,
            "warnings": warnings,
            "info": info,
            "sample_validations": sample_validations,
            "samples_checked": len(sample_products)
        }

    async def _validate_frontend_consistency(self, client_id: UUID) -> Dict[str, Any]:
        """Validate frontend-backend consistency (formatting, thresholds)"""
        errors = []
        warnings = []
        info = []

        # Get sample products
        result = await self.db.execute(
            select(Product).where(Product.client_id == client_id).limit(10)
        )
        sample_products = result.scalars().all()

        if not sample_products:
            return {
                "errors": errors,
                "warnings": warnings,
                "info": info
            }

        # Get client settings for thresholds
        settings = await self.metrics_service.get_client_settings(client_id)

        for product in sample_products:
            metrics = await self.metrics_service.compute_product_metrics(
                client_id=client_id,
                item_id=product.item_id
            )

            # Check DIR formatting (frontend expects toFixed(1))
            dir_value = metrics.get("dir")
            if dir_value is not None:
                # Check if DIR is properly formatted (1 decimal place)
                dir_float = float(dir_value)
                dir_formatted = round(dir_float, 1)
                if abs(dir_float - dir_formatted) > 0.05:  # More than 0.05 difference
                    warnings.append(
                        f"{product.item_id}: DIR precision may cause formatting issues "
                        f"(value={dir_float}, formatted={dir_formatted})"
                    )

            # Check stockout risk formatting (frontend expects 0-1 decimal, multiplies by 100 for display)
            risk = metrics.get("stockout_risk")
            if risk is not None:
                risk_float = float(risk)
                if risk_float < 0 or risk_float > 1:
                    errors.append(
                        f"{product.item_id}: Stockout risk out of range: {risk_float} "
                        f"(should be 0-1, frontend multiplies by 100 to show as percentage)"
                    )
                # Backend now returns 0-1 range, frontend multiplies by 100 - this is correct!
                info.append(
                    f"{product.item_id}: Stockout risk format correct: {risk_float} "
                    f"(0-1 range, frontend will display as {risk_float * 100:.1f}%)"
                )

            # Check status values match frontend expectations
            status = metrics.get("status")
            valid_statuses = ["understocked", "overstocked", "normal", "out_of_stock", "unknown"]
            if status and status not in valid_statuses:
                errors.append(
                    f"{product.item_id}: Invalid status '{status}' "
                    f"(frontend expects one of: {valid_statuses})"
                )

            # Check DIR thresholds match frontend cell styling
            # Frontend: DIR < 14 days = red, DIR > 90 days = green
            # Backend: Uses client_settings thresholds
            if dir_value is not None:
                dir_float = float(dir_value)
                if dir_float < 14 and settings.understocked_threshold >= 14:
                    warnings.append(
                        f"{product.item_id}: DIR={dir_float} < 14 (frontend shows red), "
                        f"but backend threshold={settings.understocked_threshold} may differ"
                    )
                if dir_float > 90 and settings.overstocked_threshold <= 90:
                    warnings.append(
                        f"{product.item_id}: DIR={dir_float} > 90 (frontend shows green), "
                        f"but backend threshold={settings.overstocked_threshold} may differ"
                    )

        return {
            "errors": errors,
            "warnings": warnings,
            "info": info
        }

    async def _validate_forecasts(self, client_id: UUID) -> Dict[str, Any]:
        """
        Validate forecast quality and completeness.
        
        Checks:
        - Forecast exists for active products
        - Forecast is recent (< 7 days old)
        - Forecast completeness (all 30 days predicted)
        - Forecast accuracy metrics (if actuals available)
        """
        from datetime import datetime
        
        errors = []
        warnings = []
        info = []
        
        # Get all active products
        products_result = await self.db.execute(
            select(Product).where(Product.client_id == client_id)
        )
        products = products_result.scalars().all()
        item_ids = [p.item_id for p in products]
        
        if not item_ids:
            info.append("No products found - skipping forecast validation")
            return {
                "errors": errors,
                "warnings": warnings,
                "info": info
            }
        
        # Check for latest forecast run
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        forecast_run_result = await self.db.execute(
            select(ForecastRun)
            .where(
                and_(
                    ForecastRun.client_id == client_id,
                    ForecastRun.status == "completed",
                    ForecastRun.created_at >= cutoff_date
                )
            )
            .order_by(ForecastRun.created_at.desc())
            .limit(1)
        )
        forecast_run = forecast_run_result.scalar_one_or_none()
        
        if not forecast_run:
            warnings.append(
                f"No fresh forecast found (last forecast > 7 days old or no forecast exists). "
                f"System will use historical data for metrics."
            )
            return {
                "errors": errors,
                "warnings": warnings,
                "info": info
            }
        
        # Check forecast age
        forecast_age_days = (datetime.utcnow() - forecast_run.created_at).days
        if forecast_age_days >= 7:
            warnings.append(
                f"Forecast is {forecast_age_days} days old (recommended: < 7 days). "
                f"Consider refreshing forecasts."
            )
        else:
            info.append(
                f"Forecast is {forecast_age_days} days old (fresh, < 7 days)"
            )
        
        # Check which items have forecasts
        forecast_item_ids = set(forecast_run.item_ids or [])
        missing_items = set(item_ids) - forecast_item_ids
        
        if missing_items:
            warnings.append(
                f"{len(missing_items)} products missing forecasts: {', '.join(list(missing_items)[:10])}"
                + (f" (and {len(missing_items) - 10} more)" if len(missing_items) > 10 else "")
            )
        
        # Check forecast completeness (all 30 days predicted)
        today = date.today()
        end_date = today + timedelta(days=30)
        method = forecast_run.recommended_method or forecast_run.primary_model
        
        forecast_results = await self.db.execute(
            select(
                ForecastResult.item_id,
                func.count(ForecastResult.date).label("day_count")
            )
            .where(
                and_(
                    ForecastResult.forecast_run_id == forecast_run.forecast_run_id,
                    ForecastResult.method == method,
                    ForecastResult.date >= today,
                    ForecastResult.date < end_date
                )
            )
            .group_by(ForecastResult.item_id)
        )
        
        incomplete_items = []
        for row in forecast_results:
            item_id, day_count = row
            if day_count < 30:
                incomplete_items.append(f"{item_id} ({day_count}/30 days)")
        
        if incomplete_items:
            warnings.append(
                f"{len(incomplete_items)} items have incomplete forecasts: "
                + ", ".join(incomplete_items[:5])
                + (f" (and {len(incomplete_items) - 5} more)" if len(incomplete_items) > 5 else "")
            )
        
        # Check forecast accuracy (if actuals available)
        accuracy_result = await self.db.execute(
            select(func.count(ForecastResult.result_id))
            .where(
                and_(
                    ForecastResult.forecast_run_id == forecast_run.forecast_run_id,
                    ForecastResult.actual_value.isnot(None)
                )
            )
        )
        actuals_count = accuracy_result.scalar() or 0
        
        if actuals_count > 0:
            info.append(
                f"Forecast accuracy tracking: {actuals_count} actual values backfilled. "
                f"Use /api/v1/forecast/forecasts/quality/{{item_id}} to view accuracy metrics."
            )
        else:
            info.append(
                "No actual values backfilled yet. Backfill actuals to track forecast accuracy."
            )
        
        # Summary
        items_with_forecasts = len(forecast_item_ids)
        coverage_pct = (items_with_forecasts / len(item_ids) * 100) if item_ids else 0
        
        if coverage_pct < 50:
            warnings.append(
                f"Low forecast coverage: {coverage_pct:.1f}% of products have forecasts "
                f"({items_with_forecasts}/{len(item_ids)})"
            )
        else:
            info.append(
                f"Forecast coverage: {coverage_pct:.1f}% ({items_with_forecasts}/{len(item_ids)} products)"
            )
        
        return {
            "errors": errors,
            "warnings": warnings,
            "info": info,
            "forecast_run_id": str(forecast_run.forecast_run_id),
            "forecast_age_days": forecast_age_days,
            "coverage_percentage": round(coverage_pct, 1),
            "items_with_forecasts": items_with_forecasts,
            "total_items": len(item_ids)
        }
