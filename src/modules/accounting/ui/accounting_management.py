"""
Simplified Accounting Management Page

A streamlined interface for the simplified accounting module that supports:
- Transaction CSV upload and processing
- Income statement generation
- Cash flow statement generation  
- Balance sheet generation from assets CSV
"""

import streamlit as st
import pandas as pd
import os
import tempfile
from datetime import datetime
from typing import Dict, Any, List

# Import simplified accounting components
from src.modules.accounting.core import (
    Transaction,
    CategoryMapper,
    REVENUE_CATEGORIES,
    TransactionProcessor,
    IncomeStatementGenerator,
    CashFlowStatementGenerator,
    BalanceSheetGenerator,
    FinancialReportGenerator,
    print_income_statement,
    print_cash_flow_statement,
    print_balance_sheet,
)

# Import new data storage and comparison components
from src.modules.accounting.core.data_storage import MonthlyDataStorage
from src.modules.accounting.core.data_storage_utils import (
    get_current_year_month, 
    get_recent_months, 
    validate_month_format,
    csv_to_dataframe
)
from src.modules.accounting.core.report_storage import MonthlyReportStorage
from src.modules.accounting.core.monthly_comparison import MonthlyComparisonEngine


def show_simplified_accounting_page():
    """Simplified accounting page with core statement generation only"""
    st.header("💰 Accounting")
    st.markdown("Professional financial statement generation from CSV data")
    
    # Create simplified tabs for core accounting functions only
    tab1, tab2, tab3 = st.tabs([
        "📊 Income & Cash Flow Statements", 
        "📈 Balance Sheet", 
        "📊 Monthly Comparison"
    ])
    
    with tab1:
        show_income_cashflow_tab()
    
    with tab2:
        show_balance_sheet_tab()
        
    with tab3:
        show_monthly_comparison_tab()
    
    # Direct users to System & Data Management for data operations
    st.divider()
    st.info("💡 **Data Management**: To upload, edit, or manage accounting data, visit the **System & Data Management** page → Accounting Data tab.")


