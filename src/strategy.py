import backtrader as bt
import pandas as pd
import numpy as np
import os
import akshare as ak
from src.app_logger import LOG
from src.config import DYNAMIC_STRATEGY_PARAMS
from src.data_loader import load_market_data, load_pe_data
from src.strategy_utils import calculate_pe_percentile, calculate_yield_percentile, get_current_yield

class DynamicAllocationStrategy(bt.Strategy):
    """
    Dynamic Asset Allocation Strategy based on valuation metrics and market conditions.
    
    This strategy implements a sophisticated multi-asset allocation approach that:
    1. Dynamically adjusts portfolio weights based on PE ratio percentiles
    2. Considers US 10Y Treasury yield conditions for bond allocation
    3. Implements automatic rebalancing when weights deviate from targets
    4. Tracks portfolio performance for visualization and analysis
    
    Strategy Rules:
    - Chinese Stocks (A股): CSI300 (20% × (1-PE percentile)), CSI500 (20% × (1-PE percentile))
    - Hong Kong Tech: HSTECH (10% × (1-PE percentile))
    - US Stocks: SP500 (15% × (1-PE percentile)), NASDAQ100 (15% × (1-PE percentile))
    - Bonds: TLT (15% × (yield percentile)²)
    - Cash: Money market allocation when US 10Y yield ≥ 4%
    - Gold: Fixed 10% allocation
    - Rebalancing: Triggered when any asset deviates >1% from target weight
    """
    
    params = (
        ('rebalance_days', DYNAMIC_STRATEGY_PARAMS['rebalance_days']),  # Rebalance every 30 days
        ('threshold', DYNAMIC_STRATEGY_PARAMS['threshold']),     # 1% threshold for rebalancing
    )
    
    def __init__(self):
        """Initialize the dynamic allocation strategy with data loading and setup"""
        # Load historical market data for PE and yield calculations
        self.market_data = load_market_data()
        self.pe_cache = load_pe_data()
        
        # Rebalancing control variables
        self.last_rebalance = 0
        self.target_weights = {}
        self.current_weights = {}
        self.rebalance_log = []
        
        # Portfolio value tracking for visualization and performance analysis
        self.portfolio_values = []
        self.portfolio_dates = []
        
        # Map strategy asset names to backtrader data feeds
        self.data_feeds = {
            'CSI300': self.datas[0] if len(self.datas) > 0 else None,      # Chinese large-cap stocks
            'CSI500': self.datas[1] if len(self.datas) > 1 else None,      # Chinese mid-cap stocks
            'HSTECH': self.datas[2] if len(self.datas) > 2 else None,      # Hong Kong tech stocks
            'SP500': self.datas[3] if len(self.datas) > 3 else None,       # US large-cap stocks
            'NASDAQ100': self.datas[4] if len(self.datas) > 4 else None,   # US tech stocks
            'TLT': self.datas[5] if len(self.datas) > 5 else None,         # Long-term US Treasury bonds
            'GLD': self.datas[6] if len(self.datas) > 6 else None,         # Gold ETF
            'CASH': self.datas[7] if len(self.datas) > 7 else None,        # Money market/cash
        }
        
    def calculate_target_weights(self, current_date):
        """
        Calculate target allocation weights based on current market conditions.
        
        This is the core of the strategy - it determines how much to allocate to each asset
        based on valuation metrics and market conditions:
        
        - Chinese stocks: Allocated based on PE percentiles (cheaper = more allocation)
        - US stocks: Allocated based on PE percentiles (cheaper = more allocation)
        - Bonds: Allocated based on yield percentiles (higher yields = more allocation)
        - Cash: Allocated when yields are attractive (≥4%)
        - Gold: Fixed 10% allocation for diversification
        
        Args:
            current_date: Current date for weight calculations
            
        Returns:
            dict: Target weights for each asset
        """
        weights = {}
        pe_percentiles = {}
        
        try:
            # Get PE percentiles for A-shares (10 years of history)
            pe_percentiles['CSI300'] = calculate_pe_percentile('CSI300', self.pe_cache, current_date, 10)
            pe_percentiles['CSI500'] = calculate_pe_percentile('CSI500', self.pe_cache, current_date, 10)
            pe_percentiles['HSTECH'] = calculate_pe_percentile('HSTECH', self.pe_cache, current_date, 10)
            
            # Get PE percentiles for US stocks (20 years of history)
            pe_percentiles['SP500'] = calculate_pe_percentile('SP500', self.pe_cache, current_date, 20)
            pe_percentiles['NASDAQ100'] = calculate_pe_percentile('NASDAQ100', self.pe_cache, current_date, 20)
            
            # Get yield percentile and current yield
            yield_pct = calculate_yield_percentile(self.market_data, current_date, 20)
            current_yield = get_current_yield(self.market_data, current_date)
            
            # A股配置 (Chinese stocks) - 20% base allocation each
            weights['CSI300'] = 0.20 * (1 - pe_percentiles['CSI300'])  # Cheaper = higher allocation
            weights['CSI500'] = 0.20 * (1 - pe_percentiles['CSI500'])  # Cheaper = higher allocation
            
            # 港股配置 (Hong Kong stocks) - 10% base allocation
            weights['HSTECH'] = 0.10 * (1 - pe_percentiles['HSTECH'])  # Cheaper = higher allocation
            
            # 美股配置 (US stocks) - 15% base allocation each
            weights['SP500'] = 0.15 * (1 - pe_percentiles['SP500'])    # Cheaper = higher allocation
            weights['NASDAQ100'] = 0.15 * (1 - pe_percentiles['NASDAQ100'])  # Cheaper = higher allocation
            
            # 个股配置 (Individual stocks) - skip for now
            individual_stocks = 0.03
            
            # 债券配置 (Bonds) - TLT allocation based on yield attractiveness
            weights['TLT'] = 0.15 * (yield_pct ** 2)  # Higher yields = more bond allocation
            
            # 美元货基 (Money market) - when yield >= 4%
            if current_yield >= 4.0:
                weights['CASH'] = current_yield / 100.0  # Allocate yield percentage to cash
            else:
                weights['CASH'] = 0.0
            
            # 黄金 (Gold) - fixed 10% allocation for diversification
            weights['GLD'] = 0.10
            
            # Calculate allocated percentage
            total_allocated = sum(weights.values()) + individual_stocks
            
            # 剩余资金配置易方达中债 (Remaining to Chinese bonds)
            chinese_bonds = max(0, 1.0 - total_allocated)
            
            # Normalize weights (exclude Chinese bonds and individual stocks for now)
            total_weight = sum(weights.values())
            if total_weight > 0:
                # Scale down to leave room for Chinese bonds and individual stocks
                scale_factor = (1.0 - chinese_bonds - individual_stocks) / total_weight
                for asset in weights:
                    weights[asset] *= scale_factor
            
            # Add debug info
            LOG.info(f"Date: {current_date}")
            LOG.info(f"PE Percentiles - CSI300: {pe_percentiles['CSI300']:.2%}, CSI500: {pe_percentiles['CSI500']:.2%}, HSTECH: {pe_percentiles['HSTECH']:.2%}")
            LOG.info(f"PE Percentiles - SP500: {pe_percentiles['SP500']:.2%}, NASDAQ: {pe_percentiles['NASDAQ100']:.2%}")
            LOG.info(f"Yield: {current_yield:.2f}%, Percentile: {yield_pct:.2%}")
            LOG.info(f"Target weights: {weights}")
            
            return weights, pe_percentiles, current_yield, yield_pct
            
        except Exception as e:
            LOG.error(f"Error calculating target weights: {e}")
            raise
    
    def get_current_weights(self):
        """
        Calculate current portfolio weights based on actual positions.
        
        This method determines what the current allocation looks like
        compared to the target allocation for rebalancing decisions.
        
        Returns:
            dict: Current weights for each asset
        """
        total_value = self.broker.getvalue()
        weights = {}
        
        for name, data_feed in self.data_feeds.items():
            if data_feed is not None:
                position = self.getposition(data_feed)
                if position.size != 0:
                    position_value = position.size * data_feed.close[0]
                    weights[name] = position_value / total_value
                else:
                    weights[name] = 0.0
            else:
                weights[name] = 0.0
                
        return weights
    
    def need_rebalancing(self, target_weights, current_weights):
        """
        Check if rebalancing is needed based on weight deviations.
        
        Rebalancing is triggered when any asset's current weight deviates
        more than the threshold (1%) from its target weight.
        
        Args:
            target_weights (dict): Target allocation weights
            current_weights (dict): Current allocation weights
            
        Returns:
            bool: True if rebalancing is needed, False otherwise
        """
        for asset in target_weights:
            current_weight = current_weights.get(asset, 0)
            target_weight = target_weights[asset]
            
            if abs(current_weight - target_weight) > self.params.threshold:
                return True
        return False
    
    def rebalance_portfolio(self, target_weights, pe_percentiles, current_yield, yield_pct):
        """
        Rebalance portfolio to match target weights.
        
        This method executes the actual trades to bring the portfolio
        in line with the target allocation. It:
        1. Calculates required trades for each asset
        2. Executes buy/sell orders to achieve target weights
        3. Logs all trading activity for transparency
        
        Args:
            target_weights (dict): Target allocation weights to achieve
        """
        total_value = self.broker.getvalue()
        
        LOG.info(f"Rebalancing portfolio with total value: {total_value:.2f}")
        
        transactions = []
        for asset, target_weight in target_weights.items():
            data_feed = self.data_feeds.get(asset)
            if data_feed is None:
                continue
                
            target_value = total_value * target_weight
            current_position = self.getposition(data_feed)
            current_value = current_position.size * data_feed.close[0]
            
            if target_value == 0 and current_position.size > 0:
                # Close position if target weight is 0
                order = self.close(data_feed)
                LOG.info(f"Closing {asset} position")
                transactions.append(f"Close {asset}")
            elif target_value > 0:
                # Calculate target shares and required trades
                target_shares = int(target_value / data_feed.close[0])
                shares_to_trade = target_shares - current_position.size
                
                if abs(shares_to_trade) > 0:
                    if shares_to_trade > 0:
                        # Buy shares to increase position
                        self.buy(data=data_feed, size=shares_to_trade)
                        LOG.info(f"Buying {shares_to_trade} shares of {asset}")
                        transactions.append(f"Buy {shares_to_trade} of {asset}")
                    else:
                        # Sell shares to decrease position
                        self.sell(data=data_feed, size=abs(shares_to_trade))
                        LOG.info(f"Selling {abs(shares_to_trade)} shares of {asset}")
                        transactions.append(f"Sell {abs(shares_to_trade)} of {asset}")

        rebalance_details = {
            'date': self.datas[0].datetime.date(0),
            'total_portfolio_value': total_value,
            'transactions': ", ".join(transactions),
        }

        for asset, weight in target_weights.items():
            rebalance_details[f'{asset}_target_weight'] = weight
            rebalance_details[f'{asset}_price'] = self.data_feeds[asset].close[0]
            rebalance_details[f'{asset}_pe_percentile'] = pe_percentiles.get(asset)
        
        rebalance_details['US_10Y_yield'] = current_yield
        rebalance_details['US_10Y_yield_percentile'] = yield_pct
        self.rebalance_log.append(rebalance_details)

    def next(self):
        """
        Main strategy logic executed on each trading day.
        
        This method is called by backtrader for each data point and:
        1. Tracks portfolio value for visualization
        2. Checks if rebalancing is needed (every 30 days or on strategy start)
        3. Calculates new target weights based on current market conditions
        4. Executes rebalancing trades if necessary
        5. Handles errors gracefully with proper logging
        """
        current_date = self.datas[0].datetime.date(0)
        
        # Track portfolio value for visualization and performance analysis
        portfolio_value = self.broker.getvalue()
        self.portfolio_values.append(portfolio_value)
        self.portfolio_dates.append(current_date)
        
        # Rebalance periodically (every 30 days) or on strategy start
        if (len(self) - self.last_rebalance >= self.params.rebalance_days) or len(self) == 1:
            
            try:
                # Calculate target weights based on current market conditions
                target_weights, pe_percentiles, current_yield, yield_pct = self.calculate_target_weights(current_date)
                current_weights = self.get_current_weights()
                
                # Check if rebalancing is needed (any weight deviation > 1%)
                if self.need_rebalancing(target_weights, current_weights) or len(self) == 1:
                    self.rebalance_portfolio(target_weights, pe_percentiles, current_yield, yield_pct)
                    self.last_rebalance = len(self)
                    self.target_weights = target_weights.copy()
                    self.current_weights = current_weights.copy()
                    
            except Exception as e:
                LOG.error(f"Strategy execution failed on {current_date}: {e}")
                # Stop the strategy when critical errors occur to prevent incorrect allocations
                raise


