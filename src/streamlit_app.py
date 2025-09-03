"""
Streamlit Web Application for Personal Finance Agent.

Refactored modular architecture with clear separation of concerns.
Main navigation controller for the professional quantitative investment management system.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import json
from src.app_logger import LOG

# Configure Streamlit page
st.set_page_config(
    page_title="Personal Finance Agent",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import page modules
from src.streamlit_pages import (
    # Portfolio Management
    show_backtest_page,
    show_attribution_page, 
    show_portfolio_page,
    
    # System Management  
    show_system_page,
    show_data_explorer_page,
    
    # Accounting Management
    show_simplified_accounting_page
)

# Cache for strategy weights
if 'target_weights_cache' not in st.session_state:
    st.session_state.target_weights_cache = {}

# Holdings file path
HOLDINGS_FILE = "data/holdings.json"


def load_holdings() -> dict:
    """Load current holdings from JSON file."""
    if os.path.exists(HOLDINGS_FILE):
        try:
            with open(HOLDINGS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            LOG.error(f"Error loading holdings: {e}")
    return {}


def save_holdings(holdings_dict: dict) -> str:
    """Save holdings to JSON file."""
    try:
        os.makedirs(os.path.dirname(HOLDINGS_FILE), exist_ok=True)
        with open(HOLDINGS_FILE, 'w') as f:
            json.dump(holdings_dict, f, indent=4)
        return "Holdings saved successfully!"
    except Exception as e:
        LOG.error(f"Error saving holdings: {e}")
        return f"Error saving holdings: {e}"


def main():
    """Main application entry point with modular page navigation."""
    st.title("💰 Personal Finance Agent")
    st.markdown("Professional quantitative investment management system")
    
    # Sidebar navigation - Three main categories
    st.sidebar.title("Navigation")
    
    # Organize pages into logical categories
    page_categories = {
        "📊 Portfolio Management": [
            "🎯 Backtest", 
            "📊 Attribution", 
            "💼 Portfolio"
        ],
        "🛠️ System Management": [
            "📈 Data Explorer", 
            "⚙️ System"
        ],
        "💰 Accounting": [
            "💰 Accounting"
        ]
    }
    
    # Flatten for radio selection while maintaining logical grouping
    all_pages = []
    for category, pages in page_categories.items():
        all_pages.extend(pages)
    
    # Display category headers in sidebar
    st.sidebar.markdown("### 📊 Portfolio Management")
    st.sidebar.markdown("- Backtesting & Attribution Analysis")
    st.sidebar.markdown("- Portfolio Optimization")
    
    st.sidebar.markdown("### 🛠️ System Management") 
    st.sidebar.markdown("- Data Management & Monitoring")
    st.sidebar.markdown("- System Health & Operations")
    
    st.sidebar.markdown("### 💰 Accounting")
    st.sidebar.markdown("- Financial Statements & Analysis")
    
    st.sidebar.markdown("---")
    
    # Page selection
    page = st.sidebar.radio("Select Page:", all_pages, index=0)
    
    # Route to appropriate page function
    try:
        if page == "🎯 Backtest":
            show_backtest_page()
        elif page == "📊 Attribution":
            show_attribution_page()
        elif page == "💼 Portfolio":
            show_portfolio_page()
        elif page == "📈 Data Explorer":
            show_data_explorer_page()
        elif page == "⚙️ System":
            show_system_page()
        elif page == "💰 Accounting":
            show_simplified_accounting_page()
        else:
            st.error(f"Unknown page: {page}")
            
    except Exception as e:
        st.error(f"Error loading page '{page}': {str(e)}")
        LOG.error(f"Page loading error for '{page}': {e}")
        
        # Show error details in expander for debugging
        with st.expander("Error Details (for debugging)"):
            st.code(str(e))
            import traceback
            st.code(traceback.format_exc())


if __name__ == "__main__":
    main()