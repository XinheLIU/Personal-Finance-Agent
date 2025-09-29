"""
Passive UI Components for Accounting Views

Pure UI components with no business logic - only handles display and input collection.
All business logic is handled by presenters.
"""

import streamlit as st
import pandas as pd
import tempfile
import os
from typing import Tuple, Optional, Dict, Any


def handle_csv_upload(upload_key: str, help_text: str = None) -> Optional[str]:
    """
    Handle CSV file upload and return temporary file path.
    
    Args:
        upload_key: Unique key for the file uploader
        help_text: Optional help text for the uploader
        
    Returns:
        Path to temporary file or None if no file uploaded
    """
    uploaded_file = st.file_uploader(
        "Upload CSV File",
        type=['csv'],
        key=upload_key,
        help=help_text or "Upload a CSV file for processing"
    )
    
    if uploaded_file is not None:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    
    return None


def show_csv_help(format_info: Dict[str, str]):
    """
    Display CSV format help information.
    
    Args:
        format_info: Dictionary with format information
    """
    with st.expander("❓ CSV Format Help", expanded=False):
        st.write("**Required CSV Format:**")
        for column, description in format_info.items():
            st.write(f"• **{column}**: {description}")


def show_data_preview_editor(df: pd.DataFrame, editor_key: str) -> pd.DataFrame:
    """
    Display enhanced data preview and editor with better user experience.
    
    Args:
        df: DataFrame to preview/edit
        editor_key: Unique key for the editor
        
    Returns:
        Edited DataFrame
    """
    # Show data summary
    st.write("**📈 Data Summary:**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📋 Total Rows", len(df))
    with col2:
        st.metric("📊 Columns", len(df.columns))
    with col3:
        if 'User' in df.columns:
            unique_users = df['User'].nunique()
            st.metric("👥 Users", unique_users)
        else:
            st.metric("💰 Numeric Cols", len(df.select_dtypes(include=['number']).columns))
    with col4:
        # Show total amount if Amount column exists
        if 'Amount' in df.columns:
            try:
                # Try to convert amounts to numeric, handling currency symbols
                amount_strings = df['Amount'].astype(str)
                # Remove currency symbols and commas
                cleaned_amounts = amount_strings.str.replace(r'[¥,￥$]', '', regex=True)
                # Convert to numeric, coercing errors to NaN
                numeric_amounts = pd.to_numeric(cleaned_amounts, errors='coerce').fillna(0)
                total_amount = float(numeric_amounts.sum())
                
                # Format the display safely
                if total_amount != 0:
                    st.metric("💸 Total Amount", f"¥{total_amount:,.2f}")
                else:
                    st.metric("💸 Total Amount", "¥0.00")
            except Exception as e:
                # Fallback to showing count if conversion fails
                st.metric("📝 Amount Entries", len(df['Amount'].dropna()))
        else:
            st.metric("📝 Text Cols", len(df.select_dtypes(include=['object']).columns))
    
    st.markdown("---")
    
    # Data editing section
    st.write("**✏️ Edit Your Data:**")
    st.info("💡 **Instructions:** You can edit any cell by clicking on it. Use the buttons below the table to add/remove rows. Your changes will be automatically saved.")
    
    # Configure column types for better editing experience
    column_config = {}
    for col in df.columns:
        if col == 'Amount' or 'amount' in col.lower():
            # Use TextColumn for Amount to avoid format conflicts with currency symbols
            column_config[col] = st.column_config.TextColumn(
                col,
                help="Monetary amount - use positive for income/assets, negative for expenses/liabilities (e.g. ¥1,000.00)"
            )
        elif col == 'Description' or 'description' in col.lower():
            column_config[col] = st.column_config.TextColumn(
                col,
                help="Transaction or item description",
                max_chars=200
            )
        elif col == 'User' or 'user' in col.lower():
            column_config[col] = st.column_config.TextColumn(
                col,
                help="User identifier for multi-user tracking"
            )
        elif col in ['Debit', 'Credit', 'Category', 'Type']:
            column_config[col] = st.column_config.TextColumn(
                col,
                help=f"{col} category or account"
            )
    
    # Show editable dataframe with enhanced configuration
    edited_df = st.data_editor(
        df,
        key=editor_key,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",  # Allow adding/removing rows
        column_config=column_config,
        disabled=False,  # Enable all editing
        height=400  # Set reasonable height for editing
    )
    
    # Show changes summary
    if not edited_df.equals(df):
        st.success("✅ **Changes detected!** Your modifications will be applied to the financial statement generation.")
        
        # Show what changed
        with st.expander("🔍 View Changes Summary", expanded=False):
            changes_detected = False
            
            # Check for row count changes
            if len(edited_df) != len(df):
                st.write(f"**Rows:** {len(df)} → {len(edited_df)} ({len(edited_df) - len(df):+d})")
                changes_detected = True
            
            # Check for value changes (simplified check)
            for col in df.columns:
                if col in edited_df.columns:
                    try:
                        orig_sum = df[col].sum() if df[col].dtype in ['int64', 'float64'] else len(df[col].dropna())
                        edit_sum = edited_df[col].sum() if edited_df[col].dtype in ['int64', 'float64'] else len(edited_df[col].dropna())
                        if orig_sum != edit_sum:
                            if df[col].dtype in ['int64', 'float64']:
                                st.write(f"**{col} total:** ¥{orig_sum:,.2f} → ¥{edit_sum:,.2f}")
                            changes_detected = True
                    except (TypeError, ValueError):
                        # Skip columns that can't be summed properly
                        changes_detected = True
            
            if not changes_detected:
                st.write("Minor text changes detected.")
    else:
        st.info("ℹ️ No changes made. Original data will be used for processing.")
    
    return edited_df


