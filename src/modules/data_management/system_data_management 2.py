"""
System & Data Management Page

Consolidated interface for Data Explorer, System Health, and Accounting Data Management.
Contains all data and system management functionality in a single page with horizontal tabs.
"""

import streamlit as st
import pandas as pd
import os
import tempfile
from datetime import date, datetime
from typing import Dict, Any, List

# Import system components
from src.modules.data_management.data_center.download import main as download_data_main, get_data_range_info
from src.modules.data_management.data_center.data_processor import (
    get_processing_status,
    process_all_strategies,
    cleanup_processed_data
)
from src.modules.portfolio.strategies.registry import strategy_registry
from src.ui.app_logger import LOG
from src.modules.data_management.visualization.charts import display_data_explorer
from src.modules.data_management.visualization.data_access import load_data_for_visualization

# Import accounting data management components
from src.modules.accounting.core.data_storage import MonthlyDataStorage
from src.modules.accounting.core.data_storage_utils import (
    get_current_year_month, 
    get_recent_months, 
    validate_month_format,
    csv_to_dataframe
)
from src.modules.accounting.core.report_storage import MonthlyReportStorage


def show_system_data_page():
    """Main system and data management page with Data Explorer, System, and Accounting Data tabs."""
    st.header("🛠️ System & Data Management")
    st.markdown("Centralized management for all system data, health monitoring, and operations")
    
    # Create horizontal tabs for data management functionality
    tab1, tab2, tab3 = st.tabs([
        "📊 Data Explorer",
        "⚙️ System Health", 
        "📋 Accounting Data"
    ])
    
    with tab1:
        show_data_explorer_tab()
    
    with tab2:
        show_system_health_tab()
    
    with tab3:
        show_accounting_data_tab()


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


def show_data_explorer_tab():
    """Display data exploration and visualization interface."""
    st.subheader("📊 Data Explorer")
    st.markdown("Explore and visualize investment data across all assets and timeframes")
    
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
        st.divider()
        display_data_explorer()
    else:
        st.warning("No data files found. Please download data first.")
    
    # Data management section
    st.divider()
    st.subheader("Data Management Operations")
    
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
            from src.modules.data_management.data_center.download import download_yfinance_data, download_akshare_index
            
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


def show_system_health_tab():
    """Display system manager dashboard (read-only config, ops, and status)."""
    st.subheader("⚙️ System Health Dashboard")
    st.markdown("Monitor system status, data quality, and perform system operations")
    
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
        st.subheader("System Operations")
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
        
        st.caption("Backtest parameters can be configured in the Investment tab. This dashboard focuses on system health and operations.")


