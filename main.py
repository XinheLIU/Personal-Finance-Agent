import backtrader as bt
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from strategy import DynamicAllocationStrategy, BuyAndHoldStrategy
from logger import LOG
import os
from datetime import datetime
import numpy as np

# Data file paths
DATA_FILES = {
    'CSI300': 'CSI300',
    'CSI500': 'CSI500', 
    'HSTECH': 'HSTECH',
    'SP500': 'SP500',
    'NASDAQ100': 'NASDAQ100',
    'TLT': 'TLT',
    'GLD': 'GLD',
    'CASH': 'CASH',
}

def load_data_feed(asset_name, name):
    """Load data feed from CSV file with new naming convention"""
    # Look for files with the new naming convention
    data_dir = 'data'
    if not os.path.exists(data_dir):
        LOG.warning(f"Data directory not found: {data_dir}")
        return None
    
    # Search for files matching the asset name pattern
    pattern = f"{asset_name}_price_"
    matching_files = [f for f in os.listdir(data_dir) if f.startswith(pattern) and f.endswith('.csv')]
    
    if not matching_files:
        LOG.warning(f"No price data file found for {name} (pattern: {pattern})")
        return None
    
    # Use the most recent file (assuming it has the latest date range)
    filename = sorted(matching_files)[-1]
    filepath = os.path.join(data_dir, filename)
    
    try:
        df = pd.read_csv(filepath)
        
        # Handle different column naming conventions
        if '日期' in df.columns and '收盘' in df.columns:
            # Chinese data format
            df = df.rename(columns={'日期': 'datetime', '收盘': 'close'})
        elif 'date' in df.columns and 'close' in df.columns:
            # English data format  
            df = df.rename(columns={'date': 'datetime'})
        else:
            LOG.warning(f"Unknown column format in {filepath}")
            return None
            
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
        
        # Add required OHLV columns for backtrader (use close price for all)
        df['open'] = df['close'].astype(float)
        df['high'] = df['close'].astype(float) * 1.01  # Simulate small spread
        df['low'] = df['close'].astype(float) * 0.99
        df['volume'] = 1000000  # Dummy volume
        
        # Create backtrader data feed
        class PandasData(bt.feeds.PandasData):
            params = (
                ('datetime', None),
                ('open', 'open'),
                ('high', 'high'), 
                ('low', 'low'),
                ('close', 'close'),
                ('volume', 'volume'),
                ('openinterest', -1),
            )
        
        data_feed = PandasData(dataname=df)
        LOG.info(f"Loaded {name}: {len(df)} records from {df.index.min()} to {df.index.max()}")
        return data_feed
        
    except Exception as e:
        LOG.error(f"Error loading {filepath}: {e}")
        return None

