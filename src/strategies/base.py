"""
Base strategy classes for Personal Finance Agent.
Provides foundation for all strategy implementations.
"""
import backtrader as bt
from abc import abstractmethod
from typing import Dict, Any, Optional

class BaseStrategy(bt.Strategy):
    """
    Abstract base class for all investment strategies.
    Provides common functionality and interface for strategy implementations.
    """
    
    def __init__(self):
        super().__init__()
        self.strategy_name = self.__class__.__name__
        self.portfolio_values = []
        self.portfolio_dates = []
        self.rebalance_log = []
        # Stores last weight calculation breakdown for transparency
        self.last_weight_calc_details: Optional[Dict[str, Any]] = None
        
    def next(self):
        """Common next() implementation for all strategies"""
        current_date = self.datas[0].datetime.date(0)
        portfolio_value = self.broker.getvalue()
        self.portfolio_values.append(portfolio_value)
        self.portfolio_dates.append(current_date)
        
    def get_current_weights(self) -> Dict[str, float]:
        """Get current portfolio weights"""
        total_value = self.broker.getvalue()
        weights = {}
        
        for data in self.datas:
            position = self.getposition(data)
            if position.size != 0:
                position_value = position.size * data.close[0]
                weights[data._name] = position_value / total_value
            else:
                weights[data._name] = 0.0
        return weights
    
    def rebalance_portfolio(self, target_weights: Dict[str, float]):
        """Rebalance portfolio to target weights"""
        total_value = self.broker.getvalue()
        transactions = []
        # Capture current weights and current prices for transparency
        current_weights_snapshot = self.get_current_weights()
        current_prices_snapshot = {}
        
        for data in self.datas:
            asset_name = data._name
            target_weight = target_weights.get(asset_name, 0.0)
            target_value = total_value * target_weight
            
            current_position = self.getposition(data)
            current_price = data.close[0]
            current_prices_snapshot[asset_name] = float(current_price)
            current_value = current_position.size * current_price
            
            if target_value == 0 and current_position.size > 0:
                order = self.close(data)
                transactions.append(f"Close {asset_name}")
            elif target_value > 0:
                target_shares = int(target_value / data.close[0])
                shares_to_trade = target_shares - current_position.size
                
                if abs(shares_to_trade) > 0:
                    if shares_to_trade > 0:
                        self.buy(data=data, size=shares_to_trade)
                        transactions.append(f"Buy {shares_to_trade} of {asset_name}")
                    else:
                        self.sell(data=data, size=abs(shares_to_trade))
                        transactions.append(f"Sell {abs(shares_to_trade)} of {asset_name}")
        
        if transactions:
            rebalance_details = {
                'date': self.datas[0].datetime.date(0),
                'total_portfolio_value': total_value,
                'transactions': ", ".join(transactions),
                'current_weights': current_weights_snapshot,
                'prices': current_prices_snapshot,
                'rebalance_days': getattr(self.params, 'rebalance_days', None),
                'threshold': getattr(self.params, 'threshold', None),
            }
            for asset, weight in target_weights.items():
                rebalance_details[f'{asset}_target_weight'] = weight
            # Attach calculation details if provided by strategy implementation
            if getattr(self, 'last_weight_calc_details', None) is not None:
                rebalance_details['calculation_details'] = self.last_weight_calc_details
            self.rebalance_log.append(rebalance_details)

class StaticAllocationStrategy(BaseStrategy):
    """
    Base class for static allocation strategies (rebalancing only).
    """
    params = (
        ('rebalance_days', 30),
        ('threshold', 0.05),
    )
    
    def __init__(self):
        super().__init__()
        self.last_rebalance = 0
        
    def get_target_weights(self) -> Dict[str, float]:
        """Override this method to provide target weights"""
        return {}
    
    def need_rebalancing(self, target_weights: Dict[str, float], current_weights: Dict[str, float]) -> bool:
        """Check if rebalancing is needed"""
        for asset in target_weights:
            current = current_weights.get(asset, 0)
            target = target_weights[asset]
            if abs(current - target) > self.params.threshold:
                return True
        return False
    
    def next(self):
        super().next()
        
        if (len(self) - self.last_rebalance >= self.params.rebalance_days) or len(self) == 1:
            target_weights = self.get_target_weights()
            # For static strategies, record simple calculation details
            self.last_weight_calc_details = {
                'inputs': {
                    'strategy_type': 'static',
                    'rebalance_days': getattr(self.params, 'rebalance_days', None),
                    'threshold': getattr(self.params, 'threshold', None)
                },
                'outputs': {
                    'final_weights': target_weights.copy()
                }
            }
            current_weights = self.get_current_weights()
            
            if self.need_rebalancing(target_weights, current_weights) or len(self) == 1:
                self.rebalance_portfolio(target_weights)
                self.last_rebalance = len(self)

class DynamicStrategy(BaseStrategy):
    """
    Base class for dynamic strategies that adjust allocation based on market conditions.
    """
    params = (
        ('rebalance_days', 30),
        ('threshold', 0.05),
    )
    
    def __init__(self):
        super().__init__()
        self.last_rebalance = 0
        
    @abstractmethod
    def calculate_target_weights(self, current_date) -> Dict[str, float]:
        """Calculate target weights based on current market conditions"""
        pass
    
    def next(self):
        super().next()
        
        if (len(self) - self.last_rebalance >= self.params.rebalance_days) or len(self) == 1:
            current_date = self.datas[0].datetime.date(0)
            try:
                target_weights = self.calculate_target_weights(current_date)
                current_weights = self.get_current_weights()
                
                if len(self) == 1 or self.need_rebalancing_dynamic(target_weights, current_weights):
                    self.rebalance_portfolio(target_weights)
                    self.last_rebalance = len(self)
            except Exception as e:
                print(f"Strategy execution failed on {current_date}: {e}")
                raise
    
    def need_rebalancing_dynamic(self, target_weights: Dict[str, float], current_weights: Dict[str, float]) -> bool:
        """Check if rebalancing is needed for dynamic strategies"""
        for asset in target_weights:
            current = current_weights.get(asset, 0)
            target = target_weights[asset]
            if abs(current - target) > self.params.threshold:
                return True
        return False

class FixedWeightStrategy(StaticAllocationStrategy):
    """
    Fixed weight strategy for custom allocations.
    Allows setting target weights via parameters.
    """
    params = (
        ('rebalance_days', 30),
        ('threshold', 0.05),
        ('target_weights', {}),
    )
    
    def get_target_weights(self) -> Dict[str, float]:
        """Return the fixed target weights"""
        return self.params.target_weights