def show_accounting_data_tab():
    """Unified accounting data management interface."""
    st.subheader("💰 Accounting Data Management")
    st.markdown("View, upload, edit, and manage all your accounting data in one place")
    
    # Initialize components
    try:
        from src.modules.accounting.core.data_storage import MonthlyDataStorage
        from src.modules.accounting.core.category_translator import CategoryTranslator
        from src.modules.accounting.core.data_storage_utils import (
            parse_user_expense_table,
            convert_parsed_data_to_transactions,
            preview_bulk_upload_conversion
        )
        
        data_storage = MonthlyDataStorage()
        translator = CategoryTranslator()
    except ImportError as e:
        st.error(f"Error importing accounting modules: {e}")
        return
    
    # 📅 Time Range Selector
    st.markdown("### 📅 Time Range Selection")
    col1, col2 = st.columns(2)
    
    with col1:
        time_range = st.selectbox(
            "Select time range",
            options=["Last 12 months", "Last 24 months", "Last 36 months", "All data"],
            index=0,
            help="Choose how much historical data to display and manage"
        )
    
    with col2:
        auto_translate = st.checkbox(
            "Auto-translate Chinese categories",
            value=True,
            help="Automatically convert Chinese categories to English when uploading"
        )
    
    # Load existing data based on time range
    available_months = data_storage.list_available_months()
    
    if not available_months:
        st.info("📝 No accounting data found. Upload some data below to get started!")
        display_months = []
        existing_transactions = pd.DataFrame()
    else:
        # Filter months based on selection
        if time_range == "All data":
            display_months = available_months
        else:
            month_count = int(time_range.split()[1])
            display_months = sorted(available_months, reverse=True)[:month_count]
        
        # Load and combine data from all selected months
        existing_transactions = _load_combined_transactions(data_storage, display_months)
        
        if not existing_transactions.empty:
            st.success(f"📊 Loaded {len(existing_transactions)} transactions from {len(display_months)} months: {', '.join(sorted(display_months))}")
    
    # 📤 Bulk Upload Section
    st.markdown("---")
    st.markdown("### 📤 Bulk Upload & Merge")
    
    upload_col1, upload_col2 = st.columns([2, 1])
    
    with upload_col1:
        bulk_data = st.text_area(
            "Paste expense table data (User×Category×Month format):",
            height=150,
            placeholder="User        Jan-25    Feb-25    Mar-25\nYY    房租    ¥11,512.80    ¥11,512.80    ¥11,512.80\nXH    餐饮    ¥3,243.94    ¥2,240.63    ¥1,854.87",
            help="Paste your expense table here. Chinese categories will be automatically translated to English."
        )
    
    with upload_col2:
        st.markdown("**Upload Options:**")
        overwrite_conflicts = st.checkbox(
            "Overwrite conflicting months",
            value=True,
            help="If uploaded data conflicts with existing months, overwrite existing data"
        )
        
        if st.button("🔄 Parse & Preview Upload", type="secondary"):
            if bulk_data.strip():
                st.session_state.bulk_upload_data = bulk_data
                st.session_state.show_upload_preview = True
    
    # Process upload and merge with existing data
    merged_data = existing_transactions.copy()
    upload_info = None
    
    if bulk_data.strip():
        try:
            # Parse uploaded data
            preview_result = preview_bulk_upload_conversion(bulk_data)
            
            if preview_result["status"] == "success":
                upload_info = preview_result["summary"]
                
                # Convert to transactions and merge
                parsed_data = parse_user_expense_table(bulk_data)
                monthly_dfs = convert_parsed_data_to_transactions(parsed_data)
                
                # Create uploaded transactions DataFrame
                uploaded_transactions = []
                for month, df in monthly_dfs:
                    uploaded_transactions.append(df)
                
                if uploaded_transactions:
                    upload_df = pd.concat(uploaded_transactions, ignore_index=True)
                    
                    # Merge with existing data
                    merged_data = _merge_transactions_data(existing_transactions, upload_df, overwrite_conflicts)
                    
                    # Show upload summary
                    conflicting_months = set(upload_info["months"]) & set(display_months)
                    new_months = set(upload_info["months"]) - set(display_months)
                    
                    if conflicting_months:
                        st.warning(f"⚠️ Will {'overwrite' if overwrite_conflicts else 'skip'} existing data for: {', '.join(sorted(conflicting_months))}")
                    
                    if new_months:
                        st.info(f"✅ Will add new data for: {', '.join(sorted(new_months))}")
            
            elif preview_result["status"] == "error":
                st.error(f"❌ Upload error: {preview_result['error']}")
            
            else:
                st.warning("⚠️ Upload validation issues found")
                for error in preview_result.get("validation_errors", []):
                    st.error(f"• {error}")
                    
        except Exception as e:
            st.error(f"❌ Error processing upload: {e}")
    
    # 📊 Unified Data Table
    st.markdown("---")
    st.markdown("### 📊 All Transactions Data")
    
    if not merged_data.empty:
        # Prepare data for editing
        edited_data = _show_editable_transactions_table(merged_data, translator)
        
        # ⚡ Batch Operations
        st.markdown("### ⚡ Batch Operations")
        batch_col1, batch_col2, batch_col3, batch_col4 = st.columns(4)
        
        with batch_col1:
            if st.button("🔄 Translate All Categories"):
                _perform_batch_translation(edited_data, translator)
                st.rerun()
        
        with batch_col2:
            if st.button("🏷️ Rename Category"):
                _show_category_rename_dialog(edited_data)
        
        with batch_col3:
            if st.button("🗑️ Delete Selected"):
                _show_delete_selected_dialog(edited_data)
        
        with batch_col4:
            if st.button("💾 Save All Changes", type="primary"):
                _save_all_changes(edited_data, data_storage, upload_info)
                st.success("✅ All changes saved successfully!")
                st.rerun()
    
    else:
        st.info("📝 No transaction data to display. Upload some data above to get started!")
        
        # Show upload summary if available
        if upload_info:
            st.markdown("**Upload Preview:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Months", upload_info["total_months"])
            with col2:
                st.metric("Users", upload_info["total_users"])
            with col3:
                st.metric("Categories", upload_info["total_categories"])


