"""
Data management views module.

Contains UI components and pages for data management,
system health monitoring, and accounting data operations.
"""

from .pages import show_system_data_page
from .components import (
    show_data_explorer_tab,
    show_system_health_tab,
    show_accounting_data_tab
)

__all__ = [
    'show_system_data_page',
    'show_data_explorer_tab',
    'show_system_health_tab',
    'show_accounting_data_tab'
]
