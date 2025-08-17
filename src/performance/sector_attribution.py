"""
Sector-based performance attribution analysis following institutional standards.

This module implements Brinson attribution methodology at the sector level,
decomposing portfolio performance into allocation, selection, and interaction effects.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import logging

from config.sectors import (
    ASSET_SECTOR_MAPPING, SECTOR_ASSET_MAPPING, BENCHMARK_SECTOR_WEIGHTS,
    get_asset_sector, calculate_sector_weights, get_sector_color, get_all_sectors
)

LOG = logging.getLogger(__name__)

@dataclass
class SectorAttributionResult:
    """Results of sector-based attribution analysis."""
    date: datetime
    sector: str
    portfolio_weight: float
    benchmark_weight: float
    portfolio_return: float
    benchmark_return: float
    allocation_effect: float
    selection_effect: float
    interaction_effect: float
    total_effect: float

class SectorAttributor:
    """
    Professional sector-based performance attribution analyzer.
    
    Implements Brinson attribution methodology:
    - Allocation Effect: (wp - wb) × rb
    - Selection Effect: wb × (rp - rb)  
    - Interaction Effect: (wp - wb) × (rp - rb)
    
    Where:
    - wp, wb = Portfolio and benchmark weights
    - rp, rb = Portfolio and benchmark returns
    """
    
    def __init__(self, results_dir: str = "analytics/attribution"):
        """
        Initialize sector attribution analyzer.
        
        Args:
            results_dir: Directory to save attribution results
        """
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        LOG.info(f"Sector attribution analyzer initialized, results dir: {self.results_dir}")
    
    def load_portfolio_data(self, strategy_name: str, start_date: str, end_date: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Load portfolio data for attribution analysis.
        
        Args:
            strategy_name: Name of the strategy to analyze
            start_date: Start date for analysis (YYYY-MM-DD)
            end_date: End date for analysis (YYYY-MM-DD)
            
        Returns:
            Tuple of (portfolio_weights, asset_returns, benchmark_weights)
        """
        try:
            # Load data from various sources
            weights_data = self._load_weights_data(strategy_name, start_date, end_date)
            returns_data = self._load_returns_data(start_date, end_date)
            benchmark_data = self._create_benchmark_data(start_date, end_date)
            
            return weights_data, returns_data, benchmark_data
            
        except Exception as e:
            LOG.error(f"Failed to load portfolio data for {strategy_name}: {e}")
            raise
    
    def _load_weights_data(self, strategy_name: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Load portfolio weights data."""
        # Try to load from saved backtest results or rebalancing logs
        strategy_safe = strategy_name.replace('/', '_').replace(' ', '_').lower()
        
        # Check for rebalancing log file
        rebal_file = self.results_dir.parent / "backtests" / f"{strategy_safe}_rebalance_log.csv"
        if rebal_file.exists():
            weights_df = pd.read_csv(rebal_file)
            weights_df['date'] = pd.to_datetime(weights_df['date'])
            weights_df = weights_df[(weights_df['date'] >= start_date) & (weights_df['date'] <= end_date)]
            weights_df.set_index('date', inplace=True)
            return weights_df
        
        # Fallback: create weights from strategy metadata
        return self._create_static_weights(strategy_name, start_date, end_date)
    
    def _load_returns_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Load asset returns data."""
        from src.data_center.data_loader import DataLoader
        
        data_loader = DataLoader()
        market_data = data_loader.load_market_data(normalize=True)
        
        # Calculate daily returns
        returns_data = {}
        for asset, data in market_data.items():
            if isinstance(data, pd.DataFrame) and 'close' in data.columns:
                data_filtered = data[(data.index >= start_date) & (data.index <= end_date)]
                returns_data[asset] = data_filtered['close'].pct_change().dropna()
        
        if returns_data:
            returns_df = pd.DataFrame(returns_data)
            return returns_df.fillna(0)
        else:
            raise ValueError("No returns data available for attribution analysis")
    
    def _create_benchmark_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Create benchmark weights data."""
        # Create a simple time series with benchmark weights
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        benchmark_data = []
        for date in date_range:
            row = {'date': date}
            row.update(BENCHMARK_SECTOR_WEIGHTS)
            benchmark_data.append(row)
        
        benchmark_df = pd.DataFrame(benchmark_data)
        benchmark_df.set_index('date', inplace=True)
        return benchmark_df
    
    def _create_static_weights(self, strategy_name: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Create static weights for fixed allocation strategies."""
        from src.strategies.registry import strategy_registry
        
        try:
            strategies = strategy_registry.list_strategies()
            if strategy_name in strategies:
                strategy_class = strategies[strategy_name]
                strategy_instance = strategy_class()
                
                # Get target weights if available
                if hasattr(strategy_instance, 'get_target_weights'):
                    weights = strategy_instance.get_target_weights()
                    
                    # Create time series with these weights
                    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
                    weights_data = []
                    
                    for date in date_range:
                        row = {'date': date}
                        row.update(weights)
                        weights_data.append(row)
                    
                    weights_df = pd.DataFrame(weights_data)
                    weights_df.set_index('date', inplace=True)
                    return weights_df
        except Exception as e:
            LOG.warning(f"Could not create static weights for {strategy_name}: {e}")
        
        # Fallback: equal weights
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
        return weights_df
    
    def calculate_sector_attribution(self, 
                                   portfolio_weights: pd.DataFrame,
                                   asset_returns: pd.DataFrame,
                                   benchmark_weights: pd.DataFrame,
                                   period: str = 'daily') -> List[SectorAttributionResult]:
        """
        Calculate sector-based attribution analysis.
        
        Args:
            portfolio_weights: DataFrame with portfolio asset weights
            asset_returns: DataFrame with asset returns
            benchmark_weights: DataFrame with benchmark sector weights  
            period: Analysis period ('daily', 'weekly', 'monthly')
            
        Returns:
            List of sector attribution results
        """
        LOG.info(f"Starting sector attribution analysis for {period} period")
        
        try:
            # Align data on common dates
            common_dates = portfolio_weights.index.intersection(asset_returns.index)
            if len(common_dates) < 2:
                LOG.warning("Insufficient common dates for sector attribution")
                return []
            
            portfolio_aligned = portfolio_weights.loc[common_dates]
            returns_aligned = asset_returns.loc[common_dates]
            
            # Convert asset weights to sector weights
            sector_attribution_results = []
            
            for i in range(1, len(common_dates)):
                current_date = common_dates[i]
                prev_date = common_dates[i-1]
                
                # Get portfolio asset weights and convert to sector weights
                portfolio_asset_weights = portfolio_aligned.loc[prev_date]
                portfolio_sector_weights = self._convert_asset_to_sector_weights(portfolio_asset_weights)
                
                # Calculate sector returns
                asset_returns_period = returns_aligned.loc[current_date]
                sector_returns = self._calculate_sector_returns(asset_returns_period, portfolio_asset_weights)
                benchmark_sector_returns = self._calculate_benchmark_sector_returns(asset_returns_period)
                
                # Calculate attribution effects for each sector
                for sector in get_all_sectors():
                    wp = portfolio_sector_weights.get(sector, 0.0)  # Portfolio weight
                    wb = BENCHMARK_SECTOR_WEIGHTS.get(sector, 0.0)  # Benchmark weight
                    rp = sector_returns.get(sector, 0.0)  # Portfolio return
                    rb = benchmark_sector_returns.get(sector, 0.0)  # Benchmark return
                    
                    # Brinson attribution formulas
                    allocation_effect = (wp - wb) * rb
                    selection_effect = wb * (rp - rb)
                    interaction_effect = (wp - wb) * (rp - rb)
                    total_effect = allocation_effect + selection_effect + interaction_effect
                    
                    result = SectorAttributionResult(
                        date=current_date,
                        sector=sector,
                        portfolio_weight=wp,
                        benchmark_weight=wb,
                        portfolio_return=rp,
                        benchmark_return=rb,
                        allocation_effect=allocation_effect,
                        selection_effect=selection_effect,
                        interaction_effect=interaction_effect,
                        total_effect=total_effect
                    )
                    
                    sector_attribution_results.append(result)
            
            LOG.info(f"Completed sector attribution analysis: {len(sector_attribution_results)} results")
            return sector_attribution_results
            
        except Exception as e:
            LOG.error(f"Error in sector attribution calculation: {e}")
            return []
    
    def _convert_asset_to_sector_weights(self, asset_weights: pd.Series) -> Dict[str, float]:
        """Convert asset weights to sector weights."""
        sector_weights = {}
        
        for asset, weight in asset_weights.items():
            if pd.isna(weight) or not isinstance(asset, str):
                continue
                
            sector = get_asset_sector(asset)
            if sector not in sector_weights:
                sector_weights[sector] = 0.0
            sector_weights[sector] += float(weight)
        
        return sector_weights
    
    def _calculate_sector_returns(self, asset_returns: pd.Series, asset_weights: pd.Series) -> Dict[str, float]:
        """Calculate sector returns weighted by portfolio holdings."""
        sector_returns = {}
        sector_weights = {}
        
        # Calculate weighted returns for each sector
        for asset, asset_return in asset_returns.items():
            if pd.isna(asset_return) or not isinstance(asset, str):
                continue
                
            asset_weight = asset_weights.get(asset, 0.0)
            if pd.isna(asset_weight) or asset_weight == 0:
                continue
                
            sector = get_asset_sector(asset)
            
            if sector not in sector_returns:
                sector_returns[sector] = 0.0
                sector_weights[sector] = 0.0
            
            sector_returns[sector] += float(asset_return) * float(asset_weight)
            sector_weights[sector] += float(asset_weight)
        
        # Normalize by sector weights to get average sector returns
        for sector in sector_returns:
            if sector_weights[sector] > 0:
                sector_returns[sector] /= sector_weights[sector]
        
        return sector_returns
    
    def _calculate_benchmark_sector_returns(self, asset_returns: pd.Series) -> Dict[str, float]:
        """Calculate benchmark sector returns using equal weights within sectors."""
        sector_returns = {}
        sector_counts = {}
        
        for asset, asset_return in asset_returns.items():
            if pd.isna(asset_return) or not isinstance(asset, str):
                continue
                
            sector = get_asset_sector(asset)
            
            if sector not in sector_returns:
                sector_returns[sector] = 0.0
                sector_counts[sector] = 0
            
            sector_returns[sector] += float(asset_return)
            sector_counts[sector] += 1
        
        # Calculate average returns for each sector
        for sector in sector_returns:
            if sector_counts[sector] > 0:
                sector_returns[sector] /= sector_counts[sector]
        
        return sector_returns
    
    def aggregate_attribution_results(self, 
                                    daily_results: List[SectorAttributionResult],
                                    period: str = 'weekly') -> List[SectorAttributionResult]:
        """
        Aggregate daily attribution results into weekly/monthly periods.
        
        Args:
            daily_results: List of daily attribution results
            period: Aggregation period ('weekly' or 'monthly')
            
        Returns:
            List of aggregated attribution results
        """
        if not daily_results:
            return []
        
        # Convert to DataFrame for easier aggregation
        df_data = []
        for result in daily_results:
            df_data.append({
                'date': result.date,
                'sector': result.sector,
                'portfolio_weight': result.portfolio_weight,
                'benchmark_weight': result.benchmark_weight,
                'portfolio_return': result.portfolio_return,
                'benchmark_return': result.benchmark_return,
                'allocation_effect': result.allocation_effect,
                'selection_effect': result.selection_effect,
                'interaction_effect': result.interaction_effect,
                'total_effect': result.total_effect
            })
        
        df = pd.DataFrame(df_data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # Define aggregation frequency
        freq = 'W' if period == 'weekly' else 'ME'
        
        aggregated_results = []
        
        # Group by sector and period
        for sector in df['sector'].unique():
            sector_data = df[df['sector'] == sector]
            grouped = sector_data.groupby(pd.Grouper(freq=freq))
            
            for period_end, group in grouped:
                if group.empty:
                    continue
                
                # Aggregate the attribution effects
                result = SectorAttributionResult(
                    date=period_end,
                    sector=sector,
                    portfolio_weight=group['portfolio_weight'].mean(),
                    benchmark_weight=group['benchmark_weight'].mean(),
                    portfolio_return=(1 + group['portfolio_return']).prod() - 1,
                    benchmark_return=(1 + group['benchmark_return']).prod() - 1,
                    allocation_effect=group['allocation_effect'].sum(),
                    selection_effect=group['selection_effect'].sum(),
                    interaction_effect=group['interaction_effect'].sum(),
                    total_effect=group['total_effect'].sum()
                )
                
                aggregated_results.append(result)
        
        return aggregated_results
    
    def create_attribution_summary(self, attribution_results: List[SectorAttributionResult]) -> Dict[str, Any]:
        """
        Create a comprehensive attribution summary.
        
        Args:
            attribution_results: List of attribution results
            
        Returns:
            Summary dictionary with attribution analysis
        """
        if not attribution_results:
            return {'error': 'No attribution results to summarize'}
        
        # Convert to DataFrame for analysis
        df_data = []
        for result in attribution_results:
            df_data.append({
                'date': result.date,
                'sector': result.sector,
                'portfolio_weight': result.portfolio_weight,
                'benchmark_weight': result.benchmark_weight,
                'portfolio_return': result.portfolio_return,
                'benchmark_return': result.benchmark_return,
                'allocation_effect': result.allocation_effect,
                'selection_effect': result.selection_effect,
                'interaction_effect': result.interaction_effect,
                'total_effect': result.total_effect
            })
        
        df = pd.DataFrame(df_data)
        
        # Calculate summary statistics by sector
        sector_summary = df.groupby('sector').agg({
            'portfolio_weight': 'mean',
            'benchmark_weight': 'mean', 
            'portfolio_return': lambda x: (1 + x).prod() - 1,
            'benchmark_return': lambda x: (1 + x).prod() - 1,
            'allocation_effect': 'sum',
            'selection_effect': 'sum',
            'interaction_effect': 'sum',
            'total_effect': 'sum'
        }).round(6)
        
        # Calculate total portfolio effects
        total_allocation = df['allocation_effect'].sum()
        total_selection = df['selection_effect'].sum()
        total_interaction = df['interaction_effect'].sum()
        total_excess_return = total_allocation + total_selection + total_interaction
        
        # Top contributors
        sector_totals = df.groupby('sector')['total_effect'].sum().sort_values(ascending=False)
        top_contributors = sector_totals.head(5).to_dict()
        bottom_contributors = sector_totals.tail(5).to_dict()
        
        return {
            'period_info': {
                'start_date': df['date'].min().strftime('%Y-%m-%d'),
                'end_date': df['date'].max().strftime('%Y-%m-%d'),
                'total_periods': len(df['date'].unique())
            },
            'total_effects': {
                'total_allocation_effect': total_allocation,
                'total_selection_effect': total_selection,
                'total_interaction_effect': total_interaction,
                'total_excess_return': total_excess_return
            },
            'sector_summary': sector_summary.to_dict('index'),
            'top_contributors': top_contributors,
            'bottom_contributors': bottom_contributors,
            'attribution_data': df.to_dict('records')
        }
    
    def save_attribution_results(self, 
                               strategy_name: str,
                               attribution_results: List[SectorAttributionResult],
                               summary: Dict[str, Any]) -> Dict[str, str]:
        """
        Save attribution results to files.
        
        Args:
            strategy_name: Name of the strategy
            attribution_results: List of attribution results
            summary: Attribution summary
            
        Returns:
            Dictionary with saved file paths
        """
        strategy_safe = strategy_name.replace('/', '_').replace(' ', '_').lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        saved_files = {}
        
        try:
            # Save detailed results to CSV
            if attribution_results:
                df_data = []
                for result in attribution_results:
                    df_data.append({
                        'Date': result.date.strftime('%Y-%m-%d'),
                        'Sector': result.sector,
                        'Portfolio_Weight': result.portfolio_weight,
                        'Benchmark_Weight': result.benchmark_weight,
                        'Portfolio_Return': result.portfolio_return,
                        'Benchmark_Return': result.benchmark_return,
                        'Allocation_Effect': result.allocation_effect,
                        'Selection_Effect': result.selection_effect,
                        'Interaction_Effect': result.interaction_effect,
                        'Total_Effect': result.total_effect
                    })
                
                df = pd.DataFrame(df_data)
                csv_file = self.results_dir / f"{strategy_safe}_sector_attribution_{timestamp}.csv"
                df.to_csv(csv_file, index=False)
                saved_files['detailed_csv'] = str(csv_file)
            
            # Save summary to JSON
            import json
            summary_file = self.results_dir / f"{strategy_safe}_attribution_summary_{timestamp}.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            saved_files['summary_json'] = str(summary_file)
            
            LOG.info(f"Attribution results saved for {strategy_name}: {list(saved_files.keys())}")
            return saved_files
            
        except Exception as e:
            LOG.error(f"Error saving attribution results: {e}")
            return {'error': str(e)}