def _load_combined_transactions(data_storage: 'MonthlyDataStorage', months: list) -> pd.DataFrame:
    """Load and combine transactions from multiple months."""
    all_transactions = []
    
    for month in months:
        transactions_df, _ = data_storage.load_monthly_data(month)
        if transactions_df is not None:
            transactions_df['month'] = month  # Add month column for tracking
            all_transactions.append(transactions_df)
    
    if all_transactions:
        combined = pd.concat(all_transactions, ignore_index=True)
        # Sort by month (newest first) - transactions don't have date column
        combined = combined.sort_values('month', ascending=False)
        return combined
    
    return pd.DataFrame()


def _merge_transactions_data(existing_df: pd.DataFrame, upload_df: pd.DataFrame, overwrite: bool) -> pd.DataFrame:
    """Merge uploaded transactions with existing data."""
    if existing_df.empty:
        return upload_df
    
    if upload_df.empty:
        return existing_df
    
    # Add merge status column to track data source
    existing_df = existing_df.copy()
    upload_df = upload_df.copy()
    
    existing_df['_data_source'] = 'existing'
    upload_df['_data_source'] = 'uploaded'
    
    if overwrite:
        # Remove existing data for months that appear in upload
        upload_months = set(upload_df.get('year_month', upload_df.get('month', [])))
        if upload_months:
            existing_months = set(existing_df.get('year_month', existing_df.get('month', [])))
            overlapping_months = upload_months & existing_months
            
            if overlapping_months:
                # Filter out overlapping months from existing data
                month_col = 'year_month' if 'year_month' in existing_df.columns else 'month'
                existing_df = existing_df[~existing_df[month_col].isin(overlapping_months)]
    
    # Combine data
    merged = pd.concat([existing_df, upload_df], ignore_index=True)
    
    # Sort by month if available, otherwise keep original order
    if 'month' in merged.columns:
        merged = merged.sort_values('month', ascending=False)
    elif 'year_month' in merged.columns:
        merged = merged.sort_values('year_month', ascending=False)
    
    return merged


