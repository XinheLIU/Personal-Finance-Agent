"""
Data Management Components

UI components for data exploration, system health monitoring, and accounting data management.
"""

import streamlit as st
import pandas as pd
import tempfile
from datetime import date, timedelta
from typing import Dict, Any, List

from src.modules.data_management.presenters.system_data_presenter import SystemDataPresenter
from src.modules.data_management.visualization.charts import display_data_explorer


def show_data_explorer_tab():
    """Display data exploration and visualization interface."""
    st.subheader("📊 Data Explorer")
    st.markdown("Explore and visualize investment data across all assets and timeframes")
    
    presenter = SystemDataPresenter()
    
    # Load available data
    available_data_df = presenter.get_available_data()
    
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
                            message = presenter.refresh_all_data()
                            st.success(message)
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
                    message = presenter.refresh_all_data()
                    st.success(message)
                    st.rerun()
                except Exception as e:
                    st.error(f"Data download failed: {e}")
    
    with col2:
        st.write("**Download New Asset**")
        new_ticker = st.text_input("Enter ticker symbol:")
        if st.button("📥 Download New Ticker") and new_ticker:
            with st.spinner(f"Downloading {new_ticker}..."):
                try:
                    message = presenter.download_new_ticker(new_ticker)
                    if "Successfully" in message:
                        st.success(message)
                    else:
                        st.error(message)
                except Exception as e:
                    st.error(f"Error downloading {new_ticker}: {e}")


def show_system_health_tab():
    """Display system manager dashboard (read-only config, ops, and status)."""
    st.subheader("⚙️ System Health Dashboard")
    st.markdown("Monitor system status, data quality, and perform system operations")
    
    presenter = SystemDataPresenter()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("System Status")
        
        # Get system health status
        health_status = presenter.get_system_health_status()
        
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Data Files", health_status['total_files'])
        m2.metric("Price Files", health_status['price_files'])
        m3.metric("PE Files", health_status['pe_files'])
        m4.metric("Yield Files", health_status['yield_files'])
        m5.metric("Stale Files (>30d)", health_status['stale_files'])
        
        st.metric("Available Strategies", health_status['available_strategies'])
        
        st.subheader("Processed Data Status")
        processing_status = presenter.get_processing_status()
        
        if processing_status.get('has_processed_data', False):
            processed = processing_status.get('processed_strategies', [])
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
        else:
            if 'error' in processing_status:
                st.error(f"Failed to load processing status: {processing_status['error']}")
            else:
                st.info("No processed data found. Run 'Process All Strategies' to generate.")
        
    with col2:
        st.subheader("System Operations")
        op_a, op_b, op_c = st.columns(3)
        
        with op_a:
            if st.button("🔄 Refresh All Data", use_container_width=True):
                with st.spinner("Refreshing data for all assets..."):
                    try:
                        message = presenter.refresh_all_data()
                        st.success(message)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Data refresh failed: {e}")
        
        with op_b:
            if st.button("🧱 Process All Strategies", use_container_width=True):
                with st.spinner("Processing data for strategies..."):
                    try:
                        result = presenter.process_all_strategies()
                        if result['success']:
                            st.success(result['message'])
                        else:
                            st.error(f"Processing failed: {result['error']}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Processing failed: {e}")
        
        with op_c:
            if st.button("🧹 Clean Processed Data", use_container_width=True):
                with st.spinner("Cleaning processed data cache..."):
                    try:
                        result = presenter.cleanup_processed_data()
                        if result['success']:
                            st.success(result['message'])
                        else:
                            st.error(f"Cleanup failed: {result['error']}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Cleanup failed: {e}")
        
        st.caption("Backtest parameters can be configured in the Investment tab. This dashboard focuses on system health and operations.")


def show_accounting_data_tab():
    """Unified accounting data management interface."""
    st.subheader("💰 Accounting Data Management")
    st.markdown("View, upload, edit, and manage all your accounting data in one place")
    
    presenter = SystemDataPresenter()
    
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
    
    # Get accounting data info
    data_info = presenter.get_accounting_data_info(time_range)
    
    if not data_info['has_data']:
        st.info(data_info['message'])
        display_months = []
        existing_transactions = pd.DataFrame()
    else:
        display_months = data_info['months']
        existing_transactions = presenter.load_combined_transactions(display_months)
        
        if not existing_transactions.empty:
            st.success(data_info['message'])
    
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
            from src.modules.accounting.core.data_storage_utils import preview_bulk_upload_conversion
            preview_result = preview_bulk_upload_conversion(bulk_data)
            
            if preview_result["status"] == "success":
                upload_info = preview_result["summary"]
                
                # Convert to transactions and merge
                from src.modules.accounting.core.data_storage_utils import (
                    parse_user_expense_table,
                    convert_parsed_data_to_transactions
                )
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
        edited_data = _show_editable_transactions_table(merged_data)
        
        # ⚡ Batch Operations
        st.markdown("### ⚡ Batch Operations")
        batch_col1, batch_col2, batch_col3, batch_col4 = st.columns(4)
        
        with batch_col1:
            if st.button("🔄 Translate All Categories"):
                _perform_batch_translation(edited_data)
                st.rerun()
        
        with batch_col2:
            if st.button("🏷️ Rename Category"):
                _show_category_rename_dialog(edited_data)
        
        with batch_col3:
            if st.button("🗑️ Delete Selected"):
                _show_delete_selected_dialog(edited_data)
        
        with batch_col4:
            if st.button("💾 Save All Changes", type="primary"):
                _save_all_changes(edited_data, presenter.data_storage, upload_info)
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


def _show_editable_transactions_table(data: pd.DataFrame) -> pd.DataFrame:
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
            options=sorted(["Food", "Transport", "Healthcare", "Entertainment", "Utilities", "Rent", "Other"])
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


def _perform_batch_translation(data: pd.DataFrame):
    """Perform batch category translation."""
    # The category data is stored in the 'Debit' column
    if 'Debit' in data.columns:
        from src.modules.accounting.core.category_translator import CategoryTranslator
        translator = CategoryTranslator()
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


def _save_all_changes(data: pd.DataFrame, data_storage, upload_info: dict):
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
