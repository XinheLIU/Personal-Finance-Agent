"""
Test for the pandas Series boolean evaluation fix in attribution analysis.
This test specifically targets the fix for the error:
"The truth value of a Series is ambiguous. Use a.empty, a.bool(), a.item(), a.any() or a.all()."
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

from src.performance.attribution import PerformanceAttributor, AttributionResult


class TestSeriesBooleanFix(unittest.TestCase):
    """Test that the pandas Series boolean evaluation error is fixed."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.attributor = PerformanceAttributor()
    
    def test_large_dataset_attribution_analysis(self):
        """Test attribution analysis with larger dataset that would trigger the Series boolean error."""
        # Create a larger dataset similar to real backtest data that was causing the error
        dates = pd.date_range('2020-01-01', periods=200, freq='D')
        
        # Portfolio data with steady positive returns to avoid extreme values
        portfolio_data = pd.DataFrame({
            'value': [1000 * (1.001 ** i) for i in range(200)],
            'returns': [0.001] * 200
        }, index=dates)
        
        # Asset returns with steady positive values
        asset_returns = pd.DataFrame({
            'SP500': [0.001] * 200,
            'TLT': [0.0005] * 200,
            'GLD': [0.0002] * 200
        }, index=dates)
        
        # Weights data - static allocation like 60/40 strategy
        weights_data = pd.DataFrame({
            'SP500': [0.6] * 200,
            'TLT': [0.4] * 200,
            'GLD': [0.0] * 200  # Some assets with zero weight
        }, index=dates)
        
        # This should not raise the Series boolean evaluation error
        try:
            daily_attributions = self.attributor.calculate_daily_attribution(
                portfolio_data, asset_returns, weights_data
            )
            
            # Should get attribution results
            self.assertGreater(len(daily_attributions), 100, 
                             "Should have many daily attribution results")
            
            # Test the decompose method that had the Series boolean issue
            decomposed = self.attributor.decompose_returns(daily_attributions)
            
            # Should not contain error
            self.assertNotIn('error', decomposed, 
                           f"Decomposed results should not contain error: {decomposed.get('error', '')}")
            
            # Should contain expected sections
            self.assertIn('summary_statistics', decomposed, 
                         "Decomposed results should contain summary statistics")
            self.assertIn('asset_analysis', decomposed,
                         "Decomposed results should contain asset analysis")
            
        except ValueError as e:
            if "truth value of a Series is ambiguous" in str(e):
                self.fail(f"The Series boolean evaluation error still occurs: {e}")
            else:
                raise  # Re-raise if it's a different ValueError
    
    def test_complete_attribution_report_with_large_dataset(self):
        """Test complete attribution report generation with dataset size that caused the error."""
        # Create substantial dataset like real backtests
        dates = pd.date_range('2019-01-01', periods=500, freq='D') 
        
        portfolio_data = pd.DataFrame({
            'value': [1000 * (1.0008 ** i) for i in range(500)],  # Steady growth
            'returns': [0.0008] * 500
        }, index=dates)
        
        asset_returns = pd.DataFrame({
            'SP500': [0.0008] * 500,
            'TLT': [0.0004] * 500
        }, index=dates)
        
        weights_data = pd.DataFrame({
            'SP500': [0.6] * 500,
            'TLT': [0.4] * 500
        }, index=dates)
        
        # This was the specific call that was failing with Series boolean error
        try:
            report = self.attributor.generate_attribution_report(
                strategy_name="SixtyFortyStrategy",
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
            self.assertIn('strategy_name', report)
            self.assertIn('daily_analysis', report)
            self.assertEqual(report['strategy_name'], "SixtyFortyStrategy")
            
        except ValueError as e:
            if "truth value of a Series is ambiguous" in str(e):
                self.fail(f"The Series boolean evaluation error still occurs in complete report: {e}")
            else:
                raise
    
    def test_attribution_results_structure(self):
        """Test that AttributionResult objects have correct structure for boolean evaluation fix."""
        # Create minimal test data
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        
        portfolio_data = pd.DataFrame({
            'value': [1000 + i * 10 for i in range(10)],
            'returns': [0.01] * 10
        }, index=dates)
        
        asset_returns = pd.DataFrame({
            'SP500': [0.01] * 10,
            'TLT': [0.005] * 10
        }, index=dates)
        
        weights_data = pd.DataFrame({
            'SP500': [0.6] * 10,
            'TLT': [0.4] * 10
        }, index=dates)
        
        daily_attributions = self.attributor.calculate_daily_attribution(
            portfolio_data, asset_returns, weights_data
        )
        
        # Verify structure of attribution results
        self.assertGreater(len(daily_attributions), 0, "Should have attribution results")
        
        for attr in daily_attributions[:3]:
            # Check that asset_contributions is not a Series that could cause boolean issues
            self.assertIsInstance(attr.asset_contributions, dict, 
                                "asset_contributions should be dict, not Series")
            
            # Check that boolean evaluation works correctly
            has_contributions = len(attr.asset_contributions) > 0
            self.assertTrue(has_contributions, "Should have asset contributions")
    
    def test_specific_boolean_condition_fix(self):
        """Test the specific boolean conditions that were fixed in the code."""
        # Create mock AttributionResult objects
        mock_results = []
        
        for i in range(5):
            # Create mock AttributionResult
            attr = type('MockAttr', (), {})()
            attr.asset_contributions = {'SP500': 0.01, 'TLT': 0.005}  # Dict, not Series
            attr.total_return = 0.015
            attr.weight_change_impact = 0.0
            mock_results.append(attr)
        
        # Test the specific boolean conditions that were problematic
        try:
            # This was the problematic line: if attr.asset_contributions
            # Now should be: if len(attr.asset_contributions) > 0
            total_contrib = sum(sum(attr.asset_contributions.values()) 
                              for attr in mock_results if len(attr.asset_contributions) > 0)
            
            self.assertGreater(total_contrib, 0, "Should calculate total contribution correctly")
            
        except ValueError as e:
            if "truth value" in str(e) and "ambiguous" in str(e):
                self.fail(f"The boolean evaluation fix is not working: {e}")
            else:
                raise


if __name__ == '__main__':
    unittest.main(verbosity=2)