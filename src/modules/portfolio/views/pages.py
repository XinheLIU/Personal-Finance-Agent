"""
Portfolio Pages

Main page components that orchestrate the portfolio management interface.
"""

import streamlit as st
from .components import show_portfolio_tab, show_backtest_tab, show_attribution_tab


def show_investment_page():
    """Main investment page with Portfolio, Backtest, and Attribution tabs."""
    st.header("📈 Investment Management")
    st.markdown("Professional portfolio management, strategy backtesting, and performance attribution analysis")
    
    # Create horizontal tabs for investment functionality
    tab1, tab2, tab3 = st.tabs([
        "💼 Portfolio Management",
        "🎯 Strategy Backtesting", 
        "📊 Attribution Analysis"
    ])
    
    with tab1:
        show_portfolio_tab()
    
    with tab2:
        show_backtest_tab()
    
    with tab3:
        show_attribution_tab()
