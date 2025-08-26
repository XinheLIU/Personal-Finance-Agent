"""
Enhanced Professional Accounting Page for Streamlit

This is a temporary file to test the new accounting functionality
before integrating it into the main streamlit_app.py
"""

import streamlit as st
import pandas as pd
import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict
import uuid

def show_enhanced_accounting_page():
    """Enhanced Professional Accounting Module interface with complete financial statements."""
    st.header("💰 Enhanced Professional Accounting")
    st.markdown("Complete financial statement suite with interactive data entry and real-time analysis")
    
    # Import additional modules
    from src.accounting.balance_sheet import generate_balance_sheet
    from src.accounting.cash_flow import generate_cash_flow_statement
    from src.accounting.sample_data import (
        generate_sample_transactions, 
        generate_sample_assets, 
        get_csv_format_template,
        get_sample_data_summary
    )
    from src.accounting import (
        load_transactions_csv,
        load_assets_csv,
        save_transactions_csv,
        save_assets_csv,
        generate_monthly_income_statement,
        save_income_statement_csv,
        EXPENSE_CATEGORIES,
        REVENUE_CATEGORIES,
        Transaction,
        Asset
    )
    from src.accounting.models import get_all_categories
    
    # Initialize session state for transaction data
    if 'accounting_transactions' not in st.session_state:
        # Load existing data or create sample data
        transactions_file = "data/accounting/transactions.csv"
        if os.path.exists(transactions_file):
            try:
                st.session_state.accounting_transactions, errors = load_transactions_csv(transactions_file)
                if errors:
                    st.warning(f"Data validation issues found: {len(errors)} errors")
            except:
                st.session_state.accounting_transactions = generate_sample_transactions()
        else:
            st.session_state.accounting_transactions = generate_sample_transactions()
    
    if 'accounting_assets' not in st.session_state:
        assets_file = "data/accounting/assets.csv"
        if os.path.exists(assets_file):
            try:
                st.session_state.accounting_assets, _ = load_assets_csv(assets_file)
            except:
                st.session_state.accounting_assets = generate_sample_assets()
        else:
            st.session_state.accounting_assets = generate_sample_assets()
    
    # Quick Stats Header
    transactions = st.session_state.accounting_transactions
    assets = st.session_state.accounting_assets
    
    if transactions:
        total_income = sum(t.amount for t in transactions if t.amount > 0)
        total_expenses = sum(abs(t.amount) for t in transactions if t.amount < 0)
        net_income = total_income - total_expenses
        total_assets = sum(a.balance for a in assets)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Income", f"¥{total_income:,.2f}")
        with col2:
            st.metric("Total Expenses", f"¥{total_expenses:,.2f}")
        with col3:
            st.metric("Net Income", f"¥{net_income:,.2f}", delta=f"{(net_income/total_income*100):.1f}%" if total_income > 0 else "0%")
        with col4:
            st.metric("Total Assets", f"¥{total_assets:,.2f}")
    
    # Main layout with three columns
    col_data, col_statements, col_analysis = st.columns([1.2, 1.5, 1])
    
    # Data Entry Column
    with col_data:
        st.subheader("📝 Transaction Data")
        
        # Data management tabs
        tab_edit, tab_upload, tab_sample = st.tabs(["✏️ Edit", "📂 Upload", "🎲 Sample"])
        
        with tab_edit:
            st.markdown("**Direct Transaction Entry:**")
            
            # Convert transactions to DataFrame for editing
            if transactions:
                df_data = []
                for t in transactions[-20:]:  # Show last 20 transactions
                    df_data.append({
                        'Date': t.date.date(),  # Use date object instead of string
                        'Description': t.description,
                        'Amount': float(t.amount),
                        'Category': t.category,
                        'Account': t.account_name,
                        'Type': t.account_type
                    })
                
                df = pd.DataFrame(df_data)
                
                # Interactive data editor
                edited_df = st.data_editor(
                    df,
                    use_container_width=True,
                    num_rows="dynamic",
                    column_config={
                        'Date': st.column_config.DateColumn('Date'),
                        'Amount': st.column_config.NumberColumn('Amount', format="%.2f"),
                        'Category': st.column_config.SelectboxColumn(
                            'Category',
                            options=get_all_categories()
                        )
                    },
                    key="transaction_editor"
                )
                
                if st.button("💾 Save Changes", type="primary"):
                    # Convert back to Transaction objects
                    updated_transactions = []
                    for _, row in edited_df.iterrows():
                        try:
                            updated_transactions.append(Transaction(
                                id=str(uuid.uuid4()),
                                user_id="demo_user",
                                date=datetime.combine(row['Date'], datetime.min.time()),
                                description=row['Description'],
                                amount=Decimal(str(row['Amount'])),
                                category=row['Category'],
                                account_name=row['Account'],
                                account_type=row['Type'],
                                transaction_type="Cash"
                            ))
                        except Exception as e:
                            st.error(f"Error processing row: {e}")
                            continue
                    
                    if updated_transactions:
                        st.session_state.accounting_transactions = updated_transactions
                        st.success("✅ Transactions updated successfully!")
                        st.rerun()
            
            # Quick add transaction
            with st.expander("➕ Add New Transaction"):
                with st.form("new_transaction"):
                    new_date = st.date_input("Date", value=date.today())
                    new_desc = st.text_input("Description")
                    new_amount = st.number_input("Amount", format="%.2f")
                    new_category = st.selectbox("Category", options=get_all_categories())
                    new_account = st.text_input("Account", value="招商银行储蓄卡")
                    
                    if st.form_submit_button("Add Transaction"):
                        new_transaction = Transaction(
                            id=str(uuid.uuid4()),
                            user_id="demo_user", 
                            date=datetime.combine(new_date, datetime.min.time()),
                            description=new_desc,
                            amount=Decimal(str(new_amount)),
                            category=new_category,
                            account_name=new_account,
                            account_type="Debit",
                            transaction_type="Cash"
                        )
                        st.session_state.accounting_transactions.append(new_transaction)
                        st.success("✅ Transaction added!")
                        st.rerun()
        
        with tab_upload:
            st.markdown("**CSV File Upload:**")
            
            with st.expander("📋 View CSV Format Requirements"):
                st.text(get_csv_format_template())
            
            uploaded_file = st.file_uploader("Choose CSV file", type=['csv'])
            if uploaded_file and st.button("📂 Load CSV"):
                try:
                    # Save and load
                    os.makedirs("data/accounting", exist_ok=True)
                    with open("data/accounting/transactions.csv", 'wb') as f:
                        f.write(uploaded_file.getvalue())
                    
                    new_transactions, errors = load_transactions_csv("data/accounting/transactions.csv")
                    if errors:
                        st.error(f"❌ {len(errors)} validation errors found")
                        for error in errors[:5]:
                            st.text(f"• {error}")
                    else:
                        st.session_state.accounting_transactions = new_transactions
                        st.success(f"✅ Loaded {len(new_transactions)} transactions!")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Error loading CSV: {e}")
        
        with tab_sample:
            st.markdown("**Sample Data Management:**")
            
            summary = get_sample_data_summary()
            st.info(f"📊 Sample includes {summary['transaction_count']} transactions over {summary['months_covered']} months")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🎲 Load Sample Data"):
                    st.session_state.accounting_transactions = generate_sample_transactions()
                    st.session_state.accounting_assets = generate_sample_assets()
                    st.success("✅ Sample data loaded!")
                    st.rerun()
            
            with col2:
                if st.button("🧹 Clear All Data"):
                    st.session_state.accounting_transactions = []
                    st.session_state.accounting_assets = []
                    st.success("✅ Data cleared!")
                    st.rerun()
    
    # Financial Statements Column
    with col_statements:
        st.subheader("📊 Financial Statements")
        
        # Period selection
        col_period1, col_period2 = st.columns(2)
        with col_period1:
            selected_year = st.selectbox("Year:", [2023, 2024, 2025], index=2, key="statements_year")
        with col_period2:
            selected_month = st.selectbox("Month:", list(range(1, 13)), index=0, key="statements_month")
        
        if transactions:
            try:
                # Generate all three statements
                income_statement = generate_monthly_income_statement(transactions, selected_month, selected_year)
                balance_sheet = generate_balance_sheet(transactions, assets, date(selected_year, selected_month, 28))
                cash_flow = generate_cash_flow_statement(transactions, 
                    date(selected_year, selected_month, 1), 
                    date(selected_year, selected_month, 28))
                
                # Statement tabs
                tab_income, tab_balance, tab_cash_flow = st.tabs(["💰 Income", "🏦 Balance Sheet", "💸 Cash Flow"])
                
                with tab_income:
                    st.markdown("**Income Statement**")
                    
                    # Key metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Revenue", f"¥{income_statement['revenue']['gross_revenue']:,.2f}")
                    with col2:
                        st.metric("Expenses", f"¥{income_statement['expenses']['total_expenses']:,.2f}")
                    with col3:
                        st.metric("Net Income", f"¥{income_statement['net_operating_income']:,.2f}")
                    
                    # Revenue breakdown
                    st.markdown("**Revenue Breakdown:**")
                    revenue_df = pd.DataFrame([
                        {"Item": "Service Revenue", "Amount": income_statement['revenue']['service_revenue'], "Percent": f"{income_statement['revenue']['service_revenue_pct']:.1f}%"},
                        {"Item": "Other Income", "Amount": income_statement['revenue']['other_income'], "Percent": f"{income_statement['revenue']['other_income_pct']:.1f}%"},
                    ])
                    st.dataframe(revenue_df, use_container_width=True, hide_index=True)
                
                with tab_balance:
                    st.markdown("**Balance Sheet**")
                    
                    # Assets and liabilities summary
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Assets", f"¥{balance_sheet['assets']['total_assets']:,.2f}")
                    with col2:
                        st.metric("Total Liabilities", f"¥{balance_sheet['liabilities']['total_liabilities']:,.2f}")
                    with col3:
                        st.metric("Owner's Equity", f"¥{balance_sheet['equity']['total_equity']:,.2f}")
                    
                    # Assets breakdown
                    st.markdown("**Assets:**")
                    assets_df = pd.DataFrame([
                        {"Category": "Cash & Equivalents", "Amount": balance_sheet['assets']['current_assets']['cash_and_equivalents']},
                        {"Category": "Investments", "Amount": balance_sheet['assets']['fixed_assets']['investments']},
                        {"Category": "Equipment", "Amount": balance_sheet['assets']['fixed_assets']['equipment']},
                    ])
                    st.dataframe(assets_df, use_container_width=True, hide_index=True)
                
                with tab_cash_flow:
                    st.markdown("**Cash Flow Statement**")
                    
                    # Cash flow summary
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Operating", f"¥{cash_flow['operating_activities']['net_cash_from_operating']:,.2f}")
                    with col2:
                        st.metric("Investing", f"¥{cash_flow['investing_activities']['net_cash_from_investing']:,.2f}")
                    with col3:
                        st.metric("Financing", f"¥{cash_flow['financing_activities']['net_cash_from_financing']:,.2f}")
                    
                    # Cash flow details
                    st.markdown("**Operating Activities:**")
                    operating_df = pd.DataFrame([
                        {"Activity": "Cash from Customers", "Amount": cash_flow['operating_activities']['cash_received_from_customers']},
                        {"Activity": "Cash to Suppliers", "Amount": cash_flow['operating_activities']['cash_paid_to_suppliers']},
                        {"Activity": "Operating Expenses", "Amount": cash_flow['operating_activities']['cash_paid_for_operating_expenses']},
                        {"Activity": "Rent Payments", "Amount": cash_flow['operating_activities']['cash_paid_for_rent']},
                    ])
                    st.dataframe(operating_df, use_container_width=True, hide_index=True)
                
            except Exception as e:
                st.error(f"❌ Error generating statements: {e}")
                st.text("Please ensure you have valid transaction data.")
    
    # Analysis Column
    with col_analysis:
        st.subheader("📈 Analysis & Export")
        
        if transactions:
            # Period comparison
            st.markdown("**Period Comparison:**")
            compare_months = st.multiselect(
                "Select months to compare:",
                options=[f"{selected_year}-{m:02d}" for m in range(1, 13)],
                default=[f"{selected_year}-{selected_month:02d}"]
            )
            
            if len(compare_months) > 1:
                comparison_data = []
                for period in compare_months:
                    year, month = period.split('-')
                    year, month = int(year), int(month)
                    
                    try:
                        stmt = generate_monthly_income_statement(transactions, month, year)
                        comparison_data.append({
                            "Period": period,
                            "Revenue": stmt['revenue']['gross_revenue'],
                            "Expenses": stmt['expenses']['total_expenses'],
                            "Net Income": stmt['net_operating_income']
                        })
                    except:
                        pass
                
                if comparison_data:
                    comparison_df = pd.DataFrame(comparison_data)
                    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
                    
                    # Trend chart
                    import plotly.express as px
                    fig = px.line(comparison_df, x='Period', y=['Revenue', 'Expenses', 'Net Income'], 
                                title='Financial Trends')
                    st.plotly_chart(fig, use_container_width=True)
            
            # Export options
            st.markdown("**Export Options:**")
            
            if st.button("📄 Export Statements"):
                try:
                    os.makedirs("data/accounting/statements", exist_ok=True)
                    
                    # Export current month statements
                    income_statement = generate_monthly_income_statement(transactions, selected_month, selected_year)
                    csv_path = save_income_statement_csv(income_statement, "data/accounting/statements")
                    
                    st.success(f"✅ Exported to: {csv_path}")
                except Exception as e:
                    st.error(f"❌ Export failed: {e}")
            
            if st.button("💾 Save Current Data"):
                try:
                    os.makedirs("data/accounting", exist_ok=True)
                    
                    # Save transactions
                    save_transactions_csv(transactions, "data/accounting/transactions.csv")
                    save_assets_csv(assets, "data/accounting/assets.csv")
                    
                    st.success("✅ Data saved to CSV files!")
                except Exception as e:
                    st.error(f"❌ Save failed: {e}")
            
            # Quick insights
            st.markdown("**Quick Insights:**")
            if transactions:
                monthly_expenses = {}
                for t in transactions:
                    if t.amount < 0:  # Expenses
                        month_key = f"{t.date.year}-{t.date.month:02d}"
                        if month_key not in monthly_expenses:
                            monthly_expenses[month_key] = 0
                        monthly_expenses[month_key] += abs(t.amount)
                
                if monthly_expenses:
                    avg_expenses = sum(monthly_expenses.values()) / len(monthly_expenses)
                    st.metric("Avg Monthly Expenses", f"¥{avg_expenses:,.2f}")
                    
                    # Top expense categories
                    category_totals = {}
                    for t in transactions:
                        if t.amount < 0:
                            if t.category not in category_totals:
                                category_totals[t.category] = 0
                            category_totals[t.category] += abs(t.amount)
                    
                    if category_totals:
                        top_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)[:3]
                        st.markdown("**Top Expense Categories:**")
                        for cat, amount in top_categories:
                            st.text(f"• {cat}: ¥{amount:,.2f}")
        else:
            st.info("Load transaction data to see analysis options.")