def _show_editable_transactions_table(data: pd.DataFrame, translator: 'CategoryTranslator') -> pd.DataFrame:
    """Display editable transactions table."""
    if data.empty:
        return data
    
    # Map stored columns to display columns - stored data has: Description, Amount, Debit, Credit, User
    display_columns = []
    column_mapping = {
        'Description': 'Description',
        'Amount': 'Amount', 
        'Debit': 'Category',  # Debit column stores the category
        'Credit': 'Account',  # Credit column stores the account
        'User': 'User'
    }
    
    # Build display data with proper column names
    display_data = pd.DataFrame()
    for stored_col, display_col in column_mapping.items():
        if stored_col in data.columns:
            display_data[display_col] = data[stored_col]
            display_columns.append(display_col)
    
    # Add month column if available
    if 'month' in data.columns:
        display_data['Month'] = data['month']
        display_columns.append('Month')
    
    # Add data source indicator if available
    if '_data_source' in data.columns:
        display_data['Data Source'] = data['_data_source']
        display_columns.append('Data Source')
    
    # Configure column settings for actual columns
    column_config = {
        "Description": st.column_config.TextColumn("Description", help="Transaction description", max_chars=200),
        "Amount": st.column_config.NumberColumn("Amount", help="Transaction amount", format="¥%.2f"),
        "Category": st.column_config.SelectboxColumn(
            "Category",
            help="Transaction category",
            options=sorted(list(translator.STANDARD_EXPENSE_CATEGORIES) + list(translator.STANDARD_REVENUE_CATEGORIES))
        ),
        "Account": st.column_config.TextColumn("Account", help="Account name"),
        "User": st.column_config.TextColumn("User", help="User identifier"),
        "Month": st.column_config.TextColumn("Month", help="Year-Month", disabled=True),
    }
    
    if 'Data Source' in display_columns:
        column_config['Data Source'] = st.column_config.TextColumn(
            "Source", 
            help="Data source: existing or uploaded",
            disabled=True
        )
    
    # Show editable table
    edited_data = st.data_editor(
        display_data,
        use_container_width=True,
        num_rows="dynamic",
        column_config=column_config,
        key="unified_transactions_editor",
        height=400
    )
    
    # Copy back the complete data with edits - map display columns back to stored columns
    result_data = data.copy()
    reverse_mapping = {v: k for k, v in column_mapping.items()}
    
    for display_col, stored_col in reverse_mapping.items():
        if display_col in edited_data.columns and stored_col in result_data.columns:
            result_data[stored_col] = edited_data[display_col]
    
    # Handle special columns
    if 'Month' in edited_data.columns and 'month' in result_data.columns:
        result_data['month'] = edited_data['Month']
    
    return result_data


def _perform_batch_translation(data: pd.DataFrame, translator: 'CategoryTranslator'):
    """Perform batch category translation."""
    # The category data is stored in the 'Debit' column
    if 'Debit' in data.columns:
        data['Debit'] = data['Debit'].apply(translator.translate_to_english)


def _show_category_rename_dialog(data: pd.DataFrame):
    """Show category rename dialog."""
    if 'category' in data.columns:
        unique_categories = sorted(data['category'].unique())
        
        col1, col2 = st.columns(2)
        with col1:
            old_category = st.selectbox("Current category:", unique_categories)
        with col2:
            new_category = st.text_input("New category name:")
        
        if old_category and new_category and st.button("Apply Rename"):
            data.loc[data['category'] == old_category, 'category'] = new_category
            st.success(f"✅ Renamed '{old_category}' to '{new_category}'")


def _show_delete_selected_dialog(data: pd.DataFrame):
    """Show delete selected rows dialog."""
    st.warning("Select rows in the table above, then confirm deletion:")
    if st.button("⚠️ Confirm Delete Selected Rows"):
        st.info("Delete functionality will be implemented with row selection")


def _save_all_changes(data: pd.DataFrame, data_storage: 'MonthlyDataStorage', upload_info: dict):
    """Save all changes to storage."""
    try:
        # Group by month and save
        if 'year_month' in data.columns:
            month_col = 'year_month'
        elif 'month' in data.columns:
            month_col = 'month'
        else:
            st.error("No month column found in data")
            return
        
        saved_months = []
        for month, month_data in data.groupby(month_col):
            # Remove internal columns before saving
            clean_data = month_data.drop(columns=['_data_source'], errors='ignore')
            
            result = data_storage.save_monthly_data(
                month,
                transactions_df=clean_data,
                overwrite=True
            )
            
            if result.get("transactions", False):
                saved_months.append(month)
        
        if saved_months:
            st.success(f"✅ Saved data for {len(saved_months)} months: {', '.join(sorted(saved_months))}")
        
    except Exception as e:
        st.error(f"❌ Error saving data: {e}")


def _show_no_accounting_data_message():
    """Show message when no accounting data is found."""
    st.info("🔍 No accounting data found")
    st.markdown("""
    No monthly accounting data was found in the system. To manage data:
    
    1. **Upload data**: Go to the **Accounting** tab to upload transaction/asset CSV files
    2. **Generate reports**: Create income statements or balance sheets 
    3. **Return here**: Once data exists, return to this tab to manage it
    
    This management interface will be available once you have uploaded data or generated reports.
    """)


