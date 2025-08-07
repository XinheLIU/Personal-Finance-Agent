"""
Built-in dynamic strategies for Personal Finance Agent.
These strategies adjust allocation based on market conditions.
"""
from src.strategies.base import DynamicStrategy
from src.strategy_utils import calculate_pe_percentile, calculate_yield_percentile, get_current_yield
from src.data_loader import load_market_data, load_pe_data
from typing import Dict
import pandas as pd

class DynamicAllocationStrategy(DynamicStrategy):
    """
    Original dynamic allocation strategy based on P/E percentiles and yield data.
    """
    def __init__(self):
        super().__init__()
        self.market_data = load_market_data()
        self.pe_cache = load_pe_data()
        
    def calculate_target_weights(self, current_date) -> Dict[str, float]:
        """Calculate target weights based on P/E percentiles and yield data"""
        weights = {}
        pe_percentiles = {}
        
        try:
            # Calculate PE percentiles for equity assets
            pe_percentiles['CSI300'] = calculate_pe_percentile('CSI300', self.pe_cache, current_date, 10)
            pe_percentiles['CSI500'] = calculate_pe_percentile('CSI500', self.pe_cache, current_date, 10)
            pe_percentiles['HSI'] = calculate_pe_percentile('HSI', self.pe_cache, current_date, 10)
            pe_percentiles['HSTECH'] = calculate_pe_percentile('HSTECH', self.pe_cache, current_date, 10)
            pe_percentiles['SP500'] = calculate_pe_percentile('SP500', self.pe_cache, current_date, 20)
            pe_percentiles['NASDAQ100'] = calculate_pe_percentile('NASDAQ100', self.pe_cache, current_date, 20)
            
            yield_pct = calculate_yield_percentile(self.market_data, current_date, 20)
            current_yield = get_current_yield(self.market_data, current_date)
            
            # Dynamic allocation based on P/E percentiles
            weights['CSI300'] = 0.15 * (1 - pe_percentiles['CSI300'])
            weights['CSI500'] = 0.15 * (1 - pe_percentiles['CSI500'])
            weights['HSI'] = 0.10 * (1 - pe_percentiles['HSI'])
            weights['HSTECH'] = 0.10 * (1 - pe_percentiles['HSTECH'])
            weights['SP500'] = 0.15 * (1 - pe_percentiles['SP500'])
            weights['NASDAQ100'] = 0.15 * (1 - pe_percentiles['NASDAQ100'])
            weights['TLT'] = 0.15 * (yield_pct ** 2)
            
            # Cash allocation based on yield threshold
            if current_yield >= 4.0:
                weights['CASH'] = current_yield / 100.0
            else:
                weights['CASH'] = 0.0
            
            weights['GLD'] = 0.10
            
            # Normalize weights
            total_weight = sum(weights.values())
            if total_weight > 0:
                scale_factor = 1.0 / total_weight
                for asset in weights:
                    weights[asset] *= scale_factor
            
            return weights
            
        except Exception as e:
            # Fallback to equal weights if calculation fails
            assets = [data._name for data in self.datas]
            return {asset: 1.0/len(assets) for asset in assets}

class MomentumStrategy(DynamicStrategy):
    """
    Simple momentum strategy based on 12-month performance.
    """
    def calculate_target_weights(self, current_date) -> Dict[str, float]:
        """Calculate target weights based on momentum"""
        assets = [data._name for data in self.datas]
        momentum_scores = {}
        
        for data in self.datas:
            if len(data) >= 252:  # 12 months of trading days
                current_price = data.close[0]
                past_price = data.close[-252]
                momentum = (current_price - past_price) / past_price
                momentum_scores[data._name] = max(momentum, 0)  # Only positive momentum
            else:
                momentum_scores[data._name] = 1.0  # Equal weight for new assets
        
        # Normalize momentum scores
        total_momentum = sum(momentum_scores.values())
        if total_momentum > 0:
            weights = {asset: score/total_momentum for asset, score in momentum_scores.items()}
        else:
            # Equal weight if no positive momentum
            weights = {asset: 1.0/len(assets) for asset in assets}
        
        return weights

class RiskParityStrategy(DynamicStrategy):
    """
    Risk parity strategy based on volatility.
    """
    def calculate_target_weights(self, current_date) -> Dict[str, float]:
        """Calculate target weights based on inverse volatility"""
        assets = [data._name for data in self.datas]
        volatility_scores = {}
        
        for data in self.datas:
            if len(data) >= 21:  # 1 month of trading days
                # Simple volatility calculation using recent returns
                returns = []
                for i in range(min(21, len(data))):
                    if i > 0:
                        ret = (data.close[-i] - data.close[-i-1]) / data.close[-i-1]
                        returns.append(abs(ret))
                
                if returns:
                    volatility = sum(returns) / len(returns)
                    volatility_scores[data._name] = 1.0 / max(volatility, 0.001)  # Avoid division by zero
                else:
                    volatility_scores[data._name] = 1.0
            else:
                volatility_scores[data._name] = 1.0
        
        # Normalize volatility scores
        total_score = sum(volatility_scores.values())
        if total_score > 0:
            weights = {asset: score/total_score for asset, score in volatility_scores.items()}
        else:
            weights = {asset: 1.0/len(assets) for asset in assets}
        
        return weights