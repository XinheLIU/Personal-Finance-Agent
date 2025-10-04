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
from ..presenters.balance_sheet_presenter import BalanceSheetPresenter
from .components import (
    handle_csv_upload,
    show_csv_help,
    show_data_preview_editor,
    display_processing_results,
    display_error_message,
    show_user_selection,
    display_cash_flow_statement,
    display_statement_table
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
            # NEW WORKFLOW: Clean and validate data FIRST
            presenter = IncomeStatementPresenter()
            cleaned_df, validation_report = presenter.clean_and_validate_csv(tmp_file_path)
            
            st.subheader("📊 Review and Edit Your Data")
            
            # Show cleaning summary
            if validation_report.cleaning_actions:
                st.success("🧹 **Data Cleaning Complete**")
                st.write(validation_report.get_cleaning_summary())
                
                with st.expander("🔍 View Cleaning Details", expanded=False):
                    for action in validation_report.cleaning_actions:
                        if action.count > 0:
                            st.write(f"• **{action.description}**: {action.count} items")
                            if action.details:
                                st.write(f"  _{action.details}_")
            
            # Show validation results
            if validation_report.has_errors():
                st.error(f"❌ **Data Validation Issues Found**")
                st.write(validation_report.get_summary())
                
                with st.expander("🔍 View Validation Errors", expanded=True):
                    for error in validation_report.errors:
                        st.write(f"• {error.message}")
                
                st.warning("⚠️ Please fix the validation errors above before proceeding. You can edit the data below to correct these issues.")
            else:
                st.success("✅ **Data validation passed!** Your data is clean and ready for processing.")
            
            st.info("📝 **Clean Data Preview**: Review your cleaned data below. You can make additional edits before generating statements.")
            
            # Show CLEAN data preview and editor (not raw data!)
            edited_df = show_data_preview_editor(cleaned_df, "income_data_editor")
            
            # Check if user made edits to the CLEAN data
            if not edited_df.equals(cleaned_df):
                st.success("✅ Data has been modified! Your changes will be used for processing.")
                # Use edited DataFrame directly
                final_df = edited_df
            else:
                # Use clean DataFrame (no user edits)
                final_df = cleaned_df
            
            # Process data with user edits (if any)
            if st.button("📈 Generate Income Statement & Cash Flow", type="primary"):
                with st.spinner("Processing your financial data..."):
                    # Use NEW WORKFLOW: Process clean DataFrame directly
                    # Now generates BOTH income and cash flow statements
                    income_statements, cashflow_statements, users = presenter.process_clean_dataframe_and_generate_statements(final_df)
                    
                    # Display results (passive view)
                    display_processing_results(income_statements, "Income Statement")

                    # User selection for detailed view
                    selected_entity = show_user_selection(users, "income_user_select")

                    # Display both statements side-by-side
                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("📊 Income Statement")
                        if selected_entity in income_statements:
                            display_statement_table(
                                income_statements[selected_entity],
                                f"{selected_entity}"
                            )

                    with col2:
                        st.subheader("💰 Cash Flow Statement")
                        if selected_entity in cashflow_statements:
                            display_cash_flow_statement(cashflow_statements[selected_entity])
                    
                    # Save to memory option
                    st.write("---")
                    st.write("**💾 Save to Memory:**")

                    col1, col2 = st.columns([2, 1])
                    with col1:
                        # Get current year-month from the data or use current date
                        from datetime import datetime
                        default_month = datetime.now().strftime("%Y-%m")
                        year_month = st.text_input(
                            "Month (YYYY-MM format)",
                            value=default_month,
                            help="Specify which month this income statement belongs to"
                        )

                    with col2:
                        st.write("")  # Spacing
                        st.write("")  # Spacing
                        if st.button("💾 Save Both Statements", type="primary", use_container_width=True):
                            try:
                                from ...core.report_storage import MonthlyReportStorage
                                storage = MonthlyReportStorage()

                                # Save each user's income statement
                                income_success = 0
                                for entity, statement in income_statements.items():
                                    metadata = {
                                        "entity": entity,
                                        "generated_at": datetime.now().isoformat(),
                                        "source": "web_upload"
                                    }
                                    if storage.save_statement(year_month, "income_statement", statement, metadata):
                                        income_success += 1

                                # Save each user's cash flow statement
                                cashflow_success = 0
                                for entity, statement in cashflow_statements.items():
                                    metadata = {
                                        "entity": entity,
                                        "generated_at": datetime.now().isoformat(),
                                        "source": "web_upload"
                                    }
                                    if storage.save_statement(year_month, "cash_flow", statement, metadata):
                                        cashflow_success += 1

                                if income_success > 0 and cashflow_success > 0:
                                    st.success(f"✅ Successfully saved {income_success} income statement(s) and {cashflow_success} cash flow statement(s) for {year_month}!")
                                    st.info(f"📁 Saved to: data/accounting/monthly_reports/{year_month}/")
                                else:
                                    st.warning(f"⚠️ Partial save: {income_success} income, {cashflow_success} cash flow statements saved")

                            except ValueError as e:
                                st.error(f"❌ Invalid month format: {e}")
                            except Exception as e:
                                st.error(f"❌ Error saving to memory: {e}")
                                with st.expander("📋 Technical Details"):
                                    st.code(str(e))
                
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
    
    # CSV format help expected by generator
    format_info = {
        "Account Name": "Name of the account (e.g., 现金账户, 股票投资). 'Account' also accepted.",
        "Account Type": "One of: Cash CNY, Cash USD, Investment, Long-Term Investment. 'Type' also accepted.",
        "CNY": "Amount in Chinese Yuan (e.g., ¥25,000.00 or 25000.00)",
        "USD": "Amount in US Dollars (e.g., $3,500.00 or 3500.00)"
    }
    show_csv_help(format_info)
    
    # File upload placeholder
    tmp_file_path = handle_csv_upload(
        "balance_csv_upload",
        "Upload CSV file with asset/liability data"
    )
    
    if tmp_file_path:
        try:
            presenter = BalanceSheetPresenter()
            cleaned_df, validation_report = presenter.clean_and_validate_csv(tmp_file_path)
            
            st.subheader("📊 Review and Edit Your Data")
            
            # Show validation results
            if validation_report.has_errors():
                st.error(f"❌ **Data Validation Issues Found**")
                st.write(validation_report.get_summary())
                
                with st.expander("🔍 View Validation Errors", expanded=True):
                    for error in validation_report.errors:
                        st.write(f"• {error.message}")
                
                st.warning("⚠️ Please fix the validation errors above before proceeding.")
            else:
                st.success("✅ **Data validation passed!** Your data is clean and ready for processing.")
            
            st.info("📝 **Clean Data Preview**: Empty rows/columns removed, whitespace normalized, and CNY/USD currency symbols cleaned. You can edit below before generating the statement.")
            
            # Show CLEAN data preview and editor
            edited_df = show_data_preview_editor(cleaned_df, "balance_data_editor")
            
            # Check if user made edits to the CLEAN data
            if not edited_df.equals(cleaned_df):
                st.success("✅ Data has been modified! Your changes will be used for processing.")
                # Use edited DataFrame directly
                final_df = edited_df
            else:
                # Use clean DataFrame (no user edits)
                final_df = cleaned_df
            
            # Process data with user edits (if any)
            if st.button("📊 Generate Balance Sheet", type="primary"):
                with st.spinner("Processing your balance sheet data..."):
                    statement = presenter.process_clean_dataframe_and_generate_statement(final_df)
                    st.success("✅ Balance sheet generated!")
                    from .components import display_balance_sheet
                    display_balance_sheet(statement)

                    # Save option
                    st.write("---")
                    st.write("**💾 Save to Memory:**")
                    from datetime import datetime
                    default_month = datetime.now().strftime("%Y-%m")
                    year_month = st.text_input(
                        "Month (YYYY-MM format)",
                        value=default_month,
                        help="Specify which month this balance sheet belongs to"
                    )
                    entity = st.text_input("Entity (for filename)", value="Combined")
                    if st.button("💾 Save Balance Sheet", type="primary", use_container_width=True):
                        try:
                            from ...core.report_storage import MonthlyReportStorage
                            storage = MonthlyReportStorage()
                            metadata = {
                                "entity": entity,
                                "generated_at": datetime.now().isoformat(),
                                "source": "web_upload"
                            }
                            ok = storage.save_statement(year_month, "balance_sheet", statement, metadata)
                            if ok:
                                st.success(f"✅ Saved balance sheet for {year_month} as balance_sheet_{entity}.json")
                                st.info(f"📁 Folder: data/accounting/monthly_reports/{year_month}/")
                            else:
                                st.warning("⚠️ Failed to save balance sheet.")
                        except ValueError as e:
                            st.error(f"❌ Invalid month format: {e}")
                        except Exception as e:
                            display_error_message(e, "Save Balance Sheet")
        
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