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
    """Load data for visualization with enhanced PE data handling."""
    data_dict = {}
    for data_type in ["price", "pe", "yield"]:
        data_dir = os.path.join("data", "raw", data_type)
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.endswith(".csv"):
                    try:
                        asset_name = file.split('_')[0]
                        df = pd.read_csv(os.path.join(data_dir, file))
                        
                        if df.empty:
                            LOG.warning(f"Empty data file: {file}")
                            continue
                        
                        # Enhanced date parsing
                        date_col = None
                        if 'date' in df.columns:
                            date_col = 'date'
                        elif 'Date' in df.columns:
                            date_col = 'Date'
                        elif len(df.columns) > 0:
                            date_col = df.columns[0]
                        
                        if date_col:
                            try:
                                df['Date'] = pd.to_datetime(df[date_col], errors='coerce')
                                # Remove invalid dates
                                df = df.dropna(subset=['Date'])
                            except Exception as e:
                                LOG.warning(f"Date parsing error in {file}: {e}")
                                continue
                        
                        # Enhanced value column detection
                        value_col = None
                        if data_type == "price":
                            if 'close' in df.columns:
                                value_col = 'close'
                            elif '收盘' in df.columns:
                                value_col = '收盘'
                        elif data_type == "pe":
                            if 'pe' in df.columns:
                                value_col = 'pe'
                            elif 'PE' in df.columns:
                                value_col = 'PE'
                            elif 'pe_ratio' in df.columns:
                                value_col = 'pe_ratio'
                        elif data_type == "yield":
                            if 'yield' in df.columns:
                                value_col = 'yield'
                            elif 'Yield' in df.columns:
                                value_col = 'Yield'
                        
                        # Fallback to last column if no specific column found
                        if not value_col and len(df.columns) > 1:
                            value_col = df.columns[-1]
                        
                        if value_col and value_col in df.columns:
                            df['Value'] = pd.to_numeric(df[value_col], errors='coerce')
                            # Remove invalid values
                            df = df.dropna(subset=['Value'])
                            
                            # Filter out unrealistic PE values for PE data
                            if data_type == "pe":
                                df = df[(df['Value'] > 0) & (df['Value'] < 100)]  # Reasonable PE range
                            
                            if not df.empty:
                                data_dict[f"{asset_name} ({data_type.upper()})"] = df[['Date', 'Value']].copy()
                            else:
                                LOG.warning(f"No valid data after cleaning: {file}")
                        else:
                            LOG.warning(f"Could not identify value column in {file}")
                            
                    except Exception as e:
                        LOG.error(f"Error loading data file {file}: {e}")
    return data_dict

def create_detailed_metrics_table(results: Dict):
    """Create a detailed metrics table with rounded values."""
    if not results:
        st.warning("No metrics available")
        return
    
    # Format metrics with appropriate rounding
    metrics_data = []
    for k, v in results.items():
        if k not in ['portfolio_dates', 'portfolio_values']:
            metric_name = k.replace("_", " ").title()
            
            # Apply appropriate rounding based on metric type
            if isinstance(v, (int, float)):
                if "return" in k.lower() or "drawdown" in k.lower():
                    formatted_value = f"{float(v):.2f}%"
                elif "ratio" in k.lower():
                    formatted_value = f"{float(v):.3f}"
                elif "value" in k.lower() or "capital" in k.lower():
                    formatted_value = f"${float(v):,.2f}"
                else:
                    formatted_value = f"{float(v):.2f}"
            else:
                formatted_value = str(v)
                
            metrics_data.append({
                "Metric": metric_name,
                "Value": formatted_value
            })
    
    if metrics_data:
        metrics_df = pd.DataFrame(metrics_data)
        st.dataframe(metrics_df, use_container_width=True, hide_index=True)

