import backtrader as bt
import pandas as pd
import numpy as np
import os
import akshare as ak
from src.ui.app_logger import LOG
from config import DYNAMIC_STRATEGY_PARAMS, INDEX_ASSETS, TRADABLE_ASSETS
from src.modules.portfolio.strategies.utils import (
    pe_percentile_from_processed,
    yield_percentile_from_processed,
    current_yield_from_processed,
)

def calculate_target_weights_standalone(current_date, processed_df):
    """
    Calculate target allocation weights using processed strategy data only.
    """
    weights = {}
    pe_percentiles = {}

    try:
        pe_percentiles['CSI300'], _ = pe_percentile_from_processed(processed_df, 'CSI300', current_date, 10)
        pe_percentiles['CSI500'], _ = pe_percentile_from_processed(processed_df, 'CSI500', current_date, 10)
        pe_percentiles['HSI'], _ = pe_percentile_from_processed(processed_df, 'HSI', current_date, 10)
        pe_percentiles['HSTECH'], _ = pe_percentile_from_processed(processed_df, 'HSTECH', current_date, 10)
        pe_percentiles['SP500'], _ = pe_percentile_from_processed(processed_df, 'SP500', current_date, 20)
        pe_percentiles['NASDAQ100'], _ = pe_percentile_from_processed(processed_df, 'NASDAQ100', current_date, 20)

        yield_pct = yield_percentile_from_processed(processed_df, current_date, 20)
        current_yield = current_yield_from_processed(processed_df, current_date)

        weights['CSI300'] = 0.15 * (1 - pe_percentiles['CSI300'])
        weights['CSI500'] = 0.15 * (1 - pe_percentiles['CSI500'])
        weights['HSI'] = 0.10 * (1 - pe_percentiles['HSI'])
        weights['HSTECH'] = 0.10 * (1 - pe_percentiles['HSTECH'])
        weights['SP500'] = 0.15 * (1 - pe_percentiles['SP500'])
        weights['NASDAQ100'] = 0.15 * (1 - pe_percentiles['NASDAQ100'])
        weights['TLT'] = 0.15 * (yield_pct ** 2)

        if current_yield >= 4.0:
            weights['CASH'] = current_yield / 100.0
        else:
            weights['CASH'] = 0.0

        weights['GLD'] = 0.10

        total_allocated = sum(weights.values()) + 0.03  # 0.03 for individual stocks
        chinese_bonds = max(0, 1.0 - total_allocated)

        total_weight = sum(weights.values())
        if total_weight > 0:
            scale_factor = (1.0 - chinese_bonds - 0.03) / total_weight
            for asset in weights:
                weights[asset] *= scale_factor

        LOG.info(f"Date: {current_date}")
        LOG.info(f"PE Percentiles - CSI300: {pe_percentiles['CSI300']:.2%}, CSI500: {pe_percentiles['CSI500']:.2%}")
        LOG.info(f"PE Percentiles - HSI: {pe_percentiles['HSI']:.2%}, HSTECH: {pe_percentiles['HSTECH']:.2%}")
        LOG.info(f"PE Percentiles - NASDAQ: {pe_percentiles['NASDAQ100']:.2%}")
        LOG.info(f"Yield: {current_yield:.2f}%, Percentile: {yield_pct:.2%}")
        LOG.info(f"Target weights: {weights}")

        return weights, pe_percentiles, current_yield, yield_pct

    except Exception as e:
        LOG.error(f"Error calculating target weights (processed): {e}")
        raise

def get_target_weights_and_metrics_standalone():
    """
    Calculate latest target weights and metrics using processed data only.
    """
    try:
        from src.modules.data_management.data_center.data_processor import get_processed_data, process_strategy_data

        if not process_strategy_data('dynamic_allocation'):
            raise RuntimeError("Unable to process data for 'dynamic_allocation'.")

        processed_df = get_processed_data('dynamic_allocation')
        if processed_df is None or processed_df.empty:
            raise ValueError("Processed dataset is empty for 'dynamic_allocation'.")

        current_date = min(processed_df.index.max(), processed_df.index.max()).to_pydatetime().date()

        weights, pe_percentiles, current_yield, yield_pct = calculate_target_weights_standalone(current_date, processed_df)

        reasoning = {}
        for asset in weights:
            if asset == 'TLT':
                reasoning[asset] = f"Yield: {current_yield:.2f}%, Yield %ile: {yield_pct:.1%}"
            elif asset in pe_percentiles:
                reasoning[asset] = f"PE %ile: {pe_percentiles.get(asset, 'N/A'):.1%}"
            elif asset == 'GLD':
                reasoning[asset] = "Fixed Allocation"
            elif asset == 'CASH':
                reasoning[asset] = f"US 10Y Yield >= 4.0%"
            else:
                reasoning[asset] = "N/A"

        return weights, reasoning

    except Exception as e:
        LOG.error(f"Error getting target weights and metrics (processed): {e}")
        return {}, {}