def show_accounting_data_overview(month: str, data_info: dict, available_reports: dict):
    """Show overview of available data for the selected month."""
    st.subheader("📋 Data Overview")
    
    # Data status section
    _show_accounting_data_status(month, data_info, available_reports)
    
    # Reports status section
    _show_accounting_reports_status(month, available_reports)
    
    # Storage statistics
    _show_accounting_storage_statistics(month, data_info, available_reports)


def _show_accounting_data_status(month: str, data_info: dict, available_reports: dict):
    """Show data availability status."""
    st.subheader("💾 Data Status")
    
    # Check what data is available
    has_transactions = data_info.get('has_transactions', False)
    has_assets = data_info.get('has_assets', False)
    has_exchange_rate = data_info.get('has_exchange_rate', False)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_icon = "✅" if has_transactions else "❌"
        st.metric("Transactions Data", f"{status_icon} {'Available' if has_transactions else 'Missing'}")
        if has_transactions:
            trans_count = data_info.get('transaction_count', 0)
            st.caption(f"{trans_count} transaction records")
    
    with col2:
        status_icon = "✅" if has_assets else "❌"
        st.metric("Assets Data", f"{status_icon} {'Available' if has_assets else 'Missing'}")
        if has_assets:
            asset_count = data_info.get('asset_count', 0)
            st.caption(f"{asset_count} asset records")
    
    with col3:
        status_icon = "✅" if has_exchange_rate else "❌"
        st.metric("Exchange Rate", f"{status_icon} {'Available' if has_exchange_rate else 'Missing'}")
        if has_exchange_rate:
            rate_info = data_info.get('exchange_rate_info', {})
            st.caption(f"USD/CNY: {rate_info.get('rate', 'N/A')}")


def _show_accounting_reports_status(month: str, available_reports: dict):
    """Show generated reports status."""
    st.subheader("📊 Generated Reports")
    
    reports_for_month = available_reports.get(month, {})
    has_income = 'income_statement' in reports_for_month
    has_balance = 'balance_sheet' in reports_for_month
    has_cashflow = 'cash_flow_statement' in reports_for_month
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_icon = "✅" if has_income else "❌"
        st.metric("Income Statement", f"{status_icon} {'Generated' if has_income else 'Not Generated'}")
    
    with col2:
        status_icon = "✅" if has_balance else "❌"
        st.metric("Balance Sheet", f"{status_icon} {'Generated' if has_balance else 'Not Generated'}")
    
    with col3:
        status_icon = "✅" if has_cashflow else "❌"
        st.metric("Cash Flow Statement", f"{status_icon} {'Generated' if has_cashflow else 'Not Generated'}")


def _show_accounting_storage_statistics(month: str, data_info: dict, available_reports: dict):
    """Show storage statistics."""
    st.subheader("💽 Storage Statistics")
    
    # Data file sizes
    total_data_size = 0
    total_reports_size = 0
    
    # Calculate approximate sizes (would need actual file size calculation in real implementation)
    transaction_count = data_info.get('transaction_count', 0)
    asset_count = data_info.get('asset_count', 0)
    total_data_size = (transaction_count + asset_count) * 0.1  # Rough estimate in KB
    
    reports_for_month = available_reports.get(month, {})
    total_reports_size = len(reports_for_month) * 2  # Rough estimate in KB
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Data Files Size", f"{total_data_size:.1f} KB")
    
    with col2:
        st.metric("Reports Size", f"{total_reports_size:.1f} KB")
    
    with col3:
        total_size = total_data_size + total_reports_size
        st.metric("Total Size", f"{total_size:.1f} KB")
    
    with col4:
        total_records = transaction_count + asset_count
        st.metric("Total Records", f"{total_records:,}")


def show_accounting_data_preview(month: str, data_storage: MonthlyDataStorage, report_storage: MonthlyReportStorage):
    """Show preview of data and reports for the selected month."""
    st.subheader("👁️ Data Preview")
    
    # Create sub-tabs for different data types
    preview_tab1, preview_tab2 = st.tabs(["📄 Raw Data", "📊 Generated Reports"])
    
    with preview_tab1:
        _show_accounting_dataframe_preview(month, data_storage)
    
    with preview_tab2:
        _show_accounting_reports_preview(month, report_storage)