def balance_portfolio_weights(holdings: Dict[str, float], updated_asset: str, new_weight: float) -> Dict[str, float]:
    """Balance portfolio weights to ensure they sum to 100%."""
    # Set the new weight for the updated asset
    holdings[updated_asset] = new_weight
    
    # Calculate current total
    total_weight = sum(holdings.values())
    
    if abs(total_weight - 1.0) < 0.001:  # Already balanced
        return holdings
    
    # If total exceeds 100%, adjust other assets proportionally
    if total_weight > 1.0:
        excess = total_weight - 1.0
        other_assets = {k: v for k, v in holdings.items() if k != updated_asset}
        
        if other_assets:
            # Reduce other assets proportionally
            other_total = sum(other_assets.values())
            if other_total > 0:
                reduction_factor = max(0, (other_total - excess) / other_total)
                for asset in other_assets:
                    holdings[asset] = max(0, holdings[asset] * reduction_factor)
        else:
            # If only one asset, cap it at 100%
            holdings[updated_asset] = 1.0
    
    # If total is less than 100%, add to the largest existing position
    elif total_weight < 1.0:
        deficit = 1.0 - total_weight
        if holdings:
            # Find largest position (excluding the just-updated asset)
            other_assets = {k: v for k, v in holdings.items() if k != updated_asset}
            if other_assets:
                largest_asset = max(other_assets.keys(), key=lambda k: other_assets[k])
                holdings[largest_asset] = min(1.0, holdings[largest_asset] + deficit)
            else:
                holdings[updated_asset] = 1.0
    
    return holdings

def update_system_configuration(capital: float, commission: float, rebalance_days: int, 
                               threshold: float, max_position: float, max_sector: float) -> bool:
    """Update system configuration parameters."""
    global INITIAL_CAPITAL, COMMISSION, DYNAMIC_STRATEGY_PARAMS
    
    try:
        config_path = "config/system.py"
        
        # Read current config
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Update values using string replacement
        content = content.replace(f"INITIAL_CAPITAL = {INITIAL_CAPITAL}", f"INITIAL_CAPITAL = {int(capital)}")
        content = content.replace(f"COMMISSION = {COMMISSION}", f"COMMISSION = {commission}")
        content = content.replace(f"'rebalance_days': {DYNAMIC_STRATEGY_PARAMS['rebalance_days']}", 
                                f"'rebalance_days': {rebalance_days}")
        content = content.replace(f"'threshold': {DYNAMIC_STRATEGY_PARAMS['threshold']}", 
                                f"'threshold': {threshold}")
        content = content.replace("MAX_POSITION_SIZE = 0.25", f"MAX_POSITION_SIZE = {max_position}")
        content = content.replace("MAX_SECTOR_ALLOCATION = 0.40", f"MAX_SECTOR_ALLOCATION = {max_sector}")
        
        # Write updated config
        with open(config_path, 'w') as f:
            f.write(content)
        
        # Update global variables
        INITIAL_CAPITAL = int(capital)
        COMMISSION = commission
        DYNAMIC_STRATEGY_PARAMS['rebalance_days'] = rebalance_days
        DYNAMIC_STRATEGY_PARAMS['threshold'] = threshold
        
        LOG.info(f"Configuration updated: Capital=${capital}, Commission={commission}")
        return True
        
    except Exception as e:
        LOG.error(f"Failed to update configuration: {e}")
        return False

def reset_system_configuration() -> bool:
    """Reset system configuration to defaults."""
    global INITIAL_CAPITAL, COMMISSION, DYNAMIC_STRATEGY_PARAMS
    
    try:
        # Default values
        default_config = """\"\"\"
System Configuration
Core system parameters for backtesting and trading.
\"\"\"

# -- Backtesting Configuration --
INITIAL_CAPITAL = 1000000
COMMISSION = 0.0

# -- Strategy Configuration --
# Parameters for the DynamicAllocationStrategy
DYNAMIC_STRATEGY_PARAMS = {
    'rebalance_days': 360,
    'threshold': 0.05,
}

# -- System Configuration --
# Data refresh settings
DATA_REFRESH_INTERVAL_HOURS = 24
CACHE_EXPIRY_DAYS = 7

# Performance analysis settings
PERFORMANCE_LOOKBACK_YEARS = 10
ROLLING_WINDOW_DAYS = [252, 504, 1260]  # 1Y, 2Y, 5Y

# Risk management
MAX_POSITION_SIZE = 0.25  # 25% max allocation per asset
MAX_SECTOR_ALLOCATION = 0.40  # 40% max allocation per sector
REBALANCE_THRESHOLD = 0.05  # 5% deviation triggers rebalance

# Logging configuration
LOG_LEVEL = "INFO"
LOG_ROTATION = "1 week"
LOG_RETENTION = "4 weeks"
"""
        
        config_path = "config/system.py"
        with open(config_path, 'w') as f:
            f.write(default_config)
        
        # Update global variables
        INITIAL_CAPITAL = 1000000
        COMMISSION = 0.0
        DYNAMIC_STRATEGY_PARAMS['rebalance_days'] = 360
        DYNAMIC_STRATEGY_PARAMS['threshold'] = 0.05
        
        LOG.info("Configuration reset to defaults")
        return True
        
    except Exception as e:
        LOG.error(f"Failed to reset configuration: {e}")
        return False