def show_income_cashflow_tab():
    """Combined tab for income statement and cash flow generation"""
    st.subheader("📊 Income Statement & Cash Flow Generation")
    
    # Add help section
    with st.expander("❓ CSV Format Help", expanded=False):
        st.markdown("""**Required CSV Columns:**
        - `Description`: Transaction description (any language supported)
        - `Amount`: Numeric amount (¥1000.50 or 1000.50)
        - `Debit`: Category name (餐饮, 房租, 工资收入, etc.)
        - `Credit`: Account name (Bank Account, Credit Card, etc.)
        - `User`: User identifier (User1, User2, etc.)
        
        **Sample Row:**
        ```
        Description,Amount,Debit,Credit,User
        Monthly Salary,8000.0,工资收入,Bank Account,User1
        Rent Payment,-2000.0,房租,Bank Account,User1
        ```""")
    
    st.markdown("Upload transaction CSV to generate both income statements and cash flow statements for all users")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Transactions CSV",
        type=['csv'],
        help="CSV should contain: Description, Amount, Debit, Credit, User columns"
    )
    
    if uploaded_file is not None:
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            # Load and show enhanced transaction preview
            df = pd.read_csv(tmp_file_path)
            st.success(f"CSV file loaded with {len(df)} transactions")
            
            # Enhanced transaction preview (50 lines, editable)
            with st.expander("📊 Transaction Data Preview & Editor (up to 50 rows)", expanded=False):
                st.info("💡 You can edit the data below before processing. Changes will be used for statement generation.")
                
                # Show up to 50 rows and make it editable
                preview_df = df.head(50)
                edited_df = st.data_editor(
                    preview_df,
                    use_container_width=True,
                    num_rows="dynamic",
                    column_config={
                        "Amount": st.column_config.NumberColumn(
                            "Amount",
                            help="Transaction amount",
                            format="¥%.2f"
                        ),
                        "Description": st.column_config.TextColumn(
                            "Description",
                            help="Transaction description",
                            max_chars=200
                        )
                    },
                    key="transaction_editor"
                )
                
                # Check if data was edited
                if not edited_df.equals(preview_df):
                    st.success("✅ Data has been edited! The modified data will be used for processing.")
                    
                    # Update the full DataFrame with edited changes
                    # For rows that were edited, update the original DataFrame
                    for idx in edited_df.index:
                        if idx < len(df):
                            for col in edited_df.columns:
                                if idx < len(edited_df) and col in df.columns:
                                    df.iloc[idx][col] = edited_df.iloc[idx][col]
                    
                    # Save the edited data to a new temporary file
                    edited_tmp_file = tmp_file_path.replace('.csv', '_edited.csv')
                    df.to_csv(edited_tmp_file, index=False)
                    tmp_file_path = edited_tmp_file  # Use edited file for processing
            
            # Process transactions with potentially edited data
            processor = TransactionProcessor(tmp_file_path)
            processor.load_transactions()
            
            # Get users
            users = processor.get_all_users()
            if users:
                st.write(f"**Found users:** {', '.join(users)}")
                
                # Add save to system option before generation
                save_to_system, selected_month = add_save_to_system_option(key_prefix="income_cashflow", data_type="transactions")
                
                if st.button("Generate All Statements", type="primary"):
                    # Generate reports using FinancialReportGenerator pattern
                    generator = FinancialReportGenerator(tmp_file_path)
                    
                    # Create generators
                    income_generator = IncomeStatementGenerator(CategoryMapper())
                    cashflow_generator = CashFlowStatementGenerator(CategoryMapper())
                    
                    # Generate statements for all users
                    income_statements = {}
                    cashflow_statements = {}
                    
                    # Individual user statements
                    for user in users:
                        user_transactions = processor.get_transactions_by_user(user)
                        
                        # Generate income statement
                        income_stmt = income_generator.generate_statement(user_transactions, user)
                        income_statements[user] = income_stmt
                        
                        # Generate cash flow statement  
                        cashflow_stmt = cashflow_generator.generate_statement(user_transactions, user)
                        cashflow_statements[user] = cashflow_stmt
                    
                    # Combined statements
                    combined_income = income_generator.generate_statement(processor.transactions, "Combined")
                    combined_cashflow = cashflow_generator.generate_statement(processor.transactions, "Combined")
                    income_statements["Combined"] = combined_income
                    cashflow_statements["Combined"] = combined_cashflow
                    
                    # Display results
                    st.success("All statements generated successfully!")
                    
                    # Save to system if requested
                    if save_to_system and selected_month:
                        try:
                            with st.spinner("Saving data to system..."):
                                # Initialize storage components
                                data_storage = MonthlyDataStorage()
                                report_storage = MonthlyReportStorage()
                                
                                # Save transaction data
                                transaction_df = pd.read_csv(tmp_file_path)
                                save_results = data_storage.save_monthly_data(
                                    selected_month,
                                    transactions_df=transaction_df,
                                    overwrite=True
                                )
                                
                                # Save generated statements
                                statement_save_count = 0
                                
                                # Save income statements
                                for entity, income_stmt in income_statements.items():
                                    if report_storage.save_statement(
                                        selected_month,
                                        "income_statement",
                                        income_stmt,
                                        {"entity": entity, "generation_method": "csv_upload"}
                                    ):
                                        statement_save_count += 1
                                
                                # Save cash flow statements  
                                for entity, cashflow_stmt in cashflow_statements.items():
                                    if report_storage.save_statement(
                                        selected_month,
                                        "cash_flow", 
                                        cashflow_stmt,
                                        {"entity": entity, "generation_method": "csv_upload"}
                                    ):
                                        statement_save_count += 1
                                
                                if save_results["transactions"] and statement_save_count > 0:
                                    st.success(f"✅ Successfully saved data for {selected_month}:")
                                    st.info(f"• Transaction data: {len(transaction_df)} records")
                                    st.info(f"• Financial statements: {statement_save_count} statements saved")
                                    st.info("📊 Data is now available in the Monthly Comparison tab")
                                    st.info("ℹ️ Note: Non-numeric amounts were automatically cleaned and converted to 0.0")
                                else:
                                    st.warning("⚠️ Some data may not have been saved properly")
                                
                        except Exception as save_error:
                            st.error(f"❌ Error saving data to system: {str(save_error)}")
                            st.info("Statements were generated successfully but not saved to system")
                    
                    # Create tabs for different views
                    result_tab1, result_tab2 = st.tabs([
                        "📊 Income Statements",
                        "💧 Cash Flow Statements"
                    ])
                    
                    with result_tab1:
                        st.subheader("Income Statements Summary")
                        
                        # Create summary table
                        income_summary = []
                        for entity, stmt in income_statements.items():
                            income_summary.append({
                                'Entity': entity,
                                'Total Revenue': stmt['Total Revenue'],
                                'Total Expenses': stmt['Total Expenses'],
                                'Net Income': stmt['Net Income']
                            })
                        
                        income_df = pd.DataFrame(income_summary)
                        st.dataframe(income_df, use_container_width=True)
                        
                        # Download button
                        csv = income_df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Income Statements CSV",
                            data=csv,
                            file_name="income_statements_summary.csv",
                            mime="text/csv"
                        )
                        
                        # Add detailed breakdowns for each entity
                        st.markdown("---")
                        st.subheader("🔍 Detailed Income Breakdowns")
                        
                        for entity, income_stmt in income_statements.items():
                            with st.expander(f"📊 {entity} - Income Details", expanded=False):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.markdown("**📈 Revenue Breakdown**")
                                    if income_stmt['Revenue']:
                                        revenue_df = pd.DataFrame(
                                            list(income_stmt['Revenue'].items()), 
                                            columns=['Category', 'Amount (¥)']
                                        )
                                        revenue_df['Amount (¥)'] = revenue_df['Amount (¥)'].apply(lambda x: f"¥{x:,.2f}")
                                        st.dataframe(revenue_df, use_container_width=True, hide_index=True)
                                    else:
                                        st.info("No revenue data for this entity")
                                
                                with col2:
                                    st.markdown("**📉 Expense Breakdown**")
                                    if income_stmt['Expenses']:
                                        expense_df = pd.DataFrame(
                                            list(income_stmt['Expenses'].items()), 
                                            columns=['Category', 'Amount (¥)']
                                        )
                                        expense_df['Amount (¥)'] = expense_df['Amount (¥)'].apply(lambda x: f"¥{x:,.2f}")
                                        st.dataframe(expense_df, use_container_width=True, hide_index=True)
                                    else:
                                        st.info("No expense data for this entity")
                                
                                # Summary metrics for this entity
                                st.markdown("**💰 Summary Metrics**")
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Total Revenue", f"¥{income_stmt['Total Revenue']:,.2f}")
                                with col2:
                                    st.metric("Total Expenses", f"¥{income_stmt['Total Expenses']:,.2f}")
                                with col3:
                                    st.metric("Net Income", f"¥{income_stmt['Net Income']:,.2f}")
                    
                    with result_tab2:
                        st.subheader("Cash Flow Summary")
                        
                        # Create summary table
                        cashflow_summary = []
                        for entity, stmt in cashflow_statements.items():
                            cashflow_summary.append({
                                'Entity': entity,
                                'Operating Cash Flow': stmt['Operating Activities']['Net Cash from Operating'],
                                'Investing Cash Flow': stmt['Investing Activities']['Net Cash from Investing'],
                                'Financing Cash Flow': stmt['Financing Activities']['Net Cash from Financing'],
                                'Net Change in Cash': stmt['Net Change in Cash']
                            })
                        
                        cashflow_df = pd.DataFrame(cashflow_summary)
                        st.dataframe(cashflow_df, use_container_width=True)
                        
                        # Download button
                        csv = cashflow_df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Cash Flow Statements CSV",
                            data=csv,
                            file_name="cashflow_statements_summary.csv",
                            mime="text/csv"
                        )
                        
                        # Add detailed cash flow activities for each entity
                        st.markdown("---")
                        st.subheader("🔍 Detailed Cash Flow Activities")
                        
                        for entity, cashflow_stmt in cashflow_statements.items():
                            with st.expander(f"💧 {entity} - Cash Flow Details", expanded=False):
                                # Summary metrics for this entity
                                st.markdown("**💰 Cash Flow Summary**")
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Operating", f"¥{cashflow_stmt['Operating Activities']['Net Cash from Operating']:,.2f}")
                                with col2:
                                    st.metric("Investing", f"¥{cashflow_stmt['Investing Activities']['Net Cash from Investing']:,.2f}")
                                with col3:
                                    st.metric("Financing", f"¥{cashflow_stmt['Financing Activities']['Net Cash from Financing']:,.2f}")
                                with col4:
                                    st.metric("Net Change", f"¥{cashflow_stmt['Net Change in Cash']:,.2f}")
                                
                                # Activity details
                                st.markdown("**📊 Activity Breakdowns**")
                                activity_cols = st.columns(3)
                                
                                for idx, activity_type in enumerate(["Operating Activities", "Investing Activities", "Financing Activities"]):
                                    with activity_cols[idx]:
                                        st.markdown(f"**{activity_type.split()[0]}**")
                                        if cashflow_stmt[activity_type]['Details']:
                                            details_df = pd.DataFrame(
                                                list(cashflow_stmt[activity_type]['Details'].items()), 
                                                columns=['Category', 'Amount (¥)']
                                            )
                                            details_df['Amount (¥)'] = details_df['Amount (¥)'].apply(lambda x: f"¥{x:,.2f}")
                                            st.dataframe(details_df, use_container_width=True, hide_index=True)
                                        else:
                                            st.info(f"No {activity_type.lower()}")
                    
                    
            # Cleanup temporary files
            _cleanup_temp_files(tmp_file_path)
            
        except Exception as e:
            st.error(f"Error processing transactions: {str(e)}")


