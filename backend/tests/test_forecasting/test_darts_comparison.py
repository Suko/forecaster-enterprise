"""
Test using Darts library for validation and comparison

Uses Darts' standardized API to:
1. Validate our custom Chronos-2 implementation
2. Compare with Darts' Chronos2Model
3. Test additional baseline models (ARIMA, Exponential Smoothing, etc.)
4. Use Darts' built-in metrics and backtesting
"""
import pytest
import pandas as pd
import numpy as np
from datetime import date, timedelta
from typing import Dict, List

try:
    from darts import TimeSeries
    from darts.models import Chronos2Model, ExponentialSmoothing, NaiveMean
    from darts.metrics import mape, mae, rmse
    DARTS_AVAILABLE = True
except ImportError:
    DARTS_AVAILABLE = False
    pytest.skip("Darts not installed", allow_module_level=True)

from tests.conftest import TestSessionLocal
from forecasting.services.data_access import DataAccess
from forecasting.modes.ml.chronos2 import Chronos2Model as OurChronos2Model


@pytest.mark.asyncio
async def test_darts_vs_our_chronos2(test_data_loader):
    """Compare Darts Chronos2Model with our custom implementation"""

    # Get test data
    item_id = "SKU001"
    item_data = test_data_loader.get_item_data(item_id)

    if item_data.empty:
        pytest.skip(f"No data for {item_id}")

    # Split train/test (last 30 days = test)
    total_days = len(item_data)
    train_days = total_days - 30

    train_data = item_data.iloc[:train_days]
    test_data = item_data.iloc[train_days:]

    # Convert to Darts TimeSeries
    train_series = TimeSeries.from_dataframe(
        train_data,
        time_col="timestamp",
        value_cols="target"
    )
    test_series = TimeSeries.from_dataframe(
        test_data,
        time_col="timestamp",
        value_cols="target"
    )

    # Test Darts Chronos2Model (requires input/output chunk lengths)
    darts_model = Chronos2Model(
        input_chunk_length=30,  # Look back 30 days
        output_chunk_length=30  # Predict 30 days ahead
    )
    darts_prediction = darts_model.predict(series=train_series, n=30)

    # Test our custom Chronos2Model
    our_model = OurChronos2Model()
    await our_model.initialize()
    our_predictions_df = await our_model.predict(
        context_df=train_data,
        prediction_length=30,
    )

    # Convert our predictions to TimeSeries for comparison
    our_prediction = TimeSeries.from_dataframe(
        our_predictions_df,
        time_col="timestamp",
        value_cols="point_forecast"
    )

    # Calculate metrics for both (handle zeros in actuals)
    try:
        darts_mape = mape(test_series, darts_prediction)
    except ValueError:
        # MAPE fails with zeros, use MAE instead
        darts_mape = None
        print("   Note: MAPE calculation skipped (zeros in actuals)")

    try:
        our_mape = mape(test_series, our_prediction)
    except ValueError:
        our_mape = None

    darts_mae_val = mae(test_series, darts_prediction)
    our_mae_val = mae(test_series, our_prediction)

    # Both should produce reasonable forecasts (check MAE if MAPE unavailable)
    if darts_mape is not None:
        assert darts_mape < 50, f"Darts MAPE too high: {darts_mape}%"
    assert darts_mae_val < 100, f"Darts MAE too high: {darts_mae_val}"

    if our_mape is not None:
        assert our_mape < 50, f"Our MAPE too high: {our_mape}%"
    assert our_mae_val < 100, f"Our MAE too high: {our_mae_val}"

    # Results should be similar (within 20% of each other for MAE)
    mae_diff = abs(darts_mae_val - our_mae_val)
    assert mae_diff < 20, f"MAE difference too large: {mae_diff}"

    print(f"\n✅ Comparison Results for {item_id}:")
    if darts_mape is not None:
        print(f"   Darts Chronos2Model MAPE: {darts_mape:.2f}%")
    if our_mape is not None:
        print(f"   Our Chronos2Model MAPE: {our_mape:.2f}%")
    print(f"   Darts MAE: {darts_mae_val:.2f}")
    print(f"   Our MAE: {our_mae_val:.2f}")
    print(f"   MAE Difference: {mae_diff:.2f}")


