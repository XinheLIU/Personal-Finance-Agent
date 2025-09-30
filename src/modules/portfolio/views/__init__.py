"""
Portfolio views module.

Contains UI components and pages for portfolio management,
backtesting, and attribution analysis.
"""

from .pages import show_investment_page
from .components import (
    show_portfolio_tab,
    show_backtest_tab,
    show_attribution_tab
)

__all__ = [
    'show_investment_page',
    'show_portfolio_tab',
    'show_backtest_tab', 
    'show_attribution_tab'
]
