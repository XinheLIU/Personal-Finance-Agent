"""
Portfolio Presenter

Orchestrates portfolio management, backtesting, and attribution analysis business logic.
Separates business logic from UI concerns for better testability and reusability.
"""

import json
import os
from datetime import date, timedelta
from typing import Dict, Optional, Any, List, Tuple

from config.assets import TRADABLE_ASSETS, ASSET_DISPLAY_INFO, DYNAMIC_STRATEGY_PARAMS
from config.system import INITIAL_CAPITAL, COMMISSION
from src.modules.portfolio.backtesting.runner import run_backtest
from src.modules.portfolio.strategies.registry import strategy_registry
from src.modules.portfolio.strategies.base import FixedWeightStrategy
from src.ui.app_logger import LOG


class PortfolioPresenter:
    """Presenter for portfolio management operations."""
    
    def __init__(self, holdings_file: str = "data/holdings.json"):
        self.holdings_file = holdings_file
    
    def get_available_strategies(self) -> Dict[str, Any]:
        """Get list of available strategies."""
        return strategy_registry.list_strategies()
    
    def get_strategy_weights(self, strategy_name: str) -> Dict[str, float]:
        """Get target weights for a strategy without running full backtest."""
        strategy_class = strategy_registry.get(strategy_name)
        if not strategy_class:
            return {}
        
        try:
            # Check if it's a static strategy
            if hasattr(strategy_class, 'get_static_target_weights'):
                weights = strategy_class.get_static_target_weights()
                return weights
            
            # For dynamic strategies, try to get weights using standalone function
            if strategy_name == "DynamicAllocationStrategy":
                try:
                    from src.modules.portfolio.strategies.classic import get_target_weights_and_metrics_standalone
                    weights, _ = get_target_weights_and_metrics_standalone()
                    return weights
                except Exception as e:
                    LOG.warning(f"Could not calculate dynamic weights: {e}")
                    return {}
            
            # For other dynamic strategies, return empty dict (weights depend on market data)
            strategy_type = strategy_class.get_strategy_type()
            if strategy_type == "dynamic":
                return {}
            
            # Fallback - shouldn't happen with proper implementation
            return {}
        except Exception as e:
            LOG.error(f"Error getting strategy weights for {strategy_name}: {e}")
            return {}
    
    def load_holdings(self) -> Dict[str, float]:
        """Load current holdings from JSON file."""
        if os.path.exists(self.holdings_file):
            try:
                with open(self.holdings_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                LOG.error(f"Error loading holdings: {e}")
        return {}
    
    def save_holdings(self, holdings_dict: Dict[str, float]) -> str:
        """Save holdings to JSON file."""
        try:
            os.makedirs(os.path.dirname(self.holdings_file), exist_ok=True)
            with open(self.holdings_file, 'w') as f:
                json.dump(holdings_dict, f, indent=4)
            return "Holdings saved successfully!"
        except Exception as e:
            LOG.error(f"Error saving holdings: {e}")
            return f"Error saving holdings: {e}"
    
    def balance_portfolio_weights(self, holdings: Dict[str, float], updated_asset: str, new_weight: float) -> Dict[str, float]:
        """Balance portfolio weights to ensure they sum to 100%."""
        # Set the new weight for the updated asset
        holdings[updated_asset] = new_weight
        
        # Calculate current total
        total_weight = sum(holdings.values())
        
        if abs(total_weight - 1.0) < 0.001:  # Already balanced
            return holdings
        
        # If total exceeds 100%, adjust other assets proportionally
        if total_weight > 1.0:
            excess = total_weight - 1.0
            other_assets = {k: v for k, v in holdings.items() if k != updated_asset}
            
            if other_assets:
                # Reduce other assets proportionally
                other_total = sum(other_assets.values())
                if other_total > 0:
                    reduction_factor = max(0, (other_total - excess) / other_total)
                    for asset in other_assets:
                        holdings[asset] = max(0, holdings[asset] * reduction_factor)
            else:
                # If only one asset, cap it at 100%
                holdings[updated_asset] = 1.0
        
        # If total is less than 100%, add to the largest existing position
        elif total_weight < 1.0:
            deficit = 1.0 - total_weight
            if holdings:
                # Find largest position (excluding the just-updated asset)
                other_assets = {k: v for k, v in holdings.items() if k != updated_asset}
                if other_assets:
                    largest_asset = max(other_assets.keys(), key=lambda k: other_assets[k])
                    holdings[largest_asset] = min(1.0, holdings[largest_asset] + deficit)
                else:
                    holdings[updated_asset] = 1.0
        
        return holdings
    
    def get_portfolio_gap_analysis(self, holdings: Dict[str, float], strategy_name: str) -> List[Dict[str, Any]]:
        """Get gap analysis between current holdings and strategy target."""
        strategy_weights = self.get_strategy_weights(strategy_name)
        
        if not strategy_weights:
            return []
        
        comparison_data = []
        all_assets = sorted(list(set(strategy_weights.keys()) | set(holdings.keys())))
        
        for asset in all_assets:
            target = strategy_weights.get(asset, 0)
            current = holdings.get(asset, 0)
            diff = target - current
            
            display_info = ASSET_DISPLAY_INFO.get(asset, {})
            asset_name = display_info.get('name', asset)
            
            # Color coding for differences
            if abs(diff) < 0.01:  # Within 1%
                status = "✅ Balanced"
            elif diff > 0:
                status = f"⬆️ Under-weighted ({diff:.1%})"
            else:
                status = f"⬇️ Over-weighted ({abs(diff):.1%})"
            
            comparison_data.append({
                "Asset": asset_name,
                "Target": f"{target:.1%}",
                "Current": f"{current:.1%}",
                "Gap": f"{diff:+.1%}",
                "Status": status
            })
        
        return comparison_data
    
    def run_backtest(self, strategy_choice: str, 
                    rebalance_days: int, 
                    threshold: float, 
                    initial_capital: float, 
                    commission: float, 
                    start_date: str,
                    enable_attribution: bool = False) -> Dict:
        """Run backtest and return results."""
        # Update dynamic strategy parameters
        DYNAMIC_STRATEGY_PARAMS['rebalance_days'] = rebalance_days
        DYNAMIC_STRATEGY_PARAMS['threshold'] = threshold
        
        strategy_class = strategy_registry.get(strategy_choice)
        if not strategy_class:
            return {"error": f"Strategy '{strategy_choice}' not found"}
        
        try:
            # Pass initial capital, commission, attribution flag, and strategy params through to the runner
            results = run_backtest(
                strategy_class,
                strategy_choice,
                start_date=start_date,
                initial_capital=initial_capital,
                commission=commission,
                enable_attribution=enable_attribution,
                rebalance_days=rebalance_days,
                threshold=threshold
            )
            return results if results else {"error": "Backtest failed"}
        except Exception as e:
            LOG.error(f"Backtest error: {e}")
            return {"error": f"Backtest failed: {e}"}
    
    def run_asset_attribution_analysis(self, strategy_choice: str, start_date: str, end_date: str, frequency: str) -> Dict[str, Any]:
        """Run asset-level attribution analysis."""
        try:
            from src.modules.portfolio.performance.attribution import PerformanceAttributor
            
            attributor = PerformanceAttributor()
            
            # Run attribution analysis
            results = attributor.run_attribution_analysis(
                strategy_name=strategy_choice,
                start_date=start_date,
                end_date=end_date,
                include_weekly=(frequency in ['weekly', 'daily']),
                include_monthly=(frequency == 'monthly')
            )
            
            return results
            
        except Exception as e:
            LOG.error(f"Asset attribution analysis failed: {e}")
            return {"error": str(e)}
    
    def run_sector_attribution_analysis(self, strategy_choice: str, start_date: str, end_date: str, frequency: str, benchmark: str) -> Dict[str, Any]:
        """Run sector-based attribution analysis."""
        try:
            from src.modules.portfolio.performance.sector_attribution import SectorAttributor
            
            sector_attributor = SectorAttributor()
            
            # Load portfolio data
            portfolio_weights, asset_returns, benchmark_weights = sector_attributor.load_portfolio_data(
                strategy_name=strategy_choice,
                start_date=start_date,
                end_date=end_date
            )
            
            # Calculate sector attribution
            daily_results = sector_attributor.calculate_sector_attribution(
                portfolio_weights=portfolio_weights,
                asset_returns=asset_returns,
                benchmark_weights=benchmark_weights,
                period='daily'
            )
            
            if not daily_results:
                return {"error": "No attribution results calculated"}
            
            # Aggregate results based on frequency
            if frequency == 'weekly':
                aggregated_results = sector_attributor.aggregate_attribution_results(daily_results, 'weekly')
            elif frequency == 'monthly':
                aggregated_results = sector_attributor.aggregate_attribution_results(daily_results, 'monthly')
            else:
                aggregated_results = daily_results
            
            # Create summary
            summary = sector_attributor.create_attribution_summary(aggregated_results)
            
            # Save results
            saved_files = sector_attributor.save_attribution_results(
                strategy_name=strategy_choice,
                attribution_results=aggregated_results,
                summary=summary
            )
            
            return {
                'attribution_results': aggregated_results,
                'summary': summary,
                'saved_files': saved_files,
                'frequency': frequency,
                'benchmark': benchmark
            }
            
        except Exception as e:
            LOG.error(f"Sector attribution analysis failed: {e}")
            return {"error": str(e)}
