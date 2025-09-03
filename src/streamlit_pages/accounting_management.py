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
from src.accounting import (
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


def show_simplified_accounting_page():
    """Main accounting page with simplified interface"""
    st.header("💰 Simplified Accounting Module")
    st.markdown("Streamlined financial statement generation from CSV data")
    
    # Create tabs for different functions
    tab1, tab2, tab3 = st.tabs([
        "📊 Income & Cash Flow Statements", 
        "📈 Balance Sheet", 
        "📝 Templates"
    ])
    
    with tab1:
        show_income_cashflow_tab()
    
    with tab2:
        show_balance_sheet_tab()
    
    with tab3:
        show_data_templates()


def show_income_cashflow_tab():
    """Combined tab for income statement and cash flow generation"""
    st.subheader("📊 Income Statement & Cash Flow Generation")
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
            os.unlink(tmp_file_path)
            # Also cleanup edited file if it exists
            edited_tmp_file = tmp_file_path.replace('.csv', '_edited.csv')
            if os.path.exists(edited_tmp_file):
                os.unlink(edited_tmp_file)
            
        except Exception as e:
            st.error(f"Error processing transactions: {str(e)}")


def show_balance_sheet_tab():
    """Tab for balance sheet generation"""
    st.subheader("📈 Balance Sheet Generation")
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
            if st.checkbox("Show assets preview"):
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
            
            if st.button("Generate Balance Sheet"):
                # Generate balance sheet
                generator = BalanceSheetGenerator(exchange_rate=exchange_rate)
                statement = generator.generate_statement(tmp_file_path)
                
                # Display results
                st.subheader("Balance Sheet Results")
                
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
            os.unlink(tmp_file_path)
            
        except Exception as e:
            st.error(f"Error processing assets: {str(e)}")




# Sample data templates for users
def show_data_templates():
    """Show sample CSV templates"""
    st.subheader("📝 CSV Template Examples")
    st.markdown("Use these templates to format your CSV files correctly")
    
    # Transaction template
    st.write("**Transactions CSV Template:**")
    st.markdown("Use this format for income statement and cash flow generation")
    transaction_template = pd.DataFrame([
        {"Description": "Monthly Salary", "Amount": 8000.0, "Debit": "工资收入", "Credit": "Bank Account", "User": "User1"},
        {"Description": "Rent Payment", "Amount": -2000.0, "Debit": "房租", "Credit": "Bank Account", "User": "User1"},
        {"Description": "Groceries", "Amount": -800.0, "Debit": "餐饮", "Credit": "Credit Card", "User": "User1"},
        {"Description": "Freelance Work", "Amount": 2000.0, "Debit": "服务收入", "Credit": "Cash Account", "User": "User2"},
        {"Description": "Transportation", "Amount": -200.0, "Debit": "交通", "Credit": "Cash Account", "User": "User2"},
    ])
    st.dataframe(transaction_template, use_container_width=True)
    
    # Download button for transaction template
    csv = transaction_template.to_csv(index=False)
    st.download_button(
        label="📥 Download Transaction Template",
        data=csv,
        file_name="transactions_template.csv",
        mime="text/csv"
    )
    
    st.markdown("---")
    
    # Assets template
    st.write("**Assets CSV Template:**")
    st.markdown("Use this format for balance sheet generation")
    assets_template = pd.DataFrame([
        {"Account Type": "Cash CNY", "Account": "招商银行储蓄卡", "CNY": "¥15,000.00", "USD": "$0.00"},
        {"Account Type": "Cash USD", "Account": "美国银行支票账户", "CNY": "¥0.00", "USD": "$2,000.00"},
        {"Account Type": "Investment", "Account": "股票投资账户", "CNY": "¥35,000.00", "USD": "$0.00"},
        {"Account Type": "Long-Term Investment", "Account": "退休基金", "CNY": "¥0.00", "USD": "$5,000.00"},
    ])
    st.dataframe(assets_template, use_container_width=True)
    
    # Download button for assets template
    csv = assets_template.to_csv(index=False)
    st.download_button(
        label="📥 Download Assets Template",
        data=csv,
        file_name="assets_template.csv",
        mime="text/csv"
    )
    
    st.markdown("---")
    
    # Category reference
    st.write("**Available Transaction Categories:**")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Revenue Categories:**")
        st.write("- 工资收入 (Salary Income)")
        st.write("- 服务收入 (Service Income)")
        st.write("- 投资收益 (Investment Income)")
        st.write("- 其他收入 (Other Income)")
    
    with col2:
        st.write("**Expense Categories:**")
        st.write("- 餐饮 (Food & Dining)")
        st.write("- 房租 (Rent)")
        st.write("- 交通 (Transportation)")
        st.write("- 水电 (Utilities)")
        st.write("- 日用购物 (General Shopping)")
        st.write("- 个人消费 (Personal Expenses)")
        st.write("- 运动和健康 (Health & Wellness)")
        st.write("- 宠物 (Pet Expenses)")


# Main function for the accounting management page
def accounting_management_page():
    """Main accounting management page function"""
    show_simplified_accounting_page()