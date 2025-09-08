"""
Trade Executor
Foundation for order execution with simulation and API integration capabilities.
Supports manual, semi-automated, and fully automated execution modes.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
from dataclasses import dataclass

from src.ui.app_logger import LOG

class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderStatus(Enum):
    """Order status"""
    PENDING = "pending"
    SUBMITTED = "submitted" 
    PARTIAL_FILLED = "partial_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"

class ExecutionMode(Enum):
    """Execution modes"""
    SIMULATION = "simulation"
    PAPER = "paper"
    LIVE = "live"

@dataclass
class Order:
    """Order representation"""
    order_id: str
    symbol: str
    quantity: float
    order_type: OrderType
    side: str  # "buy" or "sell"
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "GTC"  # Good Till Cancelled
    created_time: datetime = None
    updated_time: datetime = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    average_fill_price: float = 0.0
    commission: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_time is None:
            self.created_time = datetime.now()
        if self.updated_time is None:
            self.updated_time = self.created_time
        if self.metadata is None:
            self.metadata = {}

class TradeExecutor(ABC):
    """
    Abstract base class for trade execution
    Provides foundation for different execution modes (simulation, paper, live)
    """
    
    def __init__(self, 
                 execution_mode: ExecutionMode = ExecutionMode.SIMULATION,
                 commission_rate: float = 0.001,
                 slippage_rate: float = 0.001):
        self.execution_mode = execution_mode
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        
        # Order tracking
        self.orders: Dict[str, Order] = {}
        self.execution_history: List[Dict] = []
        
        # Performance tracking
        self.total_commission_paid = 0.0
        self.total_slippage_cost = 0.0
        self.execution_count = 0
        
        LOG.info(f"Trade executor initialized in {execution_mode.value} mode")
    
    @abstractmethod
    def submit_order(self, order: Order) -> bool:
        """Submit order for execution"""
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel pending order"""
        pass
    
    @abstractmethod
    def get_order_status(self, order_id: str) -> Optional[Order]:
        """Get current order status"""
        pass
    
    def create_market_order(self, 
                           symbol: str, 
                           quantity: float, 
                           side: str,
                           order_id: Optional[str] = None) -> Order:
        """Create market order"""
        if order_id is None:
            order_id = f"MKT_{symbol}_{int(datetime.now().timestamp())}"
        
        return Order(
            order_id=order_id,
            symbol=symbol,
            quantity=abs(quantity),
            order_type=OrderType.MARKET,
            side=side,
            metadata={'strategy': 'system_rebalance'}
        )
    
    def create_limit_order(self, 
                          symbol: str, 
                          quantity: float, 
                          side: str,
                          limit_price: float,
                          order_id: Optional[str] = None) -> Order:
        """Create limit order"""
        if order_id is None:
            order_id = f"LMT_{symbol}_{int(datetime.now().timestamp())}"
        
        return Order(
            order_id=order_id,
            symbol=symbol,
            quantity=abs(quantity),
            order_type=OrderType.LIMIT,
            side=side,
            price=limit_price,
            metadata={'strategy': 'system_rebalance'}
        )
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get execution performance summary"""
        return {
            'execution_mode': self.execution_mode.value,
            'total_orders': len(self.orders),
            'filled_orders': len([o for o in self.orders.values() if o.status == OrderStatus.FILLED]),
            'total_commission': self.total_commission_paid,
            'total_slippage': self.total_slippage_cost,
            'execution_count': self.execution_count,
            'success_rate': (
                len([o for o in self.orders.values() if o.status == OrderStatus.FILLED]) /
                max(len(self.orders), 1)
            )
        }

class SimulationExecutor(TradeExecutor):
    """
    Simulation executor for backtesting
    Simulates order execution with configurable latency and slippage
    """
    
    def __init__(self, 
                 market_data: Dict[str, pd.DataFrame],
                 execution_delay_ms: int = 100,
                 **kwargs):
        super().__init__(ExecutionMode.SIMULATION, **kwargs)
        self.market_data = market_data
        self.execution_delay_ms = execution_delay_ms
        
    def submit_order(self, order: Order) -> bool:
        """Submit order for simulation execution"""
        try:
            # Validate order
            if order.symbol not in self.market_data:
                LOG.error(f"No market data available for {order.symbol}")
                order.status = OrderStatus.REJECTED
                return False
            
            # Store order
            self.orders[order.order_id] = order
            order.status = OrderStatus.SUBMITTED
            
            # Simulate execution for market orders
            if order.order_type == OrderType.MARKET:
                success = self._simulate_market_execution(order)
                if success:
                    self.execution_count += 1
                return success
            
            # For limit orders, would need more sophisticated simulation
            LOG.warning(f"Limit order simulation not fully implemented: {order.order_id}")
            return True
            
        except Exception as e:
            LOG.error(f"Order submission failed: {e}")
            order.status = OrderStatus.REJECTED
            return False
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel order"""
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED]:
                order.status = OrderStatus.CANCELLED
                order.updated_time = datetime.now()
                return True
        return False
    
    def get_order_status(self, order_id: str) -> Optional[Order]:
        """Get order status"""
        return self.orders.get(order_id)
    
    def _simulate_market_execution(self, order: Order) -> bool:
        """Simulate market order execution"""
        try:
            # Get current market price (use latest available)
            market_df = self.market_data[order.symbol]
            if market_df.empty:
                order.status = OrderStatus.REJECTED
                return False
            
            # Use latest close price as execution price
            execution_price = market_df['close'].iloc[-1]
            
            # Apply slippage
            if order.side == "buy":
                execution_price *= (1 + self.slippage_rate)
            else:
                execution_price *= (1 - self.slippage_rate)
            
            # Calculate commission
            commission = abs(order.quantity * execution_price * self.commission_rate)
            
            # Fill order
            order.status = OrderStatus.FILLED
            order.filled_quantity = order.quantity
            order.average_fill_price = execution_price
            order.commission = commission
            order.updated_time = datetime.now()
            
            # Track costs
            self.total_commission_paid += commission
            slippage_cost = abs(order.quantity * market_df['close'].iloc[-1] * self.slippage_rate)
            self.total_slippage_cost += slippage_cost
            
            # Log execution
            execution_record = {
                'timestamp': order.updated_time,
                'order_id': order.order_id,
                'symbol': order.symbol,
                'side': order.side,
                'quantity': order.quantity,
                'price': execution_price,
                'commission': commission,
                'slippage_cost': slippage_cost
            }
            self.execution_history.append(execution_record)
            
            LOG.info(f"Simulated execution: {order.symbol} {order.side} {order.quantity} @ {execution_price:.4f}")
            return True
            
        except Exception as e:
            LOG.error(f"Execution simulation failed for {order.order_id}: {e}")
            order.status = OrderStatus.REJECTED
            return False

