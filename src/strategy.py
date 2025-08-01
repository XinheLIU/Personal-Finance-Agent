import backtrader as bt
import pandas as pd
import numpy as np
import os
import akshare as ak
from src.app_logger import LOG
from src.config import DYNAMIC_STRATEGY_PARAMS
from src.data_loader import load_market_data, load_pe_data
from src.strategy_utils import calculate_pe_percentile, calculate_yield_percentile, get_current_yield

def calculate_target_weights_standalone(current_date, pe_cache, market_data):
    """
    Calculates target allocation weights based on current market conditions, independent of backtrader.
    """
    weights = {}
    pe_percentiles = {}
    
    try:
        pe_percentiles['CSI300'] = calculate_pe_percentile('CSI300', pe_cache, current_date, 10)
        pe_percentiles['CSI500'] = calculate_pe_percentile('CSI500', pe_cache, current_date, 10)
        pe_percentiles['HSI'] = calculate_pe_percentile('HSI', pe_cache, current_date, 10)
        pe_percentiles['HSTECH'] = calculate_pe_percentile('HSTECH', pe_cache, current_date, 10)
        pe_percentiles['SP500'] = calculate_pe_percentile('SP500', pe_cache, current_date, 20)
        pe_percentiles['NASDAQ100'] = calculate_pe_percentile('NASDAQ100', pe_cache, current_date, 20)
        
        yield_pct = calculate_yield_percentile(market_data, current_date, 20)
        current_yield = get_current_yield(market_data, current_date)
        
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
        
        total_allocated = sum(weights.values()) + 0.03 # 0.03 for individual stocks
        chinese_bonds = max(0, 1.0 - total_allocated)
        
        total_weight = sum(weights.values())
        if total_weight > 0:
            scale_factor = (1.0 - chinese_bonds - 0.03) / total_weight
            for asset in weights:
                weights[asset] *= scale_factor
        
        LOG.info(f"Date: {current_date}")
        LOG.info(f"PE Percentiles - CSI300: {pe_percentiles['CSI300']:.2%}, CSI500: {pe_percentiles['CSI500']:.2%}")
        LOG.info(f"PE Percentiles - HSI: {pe_percentiles['HSI']:.2%}, HSTECH: {pe_percentiles['HSTECH']:.2%}")
        # LOG.info(f"PE Percentiles - SP500: {pe_percentiles['SP500']:.2%}, NASDAQ: {pe_percentiles['NASDAQ100']:.2%}")  # TEMPORARILY DISABLED
        LOG.info(f"PE Percentiles - NASDAQ: {pe_percentiles['NASDAQ100']:.2%} (SP500 temporarily disabled)")
        LOG.info(f"Yield: {current_yield:.2f}%, Percentile: {yield_pct:.2%}")
        LOG.info(f"Target weights: {weights}")
        
        return weights, pe_percentiles, current_yield, yield_pct
        
    except Exception as e:
        LOG.error(f"Error calculating target weights: {e}")
        raise

def get_target_weights_and_metrics_standalone():
    """
    Calculates and returns the latest target weights and metrics, independent of backtrader.
    """
    try:
        pe_cache = load_pe_data()
        market_data = load_market_data()

        latest_pe_dates = [df.index.max() for df in pe_cache.values() if not df.empty]
        if not latest_pe_dates:
            raise ValueError("No PE data available in cache.")
        
        latest_pe_date = min(latest_pe_dates)
        latest_yield_date = market_data['US10Y'].index.max()
        current_date = min(latest_pe_date, latest_yield_date).to_pydatetime().date()

        weights, pe_percentiles, current_yield, yield_pct = calculate_target_weights_standalone(current_date, pe_cache, market_data)

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
        LOG.error(f"Error getting target weights and metrics: {e}")
        return {}, {}

