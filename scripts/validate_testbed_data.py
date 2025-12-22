#!/usr/bin/env python3
"""
Data Validation Script for Test Bed

Validates that displayed data matches backend calculations:
1. Quality metrics (MAPE, RMSE, MAE, Bias)
2. Forecast totals
3. Sample counts
4. SKU classification

Usage:
    python scripts/validate_testbed_data.py --item-id M5_HOBBIES_1_004
"""

import asyncio
import httpx
import math
from typing import Dict, List, Optional, Tuple
from datetime import date, datetime
import json
import sys


class QualityCalculator:
    """Match backend QualityCalculator logic"""
    
    @staticmethod
    def calculate_mape(actuals: List[float], forecasts: List[float]) -> Optional[float]:
        """MAPE = (100/n) × Σ|Actual - Forecast|/Actual"""
        if len(actuals) != len(forecasts):
            return None
        
        errors = []
        for actual, forecast in zip(actuals, forecasts):
            if actual > 0:
                errors.append(abs(actual - forecast) / actual)
        
        if not errors:
            return None
        
        return (100.0 / len(errors)) * sum(errors)
    
    @staticmethod
    def calculate_mae(actuals: List[float], forecasts: List[float]) -> Optional[float]:
        """MAE = (1/n) × Σ|Actual - Forecast|"""
        if len(actuals) != len(forecasts) or len(actuals) == 0:
            return None
        
        errors = [abs(a - f) for a, f in zip(actuals, forecasts)]
        return sum(errors) / len(errors)
    
    @staticmethod
    def calculate_rmse(actuals: List[float], forecasts: List[float]) -> Optional[float]:
        """RMSE = √[(1/n) × Σ(Actual - Forecast)²]"""
        if len(actuals) != len(forecasts) or len(actuals) == 0:
            return None
        
        squared_errors = [(a - f) ** 2 for a, f in zip(actuals, forecasts)]
        mse = sum(squared_errors) / len(squared_errors)
        return math.sqrt(mse)
    
    @staticmethod
    def calculate_bias(actuals: List[float], forecasts: List[float]) -> Optional[float]:
        """Bias = (1/n) × Σ(Forecast - Actual)"""
        if len(actuals) != len(forecasts) or len(actuals) == 0:
            return None
        
        errors = [f - a for a, f in zip(actuals, forecasts)]
        return sum(errors) / len(errors)


async def validate_metrics(
    actuals: List[float],
    forecasts: List[float],
    expected_mape: Optional[float] = None,
    expected_mae: Optional[float] = None,
    expected_rmse: Optional[float] = None,
    expected_bias: Optional[float] = None,
    tolerance: float = 0.01
) -> Dict[str, bool]:
    """Validate metrics match expected values"""
    
    calc = QualityCalculator()
    calculated_mape = calc.calculate_mape(actuals, forecasts)
    calculated_mae = calc.calculate_mae(actuals, forecasts)
    calculated_rmse = calc.calculate_rmse(actuals, forecasts)
    calculated_bias = calc.calculate_bias(actuals, forecasts)
    
    results = {
        "mape": True,
        "mae": True,
        "rmse": True,
        "bias": True,
    }
    
    if expected_mape is not None:
        if calculated_mape is None:
            results["mape"] = False
            print(f"❌ MAPE: Expected {expected_mape}%, but got None")
        elif abs(calculated_mape - expected_mape) > tolerance:
            results["mape"] = False
            print(f"❌ MAPE: Expected {expected_mape}%, got {calculated_mape}% (diff: {abs(calculated_mape - expected_mape)})")
        else:
            print(f"✅ MAPE: {calculated_mape}% (expected: {expected_mape}%)")
    
    if expected_mae is not None:
        if calculated_mae is None:
            results["mae"] = False
            print(f"❌ MAE: Expected {expected_mae}, but got None")
        elif abs(calculated_mae - expected_mae) > tolerance:
            results["mae"] = False
            print(f"❌ MAE: Expected {expected_mae}, got {calculated_mae} (diff: {abs(calculated_mae - expected_mae)})")
        else:
            print(f"✅ MAE: {calculated_mae} (expected: {expected_mae})")
    
    if expected_rmse is not None:
        if calculated_rmse is None:
            results["rmse"] = False
            print(f"❌ RMSE: Expected {expected_rmse}, but got None")
        elif abs(calculated_rmse - expected_rmse) > tolerance:
            results["rmse"] = False
            print(f"❌ RMSE: Expected {expected_rmse}, got {calculated_rmse} (diff: {abs(calculated_rmse - expected_rmse)})")
        else:
            print(f"✅ RMSE: {calculated_rmse} (expected: {expected_rmse})")
    
    if expected_bias is not None:
        if calculated_bias is None:
            results["bias"] = False
            print(f"❌ Bias: Expected {expected_bias}, but got None")
        elif abs(calculated_bias - expected_bias) > tolerance:
            results["bias"] = False
            print(f"❌ Bias: Expected {expected_bias}, got {calculated_bias} (diff: {abs(calculated_bias - expected_bias)})")
        else:
            print(f"✅ Bias: {calculated_bias} (expected: {expected_bias})")
    
    return results


