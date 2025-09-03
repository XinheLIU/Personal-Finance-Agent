"""
Streamlit Pages Module

Modular page components for the Personal Finance Agent web interface.
Provides separation of concerns between portfolio management, system management, and accounting.
"""

# Import page modules for easy access
from .portfolio_management import (
    show_backtest_page,
    show_attribution_page, 
    show_portfolio_page
)

from .system_management import (
    show_system_page,
    show_data_explorer_page
)

from .accounting_management import (
    accounting_management_page,
    show_simplified_accounting_page
)

__all__ = [
    # Portfolio Management
    'show_backtest_page',
    'show_attribution_page',
    'show_portfolio_page',
    
    # System Management  
    'show_system_page',
    'show_data_explorer_page',
    
    # Accounting Management
    'accounting_management_page',
    'show_simplified_accounting_page'
]