def show_balance_sheet_tab():
    """Tab for balance sheet generation"""
    st.subheader("📈 Balance Sheet Generation")
    
    # Add help section
    with st.expander("❓ CSV Format Help", expanded=False):
        st.markdown("""**Required CSV Columns:**
        - `Account Type`: Asset category (Cash CNY, Cash USD, Investment, Long-Term Investment)
        - `Account`: Account name/description
        - `CNY`: Amount in Chinese Yuan (¥15,000.00 or 15000)
        - `USD`: Amount in US Dollars ($2,000.00 or 2000)
        
        **Sample Row:**
        ```
        Account Type,Account,CNY,USD
        Cash CNY,招商银行储蓄卡,¥15000.00,$0.00
        Cash USD,美国银行支票账户,¥0.00,$2000.00
        ```""")
    
    st.markdown("Upload assets CSV to generate balance sheet")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Assets CSV",
        type=['csv'],
        key="balance_upload",
        help="CSV should contain: Account Type, Account, CNY, USD columns"
    )
    
    if uploaded_file is not None:
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            # Show CSV preview
            if st.checkbox("Show assets preview", key="balance_sheet_preview"):
                df = pd.read_csv(tmp_file_path)
                st.dataframe(df)
            
            # Exchange rate input
            exchange_rate = st.number_input(
                "USD/CNY Exchange Rate", 
                value=7.0, 
                min_value=1.0, 
                max_value=20.0,
                step=0.01,
                help="Exchange rate for CNY to USD conversion"
            )
            
            # Add save to system option before generation
            save_to_system, selected_month = add_save_to_system_option(key_prefix="balance_sheet", data_type="assets")
            
            if st.button("Generate Balance Sheet"):
                # Generate balance sheet
                generator = BalanceSheetGenerator(exchange_rate=exchange_rate)
                statement = generator.generate_statement(tmp_file_path)
                
                # Display results
                st.subheader("Balance Sheet Results")
                
                # Save to system if requested
                if save_to_system and selected_month:
                    try:
                        with st.spinner("Saving balance sheet data to system..."):
                            # Initialize storage components
                            data_storage = MonthlyDataStorage()
                            report_storage = MonthlyReportStorage()
                            
                            # Save assets data
                            assets_df = pd.read_csv(tmp_file_path)
                            save_results = data_storage.save_monthly_data(
                                selected_month,
                                assets_df=assets_df,
                                overwrite=True
                            )
                            
                            # Save balance sheet statement
                            statement_saved = report_storage.save_statement(
                                selected_month,
                                "balance_sheet",
                                statement,
                                {"generation_method": "csv_upload", "exchange_rate": exchange_rate}
                            )
                            
                            if save_results["assets"] and statement_saved:
                                st.success(f"✅ Successfully saved balance sheet data for {selected_month}:")
                                st.info(f"• Asset data: {len(assets_df)} records")
                                st.info(f"• Balance sheet statement saved")
                                st.info("📊 Data is now available in the Monthly Comparison tab")
                                st.info("ℹ️ Note: Non-numeric amounts were automatically cleaned and converted to 0.0")
                            else:
                                st.warning("⚠️ Some data may not have been saved properly")
                            
                    except Exception as save_error:
                        st.error(f"❌ Error saving balance sheet data: {str(save_error)}")
                        st.info("Balance sheet was generated successfully but not saved to system")
                
                # Current Assets
                st.subheader("Current Assets")
                current_assets = statement["Current Assets"]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**CNY Values**")
                    st.write(f"Cash: ¥{current_assets['Cash']['CNY']:,.2f}")
                    st.write(f"Investments: ¥{current_assets['Investments']['CNY']:,.2f}")
                    st.write(f"Other: ¥{current_assets['Other']['CNY']:,.2f}")
                    st.write(f"**Total: ¥{current_assets['Total Current Assets']['CNY']:,.2f}**")
                
                with col2:
                    st.write("**USD Values**")
                    st.write(f"Cash: ${current_assets['Cash']['USD']:,.2f}")
                    st.write(f"Investments: ${current_assets['Investments']['USD']:,.2f}")
                    st.write(f"Other: ${current_assets['Other']['USD']:,.2f}")
                    st.write(f"**Total: ${current_assets['Total Current Assets']['USD']:,.2f}**")
                
                # Fixed Assets
                st.subheader("Fixed Assets")
                fixed_assets = statement["Fixed Assets"]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"Long-term Investments: ¥{fixed_assets['Long-term Investments']['CNY']:,.2f}")
                    st.write(f"**Total: ¥{fixed_assets['Total Fixed Assets']['CNY']:,.2f}**")
                
                with col2:
                    st.write(f"Long-term Investments: ${fixed_assets['Long-term Investments']['USD']:,.2f}")
                    st.write(f"**Total: ${fixed_assets['Total Fixed Assets']['USD']:,.2f}**")
                
                # Total Assets
                st.subheader("Total Assets")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Assets (CNY)", f"¥{statement['Total Assets']['CNY']:,.2f}")
                with col2:
                    st.metric("Total Assets (USD)", f"${statement['Total Assets']['USD']:,.2f}")
                
                # Create downloadable Balance Sheet table
                st.subheader("📊 Balance Sheet Summary Table")
                
                # Create structured DataFrame for download
                balance_sheet_data = []
                
                # Current Assets
                balance_sheet_data.extend([
                    {"Category": "Current Assets", "Item": "Cash", "CNY": current_assets['Cash']['CNY'], "USD": current_assets['Cash']['USD']},
                    {"Category": "Current Assets", "Item": "Investments", "CNY": current_assets['Investments']['CNY'], "USD": current_assets['Investments']['USD']},
                    {"Category": "Current Assets", "Item": "Other", "CNY": current_assets['Other']['CNY'], "USD": current_assets['Other']['USD']},
                    {"Category": "Current Assets", "Item": "Total Current Assets", "CNY": current_assets['Total Current Assets']['CNY'], "USD": current_assets['Total Current Assets']['USD']},
                ])
                
                # Fixed Assets
                balance_sheet_data.extend([
                    {"Category": "Fixed Assets", "Item": "Long-term Investments", "CNY": fixed_assets['Long-term Investments']['CNY'], "USD": fixed_assets['Long-term Investments']['USD']},
                    {"Category": "Fixed Assets", "Item": "Total Fixed Assets", "CNY": fixed_assets['Total Fixed Assets']['CNY'], "USD": fixed_assets['Total Fixed Assets']['USD']},
                ])
                
                # Total Assets
                balance_sheet_data.append({
                    "Category": "Total", "Item": "Total Assets", 
                    "CNY": statement['Total Assets']['CNY'], 
                    "USD": statement['Total Assets']['USD']
                })
                
                # Convert to DataFrame and display
                balance_sheet_df = pd.DataFrame(balance_sheet_data)
                st.dataframe(balance_sheet_df, use_container_width=True)
                
                # Download buttons
                col1, col2 = st.columns(2)
                with col1:
                    csv_data = balance_sheet_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Balance Sheet CSV",
                        data=csv_data,
                        file_name="balance_sheet.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    # Create Excel download
                    import io
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        balance_sheet_df.to_excel(writer, sheet_name='Balance Sheet', index=False)
                    excel_data = buffer.getvalue()
                    
                    st.download_button(
                        label="📥 Download Balance Sheet Excel",
                        data=excel_data,
                        file_name="balance_sheet.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                # Add account-level details section
                st.markdown("---")
                st.subheader("🔍 Account-Level Details")
                
                with st.expander("📋 Individual Account Balances", expanded=False):
                    st.markdown("**All individual accounts from your CSV:**")
                    
                    # Load the original CSV to show individual accounts
                    original_df = pd.read_csv(tmp_file_path)
                    
                    # Clean and prepare the account details table
                    account_details = []
                    for _, row in original_df.iterrows():
                        account_type = str(row.get('Account Type', '')).strip()
                        account_name = str(row.get('Account', '')).strip()
                        cny_val = generator.clean_currency_value(row.get('CNY', 0))
                        usd_val = generator.clean_currency_value(row.get('USD', 0))
                        
                        # Convert missing values using exchange rate
                        if cny_val == 0 and usd_val > 0:
                            cny_val = generator.convert_currency(usd_val, 'USD', 'CNY')
                        elif usd_val == 0 and cny_val > 0:
                            usd_val = generator.convert_currency(cny_val, 'CNY', 'USD')
                        
                        account_details.append({
                            'Account Type': account_type,
                            'Account Name': account_name,
                            'CNY Balance': f"¥{cny_val:,.2f}",
                            'USD Balance': f"${usd_val:,.2f}"
                        })
                    
                    account_details_df = pd.DataFrame(account_details)
                    st.dataframe(account_details_df, use_container_width=True, hide_index=True)
                    
                    # Download button for detailed accounts
                    account_csv = account_details_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Account Details CSV",
                        data=account_csv,
                        file_name="account_details.csv",
                        mime="text/csv"
                    )
            
            # Cleanup
            _cleanup_temp_files(tmp_file_path)
            
        except Exception as e:
            st.error(f"Error processing assets: {str(e)}")


