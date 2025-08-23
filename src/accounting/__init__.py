"""
Professional Accounting Module for Personal Finance Agent

This module provides CSV-based transaction and asset management with
professional financial statement generation capabilities.

MVP Features:
- Transaction and asset data models with validation
- CSV import/export with UTF-8 support
- Monthly Income Statement generation
- Streamlit UI integration
- Basic CLI commands

Components:
- models: Transaction and Asset data models
- io: CSV read/write operations with validation
- income_statement: Financial statement generation
- ui: Streamlit interface components
"""

from .models import Transaction, Asset, EXPENSE_CATEGORIES, REVENUE_CATEGORIES
from .io import (
    load_transactions_csv,
    load_assets_csv,
    save_transactions_csv,
    save_assets_csv,
    save_income_statement_csv,
    validate_csv_format,
    ValidationError
)
from .income_statement import (
    generate_monthly_income_statement,
    generate_ytd_income_statement,
    IncomeStatementGenerator,
    format_currency,
    print_income_statement
)

__version__ = "0.1.0"
__all__ = [
    "Transaction",
    "Asset", 
    "EXPENSE_CATEGORIES",
    "REVENUE_CATEGORIES",
    "load_transactions_csv",
    "load_assets_csv",
    "save_transactions_csv", 
    "save_assets_csv",
    "save_income_statement_csv",
    "validate_csv_format",
    "ValidationError",
    "generate_monthly_income_statement",
    "generate_ytd_income_statement",
    "IncomeStatementGenerator",
    "format_currency",
    "print_income_statement"
]