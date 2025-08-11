"""
Backtesting runner for Personal Finance Agent.
Provides a unified interface for running strategy backtests.
"""
import backtrader as bt
import pandas as pd
import numpy as np
import os
from src.app_logger import LOG
from config import INITIAL_CAPITAL, COMMISSION, ASSETS
from src.data_center.data_loader import load_market_data, load_data_feed

def run_backtest(strategy_class, strategy_name, start_date=None, end_date=None, **kwargs):
    """
    Run a backtest for a given strategy.
    
    Args:
        strategy_class: The strategy class to backtest
        strategy_name: Name of the strategy for display purposes
        start_date: Start date for backtest (optional)
        end_date: End date for backtest (optional)
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
        cerebro.broker.setcash(INITIAL_CAPITAL)
        cerebro.broker.setcommission(commission=COMMISSION)
        # Ensure orders execute deterministically on the same bar when needed
        try:
            cerebro.broker.set_coc(True)
        except Exception:
            pass
        
        # Add data feeds using loader (ensures proper columns/mapping)
        earliest_start = None
        latest_end = None

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
            log_dir = 'analytics'
            os.makedirs(log_dir, exist_ok=True)
            # Sanitize strategy name for filename
            safe_strategy_name = strategy_name.replace('/', '_').replace(' ', '_')
            log_file = os.path.join(log_dir, f'{safe_strategy_name}_rebalance_log.csv')
            log_df.to_csv(log_file, index=False)
            LOG.info(f"Rebalancing log saved to {log_file}")
            backtest_results['rebalance_log'] = log_file
        
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
                    'date': dates,
                    'portfolio_value': values
                })
                portfolio_dir = 'analytics'
                os.makedirs(portfolio_dir, exist_ok=True)
                # Sanitize strategy name for filename
                safe_strategy_name = strategy_name.replace('/', '_').replace(' ', '_')
                portfolio_file = os.path.join(portfolio_dir, f'{safe_strategy_name}_portfolio_values.csv')
                portfolio_df.to_csv(portfolio_file, index=False)
                LOG.info(f"Portfolio values saved to {portfolio_file}")
                backtest_results['portfolio_values_file'] = portfolio_file
        
        LOG.info(f"Backtest completed successfully for {strategy_name}")
        return backtest_results
        
    except Exception as e:
        LOG.error(f"Error running backtest for {strategy_name}: {e}")
        return None


