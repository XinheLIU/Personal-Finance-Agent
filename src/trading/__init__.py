"""
Trading Module
Executes trades as instructed by management or strategy modules.
Interfaces with external trading APIs and handles order execution.
"""

from .executor import TradeExecutor
from .order_manager import OrderManager
from .broker_interface import BrokerInterface

__all__ = ['TradeExecutor', 'OrderManager', 'BrokerInterface']