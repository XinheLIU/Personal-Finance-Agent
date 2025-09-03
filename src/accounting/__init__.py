"""
Simplified Accounting Module for Personal Finance Agent

Streamlined module for generating income statements, cash flow statements, and balance sheets
from transaction and asset data using CSV processing.

Components:
- models: Simplified Transaction and CategoryMapper data models
- io: Basic CSV processing with pandas
- income_statement: Income statement generation
- cash_flow: Cash flow statement generation
- balance_sheet: Balance sheet generation
- report_generator: Main orchestrator for financial reports
"""

from .models import Transaction, CategoryMapper, REVENUE_CATEGORIES, get_all_categories
from .io import TransactionProcessor, save_statement_csv, save_transposed_data
from .income_statement import IncomeStatementGenerator, format_currency, print_income_statement
from .cash_flow import CashFlowStatementGenerator, print_cash_flow_statement
from .balance_sheet import BalanceSheetGenerator, print_balance_sheet
from .report_generator import FinancialReportGenerator

__version__ = "1.0.0"
__all__ = [
    "Transaction",
    "CategoryMapper",
    "REVENUE_CATEGORIES",
    "get_all_categories",
    "TransactionProcessor",
    "save_statement_csv",
    "save_transposed_data",
    "IncomeStatementGenerator",
    "format_currency",
    "print_income_statement",
    "CashFlowStatementGenerator",
    "print_cash_flow_statement",
    "BalanceSheetGenerator",
    "print_balance_sheet",
    "FinancialReportGenerator"
]