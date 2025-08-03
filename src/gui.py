import gradio as gr
from src.config import DYNAMIC_STRATEGY_PARAMS, INITIAL_CAPITAL, COMMISSION, ASSET_DISPLAY_INFO, TRADABLE_ASSETS
from src.main import run_backtest
from src.strategy import (
    DynamicAllocationStrategy, 
    get_target_weights_and_metrics_standalone, 
    FixedWeightStrategy,
    SixtyFortyStrategy,
    PermanentPortfolioStrategy,
    AllWeatherPortfolioStrategy,
    DavidSwensenPortfolioStrategy
)
from src.cache import TARGET_WEIGHTS_CACHE
import pandas as pd
import json
import os
from src.data_download import main as download_data_main, get_data_range_info
from src.app_logger import LOG

def get_strategy_weights(strategy_name):
    # Define target weights for each strategy without instantiating the class
    strategy_weights = {
        "60/40 Portfolio": {'SP500': 0.60, 'TLT': 0.40},
        "Permanent Portfolio": {'SP500': 0.25, 'TLT': 0.25, 'CASH': 0.25, 'GLD': 0.25},
        "All Weather Portfolio": {'SP500': 0.30, 'TLT': 0.55, 'GLD': 0.15},
        "David Swensen Portfolio": {'SP500': 0.65, 'CSI300': 0.05, 'TLT': 0.30},
    }
    
    if strategy_name in strategy_weights:
        return strategy_weights[strategy_name]
    elif strategy_name == "Dynamic Allocation":
        # For dynamic strategy, we can show the latest cached weights
        return TARGET_WEIGHTS_CACHE.get('weights', {})
    return {}

HOLDINGS_FILE = "data/holdings.json"

