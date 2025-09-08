"""
Test suite for timezone handling in data loading.

This test ensures that timezone-aware CSV data is properly handled without
causing comparison errors between timezone-naive and timezone-aware timestamps.
"""

import unittest
import pandas as pd
import tempfile
import os
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.modules.data_management.data_center.data_loader import DataLoader
from src.ui.app_logger import LOG


class TestTimezoneHandling(unittest.TestCase):
    """Test timezone handling in data loading operations."""
    
    def setUp(self):
        """Set up test fixtures with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_loader = DataLoader(data_root=self.temp_dir)
        self.price_dir = Path(self.temp_dir) / "raw" / "price"
        self.price_dir.mkdir(parents=True, exist_ok=True)
        
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_timezone_aware_csv(self, filename: str, timezone_suffix: str = "-05:00"):
        """Create a CSV file with timezone-aware datetime stamps."""
        # Generate sample data with timezone-aware timestamps
        dates_with_tz = [
            f"2023-01-0{i+1} 00:00:00{timezone_suffix}" for i in range(5)
        ]
        prices = [100.0 + i * 2.5 for i in range(5)]
        
        df = pd.DataFrame({
            'date': dates_with_tz,
            'close': prices,
            'volume': [1000000] * 5
        })
        
        filepath = self.price_dir / filename
        df.to_csv(filepath, index=False)
        return filepath
    
    def create_mixed_timezone_csv(self, filename: str):
        """Create a CSV file with mixed timezone formats."""
        # Mix of timezone-aware and timezone-naive timestamps
        dates_mixed = [
            "2023-01-01 00:00:00-05:00",  # EST
            "2023-01-02 00:00:00-08:00",  # PST
            "2023-01-03 00:00:00+00:00",  # UTC
            "2023-01-04 00:00:00",        # Naive
            "2023-01-05 00:00:00-05:00"   # EST again
        ]
        prices = [100.0, 102.5, 105.0, 107.5, 110.0]
        
        df = pd.DataFrame({
            'date': dates_mixed,
            'close': prices,
            'volume': [1000000] * 5
        })
        
        filepath = self.price_dir / filename
        df.to_csv(filepath, index=False)
        return filepath
    
    def test_timezone_aware_data_feed_loading(self):
        """Test loading data feed with timezone-aware timestamps."""
        # Create test CSV with timezone-aware data
        csv_file = self.create_timezone_aware_csv("TEST_ASSET_price.csv")
        
        # This should not raise timezone comparison errors
        try:
            data_feed = self.data_loader.load_data_feed(
                asset_name="TEST_ASSET",
                name="Test Asset",
                start_date="2023-01-01"
            )
            
            self.assertIsNotNone(data_feed, "Data feed should be created successfully")
            
            # Verify the data feed has the expected data
            df = data_feed._dataname
            self.assertEqual(len(df), 5, "Should have 5 records")
            
            # Verify index is timezone-naive after processing
            self.assertIsNone(df.index.tz, "Index should be timezone-naive after processing")
            
            # Verify data integrity
            self.assertEqual(df['close'].iloc[0], 100.0, "First close price should be 100.0")
            self.assertEqual(df['close'].iloc[-1], 110.0, "Last close price should be 110.0")
            
            LOG.info("✅ Timezone-aware data feed loading test passed")
            
        except Exception as e:
            self.fail(f"Timezone-aware data loading failed: {e}")
    
    def test_mixed_timezone_data_feed_loading(self):
        """Test loading data feed with mixed timezone formats."""
        # Create test CSV with mixed timezone data
        csv_file = self.create_mixed_timezone_csv("MIXED_TZ_price.csv")
        
        # This should handle mixed timezones gracefully
        try:
            data_feed = self.data_loader.load_data_feed(
                asset_name="MIXED_TZ",
                name="Mixed Timezone Asset",
                start_date="2023-01-01"
            )
            
            self.assertIsNotNone(data_feed, "Data feed should be created successfully")
            
            # Verify the data feed has the expected data
            df = data_feed._dataname
            self.assertEqual(len(df), 5, "Should have 5 records")
            
            # Verify index is timezone-naive after processing
            self.assertIsNone(df.index.tz, "Index should be timezone-naive after processing")
            
            LOG.info("✅ Mixed timezone data feed loading test passed")
            
        except Exception as e:
            self.fail(f"Mixed timezone data loading failed: {e}")
    
    def test_timezone_aware_market_data_loading(self):
        """Test loading market data with timezone-aware timestamps."""
        # Create test CSV
        csv_file = self.create_timezone_aware_csv("TEST_MARKET_price.csv")
        
        # Mock the ASSETS config to include our test asset
        original_assets = {}
        try:
            from config.assets import ASSETS
            original_assets = ASSETS.copy()
            ASSETS['TEST_MARKET'] = {'name': 'Test Market Asset'}
            
            # Load market data
            market_data = self.data_loader.load_market_data()
            
            # Verify test asset was loaded
            self.assertIn('TEST_MARKET', market_data, "Test asset should be in market data")
            
            # Verify the data is timezone-naive
            df = market_data['TEST_MARKET']
            self.assertFalse(df.empty, "Market data should not be empty")
            self.assertIsNone(df.index.tz, "Market data index should be timezone-naive")
            
            LOG.info("✅ Timezone-aware market data loading test passed")
            
        except Exception as e:
            self.fail(f"Timezone-aware market data loading failed: {e}")
        finally:
            # Restore original ASSETS config
            if original_assets:
                from config.assets import ASSETS
                ASSETS.clear()
                ASSETS.update(original_assets)
    
    def test_start_date_filtering_with_timezones(self):
        """Test that start_date filtering works correctly with timezone-aware data."""
        # Create test CSV with timezone-aware data
        csv_file = self.create_timezone_aware_csv("DATE_FILTER_price.csv")
        
        # Test filtering with start_date
        try:
            data_feed = self.data_loader.load_data_feed(
                asset_name="DATE_FILTER",
                name="Date Filter Test",
                start_date="2023-01-03"  # Should filter out first 2 records
            )
            
            self.assertIsNotNone(data_feed, "Data feed should be created successfully")
            
            # Verify filtering worked
            df = data_feed._dataname
            self.assertEqual(len(df), 3, "Should have 3 records after filtering")
            
            # Verify earliest date is >= start_date
            earliest_date = df.index.min()
            start_date_parsed = pd.to_datetime("2023-01-03")
            self.assertGreaterEqual(earliest_date, start_date_parsed, 
                                  "Earliest date should be >= start_date")
            
            LOG.info("✅ Start date filtering with timezone test passed")
            
        except Exception as e:
            self.fail(f"Start date filtering with timezone data failed: {e}")
    
    def test_real_world_timezone_format(self):
        """Test with the actual timezone format from yfinance data."""
        # Create CSV that mimics the actual TIP_price.csv format
        dates_with_real_tz = [
            "2023-01-01 00:00:00-05:00",
            "2023-01-02 00:00:00-05:00", 
            "2023-01-03 00:00:00-05:00"
        ]
        
        df = pd.DataFrame({
            'date': dates_with_real_tz,
            'Open': [100.0, 101.0, 102.0],
            'High': [100.5, 101.5, 102.5],
            'Low': [99.5, 100.5, 101.5],
            'Close': [100.2, 101.2, 102.2],
            'Volume': [1000000, 1100000, 1200000],
            'Dividends': [0.0, 0.0, 0.0],
            'Stock Splits': [0.0, 0.0, 0.0],
            'Capital Gains': [0.0, 0.0, 0.0]
        })
        
        filepath = self.price_dir / "REAL_WORLD_price.csv"
        df.to_csv(filepath, index=False)
        
        try:
            data_feed = self.data_loader.load_data_feed(
                asset_name="REAL_WORLD",
                name="Real World Format Test"
            )
            
            self.assertIsNotNone(data_feed, "Real world format should load successfully")
            
            # Verify data structure
            df_loaded = data_feed._dataname
            self.assertEqual(len(df_loaded), 3, "Should have 3 records")
            self.assertIsNone(df_loaded.index.tz, "Should be timezone-naive")
            
            LOG.info("✅ Real world timezone format test passed")
            
        except Exception as e:
            self.fail(f"Real world timezone format test failed: {e}")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
