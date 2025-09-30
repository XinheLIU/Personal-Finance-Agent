"""
Investment Management Page

Consolidated interface for Portfolio, Backtest, and Attribution analysis.
Contains all investment-related functionality in a single page with horizontal tabs.

This file now serves as a thin wrapper around the MVP-structured views.
"""

from src.modules.portfolio.views.pages import show_investment_page