
import unittest
import os
from src.backtest_runner import run_backtest
from src.strategy import (
    DynamicAllocationStrategy,
    BuyAndHoldStrategy,
    SixtyFortyStrategy,
    PermanentPortfolioStrategy,
    AllWeatherPortfolioStrategy,
    DavidSwensenPortfolioStrategy
)

class TestBacktest(unittest.TestCase):
    def setUp(self):
        """Set up test parameters"""
        self.initial_capital = 1000000.0
        self.min_acceptable_return = 0.01  # 1% minimum return over test period
        self.max_acceptable_drawdown = 0.80  # 80% maximum drawdown (more realistic)
        self.min_sharpe_ratio = -2.0  # Allow negative Sharpe ratios but not extremely bad ones
        
    def validate_strategy_results(self, results, strategy_name):
        """Validate that strategy results are reasonable"""
        self.assertIsNotNone(results, f"{strategy_name}: Results should not be None")
        self.assertIn('final_value', results, f"{strategy_name}: Should have final_value")
        self.assertIn('total_return', results, f"{strategy_name}: Should have total_return")
        self.assertIn('annualized_return', results, f"{strategy_name}: Should have annualized_return")
        self.assertIn('max_drawdown', results, f"{strategy_name}: Should have max_drawdown")
        self.assertIn('sharpe_ratio', results, f"{strategy_name}: Should have sharpe_ratio")
        
        # Validate basic performance metrics
        self.assertGreater(results['final_value'], 0, f"{strategy_name}: Final value should be positive")
        self.assertGreaterEqual(results['total_return'], self.min_acceptable_return, 
                               f"{strategy_name}: Total return {results['total_return']:.2%} should be >= {self.min_acceptable_return:.2%}")
        self.assertLessEqual(results['max_drawdown'], self.max_acceptable_drawdown,
                            f"{strategy_name}: Max drawdown {results['max_drawdown']:.2%} should be <= {self.max_acceptable_drawdown:.2%}")
        self.assertGreaterEqual(results['sharpe_ratio'], self.min_sharpe_ratio,
                               f"{strategy_name}: Sharpe ratio {results['sharpe_ratio']:.3f} should be >= {self.min_sharpe_ratio}")
        
        # Validate that strategy actually invested (final value should be different from initial)
        self.assertNotEqual(results['final_value'], self.initial_capital,
                           f"{strategy_name}: Final value should not equal initial capital (indicates no investment)")
        
        print(f"✅ {strategy_name}: {results['total_return']:.2f}% return, {results['max_drawdown']:.2f}% max drawdown, Sharpe {results['sharpe_ratio']:.3f}")

    def test_dynamic_allocation_strategy(self):
        """Test Dynamic Allocation strategy with comprehensive validation"""
        results = run_backtest(DynamicAllocationStrategy, "Dynamic Allocation Strategy")
        self.validate_strategy_results(results, "Dynamic Allocation Strategy")
        
        # Strategy-specific validations
        self.assertGreater(results['total_return'], 0.05, "Dynamic Allocation should generate >5% return over test period")

    def test_buy_and_hold_strategy(self):
        """Test Buy and Hold strategy with comprehensive validation"""
        results = run_backtest(BuyAndHoldStrategy, "Buy and Hold Strategy (S&P 500)")
        self.validate_strategy_results(results, "Buy and Hold Strategy")
        
        # Buy and Hold should have significant returns over the test period
        self.assertGreater(results['total_return'], 0.10, "Buy and Hold should generate >10% return over test period")

    def test_sixty_forty_strategy(self):
        """Test 60/40 Portfolio strategy with comprehensive validation"""
        results = run_backtest(SixtyFortyStrategy, "60/40 Portfolio")
        self.validate_strategy_results(results, "60/40 Portfolio")
        
        # 60/40 should have moderate returns and lower drawdown than pure equity
        self.assertGreater(results['total_return'], 0.05, "60/40 Portfolio should generate >5% return over test period")
        self.assertLess(results['max_drawdown'], 0.30, "60/40 Portfolio should have <30% max drawdown")

    def test_permanent_portfolio_strategy(self):
        """Test Permanent Portfolio strategy with comprehensive validation"""
        results = run_backtest(PermanentPortfolioStrategy, "Permanent Portfolio")
        self.validate_strategy_results(results, "Permanent Portfolio")
        
        # Permanent Portfolio should have lower drawdown due to diversification
        self.assertLess(results['max_drawdown'], 0.25, "Permanent Portfolio should have <25% max drawdown")

    def test_all_weather_portfolio_strategy(self):
        """Test All Weather Portfolio strategy with comprehensive validation"""
        results = run_backtest(AllWeatherPortfolioStrategy, "All Weather Portfolio")
        self.validate_strategy_results(results, "All Weather Portfolio")
        
        # All Weather should have moderate returns and controlled drawdown
        self.assertGreater(results['total_return'], 0.02, "All Weather Portfolio should generate >2% return over test period")

    def test_david_swensen_portfolio_strategy(self):
        """Test David Swensen Portfolio strategy with comprehensive validation"""
        results = run_backtest(DavidSwensenPortfolioStrategy, "David Swensen Portfolio")
        self.validate_strategy_results(results, "David Swensen Portfolio")
        
        # David Swensen should have good returns with moderate risk
        self.assertGreater(results['total_return'], 0.05, "David Swensen Portfolio should generate >5% return over test period")

    def test_all_strategies_comparison(self):
        """Test that all strategies perform differently (not all returning 0%)"""
        strategies = [
            (DynamicAllocationStrategy, "Dynamic Allocation"),
            (BuyAndHoldStrategy, "Buy and Hold"),
            (SixtyFortyStrategy, "60/40 Portfolio"),
            (PermanentPortfolioStrategy, "Permanent Portfolio"),
            (AllWeatherPortfolioStrategy, "All Weather Portfolio"),
            (DavidSwensenPortfolioStrategy, "David Swensen Portfolio")
        ]
        
        results_dict = {}
        for strategy_class, strategy_name in strategies:
            results = run_backtest(strategy_class, strategy_name)
            results_dict[strategy_name] = results['total_return']
            print(f"{strategy_name}: {results['total_return']:.2f}% return")
        
        # Check that not all strategies return 0%
        zero_returns = sum(1 for ret in results_dict.values() if ret == 0)
        self.assertLess(zero_returns, len(strategies), 
                       f"All strategies should not return 0%. Found {zero_returns} strategies with 0% return")
        
        # Check that strategies have different performance (not all identical)
        unique_returns = len(set(results_dict.values()))
        self.assertGreater(unique_returns, 1, 
                          f"Strategies should have different performance. Found {unique_returns} unique return values")

if __name__ == '__main__':
    unittest.main()