def create_year_month_selector(key: str = "year_month", label: str = "Select Year-Month") -> str:
    """
    Create a year-month selector widget using separate year and month dropdowns.
    
    Args:
        key: Unique key for the widget
        label: Label for the selector
        
    Returns:
        Selected year-month in YYYY-MM format
    """
    # Get current month as default
    current_month = get_current_year_month()
    current_year, current_month_num = current_month.split('-')
    current_year = int(current_year)
    current_month_num = int(current_month_num)
    
    st.markdown(f"**{label}**")
    
    # Create two columns for year and month selection
    col1, col2 = st.columns(2)
    
    with col1:
        # Year selector (last 2 years to next 2 years)
        year_options = list(range(current_year - 2, current_year + 3))
        selected_year = st.selectbox(
            "Year",
            options=year_options,
            index=year_options.index(current_year),
            key=f"{key}_year"
        )
    
    with col2:
        # Month selector with concise format
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        selected_month = st.selectbox(
            "Month",
            options=list(range(1, 13)),
            format_func=lambda x: f"{x:02d} - {month_names[x-1]}",
            index=current_month_num - 1,
            key=f"{key}_month"
        )
    
    # Convert to YYYY-MM format
    return f"{selected_year:04d}-{selected_month:02d}"


def show_monthly_comparison_tab():
    """Monthly comparison tab with 12-month dashboard"""
    st.subheader("📊 Monthly Financial Comparison")
    st.markdown("Compare financial statements across the last 12 months with trend analysis")
    
    # Initialize storage and comparison engine
    report_storage = MonthlyReportStorage()
    comparison_engine = MonthlyComparisonEngine(report_storage)
    
    # Check available data
    available_statements = report_storage.list_available_statements()
    
    if not available_statements:
        st.warning("📝 No stored financial statements found. Please generate and save statements first.")
        st.info("💡 **To get started:**")
        st.info("1. Go to the Income & Cash Flow tab")
        st.info("2. Upload transaction data")
        st.info("3. Select 'Save to System' option")
        st.info("4. Generate statements for multiple months")
        return
    
    # Show available data summary
    total_months = len(available_statements)
    st.success(f"📊 Found financial data for {total_months} months: {', '.join(sorted(available_statements.keys()))}")
    
    # Statement type selector
    statement_type = st.selectbox(
        "Select Statement Type for Comparison",
        ["income_statement", "cash_flow", "balance_sheet"],
        format_func=lambda x: {
            "income_statement": "📊 Income Statement",
            "cash_flow": "💧 Cash Flow Statement", 
            "balance_sheet": "📈 Balance Sheet"
        }[x],
        key="comparison_statement_type"
    )
    
    # Time period selector - handle edge case when total_months is small
    if total_months < 2:
        st.warning("Need at least 2 months of data for comparison")
        st.info("💡 Generate and save statements for multiple months to enable comparison")
        return  # Exit early since we can't do comparison with < 2 months
    elif total_months == 2:
        # Special case: exactly 2 months, no slider needed
        comparison_months = 2
        st.info("📊 Comparing all available months (2 months)")
    else:
        # Normal case: 3+ months available
        comparison_months = st.slider(
            "Number of months to compare",
            min_value=2,
            max_value=min(12, total_months),
            value=min(6, total_months),
            help="Select how many recent months to include in comparison"
        )
    
    try:
        # Get comparison data
        with st.spinner("Loading comparison data..."):
            comparison_data = comparison_engine.get_comparison_data(
                statement_type, 
                count=comparison_months
            )
        
        available_months = comparison_data["metadata"]["available_months"]
        missing_months = comparison_data["metadata"]["missing_months"]
        
        if not available_months:
            st.error(f"No data available for {statement_type} comparison")
            return
        
        if missing_months:
            st.warning(f"⚠️ Missing data for months: {', '.join(missing_months)}")
        
        # Create comparison tabs
        comp_tab1, comp_tab2, comp_tab3 = st.tabs([
            "📋 Comparison Table",
            "📈 Trend Analysis", 
            "📊 Summary Statistics"
        ])
        
        with comp_tab1:
            st.subheader("Monthly Comparison Table")
            
            # Create comparison table
            comparison_table = comparison_engine.create_comparison_table(comparison_data)
            
            if not comparison_table.empty:
                # Format the table for better display
                formatted_table = comparison_table.copy()
                for col in formatted_table.columns:
                    formatted_table[col] = formatted_table[col].apply(
                        lambda x: f"¥{x:,.2f}" if pd.notnull(x) and isinstance(x, (int, float)) else x
                    )
                
                st.dataframe(formatted_table, use_container_width=True)
                
                # Export functionality
                csv_data = comparison_table.to_csv(index=True)
                st.download_button(
                    label="📥 Download Comparison Table",
                    data=csv_data,
                    file_name=f"{statement_type}_comparison_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No comparison data to display")
        
        with comp_tab2:
            st.subheader("Trend Analysis")
            
            # Let user select specific metrics for trend analysis
            all_metrics = comparison_engine._extract_all_metrics(comparison_data["data"])
            
            if all_metrics:
                # Simplify metric display names
                metric_display_names = {}
                metric_options = []
                for metric_path in all_metrics:
                    display_name = " > ".join(metric_path)
                    metric_display_names[display_name] = metric_path
                    metric_options.append(display_name)
                
                selected_metric = st.selectbox(
                    "Select metric for trend analysis",
                    options=metric_options,
                    help="Choose a specific financial metric to analyze trends"
                )
                
                if selected_metric:
                    metric_path = metric_display_names[selected_metric]
                    
                    # Calculate trends
                    trend_data = comparison_engine.calculate_monthly_trends(
                        comparison_data, 
                        metric_path
                    )
                    
                    if trend_data["trends"]:
                        # Display trend summary
                        summary = trend_data["summary"]
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Growth Periods", summary["growth_periods"])
                        with col2:
                            st.metric("Decline Periods", summary["decline_periods"])
                        with col3:
                            st.metric("Avg Change %", f"{summary['average_change_pct']}%")
                        with col4:
                            st.metric("Max Growth %", f"{summary['max_growth_pct']}%")
                        
                        # Trend details table
                        trend_records = []
                        for month, trend_info in trend_data["trends"].items():
                            trend_records.append({
                                "Month": month,
                                "Previous Value": f"¥{trend_info['previous_value']:,.2f}",
                                "Current Value": f"¥{trend_info['current_value']:,.2f}",
                                "Change %": f"{trend_info['percentage_change']}%",
                                "Trend": trend_info['trend_direction']
                            })
                        
                        trend_df = pd.DataFrame(trend_records)
                        st.dataframe(trend_df, use_container_width=True, hide_index=True)
                    else:
                        st.info("Not enough data points for trend analysis")
            else:
                st.info("No metrics available for trend analysis")
        
        with comp_tab3:
            st.subheader("Summary Statistics")
            
            # Get summary statistics
            summary_stats = comparison_engine.get_summary_statistics(
                statement_type,
                available_months
            )
            
            if "error" not in summary_stats:
                st.markdown(f"**Period:** {summary_stats['period']}")
                st.markdown(f"**Total Months:** {summary_stats['total_months']}")
                
                # Display statistics for each metric
                if summary_stats["metrics"]:
                    stats_records = []
                    for metric_name, stats in summary_stats["metrics"].items():
                        stats_records.append({
                            "Metric": metric_name,
                            "Count": stats["count"],
                            "Mean": f"¥{stats['mean']:,.2f}",
                            "Min": f"¥{stats['min']:,.2f}",
                            "Max": f"¥{stats['max']:,.2f}",
                            "Std Dev": f"¥{stats['std']:,.2f}",
                            "Total": f"¥{stats['total']:,.2f}"
                        })
                    
                    stats_df = pd.DataFrame(stats_records)
                    st.dataframe(stats_df, use_container_width=True, hide_index=True)
                    
                    # Export summary statistics
                    csv_data = stats_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Summary Statistics",
                        data=csv_data,
                        file_name=f"{statement_type}_summary_stats_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No metrics found for summary statistics")
            else:
                st.error(summary_stats["error"])
    
    except Exception as e:
        st.error(f"Error in monthly comparison: {str(e)}")
        st.info("Please ensure financial statements have been generated and saved to the system.")