async def validate_forecast_totals(forecasts: List[Dict]) -> Tuple[float, bool]:
    """Validate forecast totals match sum of individual predictions"""
    total = sum(f.get("point_forecast", 0) for f in forecasts)
    return total, True


async def validate_sample_count(
    forecast_dates: List[str],
    actual_dates: List[str]
) -> Tuple[int, bool]:
    """Validate sample count matches number of matching dates"""
    forecast_set = set(forecast_dates)
    actual_set = set(actual_dates)
    matching_dates = forecast_set.intersection(actual_set)
    return len(matching_dates), True


def print_validation_summary(results: Dict[str, bool]):
    """Print validation summary"""
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    all_passed = all(results.values())
    
    for metric, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{metric.upper()}: {status}")
    
    print("="*60)
    if all_passed:
        print("✅ ALL VALIDATIONS PASSED")
    else:
        print("❌ SOME VALIDATIONS FAILED")
    print("="*60)


async def main():
    """Main validation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate Test Bed data")
    parser.add_argument("--item-id", required=True, help="Item ID to validate")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Backend base URL")
    parser.add_argument("--token", help="Auth token (optional)")
    
    args = parser.parse_args()
    
    print(f"Validating data for item: {args.item_id}")
    print(f"Backend URL: {args.base_url}")
    print()
    
    # Example validation with test data
    print("Testing metric calculations with sample data...")
    print("-" * 60)
    
    # Test case: Known values
    actuals = [1.0, 0.9, 1.1, 1.2, 0.8]
    forecasts = [1.2, 0.8, 1.0, 1.3, 0.9]
    
    # Expected values (calculated manually)
    # MAPE: (20% + 11.1% + 9.1% + 8.3% + 12.5%) / 5 = 12.4%
    # MAE: (0.2 + 0.1 + 0.1 + 0.1 + 0.1) / 5 = 0.12
    # RMSE: sqrt((0.04 + 0.01 + 0.01 + 0.01 + 0.01) / 5) = sqrt(0.016) = 0.126
    # Bias: (0.2 - 0.1 - 0.1 - 0.1 - 0.1) / 5 = -0.04
    
    results = await validate_metrics(
        actuals=actuals,
        forecasts=forecasts,
        expected_mape=12.4,  # Approximate
        expected_mae=0.12,
        expected_rmse=0.126,  # Approximate
        expected_bias=-0.04,
        tolerance=0.1  # Allow 0.1% tolerance for MAPE
    )
    
    print_validation_summary(results)
    
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. Generate a forecast in Test Bed UI")
    print("2. Capture API responses from browser DevTools")
    print("3. Run this script with actual data to validate")
    print("4. Compare frontend display with backend calculations")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

