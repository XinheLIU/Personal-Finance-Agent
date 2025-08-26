"""
Professional Accounting Module for Personal Finance Agent

This module provides CSV-based transaction and asset management with
complete financial statement generation capabilities.

Enhanced Features:
- Transaction and asset data models with validation
- CSV import/export with UTF-8 support
- Complete financial statement suite (Income Statement, Balance Sheet, Cash Flow)
- Interactive Streamlit UI with real-time updates
- Enhanced CLI commands

Components:
- models: Transaction and Asset data models
- io: CSV read/write operations with validation
- income_statement: Income statement generation
- balance_sheet: Balance sheet generation
- cash_flow: Cash flow statement generation
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
from .balance_sheet import (
    generate_balance_sheet,
    BalanceSheetGenerator,
    format_currency as format_currency_bs,
    print_balance_sheet
)
from .cash_flow import (
    generate_cash_flow_statement,
    CashFlowGenerator,
    format_currency as format_currency_cf,
    print_cash_flow_statement
)
from .sample_data import (
    generate_sample_transactions,
    generate_sample_assets,
    get_sample_data_summary,
    create_sample_csv_data,
    get_csv_format_template
)

__version__ = "0.2.0"
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
    "print_income_statement",
    "generate_balance_sheet",
    "BalanceSheetGenerator",
    "print_balance_sheet",
    "generate_cash_flow_statement",
    "CashFlowGenerator",
    "print_cash_flow_statement",
    "generate_sample_transactions",
    "generate_sample_assets",
    "get_sample_data_summary",
    "create_sample_csv_data",
    "get_csv_format_template"
]