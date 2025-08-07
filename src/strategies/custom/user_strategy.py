"""
User-defined strategy creation utilities.
Allows users to create simple fixed-weight strategies through configuration.
"""
import json
import os
from typing import Dict
from src.strategies.base import StaticAllocationStrategy

class UserDefinedStrategy(StaticAllocationStrategy):
    """
    User-defined strategy loaded from configuration file.
    """
    def __init__(self, weights: Dict[str, float]):
        super().__init__()
        self._target_weights = weights
    
    def get_target_weights(self) -> Dict[str, float]:
        return self._target_weights

class StrategyBuilder:
    """
    Utility class for building user-defined strategies.
    """
    
    @staticmethod
    def create_strategy(name: str, weights: Dict[str, float]) -> type:
        """
        Create a new strategy class with given weights.
        """
        def __init__(self):
            super(self.__class__, self).__init__()
            self._target_weights = weights.copy()
        
        def get_target_weights(self):
            return self._target_weights
        
        # Create new strategy class
        strategy_class = type(name, (StaticAllocationStrategy,), {
            '__init__': __init__,
            'get_target_weights': get_target_weights,
            '__doc__': f"User-defined strategy with weights: {weights}"
        })
        
        return strategy_class
    
    @staticmethod
    def save_strategy(name: str, weights: Dict[str, float], filename: str = "user_strategies.json"):
        """
        Save user strategy to file.
        """
        strategies_file = os.path.join("src", "strategies", "custom", filename)
        
        # Load existing strategies
        strategies = {}
        if os.path.exists(strategies_file):
            with open(strategies_file, 'r') as f:
                strategies = json.load(f)
        
        # Add new strategy
        strategies[name] = weights
        
        # Save back to file
        with open(strategies_file, 'w') as f:
            json.dump(strategies, f, indent=2)
    
    @staticmethod
    def load_strategies(filename: str = "user_strategies.json") -> Dict[str, Dict[str, float]]:
        """
        Load user strategies from file.
        """
        strategies_file = os.path.join("src", "strategies", "custom", filename)
        
        if not os.path.exists(strategies_file):
            return {}
        
        with open(strategies_file, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def validate_weights(weights: Dict[str, float]) -> tuple[bool, str]:
        """
        Validate user-provided weights.
        """
        if not weights:
            return False, "Weights dictionary is empty"
        
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 0.01:  # Allow 1% tolerance
            return False, f"Total weights must sum to 1.0, got {total_weight:.3f}"
        
        for asset, weight in weights.items():
            if weight < 0:
                return False, f"Weight for {asset} must be non-negative"
            if weight > 1:
                return False, f"Weight for {asset} must be <= 1.0"
        
        return True, "Valid weights"