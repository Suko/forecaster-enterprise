"""
Simple Forecast Accuracy Test - Minibambini Data

Tests forecasting models directly on cleaned data without database.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import date, timedelta
import sys
import json
import asyncio

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Import models directly (avoid database imports)
from forecasting.modes.statistical.moving_average import MovingAverageModel


# Copy quality calculation functions to avoid database imports
def calculate_mape(actuals: list, forecasts: list) -> float:
    """Calculate Mean Absolute Percentage Error"""
    if len(actuals) != len(forecasts) or len(actuals) == 0:
        return None
    
    errors = []
    for actual, forecast in zip(actuals, forecasts):
        if actual != 0:
            errors.append(abs((actual - forecast) / actual))
    
    if len(errors) == 0:
        return None
    
    return (100.0 / len(errors)) * sum(errors)


def calculate_mae(actuals: list, forecasts: list) -> float:
    """Calculate Mean Absolute Error"""
    if len(actuals) != len(forecasts) or len(actuals) == 0:
        return None
    
    errors = [abs(a - f) for a, f in zip(actuals, forecasts)]
    return sum(errors) / len(errors)


def calculate_rmse(actuals: list, forecasts: list) -> float:
    """Calculate Root Mean Squared Error"""
    if len(actuals) != len(forecasts) or len(actuals) == 0:
        return None
    
    squared_errors = [(a - f) ** 2 for a, f in zip(actuals, forecasts)]
    mse = sum(squared_errors) / len(squared_errors)
    return np.sqrt(mse)


def calculate_bias(actuals: list, forecasts: list) -> float:
    """Calculate Forecast Bias"""
    if len(actuals) != len(forecasts) or len(actuals) == 0:
        return None
    
    errors = [f - a for a, f in zip(actuals, forecasts)]
    return sum(errors) / len(errors)


class ForecastAccuracyTester:
    """Test forecast accuracy on historical data"""
    
    def __init__(self, clean_data_path: str):
        self.clean_data_path = Path(clean_data_path)
        self.df = None
        self.results = []
    
    def load_data(self):
        """Load cleaned data"""
        print(f"Loading cleaned data from {self.clean_data_path}...")
        self.df = pd.read_csv(self.clean_data_path)
        self.df['date_local'] = pd.to_datetime(self.df['date_local'])
        print(f"Loaded {len(self.df):,} rows")
        print(f"Items: {self.df['item_id'].nunique()}")
        print(f"Date range: {self.df['date_local'].min().date()} to {self.df['date_local'].max().date()}")
    
    def select_test_items(self, min_sales: int = 10, min_days: int = 30) -> list:
        """Select items suitable for testing"""
        print(f"\nSelecting test items (min_sales={min_sales}, min_days={min_days})...")
        
        item_stats = self.df.groupby('item_id').agg({
            'units_sold': ['sum', lambda x: (x > 0).sum(), 'count'],
        }).reset_index()
        
        item_stats.columns = ['item_id', 'total_sales', 'days_with_sales', 'total_days']
        item_stats['sales_frequency'] = item_stats['days_with_sales'] / item_stats['total_days'] * 100
        
        # Filter items
        suitable = item_stats[
            (item_stats['total_sales'] >= min_sales) &
            (item_stats['total_days'] >= min_days)
        ].sort_values('total_sales', ascending=False)
        
        print(f"Found {len(suitable)} suitable items")
        if len(suitable) > 0:
            print(f"\nTop items:")
            for idx, row in suitable.head(10).iterrows():
                print(f"  {row['item_id']:40} | Sales: {row['total_sales']:3.0f} | Freq: {row['sales_frequency']:5.1f}% | Days: {row['total_days']:3.0f}")
        
        return suitable['item_id'].head(5).tolist()  # Test top 5
    
    def split_train_test(self, item_id: str, test_days: int = 30):
        """Split data into train/test"""
        item_data = self.df[self.df['item_id'] == item_id].sort_values('date_local')
        
        if len(item_data) < test_days + 30:  # Need at least 30 days for training
            return None, None
        
        # Last test_days for testing
        cutoff_date = item_data['date_local'].max() - timedelta(days=test_days)
        
        train = item_data[item_data['date_local'] <= cutoff_date]
        test = item_data[item_data['date_local'] > cutoff_date]
        
        return train, test
    
    async def test_item_forecast(self, item_id: str, test_days: int = 30):
        """Test forecast for one item"""
        print(f"\n{'='*60}")
        print(f"Testing {item_id}")
        print(f"{'='*60}")
        
        # Split data
        train, test = self.split_train_test(item_id, test_days)
        if train is None or len(train) < 30:
            print(f"  ⚠️  Insufficient data (need 30+ days for training, got {len(train) if train is not None else 0})")
            return None
        
        print(f"  Train: {len(train)} days ({train['date_local'].min().date()} to {train['date_local'].max().date()})")
        print(f"  Test:  {len(test)} days ({test['date_local'].min().date()} to {test['date_local'].max().date()})")
        print(f"  Train sales: {train['units_sold'].sum():.0f} units, Test sales: {test['units_sold'].sum():.0f} units")
        
        # Prepare training data in Chronos-2 format
        train_df = pd.DataFrame({
            'id': item_id,
            'timestamp': train['date_local'],
            'target': train['units_sold']
        })
        
        try:
            # Use MovingAverage model directly
            model = MovingAverageModel(window=7)
            await model.initialize()
            
            # Generate forecast
            predictions_df = await model.predict(
                context_df=train_df,
                prediction_length=test_days,
            )
            
            if predictions_df.empty:
                print(f"  ❌ No predictions generated")
                return None
            
            # Extract predictions
            predictions_df = predictions_df.sort_values('timestamp')
            forecast_values = predictions_df['point_forecast'].head(len(test)).tolist()
            actuals = test['units_sold'].head(len(forecast_values)).tolist()
            
            if len(forecast_values) != len(actuals):
                min_len = min(len(forecast_values), len(actuals))
                forecast_values = forecast_values[:min_len]
                actuals = actuals[:min_len]
                print(f"  ⚠️  Adjusted to {min_len} days for comparison")
            
            # Calculate accuracy metrics
            mape = calculate_mape(actuals, forecast_values)
            mae = calculate_mae(actuals, forecast_values)
            rmse = calculate_rmse(actuals, forecast_values)
            bias = calculate_bias(actuals, forecast_values)
            
            result = {
                'item_id': item_id,
                'train_days': len(train),
                'test_days': len(actuals),
                'train_sales': float(train['units_sold'].sum()),
                'test_sales': float(sum(actuals)),
                'mape': float(mape) if mape else None,
                'mae': float(mae) if mae else None,
                'rmse': float(rmse) if rmse else None,
                'bias': float(bias) if bias else None,
                'avg_actual': float(np.mean(actuals)) if actuals else None,
                'avg_forecast': float(np.mean(forecast_values)) if forecast_values else None,
            }
            
            print(f"  ✅ Results:")
            print(f"     MAPE: {mape:.2f}%" if mape else "     MAPE: N/A")
            print(f"     MAE:  {mae:.2f}" if mae else "     MAE: N/A")
            print(f"     RMSE: {rmse:.2f}" if rmse else "     RMSE: N/A")
            print(f"     Bias: {bias:.2f}" if bias else "     Bias: N/A")
            
            # Status
            if mape and mape < 30:
                print(f"     Status: ✅ GOOD (MAPE < 30%)")
            elif mape and mape < 50:
                print(f"     Status: ⚠️  ACCEPTABLE (MAPE 30-50%)")
            elif mape:
                print(f"     Status: ❌ POOR (MAPE > 50%)")
            
            return result
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def run_tests(self, num_items: int = 5):
        """Run accuracy tests on multiple items"""
        print("=" * 60)
        print("FORECAST ACCURACY TEST - MINIBAMBINI DATA")
        print("=" * 60)
        
        # Load data
        self.load_data()
        
        # Select test items
        test_items = self.select_test_items(min_sales=10, min_days=60)
        
        if not test_items:
            print("\n❌ No suitable items found for testing")
            print("   Try lowering min_sales or min_days criteria")
            return
        
        print(f"\nTesting {len(test_items)} items...")
        
        # Test each item
        for item_id in test_items:
            result = await self.test_item_forecast(item_id, test_days=30)
            if result:
                self.results.append(result)
        
        # Summary
        if self.results:
            print("\n" + "=" * 60)
            print("ACCURACY SUMMARY")
            print("=" * 60)
            
            valid_results = [r for r in self.results if r['mape'] is not None]
            
            if valid_results:
                avg_mape = np.mean([r['mape'] for r in valid_results])
                avg_mae = np.mean([r['mae'] for r in valid_results])
                avg_rmse = np.mean([r['rmse'] for r in valid_results])
                
                print(f"Items tested: {len(valid_results)}")
                print(f"Average MAPE: {avg_mape:.2f}%")
                print(f"Average MAE:  {avg_mae:.2f}")
                print(f"Average RMSE: {avg_rmse:.2f}")
                
                # Best and worst
                best = min(valid_results, key=lambda x: x['mape'])
                worst = max(valid_results, key=lambda x: x['mape'])
                
                print(f"\nBest item:  {best['item_id']} (MAPE: {best['mape']:.2f}%)")
                print(f"Worst item: {worst['item_id']} (MAPE: {worst['mape']:.2f}%)")
                
                # Save results
                with open("forecast_accuracy_results.json", "w") as f:
                    json.dump(self.results, f, indent=2, default=str)
                
                print(f"\n✅ Results saved to forecast_accuracy_results.json")
            else:
                print("❌ No valid results to analyze")
        else:
            print("\n❌ No successful forecasts to analyze")


async def main():
    """Main test function"""
    tester = ForecastAccuracyTester("ts_demand_daily_clean.csv")
    await tester.run_tests(num_items=5)


if __name__ == "__main__":
    asyncio.run(main())