def run_backtest(strategy_class, strategy_name):
    """Run backtest with given strategy"""
    LOG.info(f"=== Running {strategy_name} ===")
    
    # Create backtest engine
    cerebro = bt.Cerebro()
    cerebro.addstrategy(strategy_class)
    
    # Load all available data feeds
    data_feeds_loaded = 0
    for name, asset_name in DATA_FILES.items():
        data_feed = load_data_feed(asset_name, name)
        if data_feed is not None:
            cerebro.adddata(data_feed, name=name)
            data_feeds_loaded += 1
    
    if data_feeds_loaded == 0:
        LOG.error("No data feeds loaded, cannot run backtest")
        return None
        
    LOG.info(f"Loaded {data_feeds_loaded} data feeds")
    
    # Set initial capital and commission
    initial_capital = 1000000
    cerebro.broker.setcash(initial_capital)
    cerebro.broker.setcommission(commission=0.001)  # 0.1% commission
    
    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='timereturn')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    
    LOG.info(f'Initial capital: {cerebro.broker.getvalue():.2f}')
    
    # Run backtest
    try:
        results = cerebro.run()
        final_value = cerebro.broker.getvalue()
        
        # Get results
        strat = results[0]
        
        # Calculate performance metrics
        total_return = (final_value / initial_capital - 1) * 100
        timereturn_analysis = strat.analyzers.timereturn.get_analysis()
        drawdown_analysis = strat.analyzers.drawdown.get_analysis()
        sharpe_analysis = strat.analyzers.sharpe.get_analysis()
        
        # Calculate actual time period from data
        portfolio_values = getattr(strat, 'portfolio_values', [])
        portfolio_dates = getattr(strat, 'portfolio_dates', [])
        
        if portfolio_dates and len(portfolio_dates) > 1:
            start_date = portfolio_dates[0]
            end_date = portfolio_dates[-1]
            years = (end_date - start_date).days / 365.25
        else:
            years = 1  # Default to 1 year if no date data
        
        # Calculate annualized return using actual time period
        if years > 0:
            annualized_return = ((final_value / initial_capital) ** (1/years) - 1) * 100
        else:
            annualized_return = total_return
            
        max_drawdown = drawdown_analysis.max.drawdown if hasattr(drawdown_analysis, 'max') else 0
        sharpe_ratio = sharpe_analysis.get('sharperatio', 0) if sharpe_analysis and sharpe_analysis.get('sharperatio') is not None else 0
        
        # Create performance summary table
        summary_df = create_performance_summary_table(results, strategy_name, initial_capital)
        
        # Get portfolio tracking data from strategy
        strat = results[0]
        portfolio_values = getattr(strat, 'portfolio_values', [])
        portfolio_dates = getattr(strat, 'portfolio_dates', [])
        
        # Create portfolio performance plot
        if portfolio_values and portfolio_dates:
            plot_portfolio_performance(strategy_name, portfolio_values, portfolio_dates, initial_capital)
        
        return {
            'final_value': final_value,
            'total_return': total_return,
            'annualized_return': annualized_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'portfolio_values': portfolio_values,
            'portfolio_dates': portfolio_dates
        }
        
    except Exception as e:
        LOG.error(f'Error running backtest: {e}')
        
        # Provide helpful error messages for common issues
        if "No PE data available" in str(e):
            LOG.error("""
=== DATA REQUIREMENTS ===
The strategy requires PE ratio data for all assets. Please run:

python data_download.py

This will download the required PE ratio data files:
- data/CSI300_PE.csv
- data/CSI500_PE.csv  
- data/HSTECH_PE.csv
- data/SP500_PE.csv
- data/NASDAQ100_PE.csv

If some data sources are unavailable, you may need to:
1. Check your internet connection
2. Verify the data sources are accessible
3. Consider using alternative data sources
""")
        elif "No US 10Y yield data" in str(e):
            LOG.error("""
=== DATA REQUIREMENTS ===
The strategy requires US 10Y yield data. Please run:

python data_download.py

This will download the required US10Y.csv file.
""")
        
        return None

def create_performance_summary_table(results, strategy_name, initial_capital):
    """
    Create a comprehensive performance summary table and save it to CSV.
    """
    if not results:
        LOG.warning("No results to create summary table.")
        return None

    strat = results[0]
    final_value = strat.broker.getvalue()
    
    # Calculate performance metrics
    total_return = (final_value / initial_capital - 1) * 100
    timereturn_analysis = strat.analyzers.timereturn.get_analysis()
    drawdown_analysis = strat.analyzers.drawdown.get_analysis()
    sharpe_analysis = strat.analyzers.sharpe.get_analysis()
    
    # Calculate actual time period from data
    portfolio_values = getattr(strat, 'portfolio_values', [])
    portfolio_dates = getattr(strat, 'portfolio_dates', [])
    
    if portfolio_dates and len(portfolio_dates) > 1:
        start_date = portfolio_dates[0]
        end_date = portfolio_dates[-1]
        years = (end_date - start_date).days / 365.25
    else:
        years = 1  # Default to 1 year if no date data
    
    # Calculate annualized return using actual time period
    if years > 0:
        annualized_return = ((final_value / initial_capital) ** (1/years) - 1) * 100
    else:
        annualized_return = total_return
        
    max_drawdown = drawdown_analysis.max.drawdown if hasattr(drawdown_analysis, 'max') else 0
    sharpe_ratio = sharpe_analysis.get('sharperatio', 0) if sharpe_analysis else 0
    
    # Create performance summary table
    summary_data = {
        'Metric': [
            'Initial Capital',
            'Final Capital', 
            'Total Return (%)',
            'Annualized Return (%)',
            'Max Drawdown (%)',
            'Sharpe Ratio',
            'Total Years'
        ],
        'Value': [
            f'${initial_capital:,.2f}',
            f'${final_value:,.2f}',
            f'{total_return:.2f}%',
            f'{annualized_return:.2f}%',
            f'{max_drawdown:.2f}%',
            f'{sharpe_ratio:.3f}',
            f'{years:.1f}'
        ]
    }
    
    summary_df = pd.DataFrame(summary_data)
    
    # Save to CSV
    filename = f'{strategy_name.lower().replace(" ", "_")}_performance_summary.csv'
    summary_df.to_csv(filename, index=False)
    LOG.info(f'Performance summary saved to {filename}')
    
    # Print formatted table to console
    LOG.info(f'\n{"="*60}')
    LOG.info(f'{strategy_name.upper()} PERFORMANCE SUMMARY')
    LOG.info(f'{"="*60}')
    for _, row in summary_df.iterrows():
        LOG.info(f'{row["Metric"]:<20}: {row["Value"]}')
    LOG.info(f'{"="*60}')
    
    return summary_df

