import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from src.app_logger import LOG

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