class DynamicAllocationStrategy(bt.Strategy):
    params = (
        ('rebalance_days', DYNAMIC_STRATEGY_PARAMS['rebalance_days']),
        ('threshold', DYNAMIC_STRATEGY_PARAMS['threshold']),
    )
    
    def __init__(self):
        self.market_data = load_market_data()
        self.pe_cache = load_pe_data()
        self.last_rebalance = 0
        self.target_weights = {}
        self.current_weights = {}
        self.rebalance_log = []
        self.portfolio_values = []
        self.portfolio_dates = []
        self.data_feeds = {
            'CSI300': self.datas[0] if len(self.datas) > 0 else None,
            'CSI500': self.datas[1] if len(self.datas) > 1 else None,
            'HSI': self.datas[2] if len(self.datas) > 2 else None,
            'HSTECH': self.datas[3] if len(self.datas) > 3 else None,
            'SP500': self.datas[4] if len(self.datas) > 4 else None,
            'NASDAQ100': self.datas[5] if len(self.datas) > 5 else None,
            'TLT': self.datas[6] if len(self.datas) > 6 else None,
            'GLD': self.datas[7] if len(self.datas) > 7 else None,
            'CASH': self.datas[8] if len(self.datas) > 8 else None,
        }
        
    def calculate_target_weights(self, current_date):
        return calculate_target_weights_standalone(current_date, self.pe_cache, self.market_data)

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
            current_position = self.getposition(data_feed)
            current_value = current_position.size * data_feed.close[0]
            if target_value == 0 and current_position.size > 0:
                order = self.close(data_feed)
                LOG.info(f"Closing {asset} position")
                transactions.append(f"Close {asset}")
            elif target_value > 0:
                target_shares = int(target_value / data_feed.close[0])
                shares_to_trade = target_shares - current_position.size
                if abs(shares_to_trade) > 0:
                    if shares_to_trade > 0:
                        self.buy(data=data_feed, size=shares_to_trade)
                        LOG.info(f"Buying {shares_to_trade} shares of {asset}")
                        transactions.append(f"Buy {shares_to_trade} of {asset}")
                    else:
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
        current_date = self.datas[0].datetime.date(0)
        portfolio_value = self.broker.getvalue()
        self.portfolio_values.append(portfolio_value)
        self.portfolio_dates.append(current_date)
        
        if (len(self) - self.last_rebalance >= self.params.rebalance_days) or len(self) == 1:
            try:
                target_weights, pe_percentiles, current_yield, yield_pct = self.calculate_target_weights(current_date)
                current_weights = self.get_current_weights()
                if self.need_rebalancing(target_weights, current_weights) or len(self) == 1:
                    self.rebalance_portfolio(target_weights, pe_percentiles, current_yield, yield_pct)
                    self.last_rebalance = len(self)
                    self.target_weights = target_weights.copy()
                    self.current_weights = current_weights.copy()
            except Exception as e:
                LOG.error(f"Strategy execution failed on {current_date}: {e}")
                raise

class BuyAndHoldStrategy(bt.Strategy):
    def __init__(self):
        self.bought = False
        self.portfolio_values = []
        self.portfolio_dates = []
        self.shares_bought = 0

    def next(self):
        current_price = self.datas[0].close[0]
        portfolio_value = self.shares_bought * current_price + self.broker.get_cash()
        self.portfolio_values.append(portfolio_value)
        self.portfolio_dates.append(self.datas[0].datetime.date(0))
        
        if not self.bought:
            cash = self.broker.get_cash()
            price = self.datas[0].close[0]
            if price > 0:
                shares = int(cash / price)
                if shares > 0:
                    self.buy(data=self.datas[0], size=shares)
                    self.shares_bought = shares
                    LOG.info(f"Buy and Hold: Bought {shares} shares at ${price:.2f}")
                    LOG.info(f"Buy and Hold: Initial investment: ${shares * price:,.2f}")
                else:
                    LOG.warning(f"Buy and Hold: Not enough cash to buy shares. Cash: ${cash:.2f}, Price: ${price:.2f}")
            else:
                LOG.error(f"Buy and Hold: Invalid price: {price}")
            self.bought = True
        
        if len(self) % 1000 == 0:
            current_value = self.shares_bought * current_price + self.broker.get_cash()
            LOG.info(f"Buy and Hold Day {len(self)}: Price=${current_price:.2f}, Shares={self.shares_bought}, Value=${current_value:,.2f}")