def plot_portfolio_performance(strategy_name, portfolio_values, dates, initial_capital):
    """
    Create a clean seaborn line plot of portfolio performance over time.
    """
    if not portfolio_values or not dates:
        LOG.warning("No portfolio data to plot.")
        return
    
    # Create DataFrame for plotting
    df_plot = pd.DataFrame({
        'Date': dates,
        'Portfolio Value': portfolio_values
    })
    
    # Set seaborn style for better looking plots
    sns.set_style("whitegrid")
    plt.figure(figsize=(14, 8))
    
    # Create the main plot
    ax = sns.lineplot(data=df_plot, x='Date', y='Portfolio Value', 
                     linewidth=2, color='#2E86AB')
    
    # Add initial capital reference line
    plt.axhline(y=initial_capital, color='#A23B72', linestyle='--', 
                linewidth=1.5, alpha=0.7, label=f'Initial Capital (${initial_capital:,.0f})')
    
    # Customize the plot
    plt.title(f'{strategy_name} - Portfolio Performance Over Time', 
              fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Portfolio Value (USD)', fontsize=12)
    
    # Format y-axis with comma separators
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)
    
    # Add grid and legend
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=11)
    
    # Adjust layout and save
    plt.tight_layout()
    filename = f'{strategy_name.lower().replace(" ", "_")}_portfolio_performance.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    LOG.info(f'Portfolio performance chart saved to {filename}')

