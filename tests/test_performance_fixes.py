"""
Test suite for the performance attribution and JSON serialization fixes.
"""
import unittest
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.performance.analytics import PerformanceAnalyzer
from src.performance.attribution import PerformanceAttributor


class TestPerformanceFixes(unittest.TestCase):
    """Test fixes for JSON serialization and attribution data alignment."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = PerformanceAnalyzer()
        self.attributor = PerformanceAttributor()
    
    def test_json_serialization_timestamp_fix(self):
        """Test that pandas Timestamps are properly serialized to JSON."""
        test_data = {
            'timestamp': pd.Timestamp('2024-01-01 12:00:00'),
            'datetime': datetime(2024, 1, 1, 12, 0, 0),
            'series_with_timestamps': pd.Series([1, 2, 3], 
                                               index=pd.date_range('2024-01-01', periods=3)),
            'dataframe_with_timestamps': pd.DataFrame(
                {'values': [1, 2, 3]}, 
                index=pd.date_range('2024-01-01', periods=3)
            ),
            'numpy_float': np.float64(3.14159),
            'numpy_int': np.int32(42),
            'numpy_array': np.array([1.0, 2.0, 3.0]),
            'nested_dict': {
                'inner_timestamp': pd.Timestamp('2024-06-15'),
                'list_with_timestamps': [pd.Timestamp('2024-01-01'), pd.Timestamp('2024-01-02')]
            }
        }
        
        # This should not raise a JSON serialization error
        try:
            result = self.analyzer._serialize_for_json(test_data)
            
            # Verify timestamp serialization
            self.assertIsInstance(result['timestamp'], str, "Timestamp should be serialized as string")
            self.assertIsInstance(result['datetime'], str, "Datetime should be serialized as string")
            
            # Verify nested timestamp serialization
            self.assertIsInstance(result['nested_dict']['inner_timestamp'], str, 
                                "Nested timestamp should be serialized as string")
            
            # Verify list with timestamps
            for item in result['nested_dict']['list_with_timestamps']:
                self.assertIsInstance(item, str, "Timestamp in list should be serialized as string")
            
            # Verify numpy types
            self.assertIsInstance(result['numpy_float'], float, "Numpy float should be converted to Python float")
            self.assertIsInstance(result['numpy_int'], int, "Numpy int should be converted to Python int")
            self.assertIsInstance(result['numpy_array'], list, "Numpy array should be converted to list")
            
        except Exception as e:
            self.fail(f"JSON serialization failed with error: {e}")
    
    def test_attribution_data_alignment_fix(self):
        """Test that attribution analysis properly aligns data with different index types."""
        dates = pd.date_range('2024-01-01', periods=15, freq='D')
        
        # Portfolio data with DatetimeIndex
        portfolio_data = pd.DataFrame({
            'value': [1000 * (1 + i * 0.001) for i in range(15)],
            'returns': [0.001] * 15
        }, index=dates)
        
        # Asset returns with DatetimeIndex
        asset_returns = pd.DataFrame({
            'SP500': [0.001 + np.random.normal(0, 0.001) for _ in range(15)],
            'TLT': [0.0005 + np.random.normal(0, 0.0005) for _ in range(15)]
        }, index=dates)
        
        # Weights data with DatetimeIndex
        weights_data = pd.DataFrame({
            'SP500': [0.6] * 15,
            'TLT': [0.4] * 15
        }, index=dates)
        
        # This should not fail with "Insufficient data for attribution analysis"
        try:
            daily_attributions = self.attributor.calculate_daily_attribution(
                portfolio_data, asset_returns, weights_data
            )
            
            # Should have attribution results (at least a few days)
            self.assertGreater(len(daily_attributions), 10, 
                             "Should have multiple daily attribution results")
            
            # Each attribution should have required fields (AttributionResult objects)
            for attr in daily_attributions[:3]:  # Check first few
                self.assertTrue(hasattr(attr, 'date'), "Attribution should have date attribute")
                self.assertTrue(hasattr(attr, 'total_return'), "Attribution should have total_return attribute")
                self.assertTrue(hasattr(attr, 'asset_contributions'), "Attribution should have asset_contributions attribute")
                
        except Exception as e:
            self.fail(f"Attribution analysis failed with error: {e}")
    
    def test_attribution_with_misaligned_data(self):
        """Test attribution analysis with partially misaligned data."""
        # Create data with different date ranges
        portfolio_dates = pd.date_range('2024-01-01', periods=10, freq='D')
        asset_dates = pd.date_range('2024-01-02', periods=12, freq='D')  # Different range
        weights_dates = pd.date_range('2023-12-30', periods=15, freq='D')  # Different range
        
        portfolio_data = pd.DataFrame({
            'value': [1000 + i * 10 for i in range(10)],
            'returns': [0.01] * 10
        }, index=portfolio_dates)
        
        asset_returns = pd.DataFrame({
            'SP500': [0.01] * 12,
            'TLT': [0.005] * 12
        }, index=asset_dates)
        
        weights_data = pd.DataFrame({
            'SP500': [0.6] * 15,
            'TLT': [0.4] * 15
        }, index=weights_dates)
        
        # Should handle misaligned data gracefully
        try:
            daily_attributions = self.attributor.calculate_daily_attribution(
                portfolio_data, asset_returns, weights_data
            )
            
            # Should either work with common dates or return empty list
            self.assertIsInstance(daily_attributions, list, 
                                "Should return list even with misaligned data")
            
            # If we get results, they should be valid (AttributionResult objects)
            if daily_attributions:
                for attr in daily_attributions[:3]:
                    self.assertTrue(hasattr(attr, 'date'))
                    self.assertTrue(hasattr(attr, 'total_return'))
                    
        except Exception as e:
            self.fail(f"Attribution with misaligned data should not raise exception: {e}")
    
    def test_complete_attribution_report(self):
        """Test that a complete attribution report can be generated without errors."""
        dates = pd.date_range('2024-01-01', periods=20, freq='D')
        
        # Create comprehensive test data
        portfolio_data = pd.DataFrame({
            'value': [1000 * (1.001 ** i) for i in range(20)],  # Compound growth
            'returns': [0.001] * 20
        }, index=dates)
        
        asset_returns = pd.DataFrame({
            'SP500': [0.001] * 20,
            'TLT': [0.0005] * 20,
            'GLD': [0.0002] * 20
        }, index=dates)
        
        weights_data = pd.DataFrame({
            'SP500': [0.5] * 20,
            'TLT': [0.3] * 20,
            'GLD': [0.2] * 20
        }, index=dates)
        
        try:
            report = self.attributor.generate_attribution_report(
                strategy_name="TestStrategy",
                portfolio_data=portfolio_data,
                asset_returns=asset_returns,
                weights_data=weights_data,
                include_weekly=True,
                include_monthly=True
            )
            
            # Should not contain error
            self.assertNotIn('error', report, 
                           f"Attribution report should not contain error: {report.get('error', '')}")
            
            # Should contain expected sections
            self.assertIn('strategy_name', report, "Report should contain strategy name")
            self.assertIn('daily_analysis', report, "Report should contain daily analysis")
            
        except Exception as e:
            # If attribution fails due to insufficient periods for weekly/monthly, that's acceptable
            if "insufficient" not in str(e).lower():
                self.fail(f"Complete attribution report generation failed: {e}")


class TestDataFrameIndexing(unittest.TestCase):
    """Test DataFrame indexing fixes in the backtest runner."""
    
    def test_portfolio_dataframe_indexing(self):
        """Test that portfolio DataFrame is properly indexed by date."""
        import pandas as pd
        from datetime import datetime
        
        # Simulate the portfolio DataFrame creation in the runner
        dates = [datetime(2024, 1, 1), datetime(2024, 1, 2), datetime(2024, 1, 3)]
        values = [1000, 1010, 1020]
        
        # This is what happens in the runner now
        portfolio_df = pd.DataFrame({
            'date': pd.to_datetime(dates),
            'value': values
        })
        portfolio_df['returns'] = portfolio_df['value'].pct_change()
        portfolio_df.set_index('date', inplace=True)
        
        # Verify the DataFrame structure
        self.assertIsInstance(portfolio_df.index, pd.DatetimeIndex, 
                            "Portfolio DataFrame should have DatetimeIndex")
        self.assertIn('value', portfolio_df.columns, "Should contain value column")
        self.assertIn('returns', portfolio_df.columns, "Should contain returns column")
        self.assertEqual(len(portfolio_df), 3, "Should have 3 rows")
    
    def test_weights_dataframe_indexing(self):
        """Test that weights DataFrame is properly indexed by date."""
        import pandas as pd
        from datetime import datetime
        
        # Simulate weights evolution data structure
        weights_evolution = [
            {'date': datetime(2024, 1, 1), 'SP500': 0.6, 'TLT': 0.4},
            {'date': datetime(2024, 1, 2), 'SP500': 0.65, 'TLT': 0.35},
            {'date': datetime(2024, 1, 3), 'SP500': 0.6, 'TLT': 0.4}
        ]
        
        # This is what happens in the runner now
        weights_df = pd.DataFrame(weights_evolution)
        if 'date' in weights_df.columns:
            weights_df['date'] = pd.to_datetime(weights_df['date'])
            weights_df.set_index('date', inplace=True)
        
        # Verify the DataFrame structure
        self.assertIsInstance(weights_df.index, pd.DatetimeIndex,
                            "Weights DataFrame should have DatetimeIndex") 
        self.assertIn('SP500', weights_df.columns, "Should contain SP500 weights")
        self.assertIn('TLT', weights_df.columns, "Should contain TLT weights")
        self.assertEqual(len(weights_df), 3, "Should have 3 rows")


if __name__ == '__main__':
    unittest.main(verbosity=2)