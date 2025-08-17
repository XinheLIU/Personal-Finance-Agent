"""
Streamlit Web Application for Personal Finance Agent.
Replacing Gradio with Streamlit for better visualization and user experience.
"""

import streamlit as st
import pandas as pd
import json
import os
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from typing import Dict, Optional, Any

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
from src.data_center.data_processor import (
    get_processing_status,
    process_all_strategies,
    cleanup_processed_data
)
from src.app_logger import LOG
from src.visualization.charts import (
    display_portfolio_performance,
    display_asset_allocation,
    display_portfolio_comparison,
    display_backtest_summary,
    display_data_explorer,
    display_strategy_weights_table,
    create_metrics_dashboard,
    display_attribution_analysis
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
    """Get target weights for a strategy without running full backtest."""
    strategy_class = strategy_registry.get(strategy_name)
    if not strategy_class:
        return {}
    
    try:
        # Check if it's a static strategy
        if hasattr(strategy_class, 'get_static_target_weights'):
            weights = strategy_class.get_static_target_weights()
            return weights
        
        # For dynamic strategies, try to get weights using standalone function
        if strategy_name == "DynamicAllocationStrategy":
            try:
                from src.strategies.classic import get_target_weights_and_metrics_standalone
                weights, _ = get_target_weights_and_metrics_standalone()
                return weights
            except Exception as e:
                LOG.warning(f"Could not calculate dynamic weights: {e}")
                return {}
        
        # For other dynamic strategies, return empty dict (weights depend on market data)
        strategy_type = strategy_class.get_strategy_type()
        if strategy_type == "dynamic":
            return {}
        
        # Fallback - shouldn't happen with proper implementation
        return {}
    except Exception as e:
        LOG.error(f"Error getting strategy weights for {strategy_name}: {e}")
        return {}

def run_backtest_streamlit(strategy_choice: str, 
                         rebalance_days: int, 
                         threshold: float, 
                         initial_capital: float, 
                         commission: float, 
                         start_date: str,
                         enable_attribution: bool = False) -> Dict:
    """Run backtest and return results."""
    # Update dynamic strategy parameters
    DYNAMIC_STRATEGY_PARAMS['rebalance_days'] = rebalance_days
    DYNAMIC_STRATEGY_PARAMS['threshold'] = threshold
    
    strategy_class = strategy_registry.get(strategy_choice)
    if not strategy_class:
        return {"error": f"Strategy '{strategy_choice}' not found"}
    
    try:
        # Pass initial capital, commission, attribution flag, and strategy params through to the runner
        results = run_backtest(
            strategy_class,
            strategy_choice,
            start_date=start_date,
            initial_capital=initial_capital,
            commission=commission,
            enable_attribution=enable_attribution,
            rebalance_days=rebalance_days,
            threshold=threshold
        )
        return results if results else {"error": "Backtest failed"}
    except Exception as e:
        LOG.error(f"Backtest error: {e}")
        return {"error": f"Backtest failed: {e}"}

def get_available_data() -> pd.DataFrame:
    """Get information about available data files using singleton storage system."""
    data_files = []
    
    # Import here to avoid circular imports
    from config.assets import ASSETS, PE_ASSETS
    
    # Check price data (singleton files)
    price_dir = os.path.join("data", "raw", "price")
    if os.path.exists(price_dir):
        for asset_name in ASSETS.keys():
            singleton_file = os.path.join(price_dir, f"{asset_name}_price.csv")
            if os.path.exists(singleton_file):
                try:
                    df = pd.read_csv(singleton_file)
                    start_date, end_date = get_data_range_info(df)
                    # Compute freshness
                    days_since_update = None
                    stale_flag = "Unknown"
                    if end_date is not None:
                        try:
                            days_since_update = (date.today() - end_date.date()).days
                            stale_flag = "Yes" if days_since_update is not None and days_since_update > 30 else "No"
                        except Exception:
                            pass
                    data_files.append({
                        "Type": "PRICE",
                        "Asset": asset_name,
                        "Start Date": start_date.strftime('%Y-%m-%d') if start_date else "N/A",
                        "End Date": end_date.strftime('%Y-%m-%d') if end_date else "N/A",
                        "Records": len(df),
                        "Last Updated (days)": days_since_update if days_since_update is not None else "N/A",
                        "Stale (>30d)": stale_flag
                    })
                except Exception as e:
                    LOG.error(f"Error reading price data file {singleton_file}: {e}")
    
    # Check PE data (singleton files + manual folder)
    pe_dir = os.path.join("data", "raw", "pe")
    if os.path.exists(pe_dir):
        for asset_name in PE_ASSETS.keys():
            # Check singleton file first, then manual folder
            singleton_file = os.path.join(pe_dir, f"{asset_name}_pe.csv")
            manual_file = os.path.join(pe_dir, "manual", f"{asset_name}_pe.csv")
            
            pe_file = None
            data_source = "Auto"
            if os.path.exists(singleton_file):
                pe_file = singleton_file
                data_source = "Auto"
            elif os.path.exists(manual_file):
                pe_file = manual_file
                data_source = "Manual"
            
            if pe_file:
                try:
                    df = pd.read_csv(pe_file)
                    start_date, end_date = get_data_range_info(df)
                    # Compute freshness
                    days_since_update = None
                    stale_flag = "Unknown"
                    if end_date is not None:
                        try:
                            days_since_update = (date.today() - end_date.date()).days
                            stale_flag = "Yes" if days_since_update is not None and days_since_update > 30 else "No"
                        except Exception:
                            pass
                    data_files.append({
                        "Type": "PE",
                        "Asset": f"{asset_name} ({data_source})",
                        "Start Date": start_date.strftime('%Y-%m-%d') if start_date else "N/A",
                        "End Date": end_date.strftime('%Y-%m-%d') if end_date else "N/A",
                        "Records": len(df),
                        "Last Updated (days)": days_since_update if days_since_update is not None else "N/A",
                        "Stale (>30d)": stale_flag
                    })
                except Exception as e:
                    LOG.error(f"Error reading PE data file {pe_file}: {e}")
    
    # Check yield data (singleton file)
    yield_dir = os.path.join("data", "raw", "yield")
    yield_file = os.path.join(yield_dir, "US10Y_yield.csv")
    if os.path.exists(yield_file):
        try:
            df = pd.read_csv(yield_file)
            start_date, end_date = get_data_range_info(df)
            # Compute freshness
            days_since_update = None
            stale_flag = "Unknown"
            if end_date is not None:
                try:
                    days_since_update = (date.today() - end_date.date()).days
                    stale_flag = "Yes" if days_since_update is not None and days_since_update > 30 else "No"
                except Exception:
                    pass
            data_files.append({
                "Type": "YIELD",
                "Asset": "US10Y",
                "Start Date": start_date.strftime('%Y-%m-%d') if start_date else "N/A",
                "End Date": end_date.strftime('%Y-%m-%d') if end_date else "N/A",
                "Records": len(df),
                "Last Updated (days)": days_since_update if days_since_update is not None else "N/A",
                "Stale (>30d)": stale_flag
            })
        except Exception as e:
            LOG.error(f"Error reading yield data file {yield_file}: {e}")
    
    return pd.DataFrame(data_files) if data_files else pd.DataFrame()

def load_data_for_visualization() -> Dict[str, pd.DataFrame]:
    """Load data for visualization using singleton files with fallback to old naming."""
    data_dict = {}
    
    # Import here to avoid circular imports
    from config.assets import ASSETS, PE_ASSETS
    
    # Load price data using singleton files
    price_dir = os.path.join("data", "raw", "price")
    if os.path.exists(price_dir):
        for asset_name in ASSETS.keys():
            # Try singleton file first
            singleton_file = os.path.join(price_dir, f"{asset_name}_price.csv")
            if os.path.exists(singleton_file):
                try:
                    df = _load_singleton_data_file(singleton_file, "price", asset_name)
                    if df is not None:
                        data_dict[f"{asset_name} (PRICE)"] = df
                except Exception as e:
                    LOG.error(f"Error loading singleton price file {singleton_file}: {e}")
    
    # Load PE data using singleton files (check manual folder too)
    pe_dir = os.path.join("data", "raw", "pe")
    if os.path.exists(pe_dir):
        for asset_name in PE_ASSETS.keys():
            # Try singleton file first, then manual folder
            singleton_file = os.path.join(pe_dir, f"{asset_name}_pe.csv")
            manual_file = os.path.join(pe_dir, "manual", f"{asset_name}_pe.csv")
            
            pe_file = None
            if os.path.exists(singleton_file):
                pe_file = singleton_file
            elif os.path.exists(manual_file):
                pe_file = manual_file
                LOG.info(f"Using manual PE data for {asset_name}")
            
            if pe_file:
                try:
                    df = _load_singleton_data_file(pe_file, "pe", asset_name)
                    if df is not None:
                        data_dict[f"{asset_name} (PE)"] = df
                except Exception as e:
                    LOG.error(f"Error loading PE file {pe_file}: {e}")
    
    # Load yield data using singleton file
    yield_dir = os.path.join("data", "raw", "yield")
    yield_file = os.path.join(yield_dir, "US10Y_yield.csv")
    if os.path.exists(yield_file):
        try:
            df = _load_singleton_data_file(yield_file, "yield", "US10Y")
            if df is not None:
                data_dict["US10Y (YIELD)"] = df
        except Exception as e:
            LOG.error(f"Error loading singleton yield file {yield_file}: {e}")
    
    return data_dict

def _load_singleton_data_file(file_path: str, data_type: str, asset_name: str) -> pd.DataFrame:
    """Load and clean a singleton data file for visualization."""
    try:
        df = pd.read_csv(file_path)
        
        if df.empty:
            LOG.warning(f"Empty data file: {file_path}")
            return None
        
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
                LOG.warning(f"Date parsing error in {file_path}: {e}")
                return None
        
        # Enhanced value column detection
        value_col = None
        if data_type == "price":
            if 'close' in df.columns:
                value_col = 'close'
            elif 'Close' in df.columns:
                value_col = 'Close'
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
            elif 'Close' in df.columns:  # Yield files sometimes use Close column
                value_col = 'Close'
        
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
                return df[['Date', 'Value']].copy()
            else:
                LOG.warning(f"No valid data after cleaning: {file_path}")
                return None
        else:
            LOG.warning(f"Could not identify value column in {file_path}")
            return None
            
    except Exception as e:
        LOG.error(f"Error loading data file {file_path}: {e}")
        return None

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
    
    # Sidebar navigation - Updated with Attribution tab
    st.sidebar.title("Navigation")
    page_names = ["🎯 Backtest", "📊 Attribution", "💼 Portfolio", "📈 Data Explorer", "⚙️ System"]
    page = st.sidebar.radio("Select Page:", page_names, index=0)
    
    # Display selected page
    if page == "🎯 Backtest":
        show_backtest_page()
    elif page == "📊 Attribution":
        show_attribution_page()
    elif page == "💼 Portfolio":
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
        
        # Rebalancing frequency selector with presets and custom option
        preset_label_to_days = {
            "Daily": 0,          # every bar (trading days)
            "Weekly": 5,         # approx. 5 trading days
            "Bi-weekly": 10,     # approx. 10 trading days
            "Monthly": 21,       # approx. 21 trading days
            "Bi-monthly": 42,    # approx. 42 trading days
            "Quarterly": 63,     # approx. 63 trading days
            "Yearly": 252        # approx. 252 trading days
        }

        current_default_days = int(DYNAMIC_STRATEGY_PARAMS.get('rebalance_days', 60))
        default_preset = next((label for label, days in preset_label_to_days.items() if days == current_default_days), "Custom")

        freq_choice = st.selectbox(
            "Rebalancing Frequency:",
            options=list(preset_label_to_days.keys()) + ["Custom"],
            index=(list(preset_label_to_days.keys()) + ["Custom"]).index(default_preset),
            help="Choose a preset (trading-day basis) or select Custom to type an exact number of days. 0 = daily (every bar)."
        )

        if freq_choice == "Custom":
            rebalance_days = st.number_input(
                "Custom Rebalance Days:",
                min_value=0,
                max_value=365,
                value=current_default_days if default_preset == "Custom" else 60,
                step=1,
                help="Number of trading days between rebalances. 0 = daily (every bar)."
            )
        else:
            rebalance_days = preset_label_to_days[freq_choice]
            st.caption(f"Using approximately {rebalance_days} trading days between rebalances.")
        
        # Rebalancing threshold selector with presets and custom option
        preset_label_to_threshold = {
            "1%": 0.01,
            "2%": 0.02,
            "5%": 0.05,
            "10%": 0.10,
            "15%": 0.15,
            "20%": 0.20
        }

        current_default_threshold = float(DYNAMIC_STRATEGY_PARAMS.get('threshold', 0.05))
        default_threshold_preset = next((label for label, val in preset_label_to_threshold.items() if abs(val - current_default_threshold) < 1e-9), "Custom")

        threshold_choice = st.selectbox(
            "Rebalancing Threshold:",
            options=list(preset_label_to_threshold.keys()) + ["Custom"],
            index=(list(preset_label_to_threshold.keys()) + ["Custom"]).index(default_threshold_preset),
            help="Choose deviation from target weights to trigger rebalance, or select Custom to input an exact value."
        )

        if threshold_choice == "Custom":
            threshold = st.number_input(
                "Custom Threshold (0.00 - 1.00):",
                min_value=0.00,
                max_value=1.00,
                value=current_default_threshold if default_threshold_preset == "Custom" else 0.05,
                step=0.01,
                format="%.2f",
                help="Fractional threshold. Example: 0.05 = 5%."
            )
        else:
            threshold = preset_label_to_threshold[threshold_choice]
            st.caption(f"Rebalance when allocation deviates by approximately {threshold*100:.0f}% from target.")
    
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
        
        # Attribution analysis toggle and independent run button
        enable_attribution = st.checkbox(
            "📊 Enable Performance Attribution Analysis",
            value=False,
            help="Analyze how daily/weekly/monthly returns are attributed to individual assets and rebalancing activities"
        )
        
        # Backtest run
        run_button = st.button("🚀 Run Backtest", type="primary", use_container_width=True)
        # Independent attribution run button
        run_attr_button = st.button("🧮 Run Performance Attribution", use_container_width=True)
    
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
    if (run_button or run_attr_button) and strategy_choice:
        st.subheader("Results & Performance Dashboard")
        
        with st.spinner("Running backtest..."):
            results = run_backtest_streamlit(
                strategy_choice=strategy_choice,
                rebalance_days=rebalance_days,
                threshold=threshold,
                initial_capital=initial_capital,
                commission=commission,
                start_date=start_date.strftime("%Y-%m-%d"),
                enable_attribution=(enable_attribution or run_attr_button)
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
                    delta=f"{results.get('total_return', 0) * 100:.1f}%"
                )
            
            with metrics_col2:
                st.metric(
                    "Ann. Return",
                    f"{results.get('annualized_return', 0) * 100:.1f}%"
                )
            
            with metrics_col3:
                st.metric(
                    "Max Drawdown",
                    f"{results.get('max_drawdown', 0) * 100:.1f}%",
                    delta=f"{results.get('max_drawdown', 0) * 100:.1f}%",
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
            
            # Display attribution analysis if enabled and available
            if (enable_attribution or run_attr_button) and 'attribution_analysis' in results:
                st.divider()
                display_attribution_analysis(results['attribution_analysis'], strategy_choice)
            elif (enable_attribution or run_attr_button) and 'attribution_error' in results:
                st.divider()
                st.warning(f"⚠️ Attribution Analysis Failed: {results['attribution_error']}")
            elif (enable_attribution or run_attr_button):
                st.divider()
                st.info("ℹ️ Attribution analysis was enabled but no attribution data was generated. This may happen with insufficient data or strategy configuration issues.")
    else:
        st.info("💡 Configure your strategy parameters above and click 'Run Backtest' to see performance results and visualization.")

def show_attribution_page():
    """Display the performance attribution analysis interface."""
    st.header("📊 Performance Attribution Analysis")
    st.markdown("Analyze how portfolio returns are attributed to individual assets and sectors")
    
    # Configuration section
    config_col1, config_col2, config_col3 = st.columns([1, 1, 1])
    
    with config_col1:
        st.subheader("Strategy Selection")
        
        # Strategy selection
        strategies = strategy_registry.list_strategies()
        strategy_names = list(strategies.keys())
        
        strategy_choice = st.selectbox(
            "Select Strategy:",
            options=strategy_names,
            index=0 if strategy_names else None,
            help="Choose the strategy to analyze for performance attribution"
        )
        
        # Attribution type selection
        attribution_type = st.selectbox(
            "Attribution Method:",
            options=["Asset-Level Attribution", "Sector-Based Attribution"],
            index=0,
            help="Choose between asset-level or sector-based attribution analysis"
        )
    
    with config_col2:
        st.subheader("Period Selection")
        
        # Period preset selection
        period_presets = {
            "Last Week": 7,
            "Last Month": 30,
            "Last 3 Months": 90,
            "Last 6 Months": 180,
            "Last Year": 365,
            "Custom Range": 0
        }
        
        period_choice = st.selectbox(
            "Analysis Period:",
            options=list(period_presets.keys()),
            index=1,  # Default to "Last Month"
            help="Choose a preset period or select Custom Range for specific dates"
        )
        
        # Date range selection
        if period_choice == "Custom Range":
            col_start, col_end = st.columns(2)
            with col_start:
                start_date = st.date_input(
                    "Start Date:",
                    value=date.today() - timedelta(days=30),
                    max_value=date.today()
                )
            with col_end:
                end_date = st.date_input(
                    "End Date:",
                    value=date.today(),
                    max_value=date.today()
                )
        else:
            days_back = period_presets[period_choice]
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)
            st.info(f"Analyzing from {start_date} to {end_date}")
        
        # Attribution frequency
        attribution_frequency = st.selectbox(
            "Attribution Frequency:",
            options=["Daily", "Weekly", "Monthly"],
            index=1,  # Default to Weekly
            help="Choose the frequency for attribution calculations"
        )
    
    with config_col3:
        st.subheader("Analysis Options")
        
        # Benchmark selection for sector attribution
        if attribution_type == "Sector-Based Attribution":
            benchmark_options = ["Balanced Portfolio", "Equal Weight", "60/40 Portfolio"]
            benchmark_choice = st.selectbox(
                "Benchmark:",
                options=benchmark_options,
                index=0,
                help="Choose benchmark for sector attribution comparison"
            )
        
        # Export options
        export_format = st.selectbox(
            "Export Format:",
            options=["CSV", "Excel", "Both"],
            index=2,
            help="Choose format for exporting attribution results"
        )
        
        # Analysis button
        run_attribution = st.button("🔍 Run Attribution Analysis", type="primary", use_container_width=True)
    
    # Results section
    if run_attribution and strategy_choice:
        st.divider()
        st.subheader("Attribution Analysis Results")
        
        # Show loading spinner
        with st.spinner("Running attribution analysis..."):
            try:
                if attribution_type == "Asset-Level Attribution":
                    results = run_asset_attribution_analysis(
                        strategy_choice=strategy_choice,
                        start_date=start_date.strftime("%Y-%m-%d"),
                        end_date=end_date.strftime("%Y-%m-%d"),
                        frequency=attribution_frequency.lower()
                    )
                else:
                    results = run_sector_attribution_analysis(
                        strategy_choice=strategy_choice,
                        start_date=start_date.strftime("%Y-%m-%d"),
                        end_date=end_date.strftime("%Y-%m-%d"),
                        frequency=attribution_frequency.lower(),
                        benchmark=benchmark_choice
                    )
                
                if "error" in results:
                    st.error(f"Attribution analysis failed: {results['error']}")
                else:
                    # Display results based on attribution type
                    if attribution_type == "Asset-Level Attribution":
                        display_asset_attribution_results(results, strategy_choice)
                    else:
                        display_sector_attribution_results(results, strategy_choice)
                        
            except Exception as e:
                st.error(f"An error occurred during attribution analysis: {str(e)}")
                LOG.error(f"Attribution analysis error: {e}")
    
    else:
        # Show informational content when no analysis is running
        st.info("💡 Configure your attribution analysis parameters above and click 'Run Attribution Analysis' to see detailed performance attribution.")
        
        # Educational content about attribution analysis
        with st.expander("📚 About Performance Attribution Analysis", expanded=False):
            st.markdown("""
            **Performance Attribution** decomposes portfolio returns to understand the sources of performance:
            
            **Asset-Level Attribution:**
            - **Asset Contribution**: How much each individual asset contributed to portfolio returns
            - **Rebalancing Impact**: Effect of changing asset allocations over time
            - **Interaction Effects**: Combined impact of price movements and weight changes
            
            **Sector-Based Attribution (Brinson Model):**
            - **Allocation Effect**: Impact of over/under-weighting sectors vs benchmark
            - **Selection Effect**: Impact of asset selection within sectors
            - **Interaction Effect**: Combined allocation and selection impact
            
            **Use Cases:**
            - Identify top performing assets or sectors
            - Understand impact of rebalancing decisions
            - Compare portfolio performance vs benchmarks
            - Optimize future allocation strategies
            """)


def run_asset_attribution_analysis(strategy_choice: str, start_date: str, end_date: str, frequency: str) -> Dict[str, Any]:
    """Run asset-level attribution analysis."""
    try:
        from src.performance.attribution import PerformanceAttributor
        
        attributor = PerformanceAttributor()
        
        # Run attribution analysis
        results = attributor.run_attribution_analysis(
            strategy_name=strategy_choice,
            start_date=start_date,
            end_date=end_date,
            include_weekly=(frequency in ['weekly', 'daily']),
            include_monthly=(frequency == 'monthly')
        )
        
        return results
        
    except Exception as e:
        LOG.error(f"Asset attribution analysis failed: {e}")
        return {"error": str(e)}


def run_sector_attribution_analysis(strategy_choice: str, start_date: str, end_date: str, frequency: str, benchmark: str) -> Dict[str, Any]:
    """Run sector-based attribution analysis."""
    try:
        from src.performance.sector_attribution import SectorAttributor
        
        sector_attributor = SectorAttributor()
        
        # Load portfolio data
        portfolio_weights, asset_returns, benchmark_weights = sector_attributor.load_portfolio_data(
            strategy_name=strategy_choice,
            start_date=start_date,
            end_date=end_date
        )
        
        # Calculate sector attribution
        daily_results = sector_attributor.calculate_sector_attribution(
            portfolio_weights=portfolio_weights,
            asset_returns=asset_returns,
            benchmark_weights=benchmark_weights,
            period='daily'
        )
        
        if not daily_results:
            return {"error": "No attribution results calculated"}
        
        # Aggregate results based on frequency
        if frequency == 'weekly':
            aggregated_results = sector_attributor.aggregate_attribution_results(daily_results, 'weekly')
        elif frequency == 'monthly':
            aggregated_results = sector_attributor.aggregate_attribution_results(daily_results, 'monthly')
        else:
            aggregated_results = daily_results
        
        # Create summary
        summary = sector_attributor.create_attribution_summary(aggregated_results)
        
        # Save results
        saved_files = sector_attributor.save_attribution_results(
            strategy_name=strategy_choice,
            attribution_results=aggregated_results,
            summary=summary
        )
        
        return {
            'attribution_results': aggregated_results,
            'summary': summary,
            'saved_files': saved_files,
            'frequency': frequency,
            'benchmark': benchmark
        }
        
    except Exception as e:
        LOG.error(f"Sector attribution analysis failed: {e}")
        return {"error": str(e)}


def display_asset_attribution_results(results: Dict[str, Any], strategy_name: str):
    """Display asset-level attribution results."""
    st.subheader(f"Asset Attribution Analysis - {strategy_name}")
    
    # Use existing attribution display function
    display_attribution_analysis(results, strategy_name)


def display_sector_attribution_results(results: Dict[str, Any], strategy_name: str):
    """Display sector-based attribution results."""
    st.subheader(f"Sector Attribution Analysis - {strategy_name}")
    
    summary = results.get('summary', {})
    attribution_results = results.get('attribution_results', [])
    
    if not summary or 'error' in summary:
        st.error(f"Failed to generate sector attribution summary: {summary.get('error', 'Unknown error')}")
        return
    
    # Summary metrics
    total_effects = summary.get('total_effects', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Excess Return",
            f"{total_effects.get('total_excess_return', 0):.2%}",
            help="Total outperformance vs benchmark"
        )
    
    with col2:
        st.metric(
            "Allocation Effect",
            f"{total_effects.get('total_allocation_effect', 0):.2%}",
            help="Impact of sector over/under-weighting"
        )
    
    with col3:
        st.metric(
            "Selection Effect", 
            f"{total_effects.get('total_selection_effect', 0):.2%}",
            help="Impact of asset selection within sectors"
        )
    
    with col4:
        st.metric(
            "Interaction Effect",
            f"{total_effects.get('total_interaction_effect', 0):.2%}",
            help="Combined allocation and selection impact"
        )
    
    # Sector attribution table (similar to the provided image)
    st.subheader("Sector Attribution Breakdown")
    
    sector_summary = summary.get('sector_summary', {})
    if sector_summary:
        # Create attribution table
        table_data = []
        for sector, data in sector_summary.items():
            table_data.append({
                'Sector': sector,
                'Portfolio Weight': f"{data.get('portfolio_weight', 0):.1%}",
                'Benchmark Weight': f"{data.get('benchmark_weight', 0):.1%}",
                'Portfolio Return': f"{data.get('portfolio_return', 0):.2%}",
                'Benchmark Return': f"{data.get('benchmark_return', 0):.2%}",
                'Allocation Effect': f"{data.get('allocation_effect', 0):.2%}",
                'Selection Effect': f"{data.get('selection_effect', 0):.2%}",
                'Interaction Effect': f"{data.get('interaction_effect', 0):.2%}",
                'Total Effect': f"{data.get('total_effect', 0):.2%}"
            })
        
        attribution_df = pd.DataFrame(table_data)
        st.dataframe(attribution_df, use_container_width=True, hide_index=True)
    
    # Charts
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("Attribution Effects by Sector")
        if sector_summary:
            # Create stacked bar chart of attribution effects
            sectors = list(sector_summary.keys())
            allocation_effects = [sector_summary[s].get('allocation_effect', 0) for s in sectors]
            selection_effects = [sector_summary[s].get('selection_effect', 0) for s in sectors]
            interaction_effects = [sector_summary[s].get('interaction_effect', 0) for s in sectors]
            
            fig = go.Figure(data=[
                go.Bar(name='Allocation Effect', x=sectors, y=allocation_effects, marker_color='lightblue'),
                go.Bar(name='Selection Effect', x=sectors, y=selection_effects, marker_color='orange'),
                go.Bar(name='Interaction Effect', x=sectors, y=interaction_effects, marker_color='lightgreen')
            ])
            
            fig.update_layout(
                title="Attribution Effects Breakdown",
                xaxis_title="Sectors",
                yaxis_title="Attribution Effect",
                barmode='stack',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with chart_col2:
        st.subheader("Top Contributing Sectors")
        top_contributors = summary.get('top_contributors', {})
        if top_contributors:
            contrib_data = []
            for sector, effect in top_contributors.items():
                contrib_data.append({
                    'Sector': sector,
                    'Total Effect': effect
                })
            
            contrib_df = pd.DataFrame(contrib_data)
            
            # Create horizontal bar chart
            fig = go.Figure(go.Bar(
                x=contrib_df['Total Effect'],
                y=contrib_df['Sector'],
                orientation='h',
                marker_color=['green' if x >= 0 else 'red' for x in contrib_df['Total Effect']]
            ))
            
            fig.update_layout(
                title="Top Contributors",
                xaxis_title="Total Attribution Effect",
                yaxis_title="Sectors",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Export section
    st.subheader("📥 Export Attribution Results")
    
    col1, col2, col3 = st.columns(3)
    
    saved_files = results.get('saved_files', {})
    
    with col1:
        if 'detailed_csv' in saved_files:
            try:
                df = pd.DataFrame([
                    {
                        'Date': r.date.strftime('%Y-%m-%d'),
                        'Sector': r.sector,
                        'Portfolio_Weight': r.portfolio_weight,
                        'Benchmark_Weight': r.benchmark_weight,
                        'Allocation_Effect': r.allocation_effect,
                        'Selection_Effect': r.selection_effect,
                        'Total_Effect': r.total_effect
                    }
                    for r in attribution_results
                ])
                
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"{strategy_name}_sector_attribution.csv",
                    mime="text/csv"
                )
            except Exception as e:
                st.error(f"CSV export failed: {e}")
    
    with col2:
        if 'summary_json' in saved_files:
            try:
                import json
                json_data = json.dumps(summary, indent=2, default=str)
                st.download_button(
                    label="Download JSON Summary",
                    data=json_data,
                    file_name=f"{strategy_name}_attribution_summary.json",
                    mime="application/json"
                )
            except Exception as e:
                st.error(f"JSON export failed: {e}")
    
    with col3:
        if st.button("View Raw Data"):
            with st.expander("Raw Attribution Data", expanded=True):
                if attribution_results:
                    raw_data = []
                    for r in attribution_results[:50]:  # Limit to first 50 rows for display
                        raw_data.append({
                            'Date': r.date.strftime('%Y-%m-%d'),
                            'Sector': r.sector,
                            'Portfolio Weight': f"{r.portfolio_weight:.3%}",
                            'Benchmark Weight': f"{r.benchmark_weight:.3%}",
                            'Allocation Effect': f"{r.allocation_effect:.4%}",
                            'Selection Effect': f"{r.selection_effect:.4%}",
                            'Interaction Effect': f"{r.interaction_effect:.4%}",
                            'Total Effect': f"{r.total_effect:.4%}"
                        })
                    
                    raw_df = pd.DataFrame(raw_data)
                    st.dataframe(raw_df, use_container_width=True)

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
        
        if not holdings:
            st.info("No current holdings found. Use the editor below to add assets and weights.")
        
        # Inline editable holdings table
        st.subheader("Edit Holdings")
        asset_options = list(ASSET_DISPLAY_INFO.keys())

        # Prepare editable DataFrame
        editor_rows = []
        for asset_key, weight in (holdings or {}).items():
            name = ASSET_DISPLAY_INFO.get(asset_key, {}).get('name', asset_key)
            editor_rows.append({
                'Asset': asset_key,
                'Name': name,
                'Weight (%)': round(weight * 100.0, 2)
            })

        editor_df = pd.DataFrame(editor_rows if editor_rows else [{'Asset': '', 'Name': '', 'Weight (%)': 0.0}])

        edited_df = st.data_editor(
            editor_df,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config={
                'Asset': st.column_config.SelectboxColumn(
                    label='Asset',
                    options=asset_options,
                    required=False,
                    help='Select an asset code (e.g., SP500)'
                ),
                'Name': st.column_config.Column(
                    label='Name',
                    disabled=True
                ),
                'Weight (%)': st.column_config.NumberColumn(
                    label='Weight (%)',
                    min_value=0.0,
                    max_value=100.0,
                    step=0.1,
                    format="%.2f"
                )
            },
            key="holdings_editor"
        )

        save_col1, save_col2 = st.columns([1, 3])
        with save_col1:
            if st.button("💾 Save Holdings", type="primary", use_container_width=True):
                # Build holdings dict from edited rows
                updated = {}
                for _, row in edited_df.iterrows():
                    asset = str(row.get('Asset') or '').strip()
                    weight_pct = row.get('Weight (%)')
                    if asset and asset in asset_options and pd.notna(weight_pct):
                        updated[asset] = max(0.0, float(weight_pct))

                if not updated:
                    st.warning("No valid holdings to save. Please add at least one asset with a weight.")
                else:
                    total = sum(updated.values())
                    if total <= 0:
                        st.error("Total weight must be greater than 0%.")
                    else:
                        # Normalize to 100%
                        normalized = {k: (v / total) for k, v in updated.items()}
                        message = save_holdings({k: round(v, 6) for k, v in normalized.items()})
                        st.success(message)
                        st.experimental_rerun()

        # Show allocation chart below editor using current holdings
        if holdings:
            display_asset_allocation(holdings, "Current Portfolio Allocation")
    
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
        # Stale data flagging
        def is_stale(val):
            try:
                return (val == "N/A") or (float(val) > 30)
            except Exception:
                return True
        stale_mask = available_data_df["Last Updated (days)"].apply(is_stale)
        num_stale = int(stale_mask.sum()) if "Last Updated (days)" in available_data_df.columns else 0
        if num_stale > 0:
            stale_subset = available_data_df.loc[stale_mask, ["Type", "Asset", "End Date", "Last Updated (days)"]]
            with st.container(border=True):
                st.warning(f"{num_stale} data file(s) are older than 30 days. Consider downloading fresh data.")
                st.dataframe(stale_subset, use_container_width=True, hide_index=True)
                if st.button("🔄 Download Latest Data", type="primary"):
                    with st.spinner("Downloading latest data for all assets..."):
                        try:
                            download_data_main(refresh=True)
                            st.success("Data download completed. Reloading...")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Data download failed: {e}")

        st.subheader("Available Data Overview")
        st.dataframe(available_data_df, use_container_width=True, hide_index=True)
        
        # Interactive data explorer (data loading happens inside with date filtering)
        display_data_explorer()
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
    """Display system manager dashboard (read-only config, ops, and status)."""
    st.header("🛠️ System Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("System Status")
        
        # Data availability and freshness summary
        data_df = get_available_data()
        if not data_df.empty:
            total_files = len(data_df)
            price_files = len(data_df[data_df['Type'] == 'PRICE'])
            pe_files = len(data_df[data_df['Type'] == 'PE'])
            yield_files = len(data_df[data_df['Type'] == 'YIELD'])

            # Freshness
            def _is_stale(v):
                try:
                    return (v == "N/A") or (float(v) > 30)
                except Exception:
                    return True
            stale_count = data_df["Last Updated (days)"].apply(_is_stale).sum() if "Last Updated (days)" in data_df.columns else 0
            
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Total Data Files", total_files)
            m2.metric("Price Files", price_files)
            m3.metric("PE Files", pe_files)
            m4.metric("Yield Files", yield_files)
            m5.metric("Stale Files (>30d)", int(stale_count))
        else:
            st.warning("No data files found")
        
        # Strategy registry status
        strategies = strategy_registry.list_strategies()
        st.metric("Available Strategies", len(strategies))
        
        st.subheader("Processed Data Status")
        try:
            status = get_processing_status()
            processed = status.get('processed_strategies', [])
            if processed:
                status_df = pd.DataFrame([
                    {
                        'Strategy': s.get('name'),
                        'Processed At': s.get('processed_at'),
                        'Rows x Cols': ' x '.join(map(str, s.get('data_shape', []))),
                        'Date Start': s.get('date_range', {}).get('start'),
                        'Date End': s.get('date_range', {}).get('end'),
                        'File Size (MB)': s.get('file_size_mb')
                    } for s in processed
                ])
                st.dataframe(status_df, use_container_width=True, hide_index=True)
            else:
                st.info("No processed data found. Run 'Process All Strategies' to generate.")
        except Exception as e:
            st.error(f"Failed to load processing status: {e}")
        
    with col2:
        st.subheader("Operations")
        op_a, op_b, op_c = st.columns(3)
        with op_a:
            if st.button("🔄 Refresh All Data", use_container_width=True):
                with st.spinner("Refreshing data for all assets..."):
                    try:
                        download_data_main(refresh=True)
                        st.success("Data refreshed successfully.")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Data refresh failed: {e}")
        with op_b:
            if st.button("🧱 Process All Strategies", use_container_width=True):
                with st.spinner("Processing data for strategies..."):
                    try:
                        results = process_all_strategies(force_refresh=True)
                        ok = sum(1 for v in results.values() if v)
                        st.success(f"Processed {ok}/{len(results)} strategies.")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Processing failed: {e}")
        with op_c:
            if st.button("🧹 Clean Processed Data", use_container_width=True):
                with st.spinner("Cleaning processed data cache..."):
                    try:
                        cleanup_processed_data()
                        st.success("Processed data cache cleaned.")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Cleanup failed: {e}")
        
        st.caption("Backtest parameters can be configured in the Backtest tab. This dashboard focuses on system health and operations.")

if __name__ == "__main__":
    main()