
import unittest
import os
from src.main import run_backtest
from src.strategy import (
    DynamicAllocationStrategy,
    BuyAndHoldStrategy,
    SixtyFortyStrategy,
    PermanentPortfolioStrategy,
    AllWeatherPortfolioStrategy,
    DavidSwensenPortfolioStrategy
)

class TestBacktest(unittest.TestCase):
    def test_dynamic_allocation_strategy(self):
        results = run_backtest(DynamicAllocationStrategy, "Dynamic Allocation Strategy")
        self.assertIsNotNone(results)
        self.assertIn('final_value', results)

    def test_buy_and_hold_strategy(self):
        results = run_backtest(BuyAndHoldStrategy, "Buy and Hold Strategy (S&P 500)")
        self.assertIsNotNone(results)
        self.assertIn('final_value', results)

    def test_sixty_forty_strategy(self):
        results = run_backtest(SixtyFortyStrategy, "60/40 Portfolio")
        self.assertIsNotNone(results)
        self.assertIn('final_value', results)

    def test_permanent_portfolio_strategy(self):
        results = run_backtest(PermanentPortfolioStrategy, "Permanent Portfolio")
        self.assertIsNotNone(results)
        self.assertIn('final_value', results)

    def test_all_weather_portfolio_strategy(self):
        results = run_backtest(AllWeatherPortfolioStrategy, "All Weather Portfolio")
        self.assertIsNotNone(results)
        self.assertIn('final_value', results)

    def test_david_swensen_portfolio_strategy(self):
        results = run_backtest(DavidSwensenPortfolioStrategy, "David Swensen Portfolio")
        self.assertIsNotNone(results)
        self.assertIn('final_value', results)

if __name__ == '__main__':
    unittest.main()
