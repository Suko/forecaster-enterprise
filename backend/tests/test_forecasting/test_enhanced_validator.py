"""
Test Enhanced Data Validator - Demonstrates Darts-inspired validation

Shows how the enhanced validator handles:
1. Missing dates (like Darts' fill_missing_dates)
2. NaN values (like Darts' fillna_value)
3. Frequency consistency (Darts' requirement)
4. Duplicate timestamps
"""
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from forecasting.services.data_validator import DataValidator


def test_missing_dates():
    """Test missing date detection and filling (Darts' fill_missing_dates)"""
    print("=" * 80)
    print("Test 1: Missing Dates (Darts' fill_missing_dates)")
    print("=" * 80)

    # Create data with missing dates
    dates = pd.date_range('2024-01-01', '2024-01-10', freq='D')
    # Remove some dates
    dates = dates.drop([dates[2], dates[5], dates[7]])

    df = pd.DataFrame({
        'id': ['SKU001'] * len(dates),
        'timestamp': dates,
        'target': [10, 20, 30, 40, 50, 60, 70]
    })

    print(f"\nOriginal data: {len(df)} days")
    print(f"Missing dates: 3 (Jan 3, 6, 8)")

    # Test without filling
    is_valid, report, cleaned_df = DataValidator.validate_time_index(
        df, expected_freq="D", fill_missing_dates=False
    )
    print(f"\n❌ Without fill_missing_dates: {is_valid}")
    print(f"   Warnings: {report['warnings']}")

    # Test with filling (Darts' behavior)
    is_valid, report, cleaned_df = DataValidator.validate_time_index(
        df, expected_freq="D", fill_missing_dates=True
    )
    print(f"\n✅ With fill_missing_dates=True: {is_valid}")
    print(f"   Filled dates: {report['missing_dates']}")
    print(f"   Result: {len(cleaned_df)} days (complete series)")
    print(f"   Missing dates filled with: NaN -> 0 (zero-demand days)")


def test_nan_values():
    """Test NaN value handling (Darts' fillna_value)"""
    print("\n" + "=" * 80)
    print("Test 2: NaN Values (Darts' fillna_value)")
    print("=" * 80)

    dates = pd.date_range('2024-01-01', '2024-01-10', freq='D')
    df = pd.DataFrame({
        'id': ['SKU001'] * len(dates),
        'timestamp': dates,
        'target': [10, 20, np.nan, 40, np.nan, 60, 70, 80, np.nan, 100]
    })

    print(f"\nOriginal data: {len(df)} days")
    print(f"NaN values: {df['target'].isna().sum()}")

    # Test different strategies
    strategies = ['zero', 'forward_fill', 'value']

    for strategy in strategies:
        is_valid, report, cleaned_df = DataValidator.validate_nan_values(
            df, fillna_strategy=strategy, fillna_value=0
        )
        print(f"\n✅ Strategy '{strategy}':")
        print(f"   NaN count before: {report['nan_counts']['target']}")
        print(f"   NaN count after: {cleaned_df['target'].isna().sum()}")
        print(f"   Filled: {report.get('filled_nans', {}).get('target', 0)}")


def test_duplicate_dates():
    """Test duplicate timestamp handling"""
    print("\n" + "=" * 80)
    print("Test 3: Duplicate Timestamps")
    print("=" * 80)

    dates = pd.to_datetime(['2024-01-01', '2024-01-01', '2024-01-02', '2024-01-03'])
    df = pd.DataFrame({
        'id': ['SKU001'] * len(dates),
        'timestamp': dates,
        'target': [10, 20, 30, 40]  # First duplicate has 10, second has 20
    })

    print(f"\nOriginal data: {len(df)} rows")
    print(f"Duplicate dates: 1 (2024-01-01 appears twice)")

    is_valid, report, cleaned_df = DataValidator.validate_time_index(
        df, expected_freq="D", fill_missing_dates=False
    )

    print(f"\n✅ After validation:")
    print(f"   Duplicates detected: {report['duplicate_dates']}")
    print(f"   Result: {len(cleaned_df)} rows (duplicates removed, kept first)")
    print(f"   Warnings: {report['warnings']}")