class DynamicAllocationStrategy(bt.Strategy):
    params = (
        ('rebalance_days', DYNAMIC_STRATEGY_PARAMS['rebalance_days']),
        ('threshold', DYNAMIC_STRATEGY_PARAMS['threshold']),
    )
    
    def __init__(self):
        # Use processed data only
        from src.modules.data_management.data_center.data_processor import get_processed_data, process_strategy_data

        if not process_strategy_data('dynamic_allocation'):
            raise RuntimeError("Processed data not available for 'dynamic_allocation'. Please run data processing.")
        self.processed_data = get_processed_data('dynamic_allocation')
        if self.processed_data is None or self.processed_data.empty:
            raise RuntimeError("Processed data for 'dynamic_allocation' is empty.")
        
        self.last_rebalance = 0
        self.target_weights = {}
        self.current_weights = {}
        self.rebalance_log = []
        self.portfolio_values = []
        self.portfolio_dates = []
        # Track weights evolution for attribution analysis
        self.weights_evolution = []
        self.data_feeds = {data._name: data for data in self.datas}
        
    def calculate_target_weights(self, current_date):
        return calculate_target_weights_standalone(current_date, self.processed_data)

    def get_current_weights(self):
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
        for asset in target_weights:
            current_weight = current_weights.get(asset, 0)
            target_weight = target_weights[asset]
            if abs(current_weight - target_weight) > self.params.threshold:
                return True
        return False
    
    def rebalance_portfolio(self, target_weights, pe_percentiles, current_yield, yield_pct):
        total_value = self.broker.getvalue()
        LOG.info(f"Rebalancing portfolio with total value: {total_value:.2f}")
        transactions = []
        for asset, target_weight in target_weights.items():
            data_feed = self.data_feeds.get(asset)
            if data_feed is None:
                continue
            target_value = total_value * target_weight
            self.order_target_percent(data=data_feed, target=target_weight)


        rebalance_details = {
            'date': self.datas[0].datetime.date(0),
            'total_portfolio_value': total_value,
            'transactions': ", ".join(transactions),
        }

        for asset, weight in target_weights.items():
            rebalance_details[f'{asset}_target_weight'] = weight
            # Attach price only if feed exists
            if asset in self.data_feeds and self.data_feeds[asset] is not None:
                rebalance_details[f'{asset}_price'] = self.data_feeds[asset].close[0]
            rebalance_details[f'{asset}_pe_percentile'] = pe_percentiles.get(asset)
        
        rebalance_details['US_10Y_yield'] = current_yield
        rebalance_details['US_10Y_yield_percentile'] = yield_pct
        self.rebalance_log.append(rebalance_details)

    def next(self):
        current_date = self.datas[0].datetime.date(0)
        portfolio_value = self.broker.getvalue()
        self.portfolio_values.append(portfolio_value)
        self.portfolio_dates.append(current_date)
        
        # Capture weights evolution for attribution analysis
        current_weights = self.get_current_weights()
        weights_entry = {'date': current_date}
        weights_entry.update(current_weights)
        self.weights_evolution.append(weights_entry)
        
        if (len(self) - self.last_rebalance >= self.params.rebalance_days) or len(self) == 1:
            try:
                target_weights, pe_percentiles, current_yield, yield_pct = self.calculate_target_weights(current_date)
                if self.need_rebalancing(target_weights, current_weights) or len(self) == 1:
                    self.rebalance_portfolio(target_weights, pe_percentiles, current_yield, yield_pct)
                    self.last_rebalance = len(self)
                    self.target_weights = target_weights.copy()
                    self.current_weights = current_weights.copy()
            except Exception as e:
                LOG.error(f"Strategy execution failed on {current_date}: {e}")
                raise

class FixedWeightStrategy(bt.Strategy):
    params = (
        ('rebalance_days', 360),
        ('target_weights', {}),
    )

    def __init__(self):
        self.last_rebalance = 0
        self.portfolio_values = []
        self.portfolio_dates = []
        # Track weights evolution for attribution analysis
        self.weights_evolution = []
        self.rebalance_log = []
        self.data_feeds = {data._name: data for data in self.datas}
        self.validate_assets()

    def validate_assets(self):
        """Check if all assets in target_weights are in data_feeds."""
        for asset in self.p.target_weights:
            if asset not in self.data_feeds:
                LOG.warning(f"Asset '{asset}' in strategy '{self.__class__.__name__}' not found in available data. It will be ignored.")

    def next(self):
        current_date = self.datas[0].datetime.date(0)
        portfolio_value = self.broker.getvalue()
        self.portfolio_values.append(portfolio_value)
        self.portfolio_dates.append(current_date)

        # Capture weights evolution for attribution analysis
        current_weights = self.get_current_weights()
        weights_entry = {'date': current_date}
        weights_entry.update(current_weights)
        self.weights_evolution.append(weights_entry)

        if (len(self) - self.last_rebalance >= self.p.rebalance_days) or len(self) == 1:
            self.rebalance_portfolio()
            self.last_rebalance = len(self)

    def get_current_weights(self) -> dict:
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
    
    def rebalance_portfolio(self):
        current_date = self.datas[0].datetime.date(0)
        LOG.info(f"Rebalancing for {self.__class__.__name__} on {current_date}")
        
        # Log rebalancing event for attribution analysis
        rebalance_entry = {
            'date': current_date,
            'target_weights': self.p.target_weights.copy(),
            'strategy': self.__class__.__name__
        }
        self.rebalance_log.append(rebalance_entry)
        
        for asset, target_weight in self.p.target_weights.items():
            if asset in self.data_feeds:
                self.order_target_percent(data=self.data_feeds[asset], target=target_weight)