def show_save_to_system_option(year_month: str) -> bool:
    """
    Display save to system option.
    
    Args:
        year_month: Year-month string for display
        
    Returns:
        True if user wants to save to system
    """
    return st.checkbox(
        f"💾 Save results to system for {year_month}",
        help="Save generated statements for future comparison and analysis"
    )


def display_processing_results(results: Dict[str, Any], result_type: str):
    """
    Display processing results in formatted manner.
    
    Args:
        results: Results dictionary to display
        result_type: Type of results (e.g., "Income Statement", "Cash Flow")
    """
    st.success(f"✅ {result_type} generated successfully!")
    
    # Display summary metrics if available
    if 'Combined' in results:
        combined = results['Combined']
        if 'Total Revenue' in combined and 'Total Expenses' in combined:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Revenue", f"¥{combined['Total Revenue']:,.2f}")
            with col2:
                st.metric("Total Expenses", f"¥{combined['Total Expenses']:,.2f}")  
            with col3:
                st.metric("Net Income", f"¥{combined['Net Income']:,.2f}")


def display_error_message(error: Exception, context: str = ""):
    """
    Display error message in user-friendly format.
    
    Args:
        error: Exception that occurred
        context: Additional context for the error
    """
    st.error(f"❌ {context} Error: {str(error)}")
    
    with st.expander("📋 Technical Details"):
        st.code(str(error))


def show_user_selection(users: list, selection_key: str) -> str:
    """
    Display user selection dropdown.
    
    Args:
        users: List of available users
        selection_key: Unique key for selection
        
    Returns:
        Selected user or "Combined"
    """
    all_options = ["Combined"] + users
    return st.selectbox(
        "Select Entity:",
        options=all_options,
        key=selection_key,
        help="Choose individual user or Combined for all users"
    )


def display_statement_table(statement_data: Dict, title: str):
    """
    Display statement data as formatted table.
    
    Args:
        statement_data: Statement data dictionary
        title: Title for the table
    """
    st.subheader(title)
    
    # Convert to display format
    display_data = []
    
    if 'Revenue' in statement_data:
        display_data.append(["**REVENUE**", ""])
        for category, amount in statement_data['Revenue'].items():
            display_data.append([f"  {category}", f"¥{amount:,.2f}"])
        display_data.append(["**Total Revenue**", f"¥{statement_data['Total Revenue']:,.2f}"])
        display_data.append(["", ""])
    
    if 'Expenses' in statement_data:
        display_data.append(["**EXPENSES**", ""])
        for category, amount in statement_data['Expenses'].items():
            display_data.append([f"  {category}", f"¥{amount:,.2f}"])
        display_data.append(["**Total Expenses**", f"¥{statement_data['Total Expenses']:,.2f}"])
        display_data.append(["", ""])
    
    if 'Net Income' in statement_data:
        display_data.append(["**NET INCOME**", f"¥{statement_data['Net Income']:,.2f}"])
    
    # Display as dataframe
    df = pd.DataFrame(display_data, columns=["Item", "Amount"])
    st.dataframe(df, use_container_width=True, hide_index=True)


def show_export_options() -> Dict[str, bool]:
    """
    Display export options.
    
    Returns:
        Dictionary of export format selections
    """
    st.write("**Export Options:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv_export = st.checkbox("📄 CSV Export", value=True)
    with col2:
        json_export = st.checkbox("📋 JSON Export")
    with col3:
        excel_export = st.checkbox("📊 Excel Export")
    
    return {
        'csv': csv_export,
        'json': json_export,  
        'excel': excel_export
    }