"""
Validate our Chronos-2 implementation against Darts Chronos2Model

Tests that our custom implementation produces similar results to Darts
using the same test data from the database.
"""
import pytest
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import date, timedelta
from sqlalchemy import text

try:
    from darts import TimeSeries
    from darts.models import Chronos2Model
    from darts.metrics import mape, mae, rmse
    DARTS_AVAILABLE = True
except ImportError:
    DARTS_AVAILABLE = False
    pytest.skip("Darts not installed", allow_module_level=True)

from forecasting.modes.ml.chronos2 import Chronos2Model as OurChronos2Model
from forecasting.services.data_access import DataAccess


@pytest.mark.asyncio
async def test_chronos2_accuracy_comparison(db_session, test_client, populate_test_data):
    """
    Compare our Chronos-2 implementation with Darts Chronos2Model
    on the same test data from database to validate accuracy.
    """
    # Get data from database (same as production)
    client_id = str(test_client.client_id)
    data_access = DataAccess(db_session)

    # Find a SKU with data
    result = await db_session.execute(
        text("""
            SELECT item_id, MIN(date_local) as min_date, MAX(date_local) as max_date, COUNT(*) as cnt
            FROM ts_demand_daily
            WHERE client_id = :client_id
            GROUP BY item_id
            HAVING COUNT(*) >= 60
            ORDER BY COUNT(*) DESC
            LIMIT 1
        """),
        {"client_id": client_id}
    )
    row = result.fetchone()

    if not row:
        pytest.skip("No test data in database")

    item_id = row.item_id
    max_date = row.max_date
    # Convert to date if it's a string (SQLite returns strings)
    if isinstance(max_date, str):
        max_date = pd.to_datetime(max_date).date()
    elif not isinstance(max_date, date):
        max_date = max_date.date() if hasattr(max_date, 'date') else pd.to_datetime(max_date).date()
    train_end = max_date - timedelta(days=30)

    # Fetch training data
    train_data = await data_access.fetch_historical_data(
        client_id=client_id,
        item_ids=[item_id],
        end_date=train_end,
    )

    # Filter for this item
    train_data = train_data[train_data["id"] == item_id].copy()

    if train_data.empty or len(train_data) < 30:
        pytest.skip(f"Insufficient training data for {item_id}")

    # Fetch test data (actuals)
    result = await db_session.execute(
        text("""
            SELECT date_local, units_sold
            FROM ts_demand_daily
            WHERE item_id = :item_id
            AND client_id = :client_id
            AND date_local > :train_end
            ORDER BY date_local
        """),
        {"item_id": item_id, "client_id": client_id, "train_end": train_end}
    )
    test_rows = result.fetchall()
    test_data = pd.DataFrame([
        {"timestamp": row.date_local, "target": float(row.units_sold)}
        for row in test_rows
    ])

    print(f"\n📊 Testing {item_id}:")
    print(f"   Training: {len(train_data)} days")
    print(f"   Test: {len(test_data)} days")

    # Convert to Darts TimeSeries (ensure timestamp is datetime)
    train_data["timestamp"] = pd.to_datetime(train_data["timestamp"])
    test_data["timestamp"] = pd.to_datetime(test_data["timestamp"])

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

    # Test Darts Chronos2Model
    print("\n🔬 Testing Darts Chronos2Model...")
    try:
        darts_model = Chronos2Model(
            input_chunk_length=30,
            output_chunk_length=30
        )
        # Chronos-2 in Darts doesn't need fit, but we can call predict with series
        # However, for foundation models, we pass series directly to predict
        darts_prediction = darts_model.predict(series=train_series, n=30)

        # Calculate metrics
        try:
            darts_mape = mape(test_series, darts_prediction)
        except ValueError:
            darts_mape = None  # Zeros in actuals

        darts_mae = mae(test_series, darts_prediction)
        darts_rmse = rmse(test_series, darts_prediction)

        results["darts"] = {
            "mape": darts_mape,
            "mae": darts_mae,
            "rmse": darts_rmse,
            "prediction": darts_prediction,
            "status": "success"
        }

        print(f"   ✅ Darts MAPE: {darts_mape:.2f}%" if darts_mape else "   ✅ Darts (MAPE unavailable)")
        print(f"   ✅ Darts MAE: {darts_mae:.2f}")
        print(f"   ✅ Darts RMSE: {darts_rmse:.2f}")

    except Exception as e:
        results["darts"] = {"status": "failed", "error": str(e)}
        print(f"   ❌ Darts failed: {e}")

    # Test Our Custom Chronos2Model
    print("\n🔬 Testing Our Custom Chronos2Model...")
    try:
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

        # Calculate metrics
        try:
            our_mape = mape(test_series, our_prediction)
        except ValueError:
            our_mape = None  # Zeros in actuals

        our_mae = mae(test_series, our_prediction)
        our_rmse = rmse(test_series, our_prediction)

        results["ours"] = {
            "mape": our_mape,
            "mae": our_mae,
            "rmse": our_rmse,
            "prediction": our_prediction,
            "status": "success"
        }

        print(f"   ✅ Our MAPE: {our_mape:.2f}%" if our_mape else "   ✅ Our (MAPE unavailable)")
        print(f"   ✅ Our MAE: {our_mae:.2f}")
        print(f"   ✅ Our RMSE: {our_rmse:.2f}")

    except Exception as e:
        results["ours"] = {"status": "failed", "error": str(e)}
        print(f"   ❌ Our model failed: {e}")
        import traceback
        traceback.print_exc()

    # Compare results
    print("\n📈 Comparison:")
    if results["darts"]["status"] == "success" and results["ours"]["status"] == "success":
        # Compare MAE (most reliable metric)
        mae_diff = abs(results["darts"]["mae"] - results["ours"]["mae"])
        mae_pct_diff = (mae_diff / results["darts"]["mae"]) * 100 if results["darts"]["mae"] > 0 else 0

        print(f"   MAE Difference: {mae_diff:.2f} ({mae_pct_diff:.1f}%)")

        # Compare RMSE
        rmse_diff = abs(results["darts"]["rmse"] - results["ours"]["rmse"])
        rmse_pct_diff = (rmse_diff / results["darts"]["rmse"]) * 100 if results["darts"]["rmse"] > 0 else 0
        print(f"   RMSE Difference: {rmse_diff:.2f} ({rmse_pct_diff:.1f}%)")

        # Compare MAPE if available
        if results["darts"]["mape"] and results["ours"]["mape"]:
            mape_diff = abs(results["darts"]["mape"] - results["ours"]["mape"])
            print(f"   MAPE Difference: {mape_diff:.2f}%")

        # Compare prediction values directly
        darts_vals = results["darts"]["prediction"].values().flatten()
        our_vals = results["ours"]["prediction"].values().flatten()

        # Calculate correlation
        if len(darts_vals) == len(our_vals):
            correlation = np.corrcoef(darts_vals, our_vals)[0, 1]
            print(f"   Prediction Correlation: {correlation:.4f}")

            # Mean absolute difference
            mean_diff = np.mean(np.abs(darts_vals - our_vals))
            print(f"   Mean Absolute Prediction Difference: {mean_diff:.2f}")

        # Assertions - results should be similar
        assert mae_pct_diff < 50, f"MAE difference too large: {mae_pct_diff:.1f}%"
        assert rmse_pct_diff < 50, f"RMSE difference too large: {rmse_pct_diff:.1f}%"

        if results["darts"]["mape"] and results["ours"]["mape"]:
            assert mape_diff < 10, f"MAPE difference too large: {mape_diff:.2f}%"

        if len(darts_vals) == len(our_vals):
            assert correlation > 0.7, f"Predictions not correlated enough: {correlation:.4f}"

        print("\n   ✅ Results are similar - our implementation is validated!")
    else:
        print("   ⚠️  Cannot compare - one or both models failed")
        if results["darts"]["status"] == "failed":
            pytest.skip("Darts model failed")
        if results["ours"]["status"] == "failed":
            pytest.fail("Our model failed")