def _show_accounting_dataframe_preview(month: str, data_storage: MonthlyDataStorage):
    """Show preview of raw dataframes."""
    st.subheader("📄 Raw Data Preview")
    
    try:
        # Load data (new API returns tuple of DataFrames)
        monthly_data = data_storage.load_monthly_data(month)

        transactions_df = None
        assets_df = None

        if isinstance(monthly_data, tuple):
            transactions_df, assets_df = monthly_data
        elif isinstance(monthly_data, dict):
            # Backward compatibility with older dict-based structure
            transactions_df = monthly_data.get('transactions') or monthly_data.get('transactions_df')
            assets_df = monthly_data.get('assets') or monthly_data.get('assets_df')
        
        if transactions_df is not None and not transactions_df.empty:
            st.subheader("💳 Transactions")
            st.dataframe(transactions_df.head(10), use_container_width=True)
            if len(transactions_df) > 10:
                st.caption(f"Showing first 10 of {len(transactions_df)} transactions")
        
        if assets_df is not None and not assets_df.empty:
            st.subheader("💰 Assets")
            st.dataframe(assets_df.head(10), use_container_width=True)
            if len(assets_df) > 10:
                st.caption(f"Showing first 10 of {len(assets_df)} assets")
            
    except Exception as e:
        st.error(f"Failed to load data preview: {e}")


def _show_accounting_reports_preview(month: str, report_storage: MonthlyReportStorage):
    """Show preview of generated reports."""
    st.subheader("📊 Generated Reports Preview")
    
    try:
        # Load all statements for the month (helper method handles availability)
        statements = {}
        if hasattr(report_storage, 'load_monthly_statements'):
            statements = report_storage.load_monthly_statements(month) or {}
        else:
            # Fallback if helper not available
            for stmt_type in ["income_statement", "cash_flow", "balance_sheet"]:
                data = report_storage.load_statement(month, stmt_type)
                if data is not None:
                    key = 'cash_flow_statement' if stmt_type == 'cash_flow' else stmt_type
                    statements[key] = data
        
        if statements.get('income_statement'):
            st.subheader("📈 Income Statement")
            # Show key metrics from income statement
            income_stmt = statements['income_statement']
            if hasattr(income_stmt, 'dict'):
                st.json(income_stmt.dict())
            else:
                st.write(income_stmt)
        
        if statements.get('balance_sheet'):
            st.subheader("⚖️ Balance Sheet")
            # Show key metrics from balance sheet
            balance_sheet = statements['balance_sheet']
            if hasattr(balance_sheet, 'dict'):
                st.json(balance_sheet.dict())
            else:
                st.write(balance_sheet)
        
        if statements.get('cash_flow_statement') or statements.get('cash_flow'):
            st.subheader("💰 Cash Flow Statement")
            # Show key metrics from cash flow statement
            cashflow_stmt = statements.get('cash_flow_statement') or statements.get('cash_flow')
            if hasattr(cashflow_stmt, 'dict'):
                st.json(cashflow_stmt.dict())
            else:
                st.write(cashflow_stmt)
                
    except Exception as e:
        st.error(f"Failed to load reports preview: {e}")


def show_accounting_data_editor(month: str, data_storage: MonthlyDataStorage, report_storage: MonthlyReportStorage):
    """Show data editor interface."""
    st.subheader("✏️ Data Editor")
    st.warning("⚠️ Data editing functionality is not yet implemented. This is a placeholder for future enhancement.")
    
    st.markdown("""
    **Future Editor Features:**
    - Edit individual transaction records
    - Modify asset values and descriptions
    - Update exchange rates
    - Bulk edit operations
    - Data validation and error checking
    
    For now, please regenerate data by uploading corrected CSV files in the Accounting tab.
    """)


