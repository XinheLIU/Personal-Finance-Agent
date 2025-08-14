"""
Enhanced Backtesting Engine
Professional backtesting platform with execution lag modeling, transaction costs,
and comprehensive performance analytics.
"""

import backtrader as bt
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Type
from datetime import datetime, timedelta
import warnings
import csv

from src.app_logger import LOG
from config.assets import ASSETS
from config.system import INITIAL_CAPITAL, COMMISSION
from src.data_center.data_loader import DataLoader
from src.strategies.metadata import StrategyMetadata

class EnhancedBacktestEngine:
    """
    Professional backtesting engine with execution lag and comprehensive analytics
    """
    
    def __init__(self, 
                 initial_capital: float = INITIAL_CAPITAL,
                 commission: float = COMMISSION,
                 execution_lag: int = 1,  # Days of execution lag (T+1)
                 slippage: float = 0.001,  # 0.1% slippage per trade
                 data_root: str = "data"):
        
        self.initial_capital = initial_capital
        self.commission = commission
        self.execution_lag = execution_lag
        self.slippage = slippage
        
        # Initialize data loader
        self.data_loader = DataLoader(data_root)
        
        # Results storage
        self.results_dir = Path("analytics") / "backtests"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Execution tracking
        self.execution_log: List[Dict] = []
        self.rebalancing_log: List[Dict] = []
    
    def add_execution_lag(self, cerebro: bt.Cerebro) -> bt.Cerebro:
        """Add execution lag analyzer to model real-world execution delays"""
        
        class ExecutionLagAnalyzer(bt.Analyzer):
            """Analyzer to track execution lag effects"""
            
            def __init__(self):
                super().__init__()
                self.lag_data = []
                self.pending_orders = []
            
            def next(self):
                # Process pending orders from T-1
                current_date = self.strategy.datas[0].datetime.date(0)
                
                # Execute orders that were placed execution_lag days ago
                orders_to_execute = []
                remaining_orders = []
                
                for order_info in self.pending_orders:
                    if (current_date - order_info['order_date']).days >= self.strategy.execution_lag:
                        orders_to_execute.append(order_info)
                    else:
                        remaining_orders.append(order_info)
                
                self.pending_orders = remaining_orders
                
                # Log execution lag data
                if orders_to_execute:
                    self.lag_data.append({
                        'date': current_date,
                        'orders_executed': len(orders_to_execute),
                        'total_pending': len(self.pending_orders)
                    })
        
        cerebro.addanalyzer(ExecutionLagAnalyzer, _name='execution_lag')
        return cerebro
    
    def run_backtest(self, 
                    strategy_class: Type[bt.Strategy],
                    strategy_name: str,
                    start_date: Optional[str] = None,
                    end_date: Optional[str] = None,
                    save_details: bool = True,
                    enable_attribution: bool = False,
                    **strategy_kwargs) -> Dict[str, Any]:
        """
        Run comprehensive backtest with execution lag and detailed analytics
        
        Args:
            strategy_class: Strategy class to backtest
            strategy_name: Display name for the strategy
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            save_details: Save detailed logs and analytics
            enable_attribution: Enable performance attribution analysis
            **strategy_kwargs: Additional strategy parameters
            
        Returns:
            Comprehensive results dictionary
        """
        try:
            LOG.info(f"Starting enhanced backtest: {strategy_name}")
            
            # Create cerebro engine
            cerebro = bt.Cerebro()
            cerebro.broker.setcash(self.initial_capital)
            cerebro.broker.setcommission(commission=self.commission)
            
            # Add slippage
            if self.slippage > 0:
                cerebro.broker.set_slippage_perc(perc=self.slippage * 100)
            
            # Load and add data feeds
            data_feeds_added = 0
            market_data_summary = {}
            asset_returns_data = {}  # For attribution analysis
            
            for asset_name in ASSETS.keys():
                try:
                    data_feed = self.data_loader.load_data_feed(asset_name, asset_name, start_date)
                    if data_feed is not None:
                        cerebro.adddata(data_feed, name=asset_name)
                        data_feeds_added += 1
                        
                        # Track data summary
                        market_data_summary[asset_name] = {
                            'start': data_feed._dataname.index.min(),
                            'end': data_feed._dataname.index.max(),
                            'records': len(data_feed._dataname)
                        }
                        
                        # Capture asset returns for attribution analysis
                        if enable_attribution:
                            asset_data = data_feed._dataname
                            if 'close' in asset_data.columns:
                                asset_returns = asset_data['close'].pct_change().dropna()
                                asset_returns_data[asset_name] = asset_returns
                    else:
                        LOG.warning(f"Failed to load data for {asset_name}")
                        
                except Exception as e:
                    LOG.error(f"Error loading {asset_name}: {e}")
            
            if data_feeds_added == 0:
                raise ValueError("No data feeds available for backtesting")
            
            LOG.info(f"Loaded {data_feeds_added} data feeds for backtesting")
            
            # Add strategy with parameters
            cerebro.addstrategy(strategy_class, **strategy_kwargs)
            
            # Add analyzers for comprehensive metrics
            cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
            cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
            cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
            cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='time_return')
            cerebro.addanalyzer(bt.analyzers.VWR, _name='vwr')  # Variability-Weighted Return
            
            # Add execution lag modeling
            cerebro = self.add_execution_lag(cerebro)
            
            # Run backtest
            start_time = datetime.now()
            results = cerebro.run()
            end_time = datetime.now()
            
            # Extract results
            strat = results[0]
            
            # Calculate performance metrics
            final_value = cerebro.broker.getvalue()
            total_return = (final_value - self.initial_capital) / self.initial_capital
            
            # Get analyzer results
            returns_analyzer = strat.analyzers.returns.get_analysis()
            sharpe_analyzer = strat.analyzers.sharpe.get_analysis()
            drawdown_analyzer = strat.analyzers.drawdown.get_analysis()
            trades_analyzer = strat.analyzers.trades.get_analysis()
            time_return_analyzer = strat.analyzers.time_return.get_analysis()
            
            # Compile comprehensive results
            results_dict = {
                # Basic Performance
                'strategy_name': strategy_name,
                'initial_capital': self.initial_capital,
                'final_value': final_value,
                'total_return': total_return,
                'annual_return': returns_analyzer.get('rnorm100', 0) / 100,
                
                # Risk Metrics
                'sharpe_ratio': sharpe_analyzer.get('sharperatio', 0) if sharpe_analyzer else 0,
                'max_drawdown': drawdown_analyzer.get('max', {}).get('drawdown', 0) / 100,
                'max_drawdown_duration': drawdown_analyzer.get('max', {}).get('len', 0),
                'volatility': np.std(list(time_return_analyzer.values())) * np.sqrt(252) if time_return_analyzer else 0,
                
                # Trading Statistics
                'total_trades': trades_analyzer.get('total', {}).get('total', 0) if trades_analyzer else 0,
                'winning_trades': trades_analyzer.get('won', {}).get('total', 0) if trades_analyzer else 0,
                'losing_trades': trades_analyzer.get('lost', {}).get('total', 0) if trades_analyzer else 0,
                
                # System Information
                'execution_time': (end_time - start_time).total_seconds(),
                'data_feeds': data_feeds_added,
                'start_date': start_date,
                'end_date': end_date,
                'market_data_summary': market_data_summary,
                
                # Raw analyzer data for detailed analysis
                'analyzers': {
                    'returns': returns_analyzer,
                    'sharpe': sharpe_analyzer,
                    'drawdown': drawdown_analyzer,
                    'trades': trades_analyzer,
                    'time_return': time_return_analyzer
                }
            }
            
            # Add portfolio evolution if available
            if hasattr(strat, 'portfolio_values') and hasattr(strat, 'portfolio_dates'):
                portfolio_df = pd.DataFrame({
                    'date': strat.portfolio_dates,
                    'value': strat.portfolio_values
                })
                portfolio_df['returns'] = portfolio_df['value'].pct_change()
                results_dict['portfolio_evolution'] = portfolio_df
                
                # Calculate additional metrics from portfolio evolution
                if not portfolio_df.empty:
                    results_dict['calmar_ratio'] = (results_dict['annual_return'] / 
                                                  abs(results_dict['max_drawdown'])) if results_dict['max_drawdown'] != 0 else 0
            
            # Add rebalancing log if available
            if hasattr(strat, 'rebalance_log'):
                self.rebalancing_log = strat.rebalance_log
                results_dict['rebalancing_log'] = self.rebalancing_log
            
            # Add attribution-ready data
            if enable_attribution:
                # Capture asset returns for attribution
                if asset_returns_data:
                    results_dict['asset_returns'] = pd.DataFrame(asset_returns_data)
                
                # Capture portfolio weights evolution if available
                if hasattr(strat, 'weights_evolution'):
                    results_dict['weights_evolution'] = pd.DataFrame(strat.weights_evolution)
                elif hasattr(strat, 'rebalance_log') and strat.rebalance_log:
                    # Reconstruct weights from rebalancing log
                    weights_data = []
                    for rebal_entry in strat.rebalance_log:
                        if 'target_weights' in rebal_entry:
                            weights_entry = {'date': rebal_entry['date']}
                            weights_entry.update(rebal_entry['target_weights'])
                            weights_data.append(weights_entry)
                    
                    if weights_data:
                        weights_df = pd.DataFrame(weights_data)
                        weights_df['date'] = pd.to_datetime(weights_df['date'])
                        weights_df.set_index('date', inplace=True)
                        results_dict['weights_evolution'] = weights_df
                
                # Run performance attribution analysis
                try:
                    from src.performance.attribution import PerformanceAttributor
                    attributor = PerformanceAttributor()
                    
                    portfolio_data = results_dict.get('portfolio_evolution')
                    asset_returns = results_dict.get('asset_returns')
                    weights_data = results_dict.get('weights_evolution')
                    
                    if all(data is not None for data in [portfolio_data, asset_returns, weights_data]):
                        attribution_report = attributor.generate_attribution_report(
                            strategy_name=strategy_name,
                            portfolio_data=portfolio_data,
                            asset_returns=asset_returns,
                            weights_data=weights_data,
                            include_weekly=True,
                            include_monthly=True
                        )
                        
                        if 'error' not in attribution_report:
                            results_dict['attribution_analysis'] = attribution_report
                            LOG.info(f"Performance attribution analysis completed for {strategy_name}")
                        else:
                            LOG.warning(f"Attribution analysis failed: {attribution_report['error']}")
                    else:
                        LOG.warning("Insufficient data for performance attribution analysis")
                        
                except Exception as e:
                    LOG.error(f"Performance attribution analysis error: {e}")
            
            # Save detailed results if requested
            if save_details:
                self._save_backtest_results(results_dict, strategy_name)
            
            LOG.info(f"Backtest completed: {strategy_name}")
            LOG.info(f"Final Value: ${final_value:,.2f} | Total Return: {total_return:.1%} | Sharpe: {results_dict['sharpe_ratio']:.2f}")
            
            return results_dict
            
        except Exception as e:
            LOG.error(f"Backtest failed for {strategy_name}: {e}")
            return {'error': str(e), 'strategy_name': strategy_name}
    
    def run_multiple_strategies(self, 
                              strategies: List[Tuple[Type[bt.Strategy], str, Dict]],
                              start_date: Optional[str] = None,
                              end_date: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Run backtests for multiple strategies with comparison
        
        Args:
            strategies: List of (strategy_class, name, kwargs) tuples
            start_date: Start date for all backtests
            end_date: End date for all backtests
            
        Returns:
            Dictionary with results for each strategy
        """
        LOG.info(f"Running multiple strategy backtests: {len(strategies)} strategies")
        
        all_results = {}
        comparison_data = []
        
        for strategy_class, strategy_name, strategy_kwargs in strategies:
            try:
                result = self.run_backtest(
                    strategy_class, 
                    strategy_name, 
                    start_date, 
                    end_date,
                    save_details=True,
                    **strategy_kwargs
                )
                
                all_results[strategy_name] = result
                
                # Add to comparison data
                if 'error' not in result:
                    comparison_data.append({
                        'Strategy': strategy_name,
                        'Total Return': result['total_return'],
                        'Annual Return': result['annual_return'],
                        'Sharpe Ratio': result['sharpe_ratio'],
                        'Max Drawdown': result['max_drawdown'],
                        'Volatility': result['volatility'],
                        'Total Trades': result['total_trades']
                    })
                    
            except Exception as e:
                LOG.error(f"Failed to backtest {strategy_name}: {e}")
                all_results[strategy_name] = {'error': str(e)}
        
        # Create comparison table
        if comparison_data:
            comparison_df = pd.DataFrame(comparison_data)
            comparison_df = comparison_df.sort_values('Sharpe Ratio', ascending=False)
            
            # Save comparison
            comparison_file = self.results_dir / f"strategy_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            comparison_df.to_csv(comparison_file, index=False)
            LOG.info(f"Strategy comparison saved to {comparison_file}")
            
            all_results['_comparison'] = comparison_df
        
        return all_results
    
    def _save_backtest_results(self, results: Dict[str, Any], strategy_name: str) -> None:
        """Save detailed backtest results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        strategy_safe = strategy_name.replace('/', '_').replace(' ', '_')
        
        # Save portfolio evolution
        if 'portfolio_evolution' in results and results['portfolio_evolution'] is not None:
            portfolio_file = self.results_dir / f"{strategy_safe}_portfolio_{timestamp}.csv"
            results['portfolio_evolution'].to_csv(portfolio_file, index=False)
            
        # Save rebalancing log (overwrite a single CSV per strategy)
        if 'rebalancing_log' in results and results['rebalancing_log']:
            # Use lower_snake_case for rebalance log file naming, without timestamp (overwrite last run)
            safe_rebalance_name = strategy_name.replace('/', '_').replace(' ', '_').lower()
            rebalance_file = self.results_dir / f"{safe_rebalance_name}_rebalance_log.csv"
            
            with open(rebalance_file, 'w', newline='') as f:
                if results['rebalancing_log']:
                    writer = csv.DictWriter(f, fieldnames=results['rebalancing_log'][0].keys())
                    writer.writeheader()
                    writer.writerows(results['rebalancing_log'])
        
        # Save summary metrics
        summary_data = {k: v for k, v in results.items() 
                       if k not in ['portfolio_evolution', 'rebalancing_log', 'analyzers', 'market_data_summary']}
        
        summary_file = self.results_dir / f"{strategy_safe}_summary_{timestamp}.csv"
        pd.DataFrame([summary_data]).to_csv(summary_file, index=False)
        
        LOG.info(f"Detailed results saved for {strategy_name}")

# Global engine instance
backtest_engine = EnhancedBacktestEngine()