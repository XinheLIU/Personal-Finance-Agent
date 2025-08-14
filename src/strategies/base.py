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
        # Track weights evolution for attribution analysis
        self.weights_evolution = []
        # Stores last weight calculation breakdown for transparency
        self.last_weight_calc_details: Optional[Dict[str, Any]] = None
        # Track last rebalance positions for richer logging
        self.last_rebalance_bar_index: int = 0
        self.last_rebalance_calendar_date = None
    
        
    def next(self):
        """Common next() implementation for all strategies"""
        current_date = self.datas[0].datetime.date(0)
        portfolio_value = self.broker.getvalue()
        self.portfolio_values.append(portfolio_value)
        self.portfolio_dates.append(current_date)
        
        # Capture weights evolution for attribution analysis
        current_weights = self.get_current_weights()
        weights_entry = {'date': current_date}
        weights_entry.update(current_weights)
        self.weights_evolution.append(weights_entry)
        
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
    
    def rebalance_portfolio(self, target_weights: Dict[str, float], rebalance_context: Optional[Dict[str, Any]] = None):
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
            # Attach context about time vs trading-day gaps and trigger reasons
            if rebalance_context:
                rebalance_details.update(rebalance_context)
            for asset, weight in target_weights.items():
                rebalance_details[f'{asset}_target_weight'] = weight
            # Attach calculation details if provided by strategy implementation
            if getattr(self, 'last_weight_calc_details', None) is not None:
                rebalance_details['calculation_details'] = self.last_weight_calc_details
            # Store target weights for rebalancing log
            rebalance_details['target_weights'] = target_weights.copy()
            self.rebalance_log.append(rebalance_details)

class StaticAllocationStrategy(BaseStrategy):
    """
    Base class for static allocation strategies (rebalancing only).
    """
    params = (
        ('rebalance_days', 30),
        ('threshold', 0.05),
        ('rebalance_basis', 'trading'),  # 'trading' or 'calendar'
    )
    
    def __init__(self):
        super().__init__()
        self.last_rebalance = 0
        
    def get_target_weights(self) -> Dict[str, float]:
        """Override this method to provide target weights"""
        return {}
    
    @classmethod 
    def get_static_target_weights(cls) -> Dict[str, float]:
        """
        Get target weights without requiring instantiation.
        Override in subclasses for static strategies.
        """
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
        
        # Determine if time gate allows rebalancing based on basis
        current_date = self.datas[0].datetime.date(0)
        if self.params.rebalance_basis == 'calendar':
            days_since_last = (current_date - self.last_rebalance_calendar_date).days if self.last_rebalance_calendar_date else 0
            time_gate_met = (days_since_last >= self.params.rebalance_days) or len(self) == 1
        else:
            time_gate_met = ((len(self) - self.last_rebalance) >= self.params.rebalance_days) or len(self) == 1

        if time_gate_met:
            # Compute gaps
            bars_since_last = (len(self) - self.last_rebalance) if self.last_rebalance > 0 else len(self)
            days_since_last = (current_date - self.last_rebalance_calendar_date).days if self.last_rebalance_calendar_date else 0
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
            
            threshold_trigger = self.need_rebalancing(target_weights, current_weights)
            if threshold_trigger or len(self) == 1:
                context = {
                    'trigger_type': 'initial' if len(self) == 1 else 'scheduled_threshold',
                    'bars_since_last_rebalance': bars_since_last,
                    'natural_days_since_last_rebalance': days_since_last,
                    'basis': 'calendar_days' if self.params.rebalance_basis == 'calendar' else 'trading_days',
                    'configured_rebalance_days': int(self.params.rebalance_days),
                    'time_gate_met': bool(time_gate_met),
                    'note': 'Gaps may differ depending on trading vs calendar day basis; actual execution occurs on next available trading day.'
                }
                self.rebalance_portfolio(target_weights, rebalance_context=context)
                self.last_rebalance = len(self)
                self.last_rebalance_calendar_date = current_date

class DynamicStrategy(BaseStrategy):
    """
    Base class for dynamic strategies that adjust allocation based on market conditions.
    """
    params = (
        ('rebalance_days', 30),
        ('threshold', 0.05),
        ('rebalance_basis', 'trading'),  # 'trading' or 'calendar'
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
        
        # Determine if time gate allows rebalancing based on basis
        current_date = self.datas[0].datetime.date(0)
        if self.params.rebalance_basis == 'calendar':
            days_since_last = (current_date - self.last_rebalance_calendar_date).days if self.last_rebalance_calendar_date else 0
            time_gate_met = (days_since_last >= self.params.rebalance_days) or len(self) == 1
        else:
            time_gate_met = ((len(self) - self.last_rebalance) >= self.params.rebalance_days) or len(self) == 1

        if time_gate_met:
            # Compute gaps
            bars_since_last = (len(self) - self.last_rebalance) if self.last_rebalance > 0 else len(self)
            days_since_last = (current_date - self.last_rebalance_calendar_date).days if self.last_rebalance_calendar_date else 0
            try:
                target_weights = self.calculate_target_weights(current_date)
                current_weights = self.get_current_weights()
                
                threshold_trigger = self.need_rebalancing_dynamic(target_weights, current_weights)
                if len(self) == 1 or threshold_trigger:
                    context = {
                        'trigger_type': 'initial' if len(self) == 1 else 'scheduled_threshold',
                        'bars_since_last_rebalance': bars_since_last,
                        'natural_days_since_last_rebalance': days_since_last,
                        'basis': 'calendar_days' if self.params.rebalance_basis == 'calendar' else 'trading_days',
                        'configured_rebalance_days': int(self.params.rebalance_days),
                        'time_gate_met': bool(time_gate_met),
                        'note': 'Gaps may differ depending on trading vs calendar day basis; actual execution occurs on next available trading day.'
                    }
                    self.rebalance_portfolio(target_weights, rebalance_context=context)
                    self.last_rebalance = len(self)
                    self.last_rebalance_calendar_date = current_date
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
        ('rebalance_basis', 'trading'),  # 'trading' or 'calendar'
        ('target_weights', {}),
    )
    
    def get_target_weights(self) -> Dict[str, float]:
        """Return the fixed target weights"""
        return self.params.target_weights

# Add method to BaseStrategy after all subclasses are defined
def _get_strategy_type(cls) -> str:
    """Get the type of strategy (static/dynamic)"""
    if issubclass(cls, StaticAllocationStrategy):
        return "static"
    elif issubclass(cls, DynamicStrategy):
        return "dynamic"
    else:
        return "unknown"

BaseStrategy.get_strategy_type = classmethod(_get_strategy_type)