def run_backtest_interface(strategy_choice, rebalance_days, threshold, initial_capital, commission, custom_weights_df, start_date):
    """
    Gradio interface for running the backtest.
    """
    DYNAMIC_STRATEGY_PARAMS['rebalance_days'] = rebalance_days
    DYNAMIC_STRATEGY_PARAMS['threshold'] = threshold

    strategy_map = {
        "Dynamic Allocation": DynamicAllocationStrategy,
        "60/40 Portfolio": SixtyFortyStrategy,
        "Permanent Portfolio": PermanentPortfolioStrategy,
        "All Weather Portfolio": AllWeatherPortfolioStrategy,
        "David Swensen Portfolio": DavidSwensenPortfolioStrategy,
    }

    if strategy_choice == "Custom Fixed Weight":
        try:
            weights = {row['Asset']: float(row['Weight']) / 100.0 for index, row in custom_weights_df.iterrows()}
            total_weight = sum(weights.values())
            if not (0.99 <= total_weight <= 1.01):
                return pd.DataFrame({"Metric": ["Error"], "Value": ["Total weights must be 100%"]}), pd.DataFrame()
            
            class CustomFixedStrategy(FixedWeightStrategy):
                def __init__(self):
                    self.p.target_weights = weights
                    super().__init__()
            
            strategy_class = CustomFixedStrategy
        except Exception as e:
            return pd.DataFrame({"Metric": ["Error"], "Value": [f"Invalid custom weights: {e}"]}), pd.DataFrame()
    else:
        strategy_class = strategy_map[strategy_choice]


    results = run_backtest(strategy_class, strategy_choice, start_date)

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
            
            # Get display information for this asset
            display_info = ASSET_DISPLAY_INFO.get(asset, {})
            asset_name = display_info.get('name', asset)
            index_name = display_info.get('index', 'N/A')
            tradable_cn = display_info.get('tradable_cn', 'N/A') 
            tradable_us = display_info.get('tradable_us', 'N/A')
            region = display_info.get('region', 'N/A')
            
            # Format tradable products display
            tradable_products = []
            if tradable_cn and tradable_cn != 'N/A':
                tradable_products.append(f"CN: {tradable_cn}")
            if tradable_us and tradable_us != 'N/A':
                tradable_products.append(f"US: {tradable_us}")
            tradable_display = ", ".join(tradable_products) if tradable_products else "N/A"
            
            comparison_data.append({
                "Asset": asset_name,
                "Region": region,
                "Index (PE Data)": index_name,
                "Tradable Products": tradable_display,
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
        # Convert display names back to asset keys and extract weights
        holdings_dict = {}
        for _, row in holdings_df.iterrows():
            asset_display_name = row['Asset']
            weight_str = row['Weight']
            
            # Find the asset key from the display name
            asset_key = None
            for key, info in ASSET_DISPLAY_INFO.items():
                if info.get('name', key) == asset_display_name:
                    asset_key = key
                    break
            
            if asset_key:
                # Convert percentage string to float
                weight_value = float(weight_str.strip('%')) / 100
                holdings_dict[asset_key] = weight_value
            
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
        return pd.DataFrame({'Asset': [], 'Tradable Products': [], 'Weight': []})
    
    holdings_data = []
    for asset, weight in holdings.items():
        # Get display information for this asset
        display_info = ASSET_DISPLAY_INFO.get(asset, {})
        asset_name = display_info.get('name', asset)
        tradable_cn = display_info.get('tradable_cn', 'N/A') 
        tradable_us = display_info.get('tradable_us', 'N/A')
        
        # Format tradable products display
        tradable_products = []
        if tradable_cn and tradable_cn != 'N/A':
            tradable_products.append(f"CN: {tradable_cn}")
        if tradable_us and tradable_us != 'N/A':
            tradable_products.append(f"US: {tradable_us}")
        tradable_display = ", ".join(tradable_products) if tradable_products else "N/A"
        
        holdings_data.append({
            'Asset': asset_name,
            'Tradable Products': tradable_display,
            'Weight': f"{weight:.2%}"
        })
    
    return pd.DataFrame(holdings_data)

def download_data_interface():
    LOG.info("Starting data download from GUI...")
    try:
        download_data_main(refresh=True)
        return "Data download finished. Check logs for details."
    except Exception as e:
        LOG.error(f"Data download failed: {e}")
        return f"Data download failed: {e}"

with gr.Blocks() as demo:
    gr.Markdown("# Personal Finance Agent")

    with gr.Tab("Backtest"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("## Strategy Selection")
                strategy_choice = gr.Dropdown(
                    ["Dynamic Allocation", "60/40 Portfolio", "Permanent Portfolio", "All Weather Portfolio", "David Swensen Portfolio", "Custom Fixed Weight"],
                    label="Strategy",
                    value="Dynamic Allocation"
                )
                
                gr.Markdown("## Strategy Details")
                strategy_details_table = gr.DataFrame(headers=["Asset", "Weight"])

                gr.Markdown("## Strategy Parameters")
                rebalance_days = gr.Slider(label="Rebalance Days", minimum=30, maximum=365, value=DYNAMIC_STRATEGY_PARAMS['rebalance_days'], step=1)
                threshold = gr.Slider(label="Threshold", minimum=0.01, maximum=0.2, value=DYNAMIC_STRATEGY_PARAMS['threshold'], step=0.01)
                
                gr.Markdown("## Backtest Settings")
                initial_capital = gr.Number(label="Initial Capital", value=INITIAL_CAPITAL)
                commission = gr.Number(label="Commission", value=COMMISSION)
                start_date_input = gr.Textbox(label="Backtest Start Date (YYYY-MM-DD)", value="2020-01-01")


                run_button = gr.Button("Run Backtest")

            with gr.Column():
                gr.Markdown("## Backtest Results")
                summary_table = gr.DataFrame(headers=["Metric", "Value"])
                performance_plot = gr.LinePlot(x="Date", y="Value", title="Portfolio Performance")

        run_button.click(
            fn=run_backtest_interface,
            inputs=[strategy_choice, rebalance_days, threshold, initial_capital, commission, gr.State(pd.DataFrame()), start_date_input],
            outputs=[summary_table, performance_plot]
        )
        
        def update_strategy_details(strategy_name):
            weights = get_strategy_weights(strategy_name)
            if weights:
                df = pd.DataFrame(list(weights.items()), columns=["Asset", "Weight"])
                df["Weight"] = df["Weight"].apply(lambda x: f"{x:.2%}")
                return df
            return pd.DataFrame()

        strategy_choice.change(
            fn=update_strategy_details,
            inputs=strategy_choice,
            outputs=strategy_details_table
        )

    with gr.Tab("Custom Strategy"):
        gr.Markdown("## Create Your Own Fixed-Weight Strategy")
        custom_weights_df = gr.DataFrame(
            headers=["Asset", "Weight"],
            datatype=["str", "number"],
            row_count=len(TRADABLE_ASSETS),
            col_count=(2, "fixed"),
            value=pd.DataFrame({'Asset': list(TRADABLE_ASSETS.keys()), 'Weight': [0]*len(TRADABLE_ASSETS)})
        )
        run_custom_button = gr.Button("Run Custom Strategy Backtest")
        with gr.Row():
            with gr.Column():
                gr.Markdown("## Backtest Results")
                custom_summary_table = gr.DataFrame(headers=["Metric", "Value"])
                custom_performance_plot = gr.LinePlot(x="Date", y="Value", title="Portfolio Performance")
        
        run_custom_button.click(
            fn=run_backtest_interface,
            inputs=[gr.State("Custom Fixed Weight"), rebalance_days, threshold, initial_capital, commission, custom_weights_df, start_date_input],
            outputs=[custom_summary_table, custom_performance_plot]
        )

    with gr.Tab("Portfolio"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("## Target vs. Current Weights")
                comparison_table = gr.DataFrame()
                refresh_button = gr.Button("Refresh")

            with gr.Column():
                gr.Markdown("## Edit Your Current Holdings")
                holdings_df = gr.DataFrame(value=get_holdings_df(), headers=['Asset', 'Tradable Products', 'Weight'], interactive=True)
                save_button = gr.Button("Save Holdings")
                save_status = gr.Textbox(label="Status", interactive=False)
        
        with gr.Row():
            with gr.Column():
                gr.Markdown("## Gap Analysis")
                gap_analysis_table = gr.DataFrame(headers=["Asset", "Strategy Weight", "Your Weight", "Gap"])


        def update_gap_analysis(strategy_name):
            strategy_weights = get_strategy_weights(strategy_name)
            holdings = load_holdings()
            
            all_assets = sorted(list(set(strategy_weights.keys()) | set(holdings.keys())))
            
            gap_data = []
            for asset in all_assets:
                strategy_weight = strategy_weights.get(asset, 0)
                holding_weight = holdings.get(asset, 0)
                gap = strategy_weight - holding_weight
                gap_data.append({
                    "Asset": ASSET_DISPLAY_INFO.get(asset, {}).get('name', asset),
                    "Strategy Weight": f"{strategy_weight:.2%}",
                    "Your Weight": f"{holding_weight:.2%}",
                    "Gap": f"{gap:.2%}"
                })
            return pd.DataFrame(gap_data)

        strategy_choice.change(
            fn=update_gap_analysis,
            inputs=strategy_choice,
            outputs=gap_analysis_table
        )


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

    with gr.Tab("Data"):
        gr.Markdown("## Data Management")
        
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Available Data")
                available_data_table = gr.DataFrame(headers=["Type", "Asset", "File", "Start Date", "End Date"])
                
                def get_available_data():
                    data_files = []
                    for data_type in ["price", "pe", "yield"]:
                        data_dir = os.path.join("data", data_type)
                        if os.path.exists(data_dir):
                            for file in os.listdir(data_dir):
                                if file.endswith(".csv"):
                                    try:
                                        asset_name = file.split('_')[0]
                                        df = pd.read_csv(os.path.join(data_dir, file))
                                        start_date, end_date = get_data_range_info(df)
                                        data_files.append({
                                            "Type": data_type,
                                            "Asset": asset_name,
                                            "File": file,
                                            "Start Date": start_date.strftime('%Y-%m-%d') if start_date else "N/A",
                                            "End Date": end_date.strftime('%Y-%m-%d') if end_date else "N/A"
                                        })
                                    except Exception as e:
                                        LOG.error(f"Error reading data file {file}: {e}")
                    return pd.DataFrame(data_files) if data_files else pd.DataFrame()
                
                demo.load(get_available_data, None, available_data_table)

            with gr.Column():
                gr.Markdown("### Download New Data")
                new_ticker_input = gr.Textbox(label="New Ticker (e.g., AAPL for yfinance, 000001 for akshare)")
                download_new_button = gr.Button("Download New Ticker")
                download_status = gr.Textbox(label="Status", interactive=False)

                def download_new_ticker(ticker):
                    from src.data_download import download_yfinance_data, download_akshare_index
                    
                    try:
                        # Try yfinance first
                        filepath, _, _ = download_yfinance_data(ticker, ticker)
                        if filepath:
                            return f"Successfully downloaded {ticker} from yfinance."
                        
                        # Try akshare if yfinance fails
                        filepath, _, _ = download_akshare_index(ticker, ticker)
                        if filepath:
                            return f"Successfully downloaded {ticker} from akshare."
                            
                        return f"Failed to download {ticker} from both yfinance and akshare."
                    except Exception as e:
                        return f"Error downloading {ticker}: {e}"

                download_new_button.click(
                    fn=download_new_ticker,
                    inputs=new_ticker_input,
                    outputs=download_status
                )
                
                gr.Markdown("### Refresh All Data")
                download_button = gr.Button("Download/Refresh All Data")
                download_button.click(
                    fn=download_data_interface,
                    inputs=[],
                    outputs=[download_status]
                )

if __name__ == "__main__":
    demo.launch()