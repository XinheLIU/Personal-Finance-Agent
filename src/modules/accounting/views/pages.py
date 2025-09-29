"""
Accounting Page Views

Contains the main page layouts for accounting functionality.
All business logic is delegated to presenters.
"""

import streamlit as st
from typing import Optional

from ..presenters.transaction_presenter import TransactionPresenter
from ..presenters.income_statement_presenter import IncomeStatementPresenter
from ..presenters.cash_flow_presenter import CashFlowPresenter
from .components import (
    handle_csv_upload, 
    show_csv_help,
    show_data_preview_editor,
    display_processing_results,
    display_error_message,
    show_user_selection,
    display_statement_table,
    show_export_options
)


def show_income_cashflow_tab():
    """Display the income statement and cash flow generation tab (passive view)"""
    st.header("📊 Income Statement & Cash Flow Generation")
    
    # CSV format help
    format_info = {
        "Description": "Transaction description (Chinese/English supported)",
        "Amount": "Transaction amount (positive for income, negative for expenses)",
        "Debit": "Debit account/category",
        "Credit": "Credit account/category",
        "User": "User identifier for multi-user support"
    }
    show_csv_help(format_info)
    
    # File upload
    tmp_file_path = handle_csv_upload(
        "income_csv_upload",
        "Upload CSV file with transaction data for income statement generation"
    )
    
    if tmp_file_path:
        try:
            # Load and preview data for user editing
            import pandas as pd
            uploaded_df = pd.read_csv(tmp_file_path)
            
            st.subheader("📊 Review and Edit Your Data")
            st.info("📝 You can review and edit your uploaded data below before generating statements. Any changes will be applied to the final results.")
            
            # Show data preview and editor
            edited_df = show_data_preview_editor(uploaded_df, "income_data_editor")
            
            # Check if user made edits
            if not edited_df.equals(uploaded_df):
                st.success("✅ Data has been modified! Your changes will be used for processing.")
                # Save edited data to temporary file
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file:
                    edited_df.to_csv(tmp_file.name, index=False)
                    processed_file_path = tmp_file.name
            else:
                processed_file_path = tmp_file_path
            
            # Process data with user edits (if any)
            if st.button("📈 Generate Income Statement & Cash Flow", type="primary"):
                with st.spinner("Processing your financial data..."):
                    # Use presenter to handle business logic
                    presenter = TransactionPresenter()
                    income_statements, cashflow_statements, users = presenter.process_transaction_statements(processed_file_path)
                    
                    # Display results (passive view)
                    display_processing_results(income_statements, "Income Statement")
                    
                    # User selection for detailed view
                    selected_entity = show_user_selection(users, "income_user_select")
                    
                    # Display selected statement
                    if selected_entity in income_statements:
                        display_statement_table(
                            income_statements[selected_entity], 
                            f"Income Statement - {selected_entity}"
                        )
                    
                    # Export options
                    export_options = show_export_options()
                    
                    if any(export_options.values()):
                        st.info("Export functionality will be implemented by presenter layer")
                
        except TypeError as e:
            if "can only concatenate str" in str(e):
                st.error("❌ Data Type Error: Your CSV file contains mixed data types that cannot be processed.")
                st.info("🔧 **Solution**: Please ensure all text fields (Description, User, Debit, Credit) contain only text values, not numbers.")
                with st.expander("📋 Technical Details"):
                    st.code(str(e))
            else:
                display_error_message(e, "Income Statement Generation")
        except ValueError as e:
            st.error("❌ Data Format Error: There's an issue with the data format in your CSV file.")
            st.info("🔧 **Solution**: Please check that amounts are properly formatted and all required columns are present.")
            with st.expander("📋 Technical Details"):
                st.code(str(e))
        except Exception as e:
            display_error_message(e, "Income Statement Generation")


def show_balance_sheet_tab():
    """Display the balance sheet generation tab (passive view)"""
    st.header("🏦 Balance Sheet Generation")
    
    # CSV format help
    format_info = {
        "Asset/Liability": "Name of asset or liability",
        "Type": "Asset, Liability, or Equity",
        "Amount": "Current balance amount",
        "User": "User identifier for multi-user support"
    }
    show_csv_help(format_info)
    
    st.info("Balance sheet functionality will be implemented with presenter pattern")
    
    # File upload placeholder
    tmp_file_path = handle_csv_upload(
        "balance_csv_upload",
        "Upload CSV file with asset/liability data"
    )
    
    if tmp_file_path:
        try:
            # Load and preview data for user editing
            import pandas as pd
            uploaded_df = pd.read_csv(tmp_file_path)
            
            st.subheader("📊 Review and Edit Your Data")
            st.info("📝 You can review and edit your uploaded balance sheet data below before generating statements. Any changes will be applied to the final results.")
            
            # Show data preview and editor
            edited_df = show_data_preview_editor(uploaded_df, "balance_data_editor")
            
            # Check if user made edits
            if not edited_df.equals(uploaded_df):
                st.success("✅ Data has been modified! Your changes will be used for processing.")
                # Save edited data to temporary file
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file:
                    edited_df.to_csv(tmp_file.name, index=False)
                    processed_file_path = tmp_file.name
            else:
                processed_file_path = tmp_file_path
            
            # Process data with user edits (if any)
            if st.button("📊 Generate Balance Sheet", type="primary"):
                with st.spinner("Processing your balance sheet data..."):
                    st.info("Balance sheet generation functionality will be implemented with presenter pattern")
                    st.success(f"✅ Balance sheet processing will use: {processed_file_path}")
        
        except Exception as e:
            display_error_message(e, "Balance Sheet Generation")


def show_monthly_comparison_tab():
    """Display the monthly comparison tab (passive view)"""
    st.header("📈 Monthly Comparison Analysis")
    
    st.info("Monthly comparison will be refactored to use presenter pattern")
    
    # Month selection
    col1, col2 = st.columns(2)
    with col1:
        year = st.selectbox("Year:", [2024, 2025], key="comparison_year")
    with col2:
        month = st.selectbox("Month:", list(range(1, 13)), key="comparison_month")
    
    if st.button("Generate Comparison", key="generate_comparison"):
        st.info(f"Comparison for {year}-{month:02d} will be generated by presenter")


def accounting_management_page():
    """Main accounting management page with tab navigation (passive view)"""
    st.title("💰 Accounting Management")
    
    # Tab navigation
    tab1, tab2, tab3 = st.tabs([
        "📊 Income Statement & Cash Flow",
        "🏦 Balance Sheet", 
        "📈 Monthly Comparison"
    ])
    
    with tab1:
        show_income_cashflow_tab()
    
    with tab2:
        show_balance_sheet_tab()
        
    with tab3:
        show_monthly_comparison_tab()