"""
Built-in static allocation strategies for Personal Finance Agent.
These strategies use fixed allocations and rebalance periodically.
"""
from src.modules.portfolio.strategies.base import StaticAllocationStrategy
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
    
    @classmethod
    def get_static_target_weights(cls) -> Dict[str, float]:
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
            'SHY': 0.25,  # Short-term Treasury bonds as cash equivalent
            'GLD': 0.25
        }
    
    @classmethod
    def get_static_target_weights(cls) -> Dict[str, float]:
        return {
            'SP500': 0.25,
            'TLT': 0.25,
            'SHY': 0.25,
            'GLD': 0.25
        }

class AllWeatherPortfolioStrategy(StaticAllocationStrategy):
    """
    Ray Dalio's All Weather Portfolio approximation:
    30% stocks, 40% long-term bonds, 15% intermediate bonds, 7.5% gold, 7.5% commodities
    """
    def get_target_weights(self) -> Dict[str, float]:
        # Using available ETFs, with fallback allocations for missing data
        weights = {
            'SP500': 0.30,
            'TLT': 0.55,  # Combined long-term and intermediate bonds
            'GLD': 0.075,
            'DBC': 0.075   # Commodity ETF (available)
        }
        
        # Check available data and adjust weights
        available_assets = [data._name for data in self.datas]
        filtered_weights = {k: v for k, v in weights.items() if k in available_assets}
        
        # Normalize if some assets are missing
        total_weight = sum(filtered_weights.values())
        if total_weight > 0:
            scale_factor = 1.0 / total_weight
            for asset in filtered_weights:
                filtered_weights[asset] *= scale_factor
        
        return filtered_weights
    
    @classmethod
    def get_static_target_weights(cls) -> Dict[str, float]:
        return {
            'SP500': 0.30,
            'TLT': 0.55,
            'GLD': 0.075,
            'DBC': 0.075
        }

class DavidSwensenStrategy(StaticAllocationStrategy):
    """
    David Swensen's Yale Model (simplified for retail investors):
    30% US stocks, 15% developed international, 5% emerging markets, 
    15% intermediate-term bonds, 15% TIPS, 20% real estate
    """
    def get_target_weights(self) -> Dict[str, float]:
        # Using available ETFs, with fallback allocations for missing data
        weights = {
            'SP500': 0.30,      # US Total Stock Market
            'VEA': 0.15,        # Developed International Markets (available)
            'TLT': 0.20,        # Bonds (fallback for IEF+TIP)
            'GLD': 0.20,        # Real assets (fallback for VNQ)
            'NASDAQ100': 0.15   # Additional US exposure (fallback for VWO)
        }
        
        # Check available data and adjust weights
        available_assets = [data._name for data in self.datas]
        filtered_weights = {k: v for k, v in weights.items() if k in available_assets}
        
        # Normalize if some assets are missing
        total_weight = sum(filtered_weights.values())
        if total_weight > 0:
            scale_factor = 1.0 / total_weight
            for asset in filtered_weights:
                filtered_weights[asset] *= scale_factor
        
        return filtered_weights
    
    @classmethod
    def get_static_target_weights(cls) -> Dict[str, float]:
        return {
            'SP500': 0.30,
            'VEA': 0.15,
            'TLT': 0.20,
            'GLD': 0.20,
            'NASDAQ100': 0.15
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
    
    @classmethod
    def get_static_target_weights(cls) -> Dict[str, float]:
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
    
    @classmethod
    def get_static_target_weights(cls) -> Dict[str, float]:
        # For static display, use a representative equal-weight portfolio
        # This will be overridden by dynamic weights during actual backtesting
        return {
            'CSI300': 0.2,
            'SP500': 0.2,
            'TLT': 0.2,
            'GLD': 0.2,
            'VEA': 0.2
        }