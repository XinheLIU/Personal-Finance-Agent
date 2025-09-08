"""
Trading Module
Executes trades as instructed by management or strategy modules.
Interfaces with external trading APIs and handles order execution.
"""

from .executor import TradeExecutor

__all__ = ['TradeExecutor']