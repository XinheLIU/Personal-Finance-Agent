"""
Result Display Views

Handles the presentation of generated financial statements and analysis results.
All business logic is handled by presenters.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List


def display_income_statements_results(income_statements: Dict, cashflow_statements: Dict, users: List[str]):
    """
    Display income statement and cash flow results (passive view).
    
    Args:
        income_statements: Income statement results by entity
        cashflow_statements: Cash flow statement results by entity  
        users: List of users
    """
    st.success("✅ Financial statements generated successfully!")
    
    # Summary metrics
    if 'Combined' in income_statements:
        combined = income_statements['Combined']
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Total Revenue", 
                f"¥{combined['Total Revenue']:,.2f}",
                help="Combined revenue across all users"
            )
        with col2:
            st.metric(
                "Total Expenses", 
                f"¥{combined['Total Expenses']:,.2f}",
                help="Combined expenses across all users"
            )
        with col3:
            st.metric(
                "Net Income", 
                f"¥{combined['Net Income']:,.2f}",
                delta=f"{((combined['Net Income']/combined['Total Revenue'])*100):.1f}%" if combined['Total Revenue'] > 0 else None,
                help="Net income and profit margin"
            )
    
    # Entity selection
    st.subheader("📋 Detailed Statements")
    selected_entity = st.selectbox(
        "Select Entity for Detailed View:",
        options=["Combined"] + users,
        help="Choose individual user or Combined view"
    )
    
    # Display selected statements
    col1, col2 = st.columns(2)
    
    with col1:
        if selected_entity in income_statements:
            display_income_statement_table(income_statements[selected_entity])
    
    with col2:
        if selected_entity in cashflow_statements:
            display_cashflow_statement_table(cashflow_statements[selected_entity])


def display_income_statement_table(statement: Dict[str, Any]):
    """
    Display income statement as formatted table.
    
    Args:
        statement: Income statement data
    """
    st.write(f"**Income Statement - {statement['Entity']}**")
    
    # Prepare display data
    display_data = []
    
    # Revenue section
    display_data.append(["**REVENUE**", "", ""])
    for category, amount in statement['Revenue'].items():
        percentage = (amount / statement['Total Revenue'] * 100) if statement['Total Revenue'] > 0 else 0
        display_data.append([f"  {category}", f"¥{amount:,.2f}", f"{percentage:.1f}%"])
    
    display_data.append([
        "**Total Revenue**", 
        f"¥{statement['Total Revenue']:,.2f}", 
        "100.0%"
    ])
    display_data.append(["", "", ""])
    
    # Expenses section
    display_data.append(["**EXPENSES**", "", ""])
    for category, amount in statement['Expenses'].items():
        percentage = (amount / statement['Total Revenue'] * 100) if statement['Total Revenue'] > 0 else 0
        display_data.append([f"  {category}", f"¥{amount:,.2f}", f"{percentage:.1f}%"])
    
    display_data.append([
        "**Total Expenses**", 
        f"¥{statement['Total Expenses']:,.2f}",
        f"{(statement['Total Expenses'] / statement['Total Revenue'] * 100):.1f}%" if statement['Total Revenue'] > 0 else "0.0%"
    ])
    display_data.append(["", "", ""])
    
    # Net income
    net_margin = (statement['Net Income'] / statement['Total Revenue'] * 100) if statement['Total Revenue'] > 0 else 0
    display_data.append([
        "**NET INCOME**", 
        f"¥{statement['Net Income']:,.2f}",
        f"{net_margin:.1f}%"
    ])
    
    # Display as dataframe
    df = pd.DataFrame(display_data, columns=["Item", "Amount", "% of Revenue"])
    st.dataframe(df, use_container_width=True, hide_index=True)


def display_cashflow_statement_table(statement: Dict[str, Any]):
    """
    Display cash flow statement as formatted table.
    
    Args:
        statement: Cash flow statement data
    """
    st.write(f"**Cash Flow Statement - {statement['Entity']}**")
    
    display_data = []
    
    # Operating activities
    display_data.append(["**OPERATING ACTIVITIES**", ""])
    for category, amount in statement['Operating Activities']['Details'].items():
        display_data.append([f"  {category}", f"¥{amount:,.2f}"])
    display_data.append([
        "**Net Cash from Operating**",
        f"¥{statement['Operating Activities']['Net Cash from Operating']:,.2f}"
    ])
    display_data.append(["", ""])
    
    # Investing activities
    display_data.append(["**INVESTING ACTIVITIES**", ""])
    if statement['Investing Activities']['Details']:
        for category, amount in statement['Investing Activities']['Details'].items():
            display_data.append([f"  {category}", f"¥{amount:,.2f}"])
    else:
        display_data.append(["  No investing activities", "¥0.00"])
    display_data.append([
        "**Net Cash from Investing**",
        f"¥{statement['Investing Activities']['Net Cash from Investing']:,.2f}"
    ])
    display_data.append(["", ""])
    
    # Financing activities
    display_data.append(["**FINANCING ACTIVITIES**", ""])
    if statement['Financing Activities']['Details']:
        for category, amount in statement['Financing Activities']['Details'].items():
            display_data.append([f"  {category}", f"¥{amount:,.2f}"])
    else:
        display_data.append(["  No financing activities", "¥0.00"])
    display_data.append([
        "**Net Cash from Financing**",
        f"¥{statement['Financing Activities']['Net Cash from Financing']:,.2f}"
    ])
    display_data.append(["", ""])
    
    # Net change
    display_data.append([
        "**NET CHANGE IN CASH**",
        f"¥{statement['Net Change in Cash']:,.2f}"
    ])
    
    # Display as dataframe
    df = pd.DataFrame(display_data, columns=["Item", "Amount"])
    st.dataframe(df, use_container_width=True, hide_index=True)


def display_export_download_buttons(data: Dict, filename_prefix: str):
    """
    Display export/download buttons for generated data.
    
    Args:
        data: Data to export
        filename_prefix: Prefix for downloaded files
    """
    st.subheader("📥 Export Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Download CSV"):
            st.info("CSV download functionality to be implemented")
    
    with col2:
        if st.button("📋 Download JSON"):
            st.info("JSON download functionality to be implemented")
            
    with col3:
        if st.button("📊 Download Excel"):
            st.info("Excel download functionality to be implemented")