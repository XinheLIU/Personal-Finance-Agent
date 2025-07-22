import backtrader as bt
from src.app_logger import LOG
import os
import pandas as pd
from src.reporting import create_performance_summary_table, plot_portfolio_performance
from src.config import DATA_FILES, INITIAL_CAPITAL, COMMISSION
from src.data_loader import load_data_feed

def _setup_cerebro(strategy_class):
    """Creates and configures a backtrader Cerebro engine."""
    cerebro = bt.Cerebro()
    cerebro.addstrategy(strategy_class)

    data_feeds_loaded = 0
    for name, asset_name in DATA_FILES.items():
        try:
            data_feed = load_data_feed(asset_name, name)
            if data_feed is not None:
                cerebro.adddata(data_feed, name=name)
                data_feeds_loaded += 1
        except FileNotFoundError as e:
            LOG.error(e)
            return None

    if data_feeds_loaded == 0:
        LOG.error("No data feeds loaded, cannot run backtest")
        return None

    LOG.info(f"Loaded {data_feeds_loaded} data feeds")

    cerebro.broker.setcash(INITIAL_CAPITAL)
    cerebro.broker.setcommission(commission=COMMISSION)

    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='timereturn')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')

    return cerebro

def _run_and_analyze(cerebro, strategy_name):
    """Runs the backtest and analyzes the results."""
    try:
        results = cerebro.run()
        final_value = cerebro.broker.getvalue()
        strat = results[0]

        total_return = (final_value / INITIAL_CAPITAL - 1) * 100
        timereturn_analysis = strat.analyzers.timereturn.get_analysis()
        drawdown_analysis = strat.analyzers.drawdown.get_analysis()
        sharpe_analysis = strat.analyzers.sharpe.get_analysis()

        portfolio_values = getattr(strat, 'portfolio_values', [])
        portfolio_dates = getattr(strat, 'portfolio_dates', [])

        if portfolio_dates and len(portfolio_dates) > 1:
            start_date = portfolio_dates[0]
            end_date = portfolio_dates[-1]
            years = (end_date - start_date).days / 365.25
        else:
            years = 1

        if years > 0:
            annualized_return = ((final_value / INITIAL_CAPITAL) ** (1/years) - 1) * 100
        else:
            annualized_return = total_return

        max_drawdown = drawdown_analysis.max.drawdown if hasattr(drawdown_analysis, 'max') else 0
        sharpe_ratio = sharpe_analysis.get('sharperatio', 0) if sharpe_analysis and sharpe_analysis.get('sharperatio') is not None else 0

        create_performance_summary_table(results, strategy_name, INITIAL_CAPITAL)

        if portfolio_values and portfolio_dates:
            plot_portfolio_performance(strategy_name, portfolio_values, portfolio_dates, INITIAL_CAPITAL)

        return {
            'final_value': final_value,
            'total_return': total_return,
            'annualized_return': annualized_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'portfolio_values': portfolio_values,
            'portfolio_dates': portfolio_dates,
            'results': results
        }

    except Exception as e:
        LOG.error(f'Error running backtest: {e}')
        if "No PE data available" in str(e):
            LOG.error("""
=== DATA REQUIREMENTS ===
The strategy requires PE ratio data for all assets. Please run:

python -m src.data_download

This will download the required PE ratio data files.
""")
        elif "No US 10Y yield data" in str(e):
            LOG.error("""
=== DATA REQUIREMENTS ===
The strategy requires US 10Y yield data. Please run:

python -m src.data_download

This will download the required US10Y.csv file.
""")
        return None

def run_backtest(strategy_class, strategy_name):
    """Run backtest with given strategy"""
    LOG.info(f"=== Running {strategy_name} ===")
    
    cerebro = _setup_cerebro(strategy_class)
    if cerebro is None:
        return None
        
    LOG.info(f'Initial capital: {cerebro.broker.getvalue():.2f}')
    
    return _run_and_analyze(cerebro, strategy_name)