def show_accounting_data_deletion(month: str, data_storage: MonthlyDataStorage, report_storage: MonthlyReportStorage):
    """Show data deletion interface."""
    st.subheader("🗑️ Data Deletion")
    st.warning("⚠️ Data deletion is permanent and cannot be undone!")
    
    # Selective deletion section
    _show_accounting_selective_deletion_section(month, data_storage, report_storage)
    
    st.divider()
    
    # Reports deletion section  
    _show_accounting_reports_deletion_section(month, report_storage)
    
    st.divider()
    
    # Complete deletion section
    _show_accounting_complete_deletion_section(month, data_storage, report_storage)


def _show_accounting_selective_deletion_section(month: str, data_storage: MonthlyDataStorage, report_storage: MonthlyReportStorage):
    """Show selective deletion options."""
    st.subheader("🔍 Selective Deletion")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Delete Transactions", use_container_width=True):
            if _execute_accounting_deletion(month, data_storage, 'transactions'):
                st.success("Transactions deleted successfully")
                st.rerun()
    
    with col2:
        if st.button("🗑️ Delete Assets", use_container_width=True):
            if _execute_accounting_deletion(month, data_storage, 'assets'):
                st.success("Assets deleted successfully")
                st.rerun()
    
    with col3:
        if st.button("🗑️ Delete Exchange Rate", use_container_width=True):
            if _execute_accounting_deletion(month, data_storage, 'exchange_rate'):
                st.success("Exchange rate deleted successfully")
                st.rerun()


def _show_accounting_reports_deletion_section(month: str, report_storage: MonthlyReportStorage):
    """Show reports deletion options."""
    st.subheader("📊 Delete Generated Reports")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Delete Income Statement", use_container_width=True):
            if _execute_accounting_reports_deletion(month, report_storage, 'income_statement'):
                st.success("Income statement deleted successfully")
                st.rerun()
    
    with col2:
        if st.button("🗑️ Delete Balance Sheet", use_container_width=True):
            if _execute_accounting_reports_deletion(month, report_storage, 'balance_sheet'):
                st.success("Balance sheet deleted successfully")
                st.rerun()
    
    with col3:
        if st.button("🗑️ Delete Cash Flow Statement", use_container_width=True):
            if _execute_accounting_reports_deletion(month, report_storage, 'cash_flow_statement'):
                st.success("Cash flow statement deleted successfully")
                st.rerun()


def _show_accounting_complete_deletion_section(month: str, data_storage: MonthlyDataStorage, report_storage: MonthlyReportStorage):
    """Show complete deletion options."""
    st.subheader("💥 Complete Deletion")
    st.error("⚠️ This will delete ALL data and reports for the selected month!")
    
    # Confirmation checkbox
    confirm_complete = st.checkbox(f"I understand this will permanently delete all data for {month}")
    
    if confirm_complete:
        if st.button("💥 DELETE ALL DATA", type="primary", use_container_width=True):
            if _execute_accounting_complete_deletion(month, data_storage, report_storage):
                st.success(f"All data for {month} deleted successfully")
                st.rerun()


def _execute_accounting_deletion(month: str, data_storage: MonthlyDataStorage, data_type: str) -> bool:
    """Execute selective data deletion."""
    try:
        # This would need to be implemented in the data storage layer
        # For now, return False to indicate not implemented
        st.error(f"Deletion of {data_type} is not yet implemented")
        return False
    except Exception as e:
        st.error(f"Failed to delete {data_type}: {e}")
        return False


def _execute_accounting_reports_deletion(month: str, report_storage: MonthlyReportStorage, report_type: str) -> bool:
    """Execute reports deletion."""
    try:
        # This would need to be implemented in the report storage layer
        # For now, return False to indicate not implemented
        st.error(f"Deletion of {report_type} is not yet implemented")
        return False
    except Exception as e:
        st.error(f"Failed to delete {report_type}: {e}")
        return False


def _execute_accounting_complete_deletion(month: str, data_storage: MonthlyDataStorage, report_storage: MonthlyReportStorage) -> bool:
    """Execute complete deletion of all data and reports."""
    try:
        # This would need to be implemented to delete everything for the month
        # For now, return False to indicate not implemented
        st.error("Complete deletion is not yet implemented")
        return False
    except Exception as e:
        st.error(f"Failed to delete all data: {e}")
        return False