def test_frequency_consistency():
    """Test frequency consistency (Darts' key requirement)"""
    print("\n" + "=" * 80)
    print("Test 4: Frequency Consistency (Darts' Requirement)")
    print("=" * 80)

    # Consistent frequency
    dates1 = pd.date_range('2024-01-01', '2024-01-10', freq='D')
    df1 = pd.DataFrame({
        'id': ['SKU001'] * len(dates1),
        'timestamp': dates1,
        'target': np.random.randint(10, 100, len(dates1))
    })

    # Inconsistent frequency
    dates2 = pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-05', '2024-01-06', '2024-01-10'])
    df2 = pd.DataFrame({
        'id': ['SKU001'] * len(dates2),
        'timestamp': dates2,
        'target': np.random.randint(10, 100, len(dates2))
    })

    print("\n✅ Consistent frequency (daily):")
    is_valid, report, _ = DataValidator.validate_time_index(
        df1, expected_freq="D", fill_missing_dates=False
    )
    print(f"   Valid: {is_valid}")
    print(f"   Frequency consistent: {report['frequency_consistent']}")
    print(f"   Detected freq: {report.get('detected_freq', 'N/A')}")

    print("\n❌ Inconsistent frequency (gaps):")
    is_valid, report, _ = DataValidator.validate_time_index(
        df2, expected_freq="D", fill_missing_dates=False
    )
    print(f"   Valid: {is_valid}")
    print(f"   Frequency consistent: {report['frequency_consistent']}")
    print(f"   Issues: {report['issues']}")
    print(f"   Warnings: {report['warnings']}")


def test_complete_validation():
    """Test complete validation (like Darts' TimeSeries.from_dataframe)"""
    print("\n" + "=" * 80)
    print("Test 5: Complete Validation (Darts' TimeSeries.from_dataframe equivalent)")
    print("=" * 80)

    # Create data with multiple issues
    dates = pd.date_range('2024-01-01', '2024-01-10', freq='D')
    dates = dates.drop([dates[2], dates[5]])  # Missing dates

    df = pd.DataFrame({
        'id': ['SKU001'] * len(dates),
        'timestamp': dates,
        'target': [10, 20, np.nan, 40, 50, np.nan, 70, 80]
    })

    print(f"\nOriginal data issues:")
    print(f"  - Missing dates: 2")
    print(f"  - NaN values: {df['target'].isna().sum()}")
    print(f"  - Total rows: {len(df)}")

    # Complete validation (like Darts)
    is_valid, report, cleaned_df, error = DataValidator.validate_complete(
        df,
        item_id="SKU001",
        min_history_days=5,
        expected_freq="D",
        fill_missing_dates=True,  # Like Darts' fill_missing_dates=True
        fillna_strategy="zero",   # Like Darts' fillna_value=0
    )

    print(f"\n✅ After complete validation:")
    print(f"   Valid: {is_valid}")
    print(f"   Original rows: {len(df)}")
    print(f"   Cleaned rows: {len(cleaned_df)}")
    print(f"   Missing dates filled: {report['time_index_validation']['missing_dates']}")
    print(f"   NaN values filled: {sum(report['nan_validation']['filled_nans'].values())}")
    print(f"   Warnings: {len(report['warnings'])}")
    print(f"\n   Cleaned data is ready for forecasting (like Darts' TimeSeries)")


if __name__ == "__main__":
    test_missing_dates()
    test_nan_values()
    test_duplicate_dates()
    test_frequency_consistency()
    test_complete_validation()

    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print("\n✅ Enhanced validator implements Darts' data quality practices:")
    print("   1. Time frequency consistency checks")
    print("   2. Missing date detection and filling")
    print("   3. NaN value handling strategies")
    print("   4. Duplicate timestamp removal")
    print("   5. Complete validation pipeline")
    print("\n📚 See: docs/forecasting/DARTS_DATA_QUALITY_LEARNINGS.md")

