"""
Configuration Module
Centralized configuration management for the quant investment system.
"""

# Import main configurations for backward compatibility
from .assets import *
from .system import *

__all__ = ['ASSETS', 'TRADABLE_ASSETS', 'INDEX_ASSETS', 'PE_ASSETS', 'YIELD_ASSETS', 
           'INITIAL_CAPITAL', 'COMMISSION', 'DYNAMIC_STRATEGY_PARAMS']