if __name__ == '__main__':
    LOG.info("Personal Finance Agent - Multi-Asset Dynamic Allocation Backtest")
    LOG.info("=" * 60)
    
    # Run Dynamic Allocation Strategy
    dynamic_results = run_backtest(DynamicAllocationStrategy, "Dynamic Allocation Strategy")
    
    # Run Buy and Hold Strategy for comparison (using first available asset)
    LOG.info(f"\n=== Running Buy and Hold Comparison (CSI300 only) ===")
    cerebro_bh = bt.Cerebro()
    cerebro_bh.addstrategy(BuyAndHoldStrategy)
    
    # Load only CSI300 for buy and hold comparison
    csi300_feed = load_data_feed('CSI300', 'CSI300')
    bh_results = None
    if csi300_feed is not None:
        cerebro_bh.adddata(csi300_feed, name='CSI300')
        cerebro_bh.broker.setcash(1000000)
        cerebro_bh.broker.setcommission(commission=0.001)
        
        # Add analyzers for buy and hold strategy
        cerebro_bh.addanalyzer(bt.analyzers.TimeReturn, _name='timereturn')
        cerebro_bh.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro_bh.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        
        try:
            LOG.info(f"Running buy and hold strategy with initial cash: ${cerebro_bh.broker.getcash():,.2f}")
            bh_results = cerebro_bh.run()
            
            # Get portfolio tracking data from strategy
            bh_strat = bh_results[0]
            bh_portfolio_values = getattr(bh_strat, 'portfolio_values', [])
            bh_portfolio_dates = getattr(bh_strat, 'portfolio_dates', [])
            
            # Calculate final value from portfolio tracking data
            if bh_portfolio_values:
                bh_final = bh_portfolio_values[-1]
                bh_return = (bh_final / 1000000 - 1) * 100
                LOG.info(f"Buy and Hold Results - Final Value: ${bh_final:,.2f}, Return: {bh_return:.2f}%")
            else:
                bh_final = 1000000
                bh_return = 0
                LOG.warning("No portfolio values tracked, using default values")
            
            # Create performance summary for buy and hold
            create_performance_summary_table(bh_results, "Buy and Hold Strategy", 1000000)
            
            if bh_portfolio_values and bh_portfolio_dates:
                plot_portfolio_performance("Buy and Hold Strategy", bh_portfolio_values, bh_portfolio_dates, 1000000)
                
        except Exception as e:
            LOG.error(f'Error running buy and hold strategy: {e}')
            import traceback
            LOG.error(f'Traceback: {traceback.format_exc()}')
            bh_final = 1000000
            bh_return = 0
    
    # Create comprehensive comparison table
    if dynamic_results and bh_results:
        LOG.info(f"\n{'='*80}")
        LOG.info(f"COMPREHENSIVE PERFORMANCE COMPARISON")
        LOG.info(f"{'='*80}")
        
        # Calculate buy and hold metrics
        bh_strat = bh_results[0]
        bh_portfolio_values = getattr(bh_strat, 'portfolio_values', [])
        if bh_portfolio_values:
            bh_final = bh_portfolio_values[-1]
            bh_return = (bh_final / 1000000 - 1) * 100
        else:
            bh_final = 1000000
            bh_return = 0
        bh_timereturn = bh_strat.analyzers.timereturn.get_analysis()
        bh_drawdown = bh_strat.analyzers.drawdown.get_analysis()
        bh_sharpe = bh_strat.analyzers.sharpe.get_analysis()
        
        # Calculate actual time period for buy and hold strategy
        bh_portfolio_dates = getattr(bh_strat, 'portfolio_dates', [])
        if bh_portfolio_dates and len(bh_portfolio_dates) > 1:
            bh_start_date = bh_portfolio_dates[0]
            bh_end_date = bh_portfolio_dates[-1]
            bh_years = (bh_end_date - bh_start_date).days / 365.25
        else:
            bh_years = 1  # Default to 1 year if no date data
        
        bh_annualized = ((bh_final / 1000000) ** (1/bh_years) - 1) * 100 if bh_years > 0 else bh_return
        bh_max_dd = bh_drawdown.max.drawdown if hasattr(bh_drawdown, 'max') else 0
        bh_sharpe_ratio = bh_sharpe.get('sharperatio', 0) if bh_sharpe and isinstance(bh_sharpe.get('sharperatio'), (int, float)) else 0
        
        # Create comparison table
        comparison_data = {
            'Metric': [
                'Strategy',
                'Final Capital',
                'Total Return (%)',
                'Annualized Return (%)',
                'Max Drawdown (%)',
                'Sharpe Ratio',
                'Outperformance vs Buy & Hold (%)'
            ],
            'Dynamic Allocation': [
                'Dynamic Allocation',
                f'${dynamic_results["final_value"]:,.2f}',
                f'{dynamic_results["total_return"]:.2f}%',
                f'{dynamic_results["annualized_return"]:.2f}%',
                f'{dynamic_results["max_drawdown"]:.2f}%',
                f'{dynamic_results["sharpe_ratio"]:.3f}',
                f'{dynamic_results["total_return"] - bh_return:.2f}%'
            ],
            'Buy & Hold (CSI300)': [
                'Buy & Hold',
                f'${bh_final:,.2f}',
                f'{bh_return:.2f}%',
                f'{bh_annualized:.2f}%',
                f'{bh_max_dd:.2f}%',
                f'{bh_sharpe_ratio:.3f}',
                '0.00%'
            ]
        }
        
        comparison_df = pd.DataFrame(comparison_data)
        comparison_df.to_csv('performance_comparison.csv', index=False)
        LOG.info(f'Performance comparison saved to performance_comparison.csv')
        
        # Print comparison table
        LOG.info(f"\n{'Strategy':<25} {'Final Capital':<15} {'Total Return':<12} {'Ann. Return':<12} {'Max DD':<8} {'Sharpe':<8} {'Outperformance':<12}")
        LOG.info(f"{'-'*100}")
        LOG.info(f"{'Dynamic Allocation':<25} ${dynamic_results['final_value']:>13,.0f} {dynamic_results['total_return']:>10.2f}% {dynamic_results['annualized_return']:>10.2f}% {dynamic_results['max_drawdown']:>6.2f}% {dynamic_results['sharpe_ratio']:>6.3f} {dynamic_results['total_return'] - bh_return:>10.2f}%")
        LOG.info(f"{'Buy & Hold (CSI300)':<25} ${bh_final:>13,.0f} {bh_return:>10.2f}% {bh_annualized:>10.2f}% {bh_max_dd:>6.2f}% {bh_sharpe_ratio:>6.3f} {'0.00':>10}%")
        LOG.info(f"{'='*100}")
        
    elif dynamic_results:
        LOG.info(f"\n=== Performance Summary ===")
        LOG.info(f"Dynamic Strategy Return: {dynamic_results['total_return']:.2f}%")
        LOG.info(f"Dynamic Strategy Sharpe: {dynamic_results['sharpe_ratio']:.2f}")
        LOG.info(f"Dynamic Strategy Max DD: {dynamic_results['max_drawdown']:.2f}%")
    else:
        LOG.warning("Dynamic strategy failed to complete. Check the logs above for details.") 