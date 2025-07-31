
import gradio as gr
from src.config import DYNAMIC_STRATEGY_PARAMS, INITIAL_CAPITAL, COMMISSION
from src.backtest_runner import run_backtest
from src.strategy import DynamicAllocationStrategy
import pandas as pd
import json
import os

HOLDINGS_FILE = "data/holdings.json"

def run_backtest_interface(rebalance_days, threshold, initial_capital, commission):
    """
    Gradio interface for running the backtest.
    """
    DYNAMIC_STRATEGY_PARAMS['rebalance_days'] = rebalance_days
    DYNAMIC_STRATEGY_PARAMS['threshold'] = threshold

    results = run_backtest(DynamicAllocationStrategy, "DynamicAllocationStrategy")

    if results:
        summary_df = pd.DataFrame({
            "Metric": ["Final Value", "Total Return (%)", "Annualized Return (%)", "Max Drawdown (%)", "Sharpe Ratio"],
            "Value": [f"${results['final_value']:,.2f}", f"{results['total_return']:.2f}", f"{results['annualized_return']:.2f}", f"{results['max_drawdown']:.2f}", f"{results['sharpe_ratio']:.2f}"]
        })
        portfolio_df = pd.DataFrame({
            "Date": results['portfolio_dates'],
            "Value": results['portfolio_values']
        })
        return summary_df, gr.LinePlot(data=portfolio_df, x="Date", y="Value", title="Portfolio Performance")
    else:
        # Return proper DataFrame with error message instead of string
        error_df = pd.DataFrame({
            "Metric": ["Status"],
            "Value": ["Backtest failed. Check logs for details. Ensure data is downloaded by running: python -m src.data_download"]
        })
        return error_df, None

def get_target_weights_and_comparison():
    """
    Gradio interface for displaying target weights and comparison with current holdings.
    """
    try:
        strategy = DynamicAllocationStrategy()
        target_weights, reasoning = strategy.get_target_weights_and_metrics()
        
        if not target_weights:
            return pd.DataFrame({"Message": ["Could not retrieve target weights. Check logs for errors."]}), pd.DataFrame()

        current_holdings = load_holdings()
        
        # Create a DataFrame for comparison
        comparison_data = []
        all_assets = sorted(list(set(target_weights.keys()) | set(current_holdings.keys())))
        
        for asset in all_assets:
            target = target_weights.get(asset, 0)
            current = current_holdings.get(asset, 0)
            diff = target - current
            comparison_data.append({
                "Asset": asset,
                "Target Weight": f"{target:.2%}",
                "Current Weight": f"{current:.2%}",
                "Difference": f"{diff:.2%}",
                "Reasoning": reasoning.get(asset, "N/A")
            })
            
        comparison_df = pd.DataFrame(comparison_data)
        
        return comparison_df

    except Exception as e:
        return pd.DataFrame({"Error": [f"An error occurred: {e}"]})

def load_holdings():
    """
    Loads current holdings from the JSON file.
    """
    if os.path.exists(HOLDINGS_FILE):
        with open(HOLDINGS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_holdings(holdings_df):
    """
    Saves the holdings DataFrame to the JSON file.
    """
    try:
        holdings_dict = holdings_df.set_index('Asset')['Weight'].to_dict()
        # Convert weights from percentage strings to floats
        for asset, weight in holdings_dict.items():
            holdings_dict[asset] = float(weight.strip('%')) / 100
            
        with open(HOLDINGS_FILE, 'w') as f:
            json.dump(holdings_dict, f, indent=4)
        return "Holdings saved successfully!"
    except Exception as e:
        return f"Error saving holdings: {e}"

def get_holdings_df():
    """
    Returns a DataFrame of current holdings for editing.
    """
    holdings = load_holdings()
    if not holdings:
        return pd.DataFrame({'Asset': [], 'Weight': []})
    
    df = pd.DataFrame(list(holdings.items()), columns=['Asset', 'Weight'])
    df['Weight'] = df['Weight'].apply(lambda x: f"{x:.2%}")
    return df

with gr.Blocks() as demo:
    gr.Markdown("# Personal Finance Agent")

    with gr.Tab("Backtest"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("## Strategy Parameters")
                rebalance_days = gr.Slider(label="Rebalance Days", minimum=30, maximum=365, value=DYNAMIC_STRATEGY_PARAMS['rebalance_days'], step=1)
                threshold = gr.Slider(label="Threshold", minimum=0.01, maximum=0.2, value=DYNAMIC_STRATEGY_PARAMS['threshold'], step=0.01)
                
                gr.Markdown("## Backtest Settings")
                initial_capital = gr.Number(label="Initial Capital", value=INITIAL_CAPITAL)
                commission = gr.Number(label="Commission", value=COMMISSION)

                run_button = gr.Button("Run Backtest")
            
            with gr.Column():
                gr.Markdown("## Backtest Results")
                summary_table = gr.DataFrame(headers=["Metric", "Value"])
                performance_plot = gr.Plot()

        run_button.click(
            fn=run_backtest_interface,
            inputs=[rebalance_days, threshold, initial_capital, commission],
            outputs=[summary_table, performance_plot]
        )

    with gr.Tab("Monitoring"):
        gr.Markdown("## Target vs. Current Weights")
        comparison_table = gr.DataFrame()
        refresh_button = gr.Button("Refresh")
        refresh_button.click(
            fn=get_target_weights_and_comparison,
            inputs=[],
            outputs=[comparison_table]
        )

    with gr.Tab("My Holdings"):
        gr.Markdown("## Edit Your Current Holdings")
        holdings_df = gr.DataFrame(value=get_holdings_df(), headers=['Asset', 'Weight'], interactive=True)
        save_button = gr.Button("Save Holdings")
        save_status = gr.Textbox(label="Status")
        
        save_button.click(
            fn=save_holdings,
            inputs=[holdings_df],
            outputs=[save_status]
        )

if __name__ == "__main__":
    demo.launch()