class PaperTradingExecutor(TradeExecutor):
    """
    Paper trading executor
    Connects to real market data but executes trades in simulation
    """
    
    def __init__(self, **kwargs):
        super().__init__(ExecutionMode.PAPER, **kwargs)
        # Would integrate with real-time data feeds
        LOG.info("Paper trading executor initialized")
    
    def submit_order(self, order: Order) -> bool:
        """Submit paper trade order"""
        # Implementation would connect to real-time market data
        # For now, placeholder
        LOG.info(f"Paper trade submitted: {order.order_id}")
        self.orders[order.order_id] = order
        order.status = OrderStatus.SUBMITTED
        return True
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel paper trade order"""
        if order_id in self.orders:
            self.orders[order_id].status = OrderStatus.CANCELLED
            return True
        return False
    
    def get_order_status(self, order_id: str) -> Optional[Order]:
        """Get paper trade order status"""
        return self.orders.get(order_id)

class LiveTradingExecutor(TradeExecutor):
    """
    Live trading executor
    Integrates with actual broker/exchange APIs for real trading
    """
    
    def __init__(self, broker_config: Dict[str, Any], **kwargs):
        super().__init__(ExecutionMode.LIVE, **kwargs)
        self.broker_config = broker_config
        
        LOG.warning("Live trading executor - USE WITH EXTREME CAUTION")
        LOG.info("Live trading capabilities not implemented - placeholder only")
    
    def submit_order(self, order: Order) -> bool:
        """Submit live trade order"""
        # CRITICAL: Would integrate with actual broker API
        # Implementation must include extensive safety checks
        LOG.error("Live trading not implemented - safety measure")
        return False
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel live trade order"""
        LOG.error("Live trading not implemented - safety measure")
        return False
    
    def get_order_status(self, order_id: str) -> Optional[Order]:
        """Get live trade order status"""
        return None

def create_executor(execution_mode: ExecutionMode, 
                   market_data: Optional[Dict[str, pd.DataFrame]] = None,
                   **kwargs) -> TradeExecutor:
    """
    Factory function to create appropriate executor
    
    Args:
        execution_mode: Mode of execution
        market_data: Market data for simulation
        **kwargs: Additional executor parameters
        
    Returns:
        Appropriate executor instance
    """
    if execution_mode == ExecutionMode.SIMULATION:
        if market_data is None:
            raise ValueError("Market data required for simulation mode")
        return SimulationExecutor(market_data, **kwargs)
    elif execution_mode == ExecutionMode.PAPER:
        return PaperTradingExecutor(**kwargs)
    elif execution_mode == ExecutionMode.LIVE:
        return LiveTradingExecutor(**kwargs)
    else:
        raise ValueError(f"Unknown execution mode: {execution_mode}")