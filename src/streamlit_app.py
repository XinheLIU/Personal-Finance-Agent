"""
Streamlit Web Application for Personal Finance Agent.
Replacing Gradio with Streamlit for better visualization and user experience.
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date
from typing import Dict, Optional

# Configure Streamlit page
st.set_page_config(
    page_title="Personal Finance Agent",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import system components
from config.assets import TRADABLE_ASSETS, ASSET_DISPLAY_INFO, DYNAMIC_STRATEGY_PARAMS
from config.system import INITIAL_CAPITAL, COMMISSION
from src.backtesting.runner import run_backtest
from src.strategies.registry import strategy_registry
from src.strategies.base import FixedWeightStrategy
from src.data_center.download import main as download_data_main, get_data_range_info
from src.app_logger import LOG
from src.visualization.charts import (
    display_portfolio_performance,
    display_asset_allocation,
    display_portfolio_comparison,
    display_backtest_summary,
    display_data_explorer,
    display_strategy_weights_table,
    create_metrics_dashboard
)

# Cache for strategy weights
if 'target_weights_cache' not in st.session_state:
    st.session_state.target_weights_cache = {}

# Holdings file path
HOLDINGS_FILE = "data/holdings.json"

def load_holdings() -> Dict[str, float]:
    """Load current holdings from JSON file."""
    if os.path.exists(HOLDINGS_FILE):
        try:
            with open(HOLDINGS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            LOG.error(f"Error loading holdings: {e}")
    return {}

def save_holdings(holdings_dict: Dict[str, float]) -> str:
    """Save holdings to JSON file."""
    try:
        os.makedirs(os.path.dirname(HOLDINGS_FILE), exist_ok=True)
        with open(HOLDINGS_FILE, 'w') as f:
            json.dump(holdings_dict, f, indent=4)
        return "Holdings saved successfully!"
    except Exception as e:
        LOG.error(f"Error saving holdings: {e}")
        return f"Error saving holdings: {e}"

def get_strategy_weights(strategy_name: str) -> Dict[str, float]:
    """Get strategy weights based on name."""
    if strategy_name == "DynamicAllocationStrategy":
        # Calculate fresh weights for dynamic strategy
        try:
            from src.strategies.legacy import get_target_weights_and_metrics_standalone
            weights, _ = get_target_weights_and_metrics_standalone()
            return weights
        except Exception as e:
            LOG.error(f"Error calculating dynamic strategy weights: {e}")
            return {}
    
    # For static strategies, get weights from the strategy class
    strategy_class = strategy_registry.get(strategy_name)
    if strategy_class:
        try:
            temp_instance = strategy_class()
            weights = temp_instance.get_target_weights()
            return weights
        except Exception as e:
            LOG.error(f"Error getting strategy weights: {e}")
    
    return {}

def run_backtest_streamlit(strategy_choice: str, 
                         rebalance_days: int, 
                         threshold: float, 
                         initial_capital: float, 
                         commission: float, 
                         start_date: str) -> Dict:
    """Run backtest and return results."""
    # Update dynamic strategy parameters
    DYNAMIC_STRATEGY_PARAMS['rebalance_days'] = rebalance_days
    DYNAMIC_STRATEGY_PARAMS['threshold'] = threshold
    
    strategy_class = strategy_registry.get(strategy_choice)
    if not strategy_class:
        return {"error": f"Strategy '{strategy_choice}' not found"}
    
    try:
        results = run_backtest(strategy_class, strategy_choice, start_date)
        return results if results else {"error": "Backtest failed"}
    except Exception as e:
        LOG.error(f"Backtest error: {e}")
        return {"error": f"Backtest failed: {e}"}

def get_available_data() -> pd.DataFrame:
    """Get information about available data files."""
    data_files = []
    for data_type in ["price", "pe", "yield"]:
        data_dir = os.path.join("data", "raw", data_type)
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.endswith(".csv"):
                    try:
                        asset_name = file.split('_')[0]
                        df = pd.read_csv(os.path.join(data_dir, file))
                        start_date, end_date = get_data_range_info(df)
                        data_files.append({
                            "Type": data_type.upper(),
                            "Asset": asset_name,
                            "Start Date": start_date.strftime('%Y-%m-%d') if start_date else "N/A",
                            "End Date": end_date.strftime('%Y-%m-%d') if end_date else "N/A",
                            "Records": len(df)
                        })
                    except Exception as e:
                        LOG.error(f"Error reading data file {file}: {e}")
    return pd.DataFrame(data_files) if data_files else pd.DataFrame()

def load_data_for_visualization() -> Dict[str, pd.DataFrame]:
    """Load data for visualization."""
    data_dict = {}
    for data_type in ["price", "pe", "yield"]:
        data_dir = os.path.join("data", "raw", data_type)
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.endswith(".csv"):
                    try:
                        asset_name = file.split('_')[0]
                        df = pd.read_csv(os.path.join(data_dir, file))
                        
                        # Standardize column names
                        if 'date' in df.columns:
                            df['Date'] = pd.to_datetime(df['date'])
                        elif len(df.columns) > 0:
                            df['Date'] = pd.to_datetime(df.iloc[:, 0])
                        
                        if 'close' in df.columns:
                            df['Value'] = df['close']
                        elif 'pe' in df.columns:
                            df['Value'] = df['pe']
                        elif 'yield' in df.columns:
                            df['Value'] = df['yield']
                        elif len(df.columns) > 1:
                            df['Value'] = df.iloc[:, -1]
                        
                        data_dict[f"{asset_name} ({data_type.upper()})"] = df[['Date', 'Value']].dropna()
                    except Exception as e:
                        LOG.error(f"Error loading data file {file}: {e}")
    return data_dict

# Main Streamlit App
def main():
    st.title("💰 Personal Finance Agent")
    st.markdown("Professional quantitative investment management system")
    
    # Tab navigation
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Backtest", "📊 Portfolio", "📈 Data Explorer", "⚙️ System"])
    
    with tab1:
        show_backtest_page()
    
    with tab2:
        show_portfolio_page()
    
    with tab3:
        show_data_explorer_page()
    
    with tab4:
        show_system_page()

def show_backtest_page():
    """Display the backtesting interface."""
    st.header("🎯 Strategy Backtesting")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Strategy Configuration")
        
        # Strategy selection
        strategies = strategy_registry.list_strategies()
        strategy_names = list(strategies.keys())
        
        strategy_choice = st.selectbox(
            "Select Strategy:",
            options=strategy_names,
            index=0 if strategy_names else None
        )
        
        if strategy_choice:
            # Display strategy weights
            weights = get_strategy_weights(strategy_choice)
            if weights:
                display_strategy_weights_table(weights, strategy_choice)
        
        st.subheader("Parameters")
        
        # Extended rebalancing frequency: 0-360 days
        rebalance_days = st.slider(
            "Rebalancing Frequency (days):",
            min_value=0,
            max_value=360,
            value=DYNAMIC_STRATEGY_PARAMS.get('rebalance_days', 60),
            step=1,
            help="0 = Daily rebalancing, 360 = Annual rebalancing"
        )
        
        threshold = st.slider(
            "Rebalancing Threshold:",
            min_value=0.01,
            max_value=0.20,
            value=DYNAMIC_STRATEGY_PARAMS.get('threshold', 0.05),
            step=0.01,
            format="%.2f",
            help="Minimum deviation to trigger rebalancing"
        )
        
        st.subheader("Backtest Settings")
        
        initial_capital = st.number_input(
            "Initial Capital ($):",
            min_value=1000.0,
            max_value=10000000.0,
            value=float(INITIAL_CAPITAL),
            step=1000.0,
            format="%.0f"
        )
        
        commission = st.number_input(
            "Commission Rate:",
            min_value=0.0,
            max_value=0.01,
            value=float(COMMISSION),
            step=0.0001,
            format="%.4f"
        )
        
        start_date = st.date_input(
            "Backtest Start Date:",
            value=date(2020, 1, 1),
            min_value=date(2010, 1, 1),
            max_value=date.today()
        )
        
        run_button = st.button("🚀 Run Backtest", type="primary", use_container_width=True)
    
    with col2:
        st.subheader("Results")
        
        if run_button and strategy_choice:
            with st.spinner("Running backtest..."):
                results = run_backtest_streamlit(
                    strategy_choice=strategy_choice,
                    rebalance_days=rebalance_days,
                    threshold=threshold,
                    initial_capital=initial_capital,
                    commission=commission,
                    start_date=start_date.strftime("%Y-%m-%d")
                )
            
            if "error" in results:
                st.error(results["error"])
            else:
                # Display comprehensive metrics dashboard
                create_metrics_dashboard(results)
                
                # Display portfolio performance chart
                if 'portfolio_dates' in results and 'portfolio_values' in results:
                    portfolio_df = pd.DataFrame({
                        "Date": pd.to_datetime(results['portfolio_dates']),
                        "Value": [float(v) for v in results['portfolio_values']]
                    })
                    display_portfolio_performance(portfolio_df, f"{strategy_choice} Performance")
        else:
            st.info("Configure your strategy parameters and click 'Run Backtest' to see results.")

def show_portfolio_page():
    """Display portfolio management interface."""
    st.header("📊 Portfolio Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Current Holdings")
        
        # Load current holdings
        holdings = load_holdings()
        
        if holdings:
            holdings_data = []
            for asset, weight in holdings.items():
                display_info = ASSET_DISPLAY_INFO.get(asset, {})
                asset_name = display_info.get('name', asset)
                region = display_info.get('region', 'N/A')
                tradable_us = display_info.get('tradable_us', 'N/A')
                
                holdings_data.append({
                    'Asset': asset_name,
                    'Region': region,
                    'Tradable (US)': tradable_us,
                    'Weight': f"{weight:.2%}"
                })
            
            holdings_df = pd.DataFrame(holdings_data)
            st.dataframe(holdings_df, use_container_width=True, hide_index=True)
            
            # Show allocation chart
            display_asset_allocation(holdings, "Current Portfolio Allocation")
        else:
            st.info("No current holdings found. Add your holdings below.")
        
        st.subheader("Edit Holdings")
        
        # Holdings editor
        with st.form("holdings_form"):
            st.write("Add or update your current portfolio weights:")
            
            asset_options = list(ASSET_DISPLAY_INFO.keys())
            selected_asset = st.selectbox("Select Asset:", asset_options)
            
            current_weight = holdings.get(selected_asset, 0.0) * 100
            new_weight = st.number_input(
                f"Weight for {ASSET_DISPLAY_INFO[selected_asset]['name']} (%):",
                min_value=0.0,
                max_value=100.0,
                value=current_weight,
                step=0.1,
                format="%.1f"
            )
            
            submitted = st.form_submit_button("Update Holding")
            
            if submitted:
                holdings[selected_asset] = new_weight / 100.0
                save_message = save_holdings(holdings)
                st.success(save_message)
                st.experimental_rerun()
    
    with col2:
        st.subheader("Strategy Comparison")
        
        # Strategy selection for comparison
        strategies = strategy_registry.list_strategies()
        selected_strategy = st.selectbox(
            "Compare with Strategy:",
            options=list(strategies.keys()),
            key="portfolio_strategy_select"
        )
        
        if selected_strategy:
            strategy_weights = get_strategy_weights(selected_strategy)
            
            if strategy_weights:
                # Create comparison data
                comparison_data = []
                all_assets = sorted(list(set(strategy_weights.keys()) | set(holdings.keys())))
                
                for asset in all_assets:
                    target = strategy_weights.get(asset, 0)
                    current = holdings.get(asset, 0)
                    diff = target - current
                    
                    display_info = ASSET_DISPLAY_INFO.get(asset, {})
                    asset_name = display_info.get('name', asset)
                    
                    comparison_data.append({
                        "Asset": asset_name,
                        "Target Weight": f"{target:.2%}",
                        "Current Weight": f"{current:.2%}",
                        "Difference": f"{diff:.2%}"
                    })
                
                comparison_df = pd.DataFrame(comparison_data)
                display_portfolio_comparison(comparison_df)
            else:
                st.warning(f"Could not load weights for {selected_strategy}")

def show_data_explorer_page():
    """Display data exploration and visualization interface."""
    st.header("📈 Data Explorer")
    
    # Load available data
    available_data_df = get_available_data()
    
    if not available_data_df.empty:
        st.subheader("Available Data Overview")
        st.dataframe(available_data_df, use_container_width=True, hide_index=True)
        
        # Load data for visualization
        data_dict = load_data_for_visualization()
        
        if data_dict:
            # Interactive data explorer
            display_data_explorer(data_dict)
        else:
            st.warning("No data available for visualization")
    else:
        st.warning("No data files found. Please download data first.")
    
    # Data management section
    st.subheader("Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Download All Data**")
        if st.button("🔄 Refresh All Data", type="primary"):
            with st.spinner("Downloading data..."):
                try:
                    download_data_main(refresh=True)
                    st.success("Data download completed!")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Data download failed: {e}")
    
    with col2:
        st.write("**Download New Asset**")
        new_ticker = st.text_input("Enter ticker symbol:")
        if st.button("📥 Download New Ticker") and new_ticker:
            from src.data_center.download import download_yfinance_data, download_akshare_index
            
            with st.spinner(f"Downloading {new_ticker}..."):
                try:
                    # Try yfinance first
                    filepath, _, _ = download_yfinance_data(new_ticker, new_ticker)
                    if filepath:
                        st.success(f"Successfully downloaded {new_ticker} from yfinance.")
                    else:
                        # Try akshare
                        filepath, _, _ = download_akshare_index(new_ticker, new_ticker)
                        if filepath:
                            st.success(f"Successfully downloaded {new_ticker} from akshare.")
                        else:
                            st.error(f"Failed to download {new_ticker} from both sources.")
                except Exception as e:
                    st.error(f"Error downloading {new_ticker}: {e}")

def show_system_page():
    """Display system information and settings."""
    st.header("⚙️ System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("System Status")
        
        # Check data availability
        data_df = get_available_data()
        
        if not data_df.empty:
            total_files = len(data_df)
            price_files = len(data_df[data_df['Type'] == 'PRICE'])
            pe_files = len(data_df[data_df['Type'] == 'PE'])
            yield_files = len(data_df[data_df['Type'] == 'YIELD'])
            
            st.metric("Total Data Files", total_files)
            st.metric("Price Data Files", price_files)
            st.metric("PE Data Files", pe_files)
            st.metric("Yield Data Files", yield_files)
        else:
            st.warning("No data files found")
        
        # Strategy registry status
        strategies = strategy_registry.list_strategies()
        st.metric("Available Strategies", len(strategies))
        
    with col2:
        st.subheader("Configuration")
        
        st.write("**System Parameters:**")
        st.write(f"- Initial Capital: ${INITIAL_CAPITAL:,}")
        st.write(f"- Commission Rate: {COMMISSION:.4f}")
        st.write(f"- Default Rebalance Days: {DYNAMIC_STRATEGY_PARAMS['rebalance_days']}")
        st.write(f"- Default Threshold: {DYNAMIC_STRATEGY_PARAMS['threshold']:.2%}")
        
        st.write("**Available Assets:**")
        st.write(f"- Tradable Assets: {len(TRADABLE_ASSETS)}")
        st.write(f"- Display Info: {len(ASSET_DISPLAY_INFO)}")

if __name__ == "__main__":
    main()