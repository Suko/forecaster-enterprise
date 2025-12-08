"""
Data Validation Script for Minibambini Data

Validates data quality and identifies anomalies before ETL processing.
"""
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import json


class DataValidator:
    """Validates minibambini data for forecasting"""
    
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.df = None
        self.issues = []
        self.warnings = []
        self.stats = {}
    
    def load_data(self, sample_size: int = None) -> pd.DataFrame:
        """Load CSV data"""
        print(f"Loading data from {self.csv_path}...")
        
        if sample_size:
            self.df = pd.read_csv(self.csv_path, nrows=sample_size)
            print(f"Loaded sample: {len(self.df)} rows")
        else:
            self.df = pd.read_csv(self.csv_path)
            print(f"Loaded full dataset: {len(self.df)} rows")
        
        return self.df
    
    def validate_structure(self) -> Dict:
        """Validate basic structure"""
        print("\n=== Validating Structure ===")
        
        required_columns = [
            'Day', 'Product vendor', 'Product title', 
            'Product variant title', 'Net items sold', 'Ending inventory units'
        ]
        
        missing = [col for col in required_columns if col not in self.df.columns]
        if missing:
            self.issues.append(f"Missing required columns: {missing}")
            return {'valid': False, 'missing_columns': missing}
        
        self.stats['total_rows'] = len(self.df)
        self.stats['total_columns'] = len(self.df.columns)
        
        print(f"✅ Structure valid: {len(self.df.columns)} columns, {len(self.df)} rows")
        return {'valid': True}
    
    def validate_dates(self) -> Dict:
        """Validate date column"""
        print("\n=== Validating Dates ===")
        
        # Convert to datetime
        try:
            self.df['date'] = pd.to_datetime(self.df['Day'], errors='coerce')
        except Exception as e:
            self.issues.append(f"Date conversion failed: {e}")
            return {'valid': False}
        
        # Check for null dates
        null_dates = self.df['date'].isnull().sum()
        if null_dates > 0:
            self.warnings.append(f"{null_dates} rows with invalid dates")
        
        # Check date range
        min_date = self.df['date'].min()
        max_date = self.df['date'].max()
        date_range = (max_date - min_date).days
        
        self.stats['date_range_days'] = date_range
        self.stats['min_date'] = str(min_date)
        self.stats['max_date'] = str(max_date)
        
        # Check for future dates
        future_dates = (self.df['date'] > pd.Timestamp.now()).sum()
        if future_dates > 0:
            self.warnings.append(f"{future_dates} rows with future dates")
        
        print(f"✅ Date range: {min_date.date()} to {max_date.date()} ({date_range} days)")
        return {'valid': True, 'min_date': min_date, 'max_date': max_date, 'range_days': date_range}
    
    def validate_sales(self) -> Dict:
        """Validate sales data (Net items sold)"""
        print("\n=== Validating Sales Data ===")
        
        sales_col = 'Net items sold'
        
        # Check for nulls
        null_sales = self.df[sales_col].isnull().sum()
        if null_sales > 0:
            self.warnings.append(f"{null_sales} rows with null sales")
        
        # Convert to numeric
        self.df['units_sold'] = pd.to_numeric(self.df[sales_col], errors='coerce')
        
        # Check for negative sales
        negative_sales = (self.df['units_sold'] < 0).sum()
        if negative_sales > 0:
            self.issues.append(f"{negative_sales} rows with negative sales (returns?)")
        
        # Check for extremely high sales (outliers)
        q99 = self.df['units_sold'].quantile(0.99)
        extreme_sales = (self.df['units_sold'] > q99 * 3).sum()
        if extreme_sales > 0:
            self.warnings.append(f"{extreme_sales} rows with extreme sales (>3× 99th percentile)")
        
        # Statistics
        self.stats['total_sales'] = self.df['units_sold'].sum()
        self.stats['avg_daily_sales'] = self.df['units_sold'].mean()
        self.stats['zero_sales_days'] = (self.df['units_sold'] == 0).sum()
        self.stats['zero_sales_pct'] = (self.stats['zero_sales_days'] / len(self.df)) * 100
        
        print(f"✅ Sales: Total={self.stats['total_sales']:,.0f}, Avg={self.stats['avg_daily_sales']:.2f}/day")
        print(f"   Zero sales: {self.stats['zero_sales_days']:,} days ({self.stats['zero_sales_pct']:.1f}%)")
        
        return {'valid': True, 'stats': self.stats}
    
    def validate_inventory(self) -> Dict:
        """Validate inventory data"""
        print("\n=== Validating Inventory Data ===")
        
        inv_col = 'Ending inventory units'
        
        # Check for nulls
        null_inv = self.df[inv_col].isnull().sum()
        if null_inv > 0:
            self.warnings.append(f"{null_inv} rows with null inventory")
        
        # Convert to numeric
        self.df['inventory'] = pd.to_numeric(self.df[inv_col], errors='coerce')
        
        # Check for negative inventory
        negative_inv = (self.df['inventory'] < 0).sum()
        if negative_inv > 0:
            self.issues.append(f"{negative_inv} rows with negative inventory (data error!)")
        
        # Statistics
        self.stats['avg_inventory'] = self.df['inventory'].mean()
        self.stats['stockout_days'] = (self.df['inventory'] == 0).sum()
        self.stats['stockout_pct'] = (self.stats['stockout_days'] / len(self.df)) * 100
        
        print(f"✅ Inventory: Avg={self.stats['avg_inventory']:.2f}, Stockouts={self.stats['stockout_days']:,} ({self.stats['stockout_pct']:.1f}%)")
        
        return {'valid': True}
    
    def validate_products(self) -> Dict:
        """Validate product data"""
        print("\n=== Validating Product Data ===")
        
        # Check for missing vendor
        null_vendor = self.df['Product vendor'].isnull().sum()
        if null_vendor > 0:
            self.warnings.append(f"{null_vendor} rows with missing vendor")
        
        # Check for missing title
        null_title = self.df['Product title'].isnull().sum()
        if null_title > 0:
            self.warnings.append(f"{null_title} rows with missing product title")
        
        # Check for missing variant
        null_variant = self.df['Product variant title'].isnull().sum()
        if null_variant > 0:
            self.warnings.append(f"{null_variant} rows with missing variant (using 'Default Title')")
        
        # Statistics
        self.stats['unique_vendors'] = self.df['Product vendor'].nunique()
        self.stats['unique_products'] = self.df['Product title'].nunique()
        self.stats['unique_variants'] = self.df['Product variant title'].nunique()
        
        # Check for empty rows (all null)
        empty_rows = self.df[['Product vendor', 'Product title', 'Product variant title']].isnull().all(axis=1).sum()
        if empty_rows > 0:
            self.issues.append(f"{empty_rows} completely empty rows (should be removed)")
        
        print(f"✅ Products: {self.stats['unique_vendors']} vendors, {self.stats['unique_products']} products, {self.stats['unique_variants']} variants")
        
        return {'valid': True}
    
    def detect_anomalies(self) -> Dict:
        """Detect data anomalies"""
        print("\n=== Detecting Anomalies ===")
        
        anomalies = []
        
        # 1. Sales spikes (sudden large increase)
        if 'units_sold' in self.df.columns and 'date' in self.df.columns:
            # Group by product and check for spikes
            for product in self.df['Product title'].dropna().unique()[:10]:  # Sample first 10
                product_data = self.df[self.df['Product title'] == product].sort_values('date')
                if len(product_data) > 1:
                    product_data['sales_diff'] = product_data['units_sold'].diff()
                    spikes = product_data[product_data['sales_diff'] > product_data['units_sold'].quantile(0.95) * 3]
                    if len(spikes) > 0:
                        anomalies.append({
                            'type': 'sales_spike',
                            'product': product,
                            'count': len(spikes)
                        })
        
        # 2. Inventory jumps (sudden large change)
        if 'inventory' in self.df.columns and 'date' in self.df.columns:
            for product in self.df['Product title'].dropna().unique()[:10]:
                product_data = self.df[self.df['Product title'] == product].sort_values('date')
                if len(product_data) > 1:
                    product_data['inv_diff'] = product_data['inventory'].diff().abs()
                    jumps = product_data[product_data['inv_diff'] > product_data['inventory'].quantile(0.95) * 2]
                    if len(jumps) > 0:
                        anomalies.append({
                            'type': 'inventory_jump',
                            'product': product,
                            'count': len(jumps)
                        })
        
        # 3. Missing days in time series
        if 'date' in self.df.columns:
            for product in self.df['Product title'].dropna().unique()[:10]:
                product_data = self.df[self.df['Product title'] == product].sort_values('date')
                if len(product_data) > 1:
                    date_range = pd.date_range(product_data['date'].min(), product_data['date'].max(), freq='D')
                    missing_days = len(date_range) - len(product_data)
                    if missing_days > 0:
                        anomalies.append({
                            'type': 'missing_days',
                            'product': product,
                            'missing': missing_days
                        })
        
        self.stats['anomalies_detected'] = len(anomalies)
        print(f"✅ Detected {len(anomalies)} potential anomalies")
        
        return {'anomalies': anomalies}
    
    def generate_report(self) -> Dict:
        """Generate validation report"""
        report = {
            'file': str(self.csv_path),
            'timestamp': datetime.now().isoformat(),
            'stats': self.stats,
            'issues': self.issues,
            'warnings': self.warnings,
            'status': 'PASS' if len(self.issues) == 0 else 'FAIL'
        }
        
        return report
    
    def run_all_validations(self, sample_size: int = None) -> Dict:
        """Run all validations"""
        print("=" * 60)
        print("DATA VALIDATION REPORT")
        print("=" * 60)
        
        # Load data
        self.load_data(sample_size)
        
        # Run validations
        self.validate_structure()
        self.validate_dates()
        self.validate_sales()
        self.validate_inventory()
        self.validate_products()
        self.detect_anomalies()
        
        # Generate report
        report = self.generate_report()
        
        # Print summary
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Status: {report['status']}")
        print(f"Issues: {len(self.issues)}")
        print(f"Warnings: {len(self.warnings)}")
        
        if self.issues:
            print("\n❌ ISSUES:")
            for issue in self.issues:
                print(f"  - {issue}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        return report


if __name__ == "__main__":
    # Validate the data
    validator = DataValidator("minibambini.csv")
    
    # Run on sample first (1000 rows)
    print("Running validation on sample (1000 rows)...")
    report = validator.run_all_validations(sample_size=1000)
    
    # Save report
    with open("validation_report_sample.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    print("\n✅ Validation complete! Report saved to validation_report_sample.json")
    print("\nTo validate full dataset, run:")
    print("  python validate_data.py --full")