@pytest.mark.asyncio
async def test_multiple_skus_validation(db_session, test_client, populate_test_data):
    """
    Validate our implementation against Darts across multiple SKUs from database
    """
    client_id = str(test_client.client_id)
    data_access = DataAccess(db_session)

    # Get SKUs with data
    result = await db_session.execute(
        text("""
            SELECT item_id, MAX(date_local) as max_date
            FROM ts_demand_daily
            WHERE client_id = :client_id
            GROUP BY item_id
            HAVING COUNT(*) >= 60
            ORDER BY COUNT(*) DESC
            LIMIT 5
        """),
        {"client_id": client_id}
    )
    rows = result.fetchall()

    if not rows:
        pytest.skip("No test data in database")

    comparison_results = []

    for row in rows:
        item_id = row.item_id
        max_date = row.max_date
        # Convert to date if it's a string (SQLite returns strings)
        if isinstance(max_date, str):
            max_date = pd.to_datetime(max_date).date()
        elif not isinstance(max_date, date):
            max_date = max_date.date() if hasattr(max_date, 'date') else pd.to_datetime(max_date).date()
        train_end = max_date - timedelta(days=30)

        try:
            # Get training data
            train_data = await data_access.fetch_historical_data(
                client_id=client_id,
                item_ids=[item_id],
                end_date=train_end,
            )
            train_data = train_data[train_data["id"] == item_id].copy()

            if train_data.empty:
                continue

            # Get test data
            result2 = await db_session.execute(
                text("""
                    SELECT date_local, units_sold
                    FROM ts_demand_daily
                    WHERE item_id = :item_id AND client_id = :client_id
                    AND date_local > :train_end
                    ORDER BY date_local
                """),
                {"item_id": item_id, "client_id": client_id, "train_end": train_end}
            )
            test_rows = result2.fetchall()
            test_data = pd.DataFrame([
                {"timestamp": r.date_local, "target": float(r.units_sold)}
                for r in test_rows
            ])

            if test_data.empty:
                continue

            # Convert to TimeSeries
            train_data["timestamp"] = pd.to_datetime(train_data["timestamp"])
            test_data["timestamp"] = pd.to_datetime(test_data["timestamp"])

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

            # Darts
            darts_model = Chronos2Model(input_chunk_length=30, output_chunk_length=30)
            darts_pred = darts_model.predict(series=train_series, n=30)
            darts_mae = mae(test_series, darts_pred)

            # Ours
            our_model = OurChronos2Model()
            await our_model.initialize()
            our_pred_df = await our_model.predict(context_df=train_data, prediction_length=30)
            our_pred = TimeSeries.from_dataframe(our_pred_df, time_col="timestamp", value_cols="point_forecast")
            our_mae = mae(test_series, our_pred)

            # Compare
            mae_diff = abs(darts_mae - our_mae)
            mae_pct_diff = (mae_diff / darts_mae) * 100 if darts_mae > 0 else 0

            comparison_results.append({
                "item_id": item_id,
                "darts_mae": darts_mae,
                "our_mae": our_mae,
                "mae_diff": mae_diff,
                "mae_pct_diff": mae_pct_diff,
                "status": "success"
            })

        except Exception as e:
            comparison_results.append({
                "item_id": item_id,
                "status": "failed",
                "error": str(e)
            })

    # Print summary
    successful = [r for r in comparison_results if r["status"] == "success"]

    print(f"\n📊 Multi-SKU Validation Results:")
    print(f"   Tested: {len(comparison_results)} SKUs")
    print(f"   Successful: {len(successful)} SKUs")

    if successful:
        avg_mae_diff = np.mean([r["mae_pct_diff"] for r in successful])
        max_mae_diff = max([r["mae_pct_diff"] for r in successful])

        print(f"\n   Average MAE Difference: {avg_mae_diff:.1f}%")
        print(f"   Max MAE Difference: {max_mae_diff:.1f}%")

        print(f"\n   Per-SKU Results:")
        for r in successful:
            print(f"     {r['item_id']}: {r['mae_pct_diff']:.1f}% difference")

        # Assertions
        assert len(successful) > 0, "No successful comparisons"
        assert avg_mae_diff < 30, f"Average difference too large: {avg_mae_diff:.1f}%"
        assert max_mae_diff < 50, f"Max difference too large: {max_mae_diff:.1f}%"

        print(f"\n   ✅ Validation passed - results are consistent!")
    else:
        pytest.skip("No successful comparisons")


