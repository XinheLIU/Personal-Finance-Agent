"""
Streamlit Web Application for Personal Finance Agent.

Refactored modular architecture with clear separation of concerns.
Main navigation controller for the personal financial manager.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import json
from src.ui.app_logger import LOG

# Configure Streamlit page
st.set_page_config(
    page_title="Personal Finance Agent",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import page functions
from src.modules.portfolio.investment_management import show_investment_page
from src.modules.data_management.system_data_management import show_system_data_page
from src.modules.accounting.ui.accounting_management import show_simplified_accounting_page

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
    """Main application entry point with simplified 3-page navigation."""
    st.title("💰 Personal Finance Agent")
    st.caption("Your personal financial manager to help you manage your money.")
    
    # Simplified sidebar navigation - minimal design
    st.sidebar.title("Navigation")

    # Three main page categories
    main_pages = [
        "📈 Investment",
        "🛠️ System & Data Management",
        "💰 Accounting",
    ]

    # Page selection (kept clean without extra descriptions)
    page = st.sidebar.radio("Select Page:", main_pages, index=0)
    
    # Route to appropriate page function
    try:
        if page == "📈 Investment":
            show_investment_page()
        elif page == "🛠️ System & Data Management":
            show_system_data_page()
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