"""
Backtesting runner for Personal Finance Agent.
Provides a unified interface for running strategy backtests.
"""
import backtrader as bt
import pandas as pd
import numpy as np
import os
from src.app_logger import LOG
from pathlib import Path
from src.performance.analytics import PerformanceAnalyzer
from config import INITIAL_CAPITAL, COMMISSION, ASSETS
from src.data_center.data_loader import load_market_data, load_data_feed

def run_backtest(strategy_class, strategy_name, start_date=None, end_date=None, initial_capital=None, commission=None, enable_attribution=False, **kwargs):
    """
    Run a backtest for a given strategy.
    
    Args:
        strategy_class: The strategy class to backtest
        strategy_name: Name of the strategy for display purposes
        start_date: Start date for backtest (optional)
        end_date: End date for backtest (optional)
        initial_capital: Override initial capital (optional)
        commission: Override commission rate (optional)
        enable_attribution: Enable performance attribution analysis
        **kwargs: Additional parameters for the strategy
    
    Returns:
        Dictionary with backtest results
    """
    try:
        LOG.info(f"Starting backtest for strategy: {strategy_name}")
        
        # Load market data
        market_data = load_market_data()
        if not market_data:
            LOG.error("No market data available for backtesting")
            return None
        
        # Create cerebro engine
        cerebro = bt.Cerebro()
        # Allow overrides from caller (e.g., Streamlit UI); default to config values
        broker_initial_cash = float(INITIAL_CAPITAL) if initial_capital is None else float(initial_capital)
        broker_commission = float(COMMISSION) if commission is None else float(commission)
        cerebro.broker.setcash(broker_initial_cash)
        cerebro.broker.setcommission(commission=broker_commission)
        # Ensure orders execute deterministically on the same bar when needed
        try:
            cerebro.broker.set_coc(True)
        except Exception:
            pass
        
        # Add data feeds using loader (ensures proper columns/mapping)
        earliest_start = None
        latest_end = None
        asset_returns_data = {}  # For attribution analysis

        for asset_name in ASSETS.keys():
            try:
                # Derive start date from argument if provided
                data_feed = load_data_feed(asset_name, asset_name, start_date=start_date)
                if data_feed is None:
                    LOG.warning(f"Skipping {asset_name}: could not create data feed")
                    continue

                cerebro.adddata(data_feed, name=asset_name)

                # Track date ranges using already loaded market_data index if available
                df = market_data.get(asset_name)
                if df is not None and not df.empty:
                    if earliest_start is None or df.index.min() < earliest_start:
                        earliest_start = df.index.min()
                    if latest_end is None or df.index.max() > latest_end:
                        latest_end = df.index.max()
                    
                    # Capture asset returns for attribution analysis
                    if enable_attribution and 'close' in df.columns:
                        asset_returns = df['close'].pct_change().dropna()
                        asset_returns_data[asset_name] = asset_returns
                        
            except Exception as e:
                LOG.warning(f"Failed to load data feed for {asset_name}: {e}")
                continue
        
        if len(cerebro.datas) == 0:
            LOG.error("No valid data feeds found for backtesting")
            return None
        
        # Add strategy with parameters
        cerebro.addstrategy(strategy_class, **kwargs)
        
        # Add analyzers
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        
        # Run backtest
        initial_value = cerebro.broker.getvalue()
        LOG.info(f"Starting Portfolio Value: ${initial_value:,.2f}")
        
        results = cerebro.run()
        
        if not results:
            LOG.error("Backtest failed - no results returned")
            return None
        
        final_value = cerebro.broker.getvalue()
        LOG.info(f"Final Portfolio Value: ${final_value:,.2f}")
        
        # Extract results
        strat = results[0]
        
        # Handle NaN values in final portfolio value
        if np.isnan(final_value) or final_value <= 0:
            LOG.warning(f"Invalid final value: {final_value}. Using last valid portfolio value.")
            # Try to use the last valid portfolio value
            valid_values = [v for v in strat.portfolio_values if not np.isnan(v) and v > 0]
            if valid_values:
                final_value = valid_values[-1]
            else:
                final_value = initial_value
        
        # Calculate performance metrics (decimals, not percents)
        total_return = (final_value - initial_value) / initial_value
        
        # Get analyzer results
        sharpe_ratio = 0.0
        max_drawdown = 0.0
        annualized_return = 0.0
        
        try:
            if hasattr(strat, 'analyzers'):
                if strat.analyzers.sharpe:
                    sharpe_info = strat.analyzers.sharpe.get_analysis()
                    sharpe_ratio = float(sharpe_info.get('sharperatio', 0.0)) if sharpe_info else 0.0
                
                if strat.analyzers.drawdown:
                    drawdown_info = strat.analyzers.drawdown.get_analysis()
                    # Backtrader returns drawdown in percent; convert to decimal
                    max_drawdown = float(drawdown_info.get('max', {}).get('drawdown', 0.0)) / 100.0 if drawdown_info else 0.0
                
                if strat.analyzers.returns:
                    returns_info = strat.analyzers.returns.get_analysis()
                    # rnorm100 is percent; convert to decimal
                    annualized_return = float(returns_info.get('rnorm100', 0.0)) / 100.0 if returns_info else 0.0
        except Exception as e:
            LOG.warning(f"Error extracting analyzer results: {e}")
        
        # Ensure all metrics are valid numbers
        total_return = 0.0 if np.isnan(total_return) else float(total_return)
        annualized_return = 0.0 if np.isnan(annualized_return) else float(annualized_return)
        max_drawdown = 0.0 if np.isnan(max_drawdown) else float(max_drawdown)
        sharpe_ratio = 0.0 if np.isnan(sharpe_ratio) else float(sharpe_ratio)
        final_value = float(initial_value) if np.isnan(final_value) else float(final_value)
        
        # Prepare results dictionary
        backtest_results = {
            'strategy_name': strategy_name,
            'initial_value': float(initial_value),
            'final_value': final_value,
            'total_return': total_return,
            'annualized_return': annualized_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'start_date': earliest_start,
            'end_date': latest_end,
            'num_trades': len(getattr(strat, 'trades', [])) if hasattr(strat, 'trades') else 0
        }
        
        # Save rebalancing log if available
        if hasattr(strat, 'rebalance_log') and strat.rebalance_log:
            log_df = pd.DataFrame(strat.rebalance_log)
            # Ensure backtests directory exists
            log_dir = Path('analytics') / 'backtests'
            log_dir.mkdir(parents=True, exist_ok=True)
            # Sanitize strategy name for filename (lower_snake_case)
            safe_strategy_name = strategy_name.replace('/', '_').replace(' ', '_').lower()
            # Overwrite a single CSV per strategy
            log_file = log_dir / f'{safe_strategy_name}_rebalance_log.csv'
            log_df.to_csv(log_file, index=False)
            LOG.info(f"Rebalancing log saved to {log_file}")
            backtest_results['rebalance_log'] = str(log_file)
        
        # Save portfolio values if available
        if hasattr(strat, 'portfolio_values') and strat.portfolio_values:
            # Filter out NaN values
            valid_data = [(d, v) for d, v in zip(strat.portfolio_dates, strat.portfolio_values)
                          if pd.notna(v) and v > 0]
            if valid_data:
                dates, values = zip(*valid_data)
                # Include arrays directly for GUI consumption
                backtest_results['portfolio_dates'] = list(dates)
                backtest_results['portfolio_values'] = [float(v) for v in values]

                # Also persist to CSV for analytics/debugging
                portfolio_df = pd.DataFrame({
                    'date': pd.to_datetime(dates),
                    'value': values
                })
                portfolio_df['returns'] = portfolio_df['value'].pct_change()
                # Set date as index for attribution analysis compatibility
                portfolio_df.set_index('date', inplace=True)
                # Cache DataFrame in results for performance analytics
                backtest_results['portfolio_evolution'] = portfolio_df

                # Ensure backtests directory exists
                portfolio_dir = Path('analytics') / 'backtests'
                portfolio_dir.mkdir(parents=True, exist_ok=True)
                # Sanitize strategy name for filename
                safe_strategy_name = strategy_name.replace('/', '_').replace(' ', '_')
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                portfolio_file = portfolio_dir / f'{safe_strategy_name}_portfolio_values_{timestamp}.csv'
                portfolio_df.to_csv(portfolio_file, index=False)
                LOG.info(f"Portfolio values saved to {portfolio_file}")
                backtest_results['portfolio_values_file'] = str(portfolio_file)

        # Generate and cache performance stats report
        try:
            if backtest_results.get('portfolio_evolution') is not None:
                analyzer = PerformanceAnalyzer()
                performance_report = analyzer.generate_performance_report(backtest_results, save_charts=False)
                backtest_results['performance_report'] = performance_report
        except Exception as e:
            LOG.warning(f"Failed to generate performance report: {e}")
        
        # Perform attribution analysis if enabled
        if enable_attribution:
            try:
                from src.performance.attribution import PerformanceAttributor
                
                # Check if we have necessary data for attribution
                portfolio_data = backtest_results.get('portfolio_evolution')
                
                # Create asset returns DataFrame from captured data
                if asset_returns_data:
                    asset_returns_df = pd.DataFrame(asset_returns_data)
                    backtest_results['asset_returns'] = asset_returns_df
                else:
                    asset_returns_df = None
                
                # Extract weights evolution if available
                weights_df = None
                if hasattr(strat, 'weights_evolution') and strat.weights_evolution:
                    weights_df = pd.DataFrame(strat.weights_evolution)
                    if 'date' in weights_df.columns:
                        weights_df['date'] = pd.to_datetime(weights_df['date'])
                        weights_df.set_index('date', inplace=True)
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
                
                # Run attribution analysis if we have required data
                if all(data is not None for data in [portfolio_data, asset_returns_df, weights_df]):
                    attributor = PerformanceAttributor()
                    attribution_report = attributor.generate_attribution_report(
                        strategy_name=strategy_name,
                        portfolio_data=portfolio_data,
                        asset_returns=asset_returns_df,
                        weights_data=weights_df,
                        include_weekly=True,
                        include_monthly=True
                    )
                    
                    if 'error' not in attribution_report:
                        backtest_results['attribution_analysis'] = attribution_report
                        LOG.info(f"Performance attribution analysis completed for {strategy_name}")
                    else:
                        LOG.warning(f"Attribution analysis failed: {attribution_report['error']}")
                        backtest_results['attribution_error'] = attribution_report['error']
                else:
                    missing_data = []
                    if portfolio_data is None:
                        missing_data.append('portfolio_data')
                    if asset_returns_df is None:
                        missing_data.append('asset_returns')
                    if weights_df is None:
                        missing_data.append('weights_evolution')
                    
                    LOG.warning(f"Attribution analysis skipped - missing data: {', '.join(missing_data)}")
                    backtest_results['attribution_error'] = f"Missing data for attribution: {', '.join(missing_data)}"
                        
            except Exception as e:
                LOG.error(f"Performance attribution analysis error: {e}")
                backtest_results['attribution_error'] = str(e)
        
        LOG.info(f"Backtest completed successfully for {strategy_name}")
        return backtest_results
        
    except Exception as e:
        LOG.error(f"Error running backtest for {strategy_name}: {e}")
        return None


