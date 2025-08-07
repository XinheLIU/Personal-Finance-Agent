"""
Strategy registry for managing all available strategies.
"""
from typing import Dict, Type, Any
from src.strategies.builtin import *
from src.strategies.base import BaseStrategy

class StrategyRegistry:
    """
    Registry for managing all available strategies.
    """
    
    def __init__(self):
        self._strategies: Dict[str, Type[BaseStrategy]] = {}
        self._register_builtin_strategies()
        self._register_user_strategies()
    
    def _register_builtin_strategies(self):
        """Register all built-in strategies"""
        builtin_strategies = [
            SixtyFortyStrategy,
            PermanentPortfolioStrategy,
            AllWeatherPortfolioStrategy,
            DavidSwensenStrategy,
            SimpleBuyAndHoldStrategy,
            EqualWeightStrategy,
            DynamicAllocationStrategy,
            MomentumStrategy,
            RiskParityStrategy
        ]
        
        for strategy_class in builtin_strategies:
            self.register(strategy_class.__name__, strategy_class)
    
    def _register_user_strategies(self):
        """Register user-defined strategies"""
        try:
            from .custom.user_strategy import StrategyBuilder
            user_strategies = StrategyBuilder.load_strategies()
            
            for name, weights in user_strategies.items():
                strategy_class = StrategyBuilder.create_strategy(name, weights)
                self.register(name, strategy_class)
        except Exception as e:
            # Log but don't fail if user strategies can't be loaded
            print(f"Warning: Could not load user strategies: {e}")
    
    def register(self, name: str, strategy_class: Type[BaseStrategy]):
        """Register a new strategy"""
        if not issubclass(strategy_class, BaseStrategy):
            raise ValueError(f"Strategy {name} must inherit from BaseStrategy")
        self._strategies[name] = strategy_class
    
    def get(self, name: str) -> Type[BaseStrategy]:
        """Get strategy by name"""
        return self._strategies.get(name)
    
    def list_strategies(self) -> Dict[str, str]:
        """List all available strategies with descriptions"""
        strategies = {}
        for name, strategy_class in self._strategies.items():
            strategies[name] = strategy_class.__doc__.strip().split('\n')[0] if strategy_class.__doc__ else "No description"
        return strategies
    
    def get_builtin_strategies(self) -> Dict[str, str]:
        """Get only built-in strategies"""
        return self.list_strategies()

# Global registry instance
strategy_registry = StrategyRegistry()