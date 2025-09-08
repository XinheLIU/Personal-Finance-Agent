"""
Performance Attribution Module

This module provides professional-grade performance attribution analysis that decomposes
portfolio returns into asset-level contributions and rebalancing effects across different
time periods (daily, weekly, monthly).

The attribution methodology follows industry standards used by institutional asset managers:
- Asset Contribution: How each asset's price movement contributed to portfolio performance
- Weight Change Impact: How rebalancing activities affected performance  
- Time-based Analysis: Attribution across daily, weekly, and monthly periods
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
import warnings
from dataclasses import dataclass

from src.ui.app_logger import LOG
from config.assets import ASSETS

warnings.filterwarnings('ignore', category=RuntimeWarning)

@dataclass
class AttributionResult:
    """Container for attribution analysis results"""
    date: datetime
    total_return: float
    asset_contributions: Dict[str, float]
    weight_change_impact: float
    rebalancing_impact: Dict[str, float]
    attribution_period: str  # 'daily', 'weekly', 'monthly'


class PerformanceAttributor:
    """
    Standalone performance attribution analysis system
    
    Decomposes portfolio performance into:
    1. Asset-level price contributions
    2. Weight change (rebalancing) effects
    3. Interaction effects between price and weight changes
    
    Now operates independently from backtesting module.
    """
    
    def __init__(self, results_dir: str = "analytics/attribution"):
        """
        Initialize performance attributor
        
        Args:
            results_dir: Directory to save attribution analysis results
        """
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        LOG.info(f"Standalone performance attribution system initialized, results dir: {self.results_dir}")
    
    def load_strategy_data(self, strategy_name: str, start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """
        Load strategy data for attribution analysis.
        
        Args:
            strategy_name: Name of the strategy to analyze
            start_date: Start date for analysis (YYYY-MM-DD)
            end_date: End date for analysis (YYYY-MM-DD)
            
        Returns:
            Dictionary with portfolio_data, asset_returns, weights_data
        """
        LOG.info(f"Loading strategy data for {strategy_name} from {start_date} to {end_date}")
        
        try:
            # Load portfolio weights/holdings data
            weights_data = self._load_portfolio_weights(strategy_name, start_date, end_date)
            
            # Load asset returns data
            asset_returns = self._load_asset_returns(start_date, end_date)
            
            # Calculate portfolio performance from weights and returns
            portfolio_data = self._calculate_portfolio_performance(weights_data, asset_returns)
            
            return {
                'portfolio_data': portfolio_data,
                'asset_returns': asset_returns,
                'weights_data': weights_data
            }
            
        except Exception as e:
            LOG.error(f"Failed to load strategy data for {strategy_name}: {e}")
            raise
    
    def _load_portfolio_weights(self, strategy_name: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Load portfolio weights from saved data or strategy configuration."""
        strategy_safe = strategy_name.replace('/', '_').replace(' ', '_').lower()
        
        # Try to load from rebalancing log file first
        rebal_file = Path("analytics/backtests") / f"{strategy_safe}_rebalance_log.csv"
        if rebal_file.exists():
            LOG.info(f"Loading weights from rebalancing log: {rebal_file}")
            weights_df = pd.read_csv(rebal_file)
            weights_df['date'] = pd.to_datetime(weights_df['date'])
            # Normalize to date-only to align with returns
            weights_df['date'] = weights_df['date'].dt.normalize()
            # Filter requested period
            weights_df = weights_df[(weights_df['date'] >= pd.to_datetime(start_date)) & (weights_df['date'] <= pd.to_datetime(end_date))]
            
            if not weights_df.empty and len(weights_df) >= 2:
                weights_df.set_index('date', inplace=True)
                return weights_df
            else:
                LOG.warning("Rebalance log has no data in requested period; falling back to configured/equal weights")
        
        # Fallback: load from strategy configuration
        return self._load_strategy_weights(strategy_name, start_date, end_date)
    
    def _load_strategy_weights(self, strategy_name: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Load weights from strategy configuration."""
        from src.modules.portfolio.strategies.registry import strategy_registry
        
        try:
            strategy_class = strategy_registry.get(strategy_name)
            if strategy_class is not None and hasattr(strategy_class, 'get_static_target_weights'):
                target_weights = strategy_class.get_static_target_weights()
                # Create daily series for period
                date_range = pd.date_range(start=start_date, end=end_date, freq='D')
                weights_data = []
                for date in date_range:
                    row = {'date': date}
                    row.update(target_weights)
                    weights_data.append(row)
                weights_df = pd.DataFrame(weights_data)
                weights_df['date'] = pd.to_datetime(weights_df['date']).dt.normalize()
                weights_df.set_index('date', inplace=True)
                LOG.info(f"Created static weights for {strategy_name} with {len(target_weights)} assets")
                return weights_df
        except Exception as e:
            LOG.warning(f"Could not load strategy weights for {strategy_name}: {e}")
        
        # Final fallback: equal weights
        from config.assets import TRADABLE_ASSETS
        equal_weight = 1.0 / len(TRADABLE_ASSETS)
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        weights_data = []
        for date in date_range:
            row = {'date': date}
            for asset in TRADABLE_ASSETS.keys():
                row[asset] = equal_weight
            weights_data.append(row)
        
        weights_df = pd.DataFrame(weights_data)
        weights_df.set_index('date', inplace=True)
        
        LOG.warning(f"Using equal weights fallback for {strategy_name}")
        return weights_df
    
    def _load_asset_returns(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Load asset returns data."""
        from src.modules.data_management.data_center.data_loader import DataLoader
        
        data_loader = DataLoader()
        market_data = data_loader.load_market_data(normalize=True)
        
        returns_data = {}
        for asset, data in market_data.items():
            if isinstance(data, pd.DataFrame) and 'close' in data.columns:
                # Filter by date range
                data_filtered = data[(data.index >= pd.to_datetime(start_date)) & (data.index <= pd.to_datetime(end_date))]
                
                if len(data_filtered) > 1:
                    # Calculate daily returns
                    returns_data[asset] = data_filtered['close'].pct_change().dropna()
        
        if returns_data:
            returns_df = pd.DataFrame(returns_data)
            returns_df = returns_df.fillna(0)
            # Normalize to date-only to ease intersection with weights
            if isinstance(returns_df.index, pd.DatetimeIndex):
                returns_df.index = returns_df.index.normalize()
            LOG.info(f"Loaded returns for {len(returns_data)} assets from {start_date} to {end_date}")
            return returns_df
        else:
            raise ValueError(f"No asset returns data available for period {start_date} to {end_date}")
    
    def _calculate_portfolio_performance(self, weights_data: pd.DataFrame, asset_returns: pd.DataFrame) -> pd.DataFrame:
        """Calculate portfolio performance from weights and returns."""
        # Align dates
        common_dates = weights_data.index.intersection(asset_returns.index)
        if len(common_dates) < 2:
            raise ValueError("Insufficient common dates between weights and returns data")
        
        portfolio_performance = []
        initial_value = 100.0  # Start with base value of 100
        
        for i, date in enumerate(sorted(common_dates)):
            if i == 0:
                portfolio_performance.append({
                    'date': date,
                    'value': initial_value,
                    'returns': 0.0
                })
                continue
            
            prev_date = sorted(common_dates)[i-1]
            
            # Get weights and returns for the period
            weights = weights_data.loc[prev_date]
            returns = asset_returns.loc[date]
            
            # Calculate portfolio return for the day
            portfolio_return = 0.0
            for asset in weights.index:
                if asset in returns.index and not pd.isna(weights[asset]) and not pd.isna(returns[asset]):
                    portfolio_return += weights[asset] * returns[asset]
            
            # Update portfolio value
            prev_value = portfolio_performance[i-1]['value']
            new_value = prev_value * (1 + portfolio_return)
            
            portfolio_performance.append({
                'date': date,
                'value': new_value,
                'returns': portfolio_return
            })
        
        portfolio_df = pd.DataFrame(portfolio_performance)
        portfolio_df.set_index('date', inplace=True)
        
        LOG.info(f"Calculated portfolio performance for {len(portfolio_df)} periods")
        return portfolio_df
    
    # Backward-compatible wrapper expected by tests/UI
    def generate_attribution_report(self,
                                    strategy_name: str,
                                    portfolio_data: Optional[pd.DataFrame] = None,
                                    asset_returns: Optional[pd.DataFrame] = None,
                                    weights_data: Optional[pd.DataFrame] = None,
                                    include_weekly: bool = True,
                                    include_monthly: bool = True) -> Dict[str, Any]:
        """
        Compatibility method: if dataframes are provided, run attribution directly;
        otherwise, fall back to loading recent period via run_attribution_analysis.
        """
        try:
            if all(x is not None for x in [portfolio_data, asset_returns, weights_data]):
                # Calculate daily attributions
                daily_attributions = self.calculate_daily_attribution(
                    portfolio_data, asset_returns, weights_data
                )
                if not daily_attributions:
                    return {'error': 'Failed to calculate daily attributions'}
                report: Dict[str, Any] = {
                    'strategy_name': strategy_name,
                    'analysis_period': {
                        'start_date': str(min(portfolio_data.index.min(), asset_returns.index.min(), weights_data.index.min())),
                        'end_date': str(max(portfolio_data.index.max(), asset_returns.index.max(), weights_data.index.max()))
                    },
                    'report_date': datetime.now().isoformat(),
                    'daily_analysis': self.decompose_returns(daily_attributions)
                }
                if include_weekly:
                    weekly = self.calculate_periodic_attribution(daily_attributions, 'weekly')
                    if weekly:
                        report['weekly_analysis'] = self.decompose_returns(weekly)
                if include_monthly:
                    monthly = self.calculate_periodic_attribution(daily_attributions, 'monthly')
                    if monthly:
                        report['monthly_analysis'] = self.decompose_returns(monthly)
                return report
            # No dataframes provided: require external dates via run_attribution_analysis
            return {'error': 'Insufficient inputs: provide portfolio_data, asset_returns, and weights_data or use run_attribution_analysis with dates'}
        except Exception as e:
            LOG.error(f"generate_attribution_report failed: {e}")
            return {'error': str(e)}

    def run_attribution_analysis(self, 
                                strategy_name: str,
                                start_date: str,
                                end_date: str,
                                include_weekly: bool = True,
                                include_monthly: bool = True) -> Dict[str, Any]:
        """
        Run comprehensive attribution analysis for a strategy.
        
        Args:
            strategy_name: Name of the strategy to analyze
            start_date: Start date for analysis (YYYY-MM-DD)
            end_date: End date for analysis (YYYY-MM-DD)
            include_weekly: Include weekly attribution analysis
            include_monthly: Include monthly attribution analysis
            
        Returns:
            Comprehensive attribution analysis report
        """
        LOG.info(f"Running attribution analysis for {strategy_name} from {start_date} to {end_date}")
        
        try:
            # Load strategy data
            strategy_data = self.load_strategy_data(strategy_name, start_date, end_date)
            
            # Calculate daily attributions
            daily_attributions = self.calculate_daily_attribution(
                strategy_data['portfolio_data'],
                strategy_data['asset_returns'],
                strategy_data['weights_data']
            )
            
            if not daily_attributions:
                return {'error': 'Failed to calculate daily attributions'}
            
            # Generate report sections
            report = {
                'strategy_name': strategy_name,
                'analysis_period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'report_date': datetime.now().isoformat(),
                'daily_analysis': self.decompose_returns(daily_attributions)
            }
            
            # Weekly analysis
            if include_weekly:
                weekly_attributions = self.calculate_periodic_attribution(
                    daily_attributions, 'weekly'
                )
                if weekly_attributions:
                    report['weekly_analysis'] = self.decompose_returns(weekly_attributions)
            
            # Monthly analysis
            if include_monthly:
                monthly_attributions = self.calculate_periodic_attribution(
                    daily_attributions, 'monthly'
                )
                if monthly_attributions:
                    report['monthly_analysis'] = self.decompose_returns(monthly_attributions)
            
            # Save detailed data
            self.save_attribution_data(strategy_name, {
                'daily': daily_attributions,
                'weekly': weekly_attributions if include_weekly else [],
                'monthly': monthly_attributions if include_monthly else []
            })
            
            LOG.info(f"Attribution analysis completed successfully for {strategy_name}")
            return report
            
        except Exception as e:
            LOG.error(f"Error in attribution analysis for {strategy_name}: {e}")
            return {'error': f'Attribution analysis failed: {str(e)}'}
    
    def calculate_daily_attribution(self, 
                                  portfolio_data: pd.DataFrame,
                                  asset_returns: pd.DataFrame,
                                  weights_data: pd.DataFrame) -> List[AttributionResult]:
        """
        Calculate daily performance attribution
        
        Attribution Formula:
        Portfolio Return = Σ(weight_i * asset_return_i) + weight_change_effects + interaction_effects
        
        Args:
            portfolio_data: DataFrame with portfolio values and returns
            asset_returns: DataFrame with individual asset returns
            weights_data: DataFrame with asset weights over time
            
        Returns:
            List of daily attribution results
        """
        LOG.info("Starting daily performance attribution analysis")
        
        # Align all data on common dates
        try:
            # Ensure all data has datetime indices
            for df_name, df in [('portfolio', portfolio_data), ('returns', asset_returns), ('weights', weights_data)]:
                if not isinstance(df.index, pd.DatetimeIndex):
                    LOG.warning(f"{df_name} data index is not datetime, attempting conversion")
                    df.index = pd.to_datetime(df.index)
            
            common_dates = portfolio_data.index.intersection(
                asset_returns.index.intersection(weights_data.index)
            )
            
            LOG.info(f"Attribution data alignment: Portfolio={len(portfolio_data)}, Assets={len(asset_returns)}, Weights={len(weights_data)}, Common={len(common_dates)}")
            
            if len(common_dates) < 5:
                LOG.warning(f"Insufficient common dates for attribution analysis: {len(common_dates)} days")
                return []
                
        except Exception as e:
            LOG.error(f"Error aligning attribution data: {e}")
            return []
        
        portfolio_aligned = portfolio_data.loc[common_dates]
        returns_aligned = asset_returns.loc[common_dates]
        weights_aligned = weights_data.loc[common_dates]

        # Clean and filter data
        try:
            from config.assets import TRADABLE_ASSETS
            allowed_assets = set(TRADABLE_ASSETS.keys())

            # Filter weights to known assets only
            weight_cols = [col for col in weights_aligned.columns 
                          if isinstance(col, str) and col in allowed_assets]
            if weight_cols:
                weights_aligned = weights_aligned[weight_cols]

            # Filter returns to known assets only  
            return_cols = [col for col in returns_aligned.columns
                          if isinstance(col, str) and col in allowed_assets]
            if return_cols:
                returns_aligned = returns_aligned[return_cols]

            # Ensure both have same assets
            shared_cols = [c for c in weights_aligned.columns if c in returns_aligned.columns]
            if shared_cols:
                weights_aligned = weights_aligned[shared_cols]
                returns_aligned = returns_aligned[shared_cols]
                
        except Exception as e:
            LOG.warning(f"Failed to clean attribution data: {e}")

        # Filter out assets with no meaningful weights
        try:
            nonzero_assets = []
            for col in weights_aligned.columns:
                col_series = pd.to_numeric(weights_aligned[col], errors='coerce').fillna(0.0)
                if float(col_series.abs().sum()) > 0.001:  # Minimum threshold
                    nonzero_assets.append(col)

            if nonzero_assets:
                weights_aligned = weights_aligned[nonzero_assets]
                existing_return_cols = [c for c in nonzero_assets if c in returns_aligned.columns]
                if existing_return_cols:
                    returns_aligned = returns_aligned[existing_return_cols]
                    
        except Exception as e:
            LOG.warning(f"Failed to filter zero-weight assets: {e}")
        
        attribution_results = []
        
        for i in range(1, len(common_dates)):
            current_date = common_dates[i]
            prev_date = common_dates[i-1]
            
            # Portfolio return for the period
            if 'returns' in portfolio_aligned.columns:
                portfolio_return = portfolio_aligned.loc[current_date, 'returns']
                if isinstance(portfolio_return, pd.Series):
                    portfolio_return = portfolio_return.iloc[0]
            else:
                current_value = portfolio_aligned.loc[current_date, 'value']
                prev_value = portfolio_aligned.loc[prev_date, 'value']
                if isinstance(current_value, pd.Series):
                    current_value = current_value.iloc[0]
                if isinstance(prev_value, pd.Series):
                    prev_value = prev_value.iloc[0]
                portfolio_return = (current_value / prev_value) - 1
            
            # Skip if portfolio return is invalid
            if pd.isna(portfolio_return) or not np.isfinite(portfolio_return):
                continue
            
            # Current and previous weights
            current_weights = weights_aligned.loc[current_date]
            prev_weights = weights_aligned.loc[prev_date]
            
            # Asset returns for the period
            asset_returns_period = returns_aligned.loc[current_date]
            
            # Calculate asset contributions using previous period weights
            asset_contributions = {}
            total_asset_contribution = 0
            
            for asset in prev_weights.index:
                if asset in asset_returns_period.index:
                    asset_return = asset_returns_period[asset]
                    if pd.isna(asset_return) or not np.isfinite(asset_return):
                        asset_return = 0
                    
                    contribution = prev_weights[asset] * asset_return
                    asset_contributions[asset] = contribution
                    total_asset_contribution += contribution
                else:
                    asset_contributions[asset] = 0
            
            # Calculate weight change impact
            weight_changes = current_weights - prev_weights
            
            # Weight change impact using current period returns
            rebalancing_impact = {}
            total_rebalancing_impact = 0
            
            for asset in weight_changes.index:
                if asset in asset_returns_period.index:
                    weight_change = weight_changes[asset]
                    asset_return = asset_returns_period.get(asset, 0)
                    if pd.isna(asset_return) or not np.isfinite(asset_return):
                        asset_return = 0
                    
                    impact = weight_change * asset_return
                    rebalancing_impact[asset] = impact
                    total_rebalancing_impact += impact
                else:
                    rebalancing_impact[asset] = 0
            
            # Create attribution result
            attribution_result = AttributionResult(
                date=current_date,
                total_return=portfolio_return,
                asset_contributions=asset_contributions,
                weight_change_impact=total_rebalancing_impact,
                rebalancing_impact=rebalancing_impact,
                attribution_period='daily'
            )
            
            attribution_results.append(attribution_result)
        
        LOG.info(f"Completed daily attribution analysis for {len(attribution_results)} periods")
        return attribution_results
    
    def calculate_periodic_attribution(self, 
                                     daily_attributions: List[AttributionResult],
                                     period: str = 'weekly') -> List[AttributionResult]:
        """
        Aggregate daily attributions into weekly or monthly periods
        
        Args:
            daily_attributions: List of daily attribution results
            period: 'weekly' or 'monthly'
            
        Returns:
            List of aggregated attribution results
        """
        if not daily_attributions:
            LOG.warning("No daily attributions provided for periodic aggregation")
            return []
        
        LOG.info(f"Calculating {period} attribution aggregation")
        
        # Convert to DataFrame for easier manipulation
        attribution_df = pd.DataFrame([
            {
                'date': attr.date,
                'total_return': attr.total_return,
                'weight_change_impact': attr.weight_change_impact,
                **{f'asset_{asset}': contrib for asset, contrib in attr.asset_contributions.items()},
                **{f'rebal_{asset}': impact for asset, impact in attr.rebalancing_impact.items()}
            }
            for attr in daily_attributions
        ])
        
        attribution_df['date'] = pd.to_datetime(attribution_df['date'])
        attribution_df.set_index('date', inplace=True)
        
        # Define aggregation frequency
        freq = 'W' if period == 'weekly' else 'ME' if period == 'monthly' else 'D'
        
        # Aggregate by period
        grouped = attribution_df.groupby(pd.Grouper(freq=freq))
        
        periodic_results = []
        
        for period_end, group_data in grouped:
            if group_data.empty:
                continue
            
            # Calculate compound return for the period
            period_returns = group_data['total_return']
            compound_return = (1 + period_returns).prod() - 1
            
            # Sum contributions over the period
            asset_columns = [col for col in group_data.columns if col.startswith('asset_')]
            rebal_columns = [col for col in group_data.columns if col.startswith('rebal_')]
            
            # Aggregate asset contributions
            asset_contributions = {}
            for col in asset_columns:
                asset_name = col.replace('asset_', '')
                asset_contributions[asset_name] = group_data[col].sum()
            
            # Aggregate rebalancing impacts
            rebalancing_impact = {}
            for col in rebal_columns:
                asset_name = col.replace('rebal_', '')
                rebalancing_impact[asset_name] = group_data[col].sum()
            
            total_weight_change_impact = group_data['weight_change_impact'].sum()
            
            # Create periodic attribution result
            periodic_result = AttributionResult(
                date=period_end,
                total_return=compound_return,
                asset_contributions=asset_contributions,
                weight_change_impact=total_weight_change_impact,
                rebalancing_impact=rebalancing_impact,
                attribution_period=period
            )
            
            periodic_results.append(periodic_result)
        
        LOG.info(f"Completed {period} attribution aggregation for {len(periodic_results)} periods")
        return periodic_results
    
    def decompose_returns(self, 
                         attribution_results: List[AttributionResult]) -> Dict[str, Any]:
        """
        Decompose and analyze attribution results
        
        Args:
            attribution_results: List of attribution results to analyze
            
        Returns:
            Comprehensive attribution analysis dictionary
        """
        if not attribution_results:
            return {'error': 'No attribution results to analyze'}
        
        LOG.info("Decomposing attribution results for analysis")
        
        # Convert to DataFrame for analysis
        analysis_data = []
        all_assets = set()
        
        for attr in attribution_results:
            row = {
                'date': attr.date,
                'total_return': attr.total_return,
                'weight_change_impact': attr.weight_change_impact,
                'attribution_period': attr.attribution_period
            }
            
            # Add asset contributions
            for asset, contrib in attr.asset_contributions.items():
                row[f'asset_contrib_{asset}'] = contrib
                all_assets.add(asset)
            
            # Add rebalancing impacts
            for asset, impact in attr.rebalancing_impact.items():
                row[f'rebal_impact_{asset}'] = impact
            
            analysis_data.append(row)
        
        analysis_df = pd.DataFrame(analysis_data)
        analysis_df['date'] = pd.to_datetime(analysis_df['date'])
        
        # Filter to valid asset keys
        try:
            from config.assets import TRADABLE_ASSETS
            valid_assets = {a for a in all_assets if isinstance(a, str) and a in TRADABLE_ASSETS}
        except Exception:
            valid_assets = {a for a in all_assets if isinstance(a, str)}
        
        # Summary statistics
        total_returns = analysis_df['total_return'].sum()
        total_weight_impact = analysis_df['weight_change_impact'].sum()
        
        # Asset contribution analysis
        asset_summary = {}
        for asset in valid_assets:
            contrib_col = f'asset_contrib_{asset}'
            rebal_col = f'rebal_impact_{asset}'
            
            if contrib_col in analysis_df.columns:
                total_asset_contrib = analysis_df[contrib_col].sum()
                avg_asset_contrib = analysis_df[contrib_col].mean()
                contrib_volatility = analysis_df[contrib_col].std()
            else:
                total_asset_contrib = avg_asset_contrib = contrib_volatility = 0
            
            if rebal_col in analysis_df.columns:
                total_rebal_impact = analysis_df[rebal_col].sum()
                avg_rebal_impact = analysis_df[rebal_col].mean()
                rebal_volatility = analysis_df[rebal_col].std()
            else:
                total_rebal_impact = avg_rebal_impact = rebal_volatility = 0
            
            asset_summary[asset] = {
                'total_contribution': total_asset_contrib,
                'average_contribution': avg_asset_contrib,
                'contribution_volatility': contrib_volatility,
                'total_rebalancing_impact': total_rebal_impact,
                'average_rebalancing_impact': avg_rebal_impact,
                'rebalancing_volatility': rebal_volatility,
                'net_impact': total_asset_contrib + total_rebal_impact
            }
        
        # Top contributors analysis
        top_contributors = []
        if asset_summary:
            top_contributors = sorted(
                asset_summary.items(),
                key=lambda x: x[1]['net_impact'],
                reverse=True
            )[:5]
        
        bottom_contributors = []
        if asset_summary:
            bottom_contributors = sorted(
                asset_summary.items(),
                key=lambda x: x[1]['net_impact']
            )[:5]
        
        return {
            'period': attribution_results[0].attribution_period,
            'total_periods': len(attribution_results),
            'date_range': {
                'start': attribution_results[0].date.isoformat(),
                'end': attribution_results[-1].date.isoformat()
            },
            'summary_statistics': {
                'total_portfolio_return': total_returns,
                'total_asset_contribution': sum(sum(attr.asset_contributions.values()) 
                                              for attr in attribution_results if len(attr.asset_contributions) > 0),
                'total_rebalancing_impact': total_weight_impact,
                'attribution_accuracy': abs(total_returns - (
                    sum(sum(attr.asset_contributions.values()) for attr in attribution_results if len(attr.asset_contributions) > 0) + 
                    total_weight_impact
                ))
            },
            'asset_analysis': asset_summary,
            'top_contributors': dict(top_contributors),
            'bottom_contributors': dict(bottom_contributors),
            'attribution_data': analysis_df.to_dict('records')
        }
    
    def save_attribution_data(self, 
                            strategy_name: str, 
                            attribution_data: Dict[str, List[AttributionResult]]) -> Dict[str, str]:
        """
        Save attribution analysis data to CSV and Excel files
        
        Args:
            strategy_name: Name of the strategy
            attribution_data: Dictionary with different period attribution data
            
        Returns:
            Dictionary with saved file paths
        """
        saved_files = {}
        strategy_safe = strategy_name.replace('/', '_').replace(' ', '_').lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            for period, results in attribution_data.items():
                if not results:
                    continue
                
                # Convert to DataFrame
                rows = []
                for attr in results:
                    row = {
                        'Date': attr.date.strftime('%Y-%m-%d'),
                        'Total_Return': attr.total_return,
                        'Weight_Change_Impact': attr.weight_change_impact
                    }
                    
                    # Add asset contributions
                    for asset, contrib in attr.asset_contributions.items():
                        row[f'Asset_Contrib_{asset}'] = contrib
                    
                    # Add rebalancing impacts
                    for asset, impact in attr.rebalancing_impact.items():
                        row[f'Rebal_Impact_{asset}'] = impact
                    
                    rows.append(row)
                
                if rows:
                    df = pd.DataFrame(rows)
                    
                    # Save CSV
                    csv_file = self.results_dir / f"{strategy_safe}_{period}_attribution_{timestamp}.csv"
                    df.to_csv(csv_file, index=False)
                    saved_files[f'{period}_csv'] = str(csv_file)
            
            # Create comprehensive Excel file with all periods
            if any(attribution_data.values()):
                excel_file = self.results_dir / f"{strategy_safe}_attribution_analysis_{timestamp}.xlsx"
                
                with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                    for period, results in attribution_data.items():
                        if not results:
                            continue
                        
                        # Convert to DataFrame for Excel
                        rows = []
                        for attr in results:
                            row = {
                                'Date': attr.date.strftime('%Y-%m-%d'),
                                'Total_Return': attr.total_return,
                                'Weight_Change_Impact': attr.weight_change_impact
                            }
                            
                            for asset, contrib in attr.asset_contributions.items():
                                row[f'Asset_Contrib_{asset}'] = contrib
                            
                            for asset, impact in attr.rebalancing_impact.items():
                                row[f'Rebal_Impact_{asset}'] = impact
                            
                            rows.append(row)
                        
                        if rows:
                            df = pd.DataFrame(rows)
                            df.to_excel(writer, sheet_name=period.title(), index=False)
                
                saved_files['excel_comprehensive'] = str(excel_file)
            
            LOG.info(f"Attribution data saved for {strategy_name}: {list(saved_files.keys())}")
            return saved_files
            
        except Exception as e:
            LOG.error(f"Error saving attribution data for {strategy_name}: {e}")
            return {'error': f'Failed to save attribution data: {str(e)}'}