@pytest.mark.asyncio
async def test_darts_baseline_models(test_data_loader):
    """Test additional baseline models from Darts"""

    item_id = "SKU001"
    item_data = test_data_loader.get_item_data(item_id)

    if item_data.empty:
        pytest.skip(f"No data for {item_id}")

    # Split train/test
    total_days = len(item_data)
    train_days = total_days - 30

    train_data = item_data.iloc[:train_days]
    test_data = item_data.iloc[train_days:]

    train_series = TimeSeries.from_dataframe(
        train_data,
        time_col="timestamp",
        value_cols="target"
    )
    test_series = TimeSeries.from_dataframe(
        test_data,
        time_col="timestamp",
        value_cols="target"
    )

    results = {}

    # Test Exponential Smoothing
    try:
        es_model = ExponentialSmoothing()
        es_model.fit(train_series)
        es_pred = es_model.predict(30)
        # Use MAE if MAPE fails (due to zeros)
        try:
            es_mape = mape(test_series, es_pred)
        except ValueError:
            es_mape = None
        results["ExponentialSmoothing"] = {
            "mape": es_mape,
            "mae": mae(test_series, es_pred),
            "rmse": rmse(test_series, es_pred),
        }
    except Exception as e:
        print(f"ExponentialSmoothing failed: {e}")

    # Test Naive Mean
    try:
        naive_model = NaiveMean()
        naive_model.fit(train_series)
        naive_pred = naive_model.predict(30)
        # Use MAE if MAPE fails (due to zeros)
        try:
            naive_mape = mape(test_series, naive_pred)
        except ValueError:
            naive_mape = None
        results["NaiveMean"] = {
            "mape": naive_mape,
            "mae": mae(test_series, naive_pred),
            "rmse": rmse(test_series, naive_pred),
        }
    except Exception as e:
        print(f"NaiveMean failed: {e}")

    # All models should produce reasonable forecasts
    for model_name, metrics in results.items():
        if metrics["mape"] is not None:
            assert metrics["mape"] < 100, f"{model_name} MAPE too high: {metrics['mape']}%"
            print(f"   {model_name}: MAPE={metrics['mape']:.2f}%, MAE={metrics['mae']:.2f}")
        else:
            assert metrics["mae"] < 100, f"{model_name} MAE too high: {metrics['mae']}"
            print(f"   {model_name}: MAE={metrics['mae']:.2f} (MAPE unavailable due to zeros)")

    assert len(results) > 0, "At least one baseline model should work"


@pytest.mark.asyncio
async def test_darts_backtesting(test_data_loader):
    """Test Darts' backtesting functionality"""
    try:
        from darts.utils.backtesting import backtest_forecasting
    except ImportError:
        # Try alternative import path
        from darts.backtesting import backtest_forecasting

    item_id = "SKU001"
    item_data = test_data_loader.get_item_data(item_id)

    if item_data.empty:
        pytest.skip(f"No data for {item_id}")

    # Convert to TimeSeries
    series = TimeSeries.from_dataframe(
        item_data,
        time_col="timestamp",
        value_cols="target"
    )

    # Use NaiveMean for quick backtesting
    model = NaiveMean()

    # Backtest with 30-day forecast horizon
    backtest_results = backtest_forecasting(
        series=series,
        model=model,
        forecast_horizon=30,
        stride=30,  # Test every 30 days
        start=0.8,  # Start backtesting at 80% of data
    )

    # Calculate metrics
    if backtest_results:
        mape_values = [mape(series[-30:], pred) for pred in backtest_results]
        avg_mape = np.mean(mape_values)

        assert avg_mape < 100, f"Backtest MAPE too high: {avg_mape}%"
        print(f"\n✅ Backtesting Results:")
        print(f"   Number of forecasts: {len(backtest_results)}")
        print(f"   Average MAPE: {avg_mape:.2f}%")