# Main Streamlit App
def main():
    st.title("💰 Personal Finance Agent")
    st.markdown("Professional quantitative investment management system")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page_names = ["🎯 Backtest", "📊 Portfolio", "📈 Data Explorer", "⚙️ System"]
    page = st.sidebar.radio("Select Page:", page_names, index=0)
    
    # Display selected page
    if page == "🎯 Backtest":
        show_backtest_page()
    elif page == "📊 Portfolio":
        show_portfolio_page()
    elif page == "📈 Data Explorer":
        show_data_explorer_page()
    elif page == "⚙️ System":
        show_system_page()

def show_backtest_page():
    """Display the backtesting interface."""
    st.header("🎯 Strategy Backtesting")
    
    # Configuration section: Three columns for better layout
    config_col1, config_col2, config_col3 = st.columns([1, 1, 1.2])
    
    with config_col1:
        st.subheader("Strategy Configuration")
        
        # Strategy selection
        strategies = strategy_registry.list_strategies()
        strategy_names = list(strategies.keys())
        
        strategy_choice = st.selectbox(
            "Select Strategy:",
            options=strategy_names,
            index=0 if strategy_names else None
        )
        
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
    
    with config_col2:
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
    
    with config_col3:
        if strategy_choice:
            st.subheader(f"{strategy_choice} - Asset Weights")
            # Display strategy weights
            weights = get_strategy_weights(strategy_choice)
            if weights:
                display_strategy_weights_table(weights, strategy_choice)
    
    # Separator for visual clarity
    st.divider()
    
    # Results section: Full width for better chart display
    if run_button and strategy_choice:
        st.subheader("Results & Performance Dashboard")
        
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
            # Portfolio performance chart gets full width for better visibility
            if 'portfolio_dates' in results and 'portfolio_values' in results:
                portfolio_df = pd.DataFrame({
                    "Date": pd.to_datetime(results['portfolio_dates']),
                    "Value": [float(v) for v in results['portfolio_values']]
                })
                display_portfolio_performance(portfolio_df, f"{strategy_choice} Performance")
            
            # Performance metrics in a clean row layout
            st.subheader("Performance Metrics")
            
            metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
            
            with metrics_col1:
                st.metric(
                    "Final Value",
                    f"${results.get('final_value', 0):,.0f}",
                    delta=f"{results.get('total_return', 0):.1f}%"
                )
            
            with metrics_col2:
                st.metric(
                    "Ann. Return",
                    f"{results.get('annualized_return', 0):.1f}%"
                )
            
            with metrics_col3:
                st.metric(
                    "Max Drawdown",
                    f"{results.get('max_drawdown', 0):.1f}%",
                    delta=f"{results.get('max_drawdown', 0):.1f}%",
                    delta_color="inverse"
                )
            
            with metrics_col4:
                st.metric(
                    "Sharpe Ratio",
                    f"{results.get('sharpe_ratio', 0):.2f}"
                )
            
            # Display detailed metrics in expandable section
            with st.expander("Detailed Performance Analysis", expanded=False):
                create_detailed_metrics_table(results)
    else:
        st.info("💡 Configure your strategy parameters above and click 'Run Backtest' to see performance results and visualization.")

