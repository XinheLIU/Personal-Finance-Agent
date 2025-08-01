import argparse
import backtrader as bt
from src.app_logger import LOG
from src.strategy import (
    get_target_weights_and_metrics_standalone,
    DynamicAllocationStrategy,
    BuyAndHoldStrategy,
    SixtyFortyStrategy,
    PermanentPortfolioStrategy,
    AllWeatherPortfolioStrategy,
    DavidSwensenPortfolioStrategy
)
from src.cache import TARGET_WEIGHTS_CACHE
from src.reporting import create_performance_summary_table, plot_portfolio_performance
from src.config import DATA_FILES, INITIAL_CAPITAL, COMMISSION
from src.data_loader import load_data_feed
from src.analytics import log_rebalance_details

def pre_calculate_target_weights():
    """
    Pre-calculates and caches the target weights on startup.
    """
    LOG.info("Pre-calculating target weights...")
    try:
        weights, reasoning = get_target_weights_and_metrics_standalone()
        if weights:
            TARGET_WEIGHTS_CACHE['weights'] = weights
            TARGET_WEIGHTS_CACHE['reasoning'] = reasoning
            LOG.info("Target weights calculated and cached successfully.")
        else:
            LOG.warning("Could not pre-calculate target weights. The cache is empty.")
    except Exception as e:
        LOG.error(f"Error during pre-calculation of target weights: {e}")

def run_backtest(strategy_class, strategy_name, start_date=None):
    """Run backtest with given strategy"""
    LOG.info(f"=== Running {strategy_name} ===")
    
    cerebro = _setup_cerebro(strategy_class, start_date)
    if cerebro is None:
        return None
        
    LOG.info(f'Initial capital: {cerebro.broker.getvalue():.2f}')
    
    return _run_and_analyze(cerebro, strategy_name)

def _setup_cerebro(strategy_class, start_date=None):
    """Creates and configures a backtrader Cerebro engine."""
    cerebro = bt.Cerebro()
    cerebro.addstrategy(strategy_class)

    data_feeds_loaded = 0
    for name, asset_name in DATA_FILES.items():
        try:
            data_feed = load_data_feed(asset_name, name, start_date)
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
    # Sanitize strategy_name for use in file paths
    safe_strategy_name = strategy_name.replace('/', '-')

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

        create_performance_summary_table(results, safe_strategy_name, INITIAL_CAPITAL)

        if portfolio_values and portfolio_dates:
            plot_portfolio_performance(safe_strategy_name, portfolio_values, portfolio_dates, INITIAL_CAPITAL)

        # Log rebalance details
        if hasattr(strat, 'rebalance_log'):
            log_rebalance_details(safe_strategy_name, strat.rebalance_log)

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

def main():
    """
    Main entry point to launch the Gradio GUI or run CLI backtests.
    """
    parser = argparse.ArgumentParser(description='Personal Finance Agent')
    parser.add_argument('--mode', type=str, default='gui', choices=['gui', 'cli'], help='Execution mode: gui or cli')
    args = parser.parse_args()

    if args.mode == 'gui':
        pre_calculate_target_weights()
        LOG.info("Launching Personal Finance Agent GUI...")
        try:
            from src.gui import demo
            demo.launch()
        except ImportError as e:
            LOG.error(f"Could not import Gradio interface: {e}")
            LOG.error("Please ensure Gradio is installed: pip install gradio")
        except Exception as e:
            LOG.error(f"An unexpected error occurred while launching the GUI: {e}")
    elif args.mode == 'cli':
        LOG.info("Running CLI backtests...")
        run_backtest(DynamicAllocationStrategy, "Dynamic Allocation Strategy")
        run_backtest(BuyAndHoldStrategy, "Buy and Hold Strategy (S&P 500)")
        run_backtest(SixtyFortyStrategy, "60/40 Portfolio")
        run_backtest(PermanentPortfolioStrategy, "Permanent Portfolio")
        run_backtest(AllWeatherPortfolioStrategy, "All Weather Portfolio")
        run_backtest(DavidSwensenPortfolioStrategy, "David Swensen Portfolio")

if __name__ == '__main__':
    main()