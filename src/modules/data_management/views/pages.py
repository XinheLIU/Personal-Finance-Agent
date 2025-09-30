"""
Data Management Pages

Main page components that orchestrate the data management interface.
"""

import streamlit as st
from .components import show_data_explorer_tab, show_system_health_tab, show_accounting_data_tab


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
