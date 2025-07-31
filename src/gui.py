
import gradio as gr
from src.config import DYNAMIC_STRATEGY_PARAMS, INITIAL_CAPITAL, COMMISSION
from src.backtest_runner import run_backtest
from src.strategy import DynamicAllocationStrategy, get_target_weights_and_metrics_standalone
from src.cache import TARGET_WEIGHTS_CACHE
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
            "Date": pd.to_datetime(results['portfolio_dates']),
            "Value": [round(v, 2) for v in results['portfolio_values']]
        })
        return summary_df, portfolio_df
    else:
        error_df = pd.DataFrame({
            "Metric": ["Status"],
            "Value": ["Backtest failed. Check logs for details. Ensure data is downloaded by running: python -m src.data_download"]
        })
        return error_df, pd.DataFrame()

def get_portfolio_and_comparison_data():
    """
    Gradio interface for displaying target weights, current holdings, and comparison.
    """
    try:
        target_weights = TARGET_WEIGHTS_CACHE.get('weights', {})
        reasoning = TARGET_WEIGHTS_CACHE.get('reasoning', {})
        
        if not target_weights:
            from src.main import pre_calculate_target_weights
            pre_calculate_target_weights()
            target_weights = TARGET_WEIGHTS_CACHE.get('weights', {})
            reasoning = TARGET_WEIGHTS_CACHE.get('reasoning', {})

        if not target_weights:
            return pd.DataFrame({"Message": ["Target weights not available. Check logs."]}), pd.DataFrame()

        current_holdings = load_holdings()
        
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
        holdings_df = get_holdings_df()
        
        return comparison_df, holdings_df

    except Exception as e:
        return pd.DataFrame({"Error": [f"An error occurred: {e}"]}), pd.DataFrame()

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
                performance_plot = gr.LinePlot(x="Date", y="Value", title="Portfolio Performance")

        run_button.click(
            fn=run_backtest_interface,
            inputs=[rebalance_days, threshold, initial_capital, commission],
            outputs=[summary_table, performance_plot]
        )

    with gr.Tab("Portfolio"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("## Target vs. Current Weights")
                comparison_table = gr.DataFrame()
                refresh_button = gr.Button("Refresh")

            with gr.Column():
                gr.Markdown("## Edit Your Current Holdings")
                holdings_df = gr.DataFrame(value=get_holdings_df(), headers=['Asset', 'Weight'], interactive=True)
                save_button = gr.Button("Save Holdings")
                save_status = gr.Textbox(label="Status", interactive=False)

        refresh_button.click(
            fn=get_portfolio_and_comparison_data,
            inputs=[],
            outputs=[comparison_table, holdings_df]
        )
        
        save_button.click(
            fn=save_holdings,
            inputs=[holdings_df],
            outputs=[save_status]
        )

if __name__ == "__main__":
    demo.launch()
