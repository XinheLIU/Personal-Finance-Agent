"""
Focused test specifically for the strategy instantiation bug fix.
Tests that the '_next_stid' error is resolved.
"""
import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.modules.portfolio.strategies.registry import strategy_registry
from src.streamlit_app import get_strategy_weights


class TestStrategyInstantiationFix(unittest.TestCase):
    """Test that the original '_next_stid' AttributeError is fixed."""
    
    def test_original_error_fixed_60_40_strategy(self):
        """Test that SixtyFortyStrategy works without instantiation error."""
        # This was the exact error scenario that was failing
        strategy_class = strategy_registry.get('SixtyFortyStrategy')
        self.assertIsNotNone(strategy_class, "SixtyFortyStrategy should exist in registry")
        
        # The original error happened here when trying to instantiate without Cerebro context
        # temp_instance = strategy_class()  # This would cause: AttributeError: 'NoneType' object has no attribute '_next_stid'
        
        # Now it should work with class methods
        weights = strategy_class.get_static_target_weights()
        expected_weights = {'SP500': 0.6, 'TLT': 0.4}
        self.assertEqual(weights, expected_weights, "Should get correct 60/40 weights")
    
    def test_streamlit_function_no_error(self):
        """Test that get_strategy_weights function works without errors."""
        # This was the function that was failing in the Streamlit app
        weights = get_strategy_weights('SixtyFortyStrategy')
        
        self.assertIsInstance(weights, dict, "Should return a dictionary")
        self.assertEqual(len(weights), 2, "60/40 strategy should have 2 assets")
        self.assertIn('SP500', weights, "Should have SP500")
        self.assertIn('TLT', weights, "Should have TLT")
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=6, msg="Weights should sum to 1.0")
    
    def test_all_static_strategies_work(self):
        """Test that all static strategies work without instantiation errors."""
        static_strategies = [
            'SixtyFortyStrategy',
            'PermanentPortfolioStrategy', 
            'AllWeatherPortfolioStrategy',
            'DavidSwensenStrategy',
            'SimpleBuyAndHoldStrategy',
            'EqualWeightStrategy'
        ]
        
        for strategy_name in static_strategies:
            with self.subTest(strategy=strategy_name):
                # Should not raise AttributeError with '_next_stid'
                weights = get_strategy_weights(strategy_name)
                self.assertIsInstance(weights, dict, f"{strategy_name} should return dict")
                self.assertGreater(len(weights), 0, f"{strategy_name} should have weights")
    
    def test_dynamic_strategies_handled_gracefully(self):
        """Test that dynamic strategies are handled without errors."""
        dynamic_strategies = ['DynamicAllocationStrategy', 'MomentumStrategy', 'RiskParityStrategy']
        
        for strategy_name in dynamic_strategies:
            with self.subTest(strategy=strategy_name):
                # Should not raise any errors, even if weights are empty
                try:
                    weights = get_strategy_weights(strategy_name)
                    self.assertIsInstance(weights, dict, f"{strategy_name} should return dict")
                except Exception as e:
                    self.fail(f"get_strategy_weights failed for {strategy_name}: {e}")
    
    def test_specific_error_message_not_present(self):
        """Test that the specific '_next_stid' error doesn't occur."""
        strategy_class = strategy_registry.get('SixtyFortyStrategy')
        
        try:
            # Use the fixed approach
            weights = get_strategy_weights('SixtyFortyStrategy')
            # If we get here, the error is fixed
            self.assertIsInstance(weights, dict)
        except AttributeError as e:
            error_msg = str(e)
            self.assertNotIn('_next_stid', error_msg, 
                           f"The '_next_stid' error should be fixed, but got: {error_msg}")
        except Exception as e:
            # Other exceptions are acceptable, just not the specific _next_stid error
            pass


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)