class BuyAndHoldStrategy(bt.Strategy):
    """
    Simple Buy and Hold Strategy for performance comparison.
    
    This strategy implements a basic buy-and-hold approach that:
    1. Buys the maximum number of shares possible with available cash on the first day
    2. Holds the position for the entire backtest period
    3. Tracks portfolio value for visualization and comparison
    4. Serves as a benchmark to evaluate the dynamic allocation strategy
    
    This is a passive strategy that represents the simplest form of investing:
    - No rebalancing
    - No market timing
    - No active management
    - Pure exposure to the underlying asset's performance
    """
    
    def __init__(self):
        """Initialize the buy and hold strategy"""
        self.bought = False  # Flag to track if initial purchase has been made
        # Portfolio value tracking for visualization and performance analysis
        self.portfolio_values = []
        self.portfolio_dates = []
        self.shares_bought = 0  # Track shares manually for accurate value calculation

    def next(self):
        """
        Main strategy logic executed on each trading day.
        
        This method:
        1. Tracks portfolio value for visualization
        2. Executes the initial purchase on the first day
        3. Logs portfolio performance for debugging and analysis
        """
        # Track portfolio value for visualization
        current_price = self.datas[0].close[0]
        portfolio_value = self.shares_bought * current_price + self.broker.get_cash()
        self.portfolio_values.append(portfolio_value)
        self.portfolio_dates.append(self.datas[0].datetime.date(0))
        
        # Execute initial purchase if not already done
        if not self.bought:
            # Calculate how many shares we can buy with all available cash
            cash = self.broker.get_cash()
            price = self.datas[0].close[0]
            if price > 0:
                shares = int(cash / price)
                if shares > 0:
                    # Execute the purchase
                    self.buy(data=self.datas[0], size=shares)
                    self.shares_bought = shares  # Track shares manually for accurate calculations
                    LOG.info(f"Buy and Hold: Bought {shares} shares at ${price:.2f}")
                    LOG.info(f"Buy and Hold: Initial investment: ${shares * price:,.2f}")
                else:
                    LOG.warning(f"Buy and Hold: Not enough cash to buy shares. Cash: ${cash:.2f}, Price: ${price:.2f}")
            else:
                LOG.error(f"Buy and Hold: Invalid price: {price}")
            self.bought = True
        
        # Log current portfolio value for debugging (every 1000 days)
        if len(self) % 1000 == 0:
            current_value = self.shares_bought * current_price + self.broker.get_cash()
            LOG.info(f"Buy and Hold Day {len(self)}: Price=${current_price:.2f}, Shares={self.shares_bought}, Value=${current_value:,.2f}")
