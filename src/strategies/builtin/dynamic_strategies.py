"""
Built-in dynamic strategies for Personal Finance Agent.
These strategies adjust allocation based on market conditions.
"""
from src.strategies.base import DynamicStrategy
from src.app_logger import LOG
from src.strategies.utils import (
    calculate_pe_percentile_with_details,
    calculate_yield_percentile,
    get_current_yield,
)
from src.data_center.data_loader import load_market_data, load_pe_data
from typing import Dict
import pandas as pd

class DynamicAllocationStrategy(DynamicStrategy):
    """
    Original dynamic allocation strategy based on P/E percentiles and yield data.
    """
    def __init__(self):
        super().__init__()
        # Use processed data instead of raw data
        from src.data_center.data_processor import get_processed_data, process_strategy_data
        
        # Ensure processed data exists for dynamic allocation
        if not process_strategy_data('dynamic_allocation'):
            LOG.warning("Failed to process data for dynamic allocation, falling back to raw data")
            self.market_data = load_market_data()
            self.pe_cache = load_pe_data()
            self.processed_data = None
        else:
            # Load strategy-specific processed data
            self.processed_data = get_processed_data('dynamic_allocation')
            # Keep backward compatibility for now
            self.market_data = load_market_data()
            self.pe_cache = load_pe_data()
        
    def calculate_target_weights(self, current_date) -> Dict[str, float]:
        """Calculate target weights based on P/E percentiles and yield data"""
        weights = {}
        pe_percentiles = {}
        
        try:
            # Calculate PE percentiles for equity assets with detailed inputs
            pe_details_map = {}
            pe_percentiles['CSI300'], pe_details_map['CSI300'] = calculate_pe_percentile_with_details('CSI300', self.pe_cache, current_date, 10)
            pe_percentiles['CSI500'], pe_details_map['CSI500'] = calculate_pe_percentile_with_details('CSI500', self.pe_cache, current_date, 10)
            pe_percentiles['HSI'], pe_details_map['HSI'] = calculate_pe_percentile_with_details('HSI', self.pe_cache, current_date, 10)
            pe_percentiles['HSTECH'], pe_details_map['HSTECH'] = calculate_pe_percentile_with_details('HSTECH', self.pe_cache, current_date, 10)
            pe_percentiles['SP500'], pe_details_map['SP500'] = calculate_pe_percentile_with_details('SP500', self.pe_cache, current_date, 20)
            pe_percentiles['NASDAQ100'], pe_details_map['NASDAQ100'] = calculate_pe_percentile_with_details('NASDAQ100', self.pe_cache, current_date, 20)
            
            yield_pct = calculate_yield_percentile(self.market_data, current_date, 20)
            current_yield = get_current_yield(self.market_data, current_date)
            
            # Dynamic allocation based on P/E percentiles
            raw_weights = {}
            raw_weights['CSI300'] = 0.15 * (1 - pe_percentiles['CSI300'])
            raw_weights['CSI500'] = 0.15 * (1 - pe_percentiles['CSI500'])
            raw_weights['HSI'] = 0.10 * (1 - pe_percentiles['HSI'])
            raw_weights['HSTECH'] = 0.10 * (1 - pe_percentiles['HSTECH'])
            raw_weights['SP500'] = 0.15 * (1 - pe_percentiles['SP500'])
            raw_weights['NASDAQ100'] = 0.15 * (1 - pe_percentiles['NASDAQ100'])
            raw_weights['TLT'] = 0.15 * (yield_pct ** 2)
            
            # Cash allocation based on yield threshold
            if current_yield >= 4.0:
                raw_weights['CASH'] = current_yield / 100.0
            else:
                raw_weights['CASH'] = 0.0
            
            raw_weights['GLD'] = 0.10
            
            # Normalize weights
            total_weight = sum(raw_weights.values())
            if total_weight > 0:
                scale_factor = 1.0 / total_weight
                for asset, value in raw_weights.items():
                    weights[asset] = value * scale_factor
            else:
                weights = raw_weights.copy()

            # Persist detailed calculation inputs/outputs for rebalance logging
            self.last_weight_calc_details = {
                'inputs': {
                    'pe_percentiles': pe_percentiles,
                    'pe_inputs': pe_details_map,
                    'yield_percentile': yield_pct,
                    'current_yield': current_yield,
                },
                'raw_weights': raw_weights,
                'normalization': {
                    'total_raw_weight': total_weight,
                    'scale_factor': (1.0 / total_weight) if total_weight > 0 else None,
                },
                'outputs': {
                    'final_weights': weights.copy()
                }
            }
            
            return weights
            
        except Exception as e:
            # Fallback to equal weights if calculation fails
            assets = [data._name for data in self.datas]
            LOG.warning(f"DynamicAllocationStrategy calculation failed on {current_date}: {e}. Falling back to equal weights.")
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

        # Record simple transparency for momentum inputs/outputs
        self.last_weight_calc_details = {
            'inputs': {
                'momentum_window_days': 252,
                'momentum_raw': momentum_scores,
            },
            'outputs': {
                'final_weights': weights.copy()
            }
        }
        
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

        # Record simple transparency for risk parity inputs/outputs
        self.last_weight_calc_details = {
            'inputs': {
                'volatility_window_days': 21,
                'inverse_volatility_scores': volatility_scores,
            },
            'outputs': {
                'final_weights': weights.copy()
            }
        }
        
        return weights