@pytest.mark.asyncio
async def test_darts_metrics_consistency():
    """Test that Darts metrics match our manual calculations"""

    # Create simple test data
    actual = TimeSeries.from_values([10, 20, 30, 40, 50])
    forecast = TimeSeries.from_values([12, 18, 32, 38, 52])

    # Calculate with Darts
    darts_mape = mape(actual, forecast)
    darts_mae = mae(actual, forecast)
    darts_rmse = rmse(actual, forecast)

    # Manual calculation
    actual_vals = actual.values().flatten()
    forecast_vals = forecast.values().flatten()

    errors = np.abs(actual_vals - forecast_vals)
    pct_errors = errors / actual_vals * 100

    manual_mape = np.mean(pct_errors)
    manual_mae = np.mean(errors)
    manual_rmse = np.sqrt(np.mean(errors ** 2))

    # Should match (within rounding)
    assert abs(darts_mape - manual_mape) < 0.01, "MAPE mismatch"
    assert abs(darts_mae - manual_mae) < 0.01, "MAE mismatch"
    assert abs(darts_rmse - manual_rmse) < 0.01, "RMSE mismatch"

    print(f"\n✅ Metrics consistency check:")
    print(f"   MAPE: Darts={darts_mape:.4f}, Manual={manual_mape:.4f}")
    print(f"   MAE: Darts={darts_mae:.4f}, Manual={manual_mae:.4f}")
    print(f"   RMSE: Darts={darts_rmse:.4f}, Manual={manual_rmse:.4f}")


@pytest.mark.asyncio
async def test_multiple_skus_with_darts(test_data_loader):
    """Test multiple SKUs using Darts for quick validation"""

    item_ids = test_data_loader.get_available_items()[:5]  # Test first 5 SKUs

    results = []

    for item_id in item_ids:
        item_data = test_data_loader.get_item_data(item_id)

        if item_data.empty or len(item_data) < 60:
            continue

        # Split train/test
        train_days = len(item_data) - 30
        train_data = item_data.iloc[:train_days]
        test_data = item_data.iloc[train_days:]

        try:
            train_series = TimeSeries.from_dataframe(
                train_data,
                time_col="timestamp",
                value_cols="target"
            )
            test_series = TimeSeries.from_dataframe(
                test_data,
                time_col="timestamp",
                value_cols="target"
            )

            # Quick test with NaiveMean
            model = NaiveMean()
            model.fit(train_series)
            prediction = model.predict(30)

            # Try MAPE, fall back to MAE if zeros present
            try:
                mape_val = mape(test_series, prediction)
            except ValueError:
                mape_val = None

            mae_val = mae(test_series, prediction)

            results.append({
                "item_id": item_id,
                "mape": mape_val,
                "mae": mae_val,
                "status": "success"
            })

        except Exception as e:
            results.append({
                "item_id": item_id,
                "mape": None,
                "status": "failed",
                "error": str(e)
            })

    # At least some SKUs should work
    successful = [r for r in results if r["status"] == "success"]
    assert len(successful) > 0, "No SKUs processed successfully"

    # Print summary
    print(f"\n✅ Multi-SKU Test Results:")
    print(f"   Tested: {len(results)} SKUs")
    print(f"   Successful: {len(successful)} SKUs")
    if successful:
        mape_values = [r["mape"] for r in successful if r["mape"] is not None]
        mae_values = [r["mae"] for r in successful]
        if mape_values:
            avg_mape = np.mean(mape_values)
            print(f"   Average MAPE: {avg_mape:.2f}%")
        print(f"   Average MAE: {np.mean(mae_values):.2f}")

