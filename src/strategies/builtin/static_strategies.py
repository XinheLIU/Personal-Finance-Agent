"""
Built-in static allocation strategies for Personal Finance Agent.
These strategies use fixed allocations and rebalance periodically.
"""
from src.strategies.base import StaticAllocationStrategy
from typing import Dict

class SixtyFortyStrategy(StaticAllocationStrategy):
    """
    Classic 60/40 portfolio: 60% stocks, 40% bonds.
    Uses SP500 for stocks and TLT for bonds.
    """
    def get_target_weights(self) -> Dict[str, float]:
        return {
            'SP500': 0.60,
            'TLT': 0.40
        }

class PermanentPortfolioStrategy(StaticAllocationStrategy):
    """
    Harry Browne's Permanent Portfolio:
    25% stocks, 25% long-term bonds, 25% cash, 25% gold
    """
    def get_target_weights(self) -> Dict[str, float]:
        return {
            'SP500': 0.25,
            'TLT': 0.25,
            'CASH': 0.25,
            'GLD': 0.25
        }

class AllWeatherPortfolioStrategy(StaticAllocationStrategy):
    """
    Ray Dalio's All Weather Portfolio approximation:
    30% stocks, 40% long-term bonds, 15% intermediate bonds, 7.5% gold, 7.5% commodities
    """
    def get_target_weights(self) -> Dict[str, float]:
        return {
            'SP500': 0.30,
            'TLT': 0.40,
            'CASH': 0.15,  # Using CASH as proxy for intermediate bonds
            'GLD': 0.075,
            'CSI300': 0.075  # Using CSI300 as proxy for commodities exposure
        }

class DavidSwensenStrategy(StaticAllocationStrategy):
    """
    David Swensen's Yale Model (simplified for retail investors):
    30% US stocks, 20% international stocks, 20% real estate, 30% bonds
    """
    def get_target_weights(self) -> Dict[str, float]:
        return {
            'SP500': 0.30,
            'NASDAQ100': 0.20,  # Using NASDAQ100 as proxy for international
            'TLT': 0.30,
            'GLD': 0.20  # Using GLD as proxy for real estate
        }

class SimpleBuyAndHoldStrategy(StaticAllocationStrategy):
    """
    Simple buy and hold strategy that invests 100% in the first asset.
    """
    def __init__(self):
        super().__init__()
        self.bought = False
        
    def get_target_weights(self) -> Dict[str, float]:
        return {'SP500': 1.0}
    
    def next(self):
        if not self.bought:
            target_weights = self.get_target_weights()
            self.rebalance_portfolio(target_weights)
            self.bought = True
            self.last_rebalance = len(self)

class EqualWeightStrategy(StaticAllocationStrategy):
    """
    Equal weight strategy across all available assets.
    """
    def get_target_weights(self) -> Dict[str, float]:
        # Get all available assets from data feeds
        assets = [data._name for data in self.datas]
        weight = 1.0 / len(assets)
        return {asset: weight for asset in assets}