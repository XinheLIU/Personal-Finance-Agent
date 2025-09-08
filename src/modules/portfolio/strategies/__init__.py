"""
Strategy module for investment strategies.

Contains:
- base: Base strategy classes
- builtin: Built-in strategy implementations
- custom: User-defined custom strategies
- registry: Strategy registry for management
- utils: Utility functions for strategies
"""

from .base import BaseStrategy
from .registry import StrategyRegistry
from .builtin import *

__all__ = ['BaseStrategy', 'StrategyRegistry']
