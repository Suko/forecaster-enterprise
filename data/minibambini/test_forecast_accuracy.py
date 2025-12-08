"""
Test Forecast Accuracy on Minibambini Cleaned Data

Tests forecasting system on cleaned ETL data to validate accuracy.
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

from forecasting.services.forecast_service import ForecastService
from forecasting.services.quality_calculator import QualityCalculator
from models.forecast import ForecastStatus
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models.database import Base, create_tables


class MinibambiniDataLoader:
    """Load cleaned minibambini data for forecasting"""
    
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.df = None
    
    def load_data(self):
        """Load cleaned CSV data"""
        print(f"Loading cleaned data from {self.csv_path}...")
        self.df = pd.read_csv(self.csv_path)
        self.df['date_local'] = pd.to_datetime(self.df['date_local'])
        print(f"Loaded {len(self.df):,} rows")
        return self.df
    
    def get_item_data(self, item_id: str, start_date: date = None, end_date: date = None):
        """Get data for specific item in Chronos-2 format"""
        item_data = self.df[self.df['item_id'] == item_id].copy()
        
        if start_date:
            item_data = item_data[item_data['date_local'] >= pd.Timestamp(start_date)]
        if end_date:
            item_data = item_data[item_data['date_local'] <= pd.Timestamp(end_date)]
        
        # Transform to Chronos-2 format
        result = pd.DataFrame({
            'id': item_id,
            'timestamp': item_data['date_local'],
            'target': item_data['units_sold']
        })
        
        return result.sort_values('timestamp')
    
    def get_available_items(self):
        """Get list of available item IDs"""
        return self.df['item_id'].unique().tolist()


class ForecastAccuracyTester:
    """Test forecast accuracy on historical data"""
    
    def __init__(self, clean_data_path: str, db_session: AsyncSession):
        self.data_loader = MinibambiniDataLoader(clean_data_path)
        self.db = db_session
        self.results = []
    
    def load_data(self):
        """Load cleaned data"""
        self.data_loader.load_data()
    
    def select_test_items(self, min_sales: int = 10, min_days: int = 30) -> list:
        """Select items suitable for testing"""
        print(f"\nSelecting test items (min_sales={min_sales}, min_days={min_days})...")
        
        df = self.data_loader.df
        item_stats = df.groupby('item_id').agg({
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
        item_data = self.data_loader.get_item_data(item_id)
        
        if len(item_data) < test_days + 30:  # Need at least 30 days for training
            return None, None
        
        # Last test_days for testing
        cutoff_date = item_data['timestamp'].max() - timedelta(days=test_days)
        
        train = item_data[item_data['timestamp'] <= cutoff_date]
        test = item_data[item_data['timestamp'] > cutoff_date]
        
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
        
        print(f"  Train: {len(train)} days ({train['timestamp'].min().date()} to {train['timestamp'].max().date()})")
        print(f"  Test:  {len(test)} days ({test['timestamp'].min().date()} to {test['timestamp'].max().date()})")
        print(f"  Train sales: {train['target'].sum():.0f} units, Test sales: {test['target'].sum():.0f} units")
        
        # Save train data to temp CSV for DataAccess to use
        temp_csv = Path(__file__).parent / "temp_train_data.csv"
        train.to_csv(temp_csv, index=False)
        
        try:
            # Create service with custom data loader
            # For now, we'll manually prepare the data
            service = ForecastService(self.db, use_test_data=False)
            
            # We need to inject the training data
            # Since DataAccess expects database or test_data=True, we'll use a workaround
            # Create a custom data access that uses our CSV
            
            # Actually, let's use the test_data approach but with our cleaned data
            # We'll modify the approach to use the cleaned CSV directly
            
            # For this test, let's use the statistical MA7 model directly
            from forecasting.modes.statistical.moving_average import MovingAverageModel
            
            model = MovingAverageModel(window=7)
            await model.initialize()
            
            # Generate forecast
            predictions_df = await model.predict(
                context_df=train,
                prediction_length=test_days,
            )
            
            if predictions_df.empty:
                print(f"  ❌ No predictions generated")
                return None
            
            # Extract predictions
            predictions_df = predictions_df.sort_values('timestamp')
            forecast_values = predictions_df['point_forecast'].head(len(test)).tolist()
            actuals = test['target'].head(len(forecast_values)).tolist()
            
            if len(forecast_values) != len(actuals):
                min_len = min(len(forecast_values), len(actuals))
                forecast_values = forecast_values[:min_len]
                actuals = actuals[:min_len]
                print(f"  ⚠️  Adjusted to {min_len} days for comparison")
            
            # Calculate accuracy metrics
            mape = QualityCalculator.calculate_mape(actuals, forecast_values)
            mae = QualityCalculator.calculate_mae(actuals, forecast_values)
            rmse = QualityCalculator.calculate_rmse(actuals, forecast_values)
            bias = QualityCalculator.calculate_bias(actuals, forecast_values)
            
            result = {
                'item_id': item_id,
                'train_days': len(train),
                'test_days': len(actuals),
                'train_sales': float(train['target'].sum()),
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
        finally:
            # Clean up temp file
            if temp_csv.exists():
                temp_csv.unlink()
    
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
    # Create in-memory database for testing
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        tester = ForecastAccuracyTester("ts_demand_daily_clean.csv", session)
        await tester.run_tests(num_items=5)
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
