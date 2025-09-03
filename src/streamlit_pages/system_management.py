"""
System Management Pages

Contains system status monitoring and data exploration interfaces.
Focuses on data management, system health monitoring, and data exploration features.
"""

import streamlit as st
import pandas as pd
import os
from datetime import date
from typing import Dict

# Import system components
from src.data_center.download import main as download_data_main, get_data_range_info
from src.data_center.data_processor import (
    get_processing_status,
    process_all_strategies,
    cleanup_processed_data
)
from src.strategies.registry import strategy_registry
from src.app_logger import LOG
from src.visualization.charts import display_data_explorer


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
                            st.rerun()
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
                    st.rerun()
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
                        st.rerun()
                    except Exception as e:
                        st.error(f"Data refresh failed: {e}")
        with op_b:
            if st.button("🧱 Process All Strategies", use_container_width=True):
                with st.spinner("Processing data for strategies..."):
                    try:
                        results = process_all_strategies(force_refresh=True)
                        ok = sum(1 for v in results.values() if v)
                        st.success(f"Processed {ok}/{len(results)} strategies.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Processing failed: {e}")
        with op_c:
            if st.button("🧹 Clean Processed Data", use_container_width=True):
                with st.spinner("Cleaning processed data cache..."):
                    try:
                        cleanup_processed_data()
                        st.success("Processed data cache cleaned.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Cleanup failed: {e}")
        
        st.caption("Backtest parameters can be configured in the Backtest tab. This dashboard focuses on system health and operations.")