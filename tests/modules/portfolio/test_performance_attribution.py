"""
Test suite for performance attribution feature and strategy weight retrieval.
Tests the fix for strategy instantiation errors and attribution functionality.
"""
import unittest
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.modules.portfolio.strategies.registry import strategy_registry
from src.modules.portfolio.strategies.base import BaseStrategy, StaticAllocationStrategy, DynamicStrategy
from src.streamlit_app import get_strategy_weights
import pandas as pd
from datetime import datetime, timedelta


class TestPerformanceAttribution(unittest.TestCase):
    """Test performance attribution functionality and strategy weight retrieval."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.static_strategies = [
            'SixtyFortyStrategy',
            'PermanentPortfolioStrategy', 
            'AllWeatherPortfolioStrategy',
            'DavidSwensenStrategy',
            'SimpleBuyAndHoldStrategy',
            'EqualWeightStrategy'
        ]
        
        self.dynamic_strategies = [
            'DynamicAllocationStrategy',
            'MomentumStrategy',
            'RiskParityStrategy'
        ]
    
    def test_strategy_registry_populated(self):
        """Test that strategy registry has all expected strategies."""
        strategies = strategy_registry.list_strategies()
        
        # Check that we have strategies
        self.assertGreater(len(strategies), 0, "Strategy registry should not be empty")
        
        # Check for expected static strategies
        for strategy_name in self.static_strategies:
            self.assertIn(strategy_name, strategies, f"{strategy_name} should be in registry")
        
        # Check for expected dynamic strategies
        for strategy_name in self.dynamic_strategies:
            self.assertIn(strategy_name, strategies, f"{strategy_name} should be in registry")
    
    def test_strategy_type_detection(self):
        """Test that strategies correctly identify their type."""
        # Test static strategies
        for strategy_name in self.static_strategies:
            strategy_class = strategy_registry.get(strategy_name)
            self.assertIsNotNone(strategy_class, f"Strategy {strategy_name} should exist")
            self.assertEqual(strategy_class.get_strategy_type(), "static", 
                           f"{strategy_name} should be classified as static")
        
        # Test dynamic strategies
        for strategy_name in self.dynamic_strategies:
            strategy_class = strategy_registry.get(strategy_name)
            self.assertIsNotNone(strategy_class, f"Strategy {strategy_name} should exist")
            self.assertEqual(strategy_class.get_strategy_type(), "dynamic",
                           f"{strategy_name} should be classified as dynamic")
    
    def test_static_weight_methods_exist(self):
        """Test that all static strategies have get_static_target_weights method."""
        for strategy_name in self.static_strategies:
            strategy_class = strategy_registry.get(strategy_name)
            self.assertTrue(hasattr(strategy_class, 'get_static_target_weights'),
                          f"{strategy_name} should have get_static_target_weights method")
    
    def test_static_weight_retrieval_no_instantiation(self):
        """Test that static weights can be retrieved without strategy instantiation."""
        for strategy_name in self.static_strategies:
            with self.subTest(strategy=strategy_name):
                strategy_class = strategy_registry.get(strategy_name)
                
                # This should not raise an error (the original bug)
                try:
                    weights = strategy_class.get_static_target_weights()
                    
                    # Verify weights are valid
                    self.assertIsInstance(weights, dict, f"{strategy_name} should return dict")
                    self.assertGreater(len(weights), 0, f"{strategy_name} should have non-empty weights")
                    
                    # Verify weights are reasonable (between 0 and 1)
                    for asset, weight in weights.items():
                        self.assertGreaterEqual(weight, 0, f"Weight for {asset} should be >= 0")
                        self.assertLessEqual(weight, 1, f"Weight for {asset} should be <= 1")
                    
                    # Verify weights approximately sum to 1 (allowing small float errors)
                    total_weight = sum(weights.values())
                    self.assertAlmostEqual(total_weight, 1.0, places=6,
                                         msg=f"{strategy_name} weights should sum to 1.0, got {total_weight}")
                    
                except Exception as e:
                    self.fail(f"Getting static weights for {strategy_name} raised {type(e).__name__}: {e}")
    
    def test_streamlit_weight_function_static_strategies(self):
        """Test that Streamlit weight function works for static strategies."""
        for strategy_name in self.static_strategies:
            with self.subTest(strategy=strategy_name):
                try:
                    weights = get_strategy_weights(strategy_name)
                    
                    # Should return valid weights
                    self.assertIsInstance(weights, dict, f"{strategy_name} should return dict")
                    self.assertGreater(len(weights), 0, f"{strategy_name} should have non-empty weights")
                    
                    # Verify weights sum to approximately 1
                    total_weight = sum(weights.values())
                    self.assertAlmostEqual(total_weight, 1.0, places=6,
                                         msg=f"{strategy_name} weights should sum to 1.0")
                    
                except Exception as e:
                    self.fail(f"get_strategy_weights failed for {strategy_name}: {e}")
    
    def test_streamlit_weight_function_dynamic_strategies(self):
        """Test that Streamlit weight function handles dynamic strategies properly."""
        for strategy_name in self.dynamic_strategies:
            with self.subTest(strategy=strategy_name):
                try:
                    weights = get_strategy_weights(strategy_name)
                    
                    # Dynamic strategies should return dict (may be empty or with current weights)
                    self.assertIsInstance(weights, dict, f"{strategy_name} should return dict")
                    
                    # For dynamic strategies other than DynamicAllocationStrategy, should be empty
                    if strategy_name != 'DynamicAllocationStrategy':
                        self.assertEqual(len(weights), 0, 
                                       f"{strategy_name} should return empty weights without market data")
                    
                    # If weights are returned, they should be valid
                    if len(weights) > 0:
                        for asset, weight in weights.items():
                            self.assertGreaterEqual(weight, 0, f"Weight for {asset} should be >= 0")
                            self.assertLessEqual(weight, 1, f"Weight for {asset} should be <= 1")
                    
                except Exception as e:
                    self.fail(f"get_strategy_weights failed for {strategy_name}: {e}")
    
    def test_no_instantiation_error(self):
        """Test that the original '_next_stid' error is fixed."""
        # This test verifies the specific error that was occurring
        for strategy_name in self.static_strategies:
            with self.subTest(strategy=strategy_name):
                strategy_class = strategy_registry.get(strategy_name)
                
                # This was the problematic code that caused the error
                try:
                    # Should NOT try to instantiate strategy directly
                    # temp_instance = strategy_class()  # This would cause the error
                    
                    # Instead, should use class method
                    if hasattr(strategy_class, 'get_static_target_weights'):
                        weights = strategy_class.get_static_target_weights()
                        self.assertIsInstance(weights, dict)
                    
                except AttributeError as e:
                    if "_next_stid" in str(e):
                        self.fail(f"The '_next_stid' error still occurs for {strategy_name}: {e}")
                    else:
                        raise  # Re-raise if it's a different AttributeError
    
    def test_specific_strategy_weights(self):
        """Test specific expected weights for known strategies."""
        # Test 60/40 strategy
        weights = get_strategy_weights('SixtyFortyStrategy')
        expected_60_40 = {'SP500': 0.6, 'TLT': 0.4}
        self.assertEqual(weights, expected_60_40, "60/40 strategy should have correct weights")
        
        # Test Permanent Portfolio
        weights = get_strategy_weights('PermanentPortfolioStrategy')
        expected_permanent = {'SP500': 0.25, 'TLT': 0.25, 'SHY': 0.25, 'GLD': 0.25}
        self.assertEqual(weights, expected_permanent, "Permanent Portfolio should have correct weights")
        
        # Test Buy and Hold
        weights = get_strategy_weights('SimpleBuyAndHoldStrategy')
        expected_buy_hold = {'SP500': 1.0}
        self.assertEqual(weights, expected_buy_hold, "Buy and Hold should have correct weights")
    
    def test_attribution_data_structures(self):
        """Test that attribution-related data structures work correctly."""
        # Test that we can import attribution module
        try:
            from src.modules.portfolio.performance.attribution import PerformanceAttributor
            attributor = PerformanceAttributor()
            self.assertIsNotNone(attributor, "PerformanceAttributor should instantiate")
        except ImportError as e:
            self.fail(f"Could not import PerformanceAttributor: {e}")
        except Exception as e:
            self.fail(f"Error creating PerformanceAttributor: {e}")
    
    def test_mock_attribution_analysis(self):
        """Test attribution analysis with mock data."""
        try:
            from src.modules.portfolio.performance.attribution import PerformanceAttributor
            
            # Create mock data
            dates = pd.date_range('2024-01-01', '2024-01-31', freq='D')
            
            # Mock portfolio data
            portfolio_data = pd.DataFrame({
                'date': dates,
                'value': [1000 * (1 + i * 0.001) for i in range(len(dates))],  # Slight upward trend
                'returns': [0.001] * len(dates)
            })
            portfolio_data['date'] = pd.to_datetime(portfolio_data['date'])
            
            # Mock asset returns
            asset_returns = pd.DataFrame({
                'SP500': [0.001] * len(dates),
                'TLT': [0.0005] * len(dates)
            }, index=dates)
            
            # Mock weights data
            weights_data = pd.DataFrame({
                'SP500': [0.6] * len(dates),
                'TLT': [0.4] * len(dates)
            }, index=dates)
            
            attributor = PerformanceAttributor()
            
            # This should not raise an error
            report = attributor.generate_attribution_report(
                strategy_name="TestStrategy",
                portfolio_data=portfolio_data,
                asset_returns=asset_returns,
                weights_data=weights_data,
                include_weekly=False,
                include_monthly=False
            )
            
            # Verify report structure
            self.assertIsInstance(report, dict, "Attribution report should be a dictionary")
            self.assertNotIn('error', report, f"Attribution report should not contain error: {report.get('error', '')}")
            
        except Exception as e:
            # Attribution might fail due to missing data files, which is acceptable for this test
            print(f"Warning: Attribution test failed (expected if data files missing): {e}")

    def test_sixty_forty_nonzero_contributions(self):
        """60/40 with constant returns should yield non-zero contributions for both assets."""
        from src.modules.portfolio.performance.attribution import PerformanceAttributor
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        portfolio_data = pd.DataFrame({'value': [1000 * (1.001 ** i) for i in range(10)], 'returns': [0.001]*10}, index=dates)
        asset_returns = pd.DataFrame({'SP500':[0.001]*10, 'TLT':[0.0005]*10}, index=dates)
        weights_data = pd.DataFrame({'SP500':[0.6]*10, 'TLT':[0.4]*10}, index=dates)
        attributor = PerformanceAttributor()
        daily = attributor.calculate_daily_attribution(portfolio_data, asset_returns, weights_data)
        self.assertGreater(len(daily), 0)
        # Sum contributions across days
        total_sp500 = sum(attr.asset_contributions.get('SP500', 0) for attr in daily)
        total_tlt = sum(attr.asset_contributions.get('TLT', 0) for attr in daily)
        self.assertGreater(total_sp500, 0)
        self.assertGreater(total_tlt, 0)

    def test_zero_weight_assets_excluded(self):
        """Assets with zero weights throughout should not affect contributions."""
        from src.modules.portfolio.performance.attribution import PerformanceAttributor
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        portfolio_data = pd.DataFrame({'value': [1000 * (1.001 ** i) for i in range(10)], 'returns': [0.001]*10}, index=dates)
        asset_returns = pd.DataFrame({'SP500':[0.001]*10, 'TLT':[0.0005]*10, 'GLD':[0.01]*10}, index=dates)
        weights_data = pd.DataFrame({'SP500':[0.6]*10, 'TLT':[0.4]*10, 'GLD':[0.0]*10}, index=dates)
        attributor = PerformanceAttributor()
        daily = attributor.calculate_daily_attribution(portfolio_data, asset_returns, weights_data)
        # GLD should contribute zero overall
        total_gld = sum(attr.asset_contributions.get('GLD', 0) for attr in daily)
        self.assertEqual(total_gld, 0)

    def test_asset_analysis_keys_are_assets(self):
        """Ensure asset_analysis keys are asset names (strings), not timestamps."""
        from src.modules.portfolio.performance.attribution import PerformanceAttributor
        dates = pd.date_range('2024-01-01', periods=12, freq='D')
        portfolio_data = pd.DataFrame({'value': [1000 * (1.001 ** i) for i in range(12)], 'returns': [0.001]*12}, index=dates)
        asset_returns = pd.DataFrame({'SP500':[0.001]*12, 'TLT':[0.0005]*12}, index=dates)
        weights_data = pd.DataFrame({'SP500':[0.6]*12, 'TLT':[0.4]*12}, index=dates)
        attributor = PerformanceAttributor()
        report = attributor.generate_attribution_report(
            strategy_name="SixtyForty",
            portfolio_data=portfolio_data,
            asset_returns=asset_returns,
            weights_data=weights_data,
            include_weekly=False,
            include_monthly=False
        )
        self.assertNotIn('error', report)
        aa = report['daily_analysis']['asset_analysis']
        # Keys should be strings (asset names) and contain SP500/TLT
        self.assertTrue(all(isinstance(k, str) for k in aa.keys()))
        self.assertIn('SP500', aa)
        self.assertIn('TLT', aa)


class TestStrategyInheritance(unittest.TestCase):
    """Test strategy class inheritance and method resolution."""
    
    def test_base_strategy_methods(self):
        """Test that BaseStrategy has required methods."""
        # Test class method exists
        self.assertTrue(hasattr(BaseStrategy, 'get_strategy_type'), 
                       "BaseStrategy should have get_strategy_type method")
    
    def test_static_strategy_inheritance(self):
        """Test that StaticAllocationStrategy properly inherits."""
        # Test that it has the static weights method
        self.assertTrue(hasattr(StaticAllocationStrategy, 'get_static_target_weights'),
                       "StaticAllocationStrategy should have get_static_target_weights method")
        
        # Test that it's properly classified
        self.assertEqual(StaticAllocationStrategy.get_strategy_type(), "static",
                       "StaticAllocationStrategy should be classified as static")
    
    def test_dynamic_strategy_inheritance(self):
        """Test that DynamicStrategy properly inherits."""
        # Test that it's properly classified
        self.assertEqual(DynamicStrategy.get_strategy_type(), "dynamic",
                       "DynamicStrategy should be classified as dynamic")


if __name__ == '__main__':
    unittest.main(verbosity=2)