"""
Tests for TestDataLoader
"""
import pytest
import pandas as pd
from tests.fixtures.test_data_loader import TestDataLoader


class TestTestDataLoader:
    """Test test data loading and transformation"""

    @pytest.fixture
    def loader(self):
        return TestDataLoader()

    def test_load_csv(self, loader):
        """Test CSV loading"""
        df = loader.load_csv()
        assert not df.empty
        assert "date" in df.columns
        assert "sku" in df.columns
        assert "sales_qty" in df.columns

    def test_get_item_data(self, loader):
        """Test getting item data"""
        item_data = loader.get_item_data("SKU001")

        assert not item_data.empty
        assert "id" in item_data.columns
        assert "timestamp" in item_data.columns
        assert "target" in item_data.columns
        assert len(item_data) > 0

    def test_get_item_data_format(self, loader):
        """Test data format for Chronos-2"""
        item_data = loader.get_item_data("SKU001")

        # Check required columns
        required = ["id", "timestamp", "target"]
        for col in required:
            assert col in item_data.columns

        # Check data types
        assert pd.api.types.is_datetime64_any_dtype(item_data["timestamp"])
        assert pd.api.types.is_numeric_dtype(item_data["target"])

        # Check covariates (if available)
        if "promo_flag" in item_data.columns:
            assert pd.api.types.is_numeric_dtype(item_data["promo_flag"])

    def test_get_available_items(self, loader):
        """Test getting available items"""
        items = loader.get_available_items()
        assert len(items) > 0
        assert "SKU001" in items

    def test_get_date_range(self, loader):
        """Test getting date range"""
        min_date, max_date = loader.get_date_range()
        assert min_date < max_date

    def test_get_item_summary(self, loader):
        """Test item summary"""
        summary = loader.get_item_summary("SKU001")

        assert "item_id" in summary
        assert "date_range" in summary
        assert "total_days" in summary
        assert "avg_daily_sales" in summary
        assert summary["total_days"] > 0

