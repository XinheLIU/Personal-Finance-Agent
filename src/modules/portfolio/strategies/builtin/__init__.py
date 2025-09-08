"""
Built-in strategy implementations for Personal Finance Agent.
"""
from .static_strategies import (
    SixtyFortyStrategy,
    PermanentPortfolioStrategy,
    AllWeatherPortfolioStrategy,
    DavidSwensenStrategy,
    SimpleBuyAndHoldStrategy,
    EqualWeightStrategy
)

from .dynamic_strategies import (
    DynamicAllocationStrategy,
    MomentumStrategy,
    RiskParityStrategy
)

__all__ = [
    'SixtyFortyStrategy',
    'PermanentPortfolioStrategy', 
    'AllWeatherPortfolioStrategy',
    'DavidSwensenStrategy',
    'SimpleBuyAndHoldStrategy',
    'EqualWeightStrategy',
    'DynamicAllocationStrategy',
    'MomentumStrategy',
    'RiskParityStrategy'
]