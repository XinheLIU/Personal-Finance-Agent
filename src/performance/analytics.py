"""
Enhanced Performance Analytics
Professional performance evaluation with comprehensive metrics and attribution analysis.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from src.app_logger import LOG

class PerformanceAnalyzer:
    """
    Comprehensive performance analysis for investment strategies
    """
    
    def __init__(self, results_dir: str = "analytics/performance"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_realized_holdings(self, 
                                 holdings_file: str = "data/accounts/account_holdings.csv") -> Dict[str, Any]:
        """
        Analyze realized holdings from account data
        
        Args:
            holdings_file: Path to account holdings CSV file
            
        Returns:
            Dictionary with realized performance metrics
        """
        try:
            holdings_df = pd.read_csv(holdings_file)
            holdings_df['date'] = pd.to_datetime(holdings_df['date'])
            holdings_df.set_index('date', inplace=True)
            
            # Normalize to weights (assuming 'amount' column contains total portfolio value)
            if 'amount' not in holdings_df.columns:
                LOG.error("Holdings file must contain 'amount' column for total portfolio value")
                return {}
            
            # Calculate asset weights
            asset_columns = [col for col in holdings_df.columns if col != 'amount']
            holdings_weights = holdings_df[asset_columns].div(holdings_df['amount'], axis=0)
            
            # Calculate portfolio returns
            holdings_returns = holdings_df['amount'].pct_change().dropna()
            
            # Comprehensive metrics
            metrics = self._calculate_comprehensive_metrics(holdings_returns, "Realized Portfolio")
            
            # Add holdings-specific data
            metrics.update({
                'holdings_evolution': holdings_df,
                'weights_evolution': holdings_weights,
                'average_weights': holdings_weights.mean().to_dict(),
                'weight_volatility': holdings_weights.std().to_dict()
            })
            
            LOG.info("Analyzed realized holdings performance")
            return metrics
            
        except Exception as e:
            LOG.error(f"Error analyzing realized holdings: {e}")
            return {}
    
    def compare_strategy_performance(self, 
                                   strategies_results: Dict[str, Dict[str, Any]],
                                   benchmarks: Optional[Dict[str, pd.Series]] = None) -> pd.DataFrame:
        """
        Compare performance across multiple strategies
        
        Args:
            strategies_results: Dictionary of strategy results
            benchmarks: Optional benchmark series for comparison
            
        Returns:
            Comparison DataFrame with key metrics
        """
        comparison_data = []
        
        for strategy_name, results in strategies_results.items():
            if 'error' in results:
                continue
                
            row = {
                'Strategy': strategy_name,
                'Total Return': results.get('total_return', 0),
                'Annual Return': results.get('annual_return', 0),
                'Volatility': results.get('volatility', 0),
                'Sharpe Ratio': results.get('sharpe_ratio', 0),
                'Max Drawdown': results.get('max_drawdown', 0),
                'Calmar Ratio': results.get('calmar_ratio', 0),
                'Total Trades': results.get('total_trades', 0),
                'Win Rate': (results.get('winning_trades', 0) / 
                           max(results.get('total_trades', 1), 1)),
                'Execution Time': results.get('execution_time', 0)
            }
            
            # Add risk-adjusted metrics
            if results.get('volatility', 0) > 0:
                row['Return/Risk'] = results.get('annual_return', 0) / results.get('volatility', 1)
            else:
                row['Return/Risk'] = 0
                
            comparison_data.append(row)
        
        if not comparison_data:
            return pd.DataFrame()
        
        comparison_df = pd.DataFrame(comparison_data)
        
        # Add rankings
        comparison_df['Sharpe Rank'] = comparison_df['Sharpe Ratio'].rank(ascending=False)
        comparison_df['Return Rank'] = comparison_df['Annual Return'].rank(ascending=False)
        comparison_df['Risk Rank'] = comparison_df['Volatility'].rank(ascending=True)
        
        # Calculate composite score
        comparison_df['Composite Score'] = (
            comparison_df['Sharpe Rank'] * 0.4 +
            comparison_df['Return Rank'] * 0.3 +
            comparison_df['Risk Rank'] * 0.3
        )
        
        comparison_df = comparison_df.sort_values('Composite Score')
        
        # Save comparison
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        comparison_file = self.results_dir / f"strategy_comparison_{timestamp}.csv"
        comparison_df.to_csv(comparison_file, index=False)
        
        LOG.info(f"Strategy comparison saved to {comparison_file}")
        return comparison_df
    
    def _calculate_comprehensive_metrics(self, 
                                       returns: pd.Series, 
                                       name: str) -> Dict[str, float]:
        """Calculate comprehensive performance metrics"""
        if returns.empty:
            return {}
        
        # Remove NaN and infinite values
        clean_returns = returns.dropna().replace([np.inf, -np.inf], 0)
        
        if clean_returns.empty or clean_returns.std() == 0:
            return {'name': name, 'error': 'Insufficient or invalid data'}
        
        # Basic metrics
        total_return = (1 + clean_returns).prod() - 1
        annual_return = (1 + clean_returns).prod() ** (252 / len(clean_returns)) - 1
        volatility = clean_returns.std() * np.sqrt(252)
        
        # Risk-adjusted metrics
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0
        
        # Drawdown analysis
        cumulative = (1 + clean_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Calmar ratio
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Sortino ratio (downside deviation)
        downside_returns = clean_returns[clean_returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252) if not downside_returns.empty else 0
        sortino_ratio = annual_return / downside_std if downside_std > 0 else 0
        
        # Value at Risk (VaR)
        var_95 = clean_returns.quantile(0.05)
        var_99 = clean_returns.quantile(0.01)
        
        # Maximum drawdown duration
        drawdown_periods = []
        in_drawdown = False
        drawdown_start = None
        
        for i, dd in enumerate(drawdown):
            if dd < 0 and not in_drawdown:
                in_drawdown = True
                drawdown_start = i
            elif dd == 0 and in_drawdown:
                in_drawdown = False
                if drawdown_start is not None:
                    drawdown_periods.append(i - drawdown_start)
        
        max_dd_duration = max(drawdown_periods) if drawdown_periods else 0
        
        # Tail ratio
        upside_returns = clean_returns[clean_returns > 0]
        tail_ratio = (upside_returns.quantile(0.95) / abs(clean_returns.quantile(0.05))) if not upside_returns.empty else 0
        
        return {
            'name': name,
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'max_drawdown': max_drawdown,
            'max_drawdown_duration': max_dd_duration,
            'var_95': var_95,
            'var_99': var_99,
            'tail_ratio': tail_ratio,
            'skewness': clean_returns.skew(),
            'kurtosis': clean_returns.kurtosis(),
            'best_month': clean_returns.max(),
            'worst_month': clean_returns.min(),
            'positive_months': (clean_returns > 0).sum(),
            'negative_months': (clean_returns < 0).sum(),
            'total_periods': len(clean_returns)
        }
    
    def rolling_performance_analysis(self, 
                                   returns: pd.Series, 
                                   windows: List[int] = [252, 504, 1260]) -> Dict[str, pd.DataFrame]:
        """
        Calculate rolling performance metrics
        
        Args:
            returns: Daily returns series
            windows: List of rolling window sizes (in days)
            
        Returns:
            Dictionary of rolling metrics DataFrames
        """
        rolling_metrics = {}
        
        for window in windows:
            if len(returns) < window:
                continue
                
            # Rolling returns and volatility
            rolling_return = returns.rolling(window=window).apply(lambda x: (1 + x).prod() - 1)
            rolling_vol = returns.rolling(window=window).std() * np.sqrt(252)
            rolling_sharpe = (rolling_return * 252 / window) / rolling_vol
            
            # Rolling drawdown
            cumulative = (1 + returns).cumprod()
            rolling_max = cumulative.rolling(window=window).max()
            rolling_dd = (cumulative - rolling_max) / rolling_max
            
            # Combine metrics
            rolling_df = pd.DataFrame({
                f'return_{window}d': rolling_return,
                f'volatility_{window}d': rolling_vol,
                f'sharpe_{window}d': rolling_sharpe,
                f'drawdown_{window}d': rolling_dd
            })
            
            rolling_metrics[f'{window}d'] = rolling_df
        
        return rolling_metrics
    
    def sector_attribution_analysis(self, 
                                  portfolio_weights: pd.DataFrame,
                                  asset_returns: pd.DataFrame,
                                  sector_mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        Perform sector attribution analysis
        
        Args:
            portfolio_weights: DataFrame with asset weights over time
            asset_returns: DataFrame with asset returns
            sector_mapping: Mapping from assets to sectors
            
        Returns:
            Attribution analysis results
        """
        # Align data
        common_dates = portfolio_weights.index.intersection(asset_returns.index)
        weights_aligned = portfolio_weights.loc[common_dates]
        returns_aligned = asset_returns.loc[common_dates]
        
        # Group by sectors
        sector_data = {}
        for sector in set(sector_mapping.values()):
            sector_assets = [asset for asset, sec in sector_mapping.items() if sec == sector]
            sector_assets = [asset for asset in sector_assets if asset in weights_aligned.columns]
            
            if not sector_assets:
                continue
            
            # Sector weights and returns
            sector_weights = weights_aligned[sector_assets].sum(axis=1)
            sector_returns = (weights_aligned[sector_assets] * returns_aligned[sector_assets]).sum(axis=1) / sector_weights
            sector_returns = sector_returns.fillna(0)
            
            sector_data[sector] = {
                'weights': sector_weights,
                'returns': sector_returns,
                'contribution': sector_weights * sector_returns
            }
        
        # Create attribution DataFrame
        attribution_df = pd.DataFrame({
            sector: data['contribution'] for sector, data in sector_data.items()
        })
        
        return {
            'sector_data': sector_data,
            'attribution': attribution_df,
            'total_attribution': attribution_df.sum(axis=1),
            'sector_summary': {
                sector: {
                    'avg_weight': data['weights'].mean(),
                    'total_return': (1 + data['returns']).prod() - 1,
                    'volatility': data['returns'].std() * np.sqrt(252),
                    'contribution': data['contribution'].sum()
                }
                for sector, data in sector_data.items()
            }
        }
    
    def generate_performance_report(self, 
                                  strategy_results: Dict[str, Any],
                                  save_charts: bool = True) -> Dict[str, Any]:
        """
        Generate comprehensive performance report
        
        Args:
            strategy_results: Strategy backtest results
            save_charts: Whether to save performance charts
            
        Returns:
            Comprehensive performance report
        """
        if 'error' in strategy_results:
            return {'error': 'Cannot generate report for failed backtest'}
        
        strategy_name = strategy_results.get('strategy_name', 'Unknown Strategy')
        
        # Extract portfolio evolution
        portfolio_df = strategy_results.get('portfolio_evolution')
        if portfolio_df is None or portfolio_df.empty:
            return {'error': 'No portfolio data available'}
        
        # Calculate comprehensive metrics
        returns = portfolio_df['returns'].dropna()
        metrics = self._calculate_comprehensive_metrics(returns, strategy_name)
        
        # Rolling analysis
        rolling_metrics = self.rolling_performance_analysis(returns)
        
        # Generate charts if requested
        charts_info = {}
        if save_charts:
            charts_info = self._generate_performance_charts(
                portfolio_df, strategy_name, metrics
            )
        
        # Compile report
        report = {
            'strategy_name': strategy_name,
            'report_date': datetime.now().isoformat(),
            'performance_metrics': metrics,
            'rolling_analysis': rolling_metrics,
            'portfolio_evolution': portfolio_df,
            'rebalancing_summary': self._analyze_rebalancing(strategy_results.get('rebalancing_log', [])),
            'charts': charts_info,
            'recommendations': self._generate_recommendations(metrics)
        }
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        strategy_safe = strategy_name.replace('/', '_').replace(' ', '_')
        report_file = self.results_dir / f"{strategy_safe}_performance_report_{timestamp}.json"
        
        # Convert to JSON-serializable format
        import json
        json_report = self._serialize_for_json(report)
        
        with open(report_file, 'w') as f:
            json.dump(json_report, f, indent=2)
        
        LOG.info(f"Performance report saved to {report_file}")
        return report
    
    def _generate_performance_charts(self, 
                                   portfolio_df: pd.DataFrame, 
                                   strategy_name: str,
                                   metrics: Dict[str, float]) -> Dict[str, str]:
        """Generate performance visualization charts"""
        charts = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        strategy_safe = strategy_name.replace('/', '_').replace(' ', '_')
        
        # Set style
        plt.style.use('seaborn-v0_8')
        
        # 1. Portfolio Value Evolution
        fig, ax = plt.subplots(figsize=(12, 6))
        portfolio_df.plot(x='date', y='value', ax=ax, title=f'{strategy_name} - Portfolio Value Evolution')
        ax.set_ylabel('Portfolio Value ($)')
        ax.grid(True)
        
        chart_file = self.results_dir / f"{strategy_safe}_portfolio_evolution_{timestamp}.png"
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        charts['portfolio_evolution'] = str(chart_file)
        plt.close()
        
        # 2. Returns Distribution
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        returns = portfolio_df['returns'].dropna()
        
        # Histogram
        returns.hist(bins=50, ax=ax1, alpha=0.7)
        ax1.axvline(returns.mean(), color='red', linestyle='--', label=f'Mean: {returns.mean():.3f}')
        ax1.set_title(f'{strategy_name} - Returns Distribution')
        ax1.set_xlabel('Daily Returns')
        ax1.set_ylabel('Frequency')
        ax1.legend()
        
        # Cumulative returns
        cumulative_returns = (1 + returns).cumprod()
        cumulative_returns.plot(ax=ax2, title=f'{strategy_name} - Cumulative Returns')
        ax2.set_ylabel('Cumulative Return')
        ax2.grid(True)
        
        chart_file = self.results_dir / f"{strategy_safe}_returns_analysis_{timestamp}.png"
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        charts['returns_analysis'] = str(chart_file)
        plt.close()
        
        # 3. Drawdown Chart
        fig, ax = plt.subplots(figsize=(12, 6))
        
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        
        drawdown.plot(ax=ax, title=f'{strategy_name} - Drawdown Analysis', color='red')
        ax.fill_between(drawdown.index, drawdown, 0, alpha=0.3, color='red')
        ax.set_ylabel('Drawdown')
        ax.grid(True)
        
        chart_file = self.results_dir / f"{strategy_safe}_drawdown_{timestamp}.png"
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        charts['drawdown'] = str(chart_file)
        plt.close()
        
        return charts
    
    def _analyze_rebalancing(self, rebalancing_log: List[Dict]) -> Dict[str, Any]:
        """Analyze rebalancing patterns"""
        if not rebalancing_log:
            return {'total_rebalances': 0}
        
        rebalance_df = pd.DataFrame(rebalancing_log)
        
        return {
            'total_rebalances': len(rebalancing_log),
            'avg_days_between': np.mean([
                (rebalancing_log[i]['date'] - rebalancing_log[i-1]['date']).days 
                for i in range(1, len(rebalancing_log))
            ]) if len(rebalancing_log) > 1 else 0,
            'rebalancing_frequency': len(rebalancing_log) / max((
                rebalancing_log[-1]['date'] - rebalancing_log[0]['date']).days / 365, 1) if len(rebalancing_log) > 1 else 0
        }
    
    def _generate_recommendations(self, metrics: Dict[str, float]) -> List[str]:
        """Generate performance-based recommendations"""
        recommendations = []
        
        sharpe = metrics.get('sharpe_ratio', 0)
        volatility = metrics.get('volatility', 0)
        max_dd = abs(metrics.get('max_drawdown', 0))
        
        if sharpe < 0.5:
            recommendations.append("Low Sharpe ratio suggests poor risk-adjusted returns. Consider reviewing asset allocation or risk management.")
        elif sharpe > 1.5:
            recommendations.append("Excellent Sharpe ratio indicates strong risk-adjusted performance.")
        
        if volatility > 0.25:
            recommendations.append("High volatility detected. Consider adding defensive assets or implementing volatility targeting.")
        elif volatility < 0.08:
            recommendations.append("Very low volatility may indicate overly conservative allocation. Consider adding growth assets.")
        
        if max_dd > 0.30:
            recommendations.append("Large maximum drawdown suggests high risk. Implement stricter risk controls.")
        elif max_dd < 0.05:
            recommendations.append("Low drawdown indicates good downside protection.")
        
        return recommendations
    
    def _serialize_for_json(self, obj: Any) -> Any:
        """Convert objects to JSON-serializable format"""
        if isinstance(obj, pd.DataFrame):
            # Convert DataFrame to dict and handle Timestamp columns
            df_dict = obj.to_dict()
            return self._serialize_for_json(df_dict)
        elif isinstance(obj, pd.Series):
            return self._serialize_for_json(obj.to_dict())
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self._serialize_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_for_json(item) for item in obj]
        else:
            return obj

def log_rebalance_details(strategy_name: str, rebalance_data: list) -> None:
    """Lightweight helper to persist rebalancing details (moved from src/analytics.py)."""
    if not rebalance_data:
        LOG.info("No rebalancing data to log.")
        return
    df = pd.DataFrame(rebalance_data)
    output_dir = Path("analytics") / "backtests"
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"{strategy_name.replace(' ', '_').lower()}_rebalance_log.csv"
    df.to_csv(file_path, index=False)
    LOG.info(f"Rebalancing details logged to {file_path}")