class SixtyFortyStrategy(FixedWeightStrategy):
    def __init__(self):
        # 60% Stocks (S&P 500), 40% Bonds (US Treasury)
        self.p.target_weights = {'SP500': 0.60, 'TLT': 0.40}
        super().__init__()

class PermanentPortfolioStrategy(FixedWeightStrategy):
    def __init__(self):
        # 25% Stocks (S&P 500), 25% Long-Term Bonds (TLT), 25% Cash (SHV), 25% Gold (GLD)
        self.p.target_weights = {'SP500': 0.25, 'TLT': 0.25, 'CASH': 0.25, 'GLD': 0.25}
        super().__init__()

class AllWeatherPortfolioStrategy(FixedWeightStrategy):
    def __init__(self):
        # 30% Stocks (S&P 500), 40% Long-Term Bonds (TLT), 15% Intermediate-Term Bonds (IEF), 7.5% Gold (GLD), 7.5% Commodities (DBC)
        self.p.target_weights = {'SP500': 0.30, 'TLT': 0.40, 'IEF': 0.15, 'GLD': 0.075, 'DBC': 0.075}
        super().__init__()

class DavidSwensenPortfolioStrategy(FixedWeightStrategy):
    def __init__(self):
        # 30% US Equities (S&P 500), 15% International Developed Equities (using SP500 as proxy), 5% Emerging Market Equities (using CSI300 as proxy), 20% REITs (using SP500 as proxy), 15% Long-Term Treasuries, 15% TIPS (using TLT as proxy)
        LOG.warning("Using SP500 as a proxy for International Developed Equities and REITs in DavidSwensenPortfolioStrategy.")
        LOG.warning("Using CSI300 as a proxy for Emerging Market Equities in DavidSwensenPortfolioStrategy.")
        LOG.warning("Using TLT as a proxy for TIPS in DavidSwensenPortfolioStrategy.")
        self.p.target_weights = {'SP500': 0.65, 'CSI300': 0.05, 'TLT': 0.30}
        super().__init__()

class BuyAndHoldStrategy(bt.Strategy):
    def __init__(self):
        self.bought = False
        self.portfolio_values = []
        self.portfolio_dates = []
        # Track weights evolution for attribution analysis
        self.weights_evolution = []
        self.rebalance_log = []
        self.shares_bought = 0
        self.order = None

        # Robustly select SP500 feed by name
        self.data_feed = None
        for data in self.datas:
            if getattr(data, '_name', '') == 'SP500':
                self.data_feed = data
                break
        if self.data_feed is None:
            self.data_feed = self.datas[0]

    def get_current_weights(self) -> dict:
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

    def next(self):
        # Use broker's marked-to-market portfolio value for robustness
        current_price = self.data_feed.close[0]
        portfolio_value = self.broker.getvalue()
        current_date = self.data_feed.datetime.date(0)
        
        self.portfolio_values.append(portfolio_value)
        self.portfolio_dates.append(current_date)
        
        # Capture weights evolution for attribution analysis
        current_weights = self.get_current_weights()
        weights_entry = {'date': current_date}
        weights_entry.update(current_weights)
        self.weights_evolution.append(weights_entry)
        
        if not self.bought:
            if current_price > 0:
                # Market-in at first bar using cash-based sizing to ensure execution
                available_cash = self.broker.getcash()
                size = int(available_cash / current_price)
                if size > 0:
                    self.buy(data=self.data_feed, size=size)
                    self.bought = True
                    
                    # Log initial purchase as rebalancing event for attribution
                    rebalance_entry = {
                        'date': current_date,
                        'target_weights': {self.data_feed._name: 1.0},
                        'strategy': self.__class__.__name__,
                        'trigger': 'initial_purchase'
                    }
                    self.rebalance_log.append(rebalance_entry)
                else:
                    LOG.warning("Buy and Hold: Not enough cash to buy any shares")
            else:
                LOG.error(f"Buy and Hold: Invalid price: {current_price}")
        
        if len(self) % 1000 == 0:
            LOG.info(f"Buy and Hold Day {len(self)}: Price=${current_price:.2f}, Shares={self.shares_bought}, Value=${portfolio_value:,.2f}")

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.shares_bought = int(order.executed.size)
                LOG.info(f"Buy and Hold: Bought {self.shares_bought} shares at ${order.executed.price:.2f}")
                LOG.info(f"Buy and Hold: Initial investment: ${order.executed.size * order.executed.price:,.2f}")


