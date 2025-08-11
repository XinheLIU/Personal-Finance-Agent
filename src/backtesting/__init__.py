"""
Backtesting Platform Module
Functions like an offline testing environment in machine learning.
Allows strategies to be tested on historical data with execution lag modeling.
"""

from .engine import EnhancedBacktestEngine

__all__ = ['EnhancedBacktestEngine']