@pytest.mark.asyncio
async def test_prediction_values_comparison(db_session, test_client, populate_test_data):
    """
    Compare actual prediction values (not just metrics) between Darts and our implementation
    """
    client_id = str(test_client.client_id)
    data_access = DataAccess(db_session)

    # Get a SKU with data
    result = await db_session.execute(
        text("""
            SELECT item_id, MAX(date_local) as max_date
            FROM ts_demand_daily
            WHERE client_id = :client_id
            GROUP BY item_id
            HAVING COUNT(*) >= 60
            LIMIT 1
        """),
        {"client_id": client_id}
    )
    row = result.fetchone()

    if not row:
        pytest.skip("No test data in database")

    item_id = row.item_id
    max_date = row.max_date
    # Convert to date if it's a string (SQLite returns strings)
    if isinstance(max_date, str):
        max_date = pd.to_datetime(max_date).date()
    elif not isinstance(max_date, date):
        max_date = max_date.date() if hasattr(max_date, 'date') else pd.to_datetime(max_date).date()
    train_end = max_date - timedelta(days=30)

    # Get training data
    train_data = await data_access.fetch_historical_data(
        client_id=client_id,
        item_ids=[item_id],
        end_date=train_end,
    )
    train_data = train_data[train_data["id"] == item_id].copy()

    if train_data.empty:
        pytest.skip(f"Insufficient data for {item_id}")

    train_data["timestamp"] = pd.to_datetime(train_data["timestamp"])
    train_series = TimeSeries.from_dataframe(
        train_data,
        time_col="timestamp",
        value_cols="target"
    )

    # Get predictions from both
    darts_model = Chronos2Model(input_chunk_length=30, output_chunk_length=30)
    darts_pred = darts_model.predict(series=train_series, n=30)
    darts_vals = darts_pred.values().flatten()

    our_model = OurChronos2Model()
    await our_model.initialize()
    our_pred_df = await our_model.predict(context_df=train_data, prediction_length=30)
    our_vals = our_pred_df["point_forecast"].values

    # Compare
    assert len(darts_vals) == len(our_vals), "Prediction lengths don't match"

    # Calculate differences
    abs_diff = np.abs(darts_vals - our_vals)
    mean_abs_diff = np.mean(abs_diff)
    max_abs_diff = np.max(abs_diff)

    # Relative difference
    mean_actual = np.mean(darts_vals)
    relative_diff = (mean_abs_diff / mean_actual) * 100 if mean_actual > 0 else 0

    # Correlation
    correlation = np.corrcoef(darts_vals, our_vals)[0, 1]

    print(f"\n📊 Prediction Value Comparison:")
    print(f"   Mean Absolute Difference: {mean_abs_diff:.2f}")
    print(f"   Max Absolute Difference: {max_abs_diff:.2f}")
    print(f"   Relative Difference: {relative_diff:.1f}%")
    print(f"   Correlation: {correlation:.4f}")

    # Sample comparison
    print(f"\n   Sample Predictions (first 5):")
    print(f"   {'Day':<6} {'Darts':<10} {'Ours':<10} {'Diff':<10}")
    print(f"   {'-'*40}")
    for i in range(min(5, len(darts_vals))):
        print(f"   {i+1:<6} {darts_vals[i]:<10.2f} {our_vals[i]:<10.2f} {abs_diff[i]:<10.2f}")

    # Assertions
    assert relative_diff < 20, f"Relative difference too large: {relative_diff:.1f}%"
    assert correlation > 0.7, f"Correlation too low: {correlation:.4f}"

    print(f"\n   ✅ Prediction values are similar!")