def show_portfolio_page():
    """Display portfolio management interface."""
    st.header("📊 Portfolio Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Current Holdings")
        
        # Load current holdings
        holdings = load_holdings()
        
        # Calculate total weight for validation
        total_weight = sum(holdings.values()) if holdings else 0
        
        # Display weight validation status
        if holdings:
            if abs(total_weight - 1.0) < 0.001:  # Within 0.1%
                st.success(f"✅ Portfolio weights total: {total_weight:.1%}")
            else:
                st.warning(f"⚠️ Portfolio weights total: {total_weight:.1%} (Should be 100%)")
        
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
                # Update holdings with automatic balancing
                updated_holdings = balance_portfolio_weights(holdings.copy(), selected_asset, new_weight / 100.0)
                save_message = save_holdings(updated_holdings)
                st.success(save_message)
                st.experimental_rerun()
    
    with col2:
        st.subheader("Strategy Gap Analysis")
        
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
                st.write(f"**Gap Analysis vs {selected_strategy}:**")
                
                # Create comparison data with enhanced formatting
                comparison_data = []
                all_assets = sorted(list(set(strategy_weights.keys()) | set(holdings.keys())))
                
                for asset in all_assets:
                    target = strategy_weights.get(asset, 0)
                    current = holdings.get(asset, 0)
                    diff = target - current
                    
                    display_info = ASSET_DISPLAY_INFO.get(asset, {})
                    asset_name = display_info.get('name', asset)
                    
                    # Color coding for differences
                    if abs(diff) < 0.01:  # Within 1%
                        status = "✅ Balanced"
                    elif diff > 0:
                        status = f"⬆️ Under-weighted ({diff:.1%})"
                    else:
                        status = f"⬇️ Over-weighted ({abs(diff):.1%})"
                    
                    comparison_data.append({
                        "Asset": asset_name,
                        "Target": f"{target:.1%}",
                        "Current": f"{current:.1%}",
                        "Gap": f"{diff:+.1%}",
                        "Status": status
                    })
                
                comparison_df = pd.DataFrame(comparison_data)
                st.dataframe(comparison_df, use_container_width=True, hide_index=True)
                
                # Show visual comparison chart
                display_portfolio_comparison(comparison_df)
                
                # Add rebalancing suggestions
                large_gaps = [row for _, row in comparison_df.iterrows() 
                             if abs(float(row['Gap'].replace('%', '').replace('+', ''))) > 5]
                
                if large_gaps:
                    st.subheader("💡 Rebalancing Suggestions")
                    for gap in large_gaps:
                        gap_value = float(gap['Gap'].replace('%', '').replace('+', ''))
                        if gap_value > 0:
                            st.info(f"Consider increasing {gap['Asset']} by {abs(gap_value):.1f}%")
                        else:
                            st.info(f"Consider decreasing {gap['Asset']} by {abs(gap_value):.1f}%")
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
    st.header("⚙️ System Configuration")
    
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
        
        st.subheader("Available Assets")
        st.write(f"- Tradable Assets: {len(TRADABLE_ASSETS)}")
        st.write(f"- Display Info: {len(ASSET_DISPLAY_INFO)}")
        
    with col2:
        st.subheader("Editable Configuration")
        
        # Configuration editor
        with st.form("config_form"):
            st.write("**Backtesting Parameters:**")
            
            new_capital = st.number_input(
                "Initial Capital ($):",
                min_value=10000.0,
                max_value=100000000.0,
                value=float(INITIAL_CAPITAL),
                step=10000.0,
                format="%.0f"
            )
            
            new_commission = st.number_input(
                "Commission Rate:",
                min_value=0.0,
                max_value=0.01,
                value=float(COMMISSION),
                step=0.0001,
                format="%.4f"
            )
            
            st.write("**Strategy Parameters:**")
            
            new_rebalance_days = st.number_input(
                "Default Rebalance Days:",
                min_value=1,
                max_value=365,
                value=int(DYNAMIC_STRATEGY_PARAMS['rebalance_days']),
                step=1
            )
            
            new_threshold = st.slider(
                "Default Rebalancing Threshold:",
                min_value=0.01,
                max_value=0.20,
                value=float(DYNAMIC_STRATEGY_PARAMS['threshold']),
                step=0.01,
                format="%.2f"
            )
            
            st.write("**Risk Management:**")
            
            new_max_position = st.slider(
                "Max Position Size (% per asset):",
                min_value=0.05,
                max_value=1.0,
                value=0.25,  # Default from config
                step=0.05,
                format="%.2f"
            )
            
            new_max_sector = st.slider(
                "Max Sector Allocation (%):",
                min_value=0.10,
                max_value=1.0,
                value=0.40,  # Default from config
                step=0.05,
                format="%.2f"
            )
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                update_config = st.form_submit_button("💾 Update Configuration", type="primary")
            
            with col_b:
                reset_config = st.form_submit_button("🔄 Reset to Defaults")
            
            if update_config:
                success = update_system_configuration(
                    new_capital, new_commission, new_rebalance_days,
                    new_threshold, new_max_position, new_max_sector
                )
                if success:
                    st.success("Configuration updated successfully!")
                    st.experimental_rerun()
                else:
                    st.error("Failed to update configuration")
            
            if reset_config:
                success = reset_system_configuration()
                if success:
                    st.success("Configuration reset to defaults!")
                    st.experimental_rerun()
                else:
                    st.error("Failed to reset configuration")

if __name__ == "__main__":
    main()