def add_save_to_system_option(year_month: str = None, key_prefix: str = "default", data_type: str = "both") -> tuple[bool, str]:
    """
    Add save to system option widget with streamlined interface.
    
    Args:
        year_month: Pre-selected year-month (optional)
        key_prefix: Unique prefix for widget keys
        data_type: Type of data being saved ("transactions", "assets", or "both")
        
    Returns:
        Tuple of (save_enabled, selected_month)
    """
    st.markdown("---")
    st.subheader("💾 Save to System (Optional)")
    
    save_to_system = st.checkbox(
        "Save data to system for monthly comparison",
        help="Save processed data and generated statements for later comparison and trend analysis",
        key=f"{key_prefix}_save_to_system"
    )
    
    selected_month = None
    if save_to_system:
        if year_month:
            selected_month = year_month
            st.info(f"📅 Data will be saved for month: **{year_month}**")
        else:
            selected_month = create_year_month_selector(
                f"{key_prefix}_save_month", 
                "Select month for saving data"
            )
            
        if selected_month:
            _show_existing_data_warning(selected_month, data_type)
    
    return save_to_system, selected_month


def _show_existing_data_warning(selected_month: str, data_type: str):
    """Helper function to show existing data warnings."""
    data_storage = MonthlyDataStorage()
    report_storage = MonthlyReportStorage()
    
    data_info = data_storage.get_monthly_data_info(selected_month)
    existing_reports = report_storage.list_available_statements()
    
    # Check for existing data based on data type
    has_existing_data = False
    existing_data_types = []
    
    if data_type in ["transactions", "both"]:
        if data_info["transactions"]["exists"]:
            has_existing_data = True
            existing_data_types.append("transaction data")
            
    if data_type in ["assets", "both"]:
        if data_info["assets"]["exists"]:
            has_existing_data = True
            existing_data_types.append("asset data")
            
    # Check for relevant reports
    if selected_month in existing_reports:
        relevant_reports = []
        if data_type in ["transactions", "both"]:
            if "income_statement" in existing_reports[selected_month]:
                relevant_reports.append("income statements")
            if "cash_flow" in existing_reports[selected_month]:
                relevant_reports.append("cash flow statements")
        if data_type in ["assets", "both"]:
            if "balance_sheet" in existing_reports[selected_month]:
                relevant_reports.append("balance sheets")
                
        if relevant_reports:
            has_existing_data = True
            existing_data_types.extend(relevant_reports)
    
    if has_existing_data:
        data_list = ", ".join(existing_data_types)
        st.warning(f"⚠️ Existing {data_list} found for {selected_month}. Saving will overwrite previous data.")


def _cleanup_temp_files(tmp_file_path: str):
    """Helper function to cleanup temporary files."""
    try:
        os.unlink(tmp_file_path)
        # Also cleanup edited file if it exists
        edited_tmp_file = tmp_file_path.replace('.csv', '_edited.csv')
        if os.path.exists(edited_tmp_file):
            os.unlink(edited_tmp_file)
    except Exception as e:
        # Log error but don't fail the operation
        st.warning(f"Note: Could not clean up temporary files: {str(e)}")


# Legacy alias for backward compatibility
def accounting_management_page():
    """Legacy alias - use show_simplified_accounting_page() instead"""
    return show_simplified_accounting_page()