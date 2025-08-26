"""
CSV I/O operations for Professional Accounting Module

This module provides robust CSV import/export functionality with comprehensive
validation, UTF-8 encoding support, and error handling for transactions and assets.
"""

import csv
import os
import decimal
from decimal import Decimal
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import uuid

from .models import (
    Transaction, Asset, EXPENSE_CATEGORIES, get_all_categories,
    MonthlyAsset, MonthlyTransaction, ExchangeRate
)


class ValidationError(Exception):
    """Custom exception for data validation errors"""
    pass


class TransactionInputValidator:
    """Transaction input validation service"""
    
    @staticmethod
    def validate_description(description: str) -> bool:
        """Validate transaction description"""
        if not description or not description.strip():
            return False
        
        # Check length limits
        if len(description.strip()) > 200:
            return False
            
        return True
    
    @staticmethod
    def validate_amount(amount_str: str) -> Tuple[bool, Optional[Decimal]]:
        """Validate and parse amount string"""
        try:
            if not amount_str or not amount_str.strip():
                return False, None
                
            # Remove currency symbols but reject invalid formats
            cleaned = amount_str.replace('¥', '').replace('CNY', '').strip()
            
            # Check for invalid patterns
            if '¥¥' in amount_str or '..' in cleaned or ',' in cleaned:
                return False, None
            
            # Convert to Decimal
            amount = Decimal(cleaned)
            
            # Check decimal places (max 2)
            if amount.as_tuple().exponent < -2:
                return False, None
                
            return True, amount
            
        except (ValueError, TypeError, decimal.InvalidOperation):
            return False, None
    
    @staticmethod
    def validate_category(category: str, valid_categories: List[str]) -> bool:
        """Validate category against predefined taxonomy"""
        return category in valid_categories
    
    @staticmethod
    def validate_account_type(account_type: str) -> bool:
        """Validate account type"""
        valid_types = ["Cash", "Credit", "Debit"]
        return account_type in valid_types
    
    @staticmethod
    def validate_transaction_type(transaction_type: str) -> bool:
        """Validate transaction type"""
        valid_types = ["Cash", "Non-Cash"]
        return transaction_type in valid_types


class AssetInputValidator:
    """Asset input validation service"""
    
    @staticmethod
    def validate_account_name(account_name: str) -> bool:
        """Validate asset account name"""
        if not account_name or not account_name.strip():
            return False
        return len(account_name.strip()) <= 100
    
    @staticmethod
    def validate_balance(balance_str: str) -> Tuple[bool, Optional[Decimal]]:
        """Validate and parse balance string"""
        try:
            # Remove currency symbols
            cleaned = balance_str.replace('¥', '').replace('CNY', '').strip()
            
            # Convert to Decimal
            balance = Decimal(cleaned)
            
            # Check decimal places (max 2)
            if balance.as_tuple().exponent < -2:
                return False, None
                
            return True, balance
            
        except (ValueError, TypeError):
            return False, None
    
    @staticmethod
    def validate_account_type(account_type: str) -> bool:
        """Validate asset account type"""
        valid_types = ["checking", "savings", "investment", "retirement"]
        return account_type in valid_types


def load_transactions_csv(file_path: str, user_id: str = None) -> Tuple[List[Transaction], List[str]]:
    """
    Load transactions from CSV file with validation
    
    Args:
        file_path: Path to CSV file
        user_id: User ID for transactions (generates UUID if not provided)
    
    Returns:
        Tuple of (valid_transactions_list, errors_list)
    """
    validator = TransactionInputValidator()
    valid_categories = get_all_categories()
    transactions = []
    errors = []
    
    if not os.path.exists(file_path):
        errors.append(f"File not found: {file_path}")
        return transactions, errors
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Check required headers
            required_headers = ['date', 'description', 'amount', 'category', 'account_name', 'account_type']
            missing_headers = [h for h in required_headers if h not in reader.fieldnames]
            if missing_headers:
                errors.append(f"Missing required headers: {', '.join(missing_headers)}")
                return transactions, errors
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                try:
                    transaction = _validate_and_parse_transaction_row(
                        row, row_num, validator, valid_categories, user_id
                    )
                    if transaction:
                        transactions.append(transaction)
                except ValidationError as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                except Exception as e:
                    errors.append(f"Row {row_num}: Unexpected error - {str(e)}")
                    
    except UnicodeDecodeError as e:
        errors.append(f"File encoding error: {str(e)}. Please ensure file is UTF-8 encoded.")
    except Exception as e:
        errors.append(f"File reading error: {str(e)}")
    
    return transactions, errors


def load_assets_csv(file_path: str, user_id: str = None) -> Tuple[List[Asset], List[str]]:
    """
    Load assets from CSV file with validation
    
    Args:
        file_path: Path to CSV file  
        user_id: User ID for assets (generates UUID if not provided)
    
    Returns:
        Tuple of (valid_assets_list, errors_list)
    """
    validator = AssetInputValidator()
    assets = []
    errors = []
    
    if not os.path.exists(file_path):
        errors.append(f"File not found: {file_path}")
        return assets, errors
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Check required headers
            required_headers = ['as_of_date', 'account_name', 'balance', 'account_type', 'currency']
            missing_headers = [h for h in required_headers if h not in reader.fieldnames]
            if missing_headers:
                errors.append(f"Missing required headers: {', '.join(missing_headers)}")
                return assets, errors
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                try:
                    asset = _validate_and_parse_asset_row(row, row_num, validator, user_id)
                    if asset:
                        assets.append(asset)
                except ValidationError as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                except Exception as e:
                    errors.append(f"Row {row_num}: Unexpected error - {str(e)}")
                    
    except UnicodeDecodeError as e:
        errors.append(f"File encoding error: {str(e)}. Please ensure file is UTF-8 encoded.")
    except Exception as e:
        errors.append(f"File reading error: {str(e)}")
    
    return assets, errors


def save_transactions_csv(transactions: List[Transaction], file_path: str) -> List[str]:
    """
    Save transactions to CSV file
    
    Args:
        transactions: List of Transaction objects
        file_path: Output CSV file path
    
    Returns:
        List of errors (empty if successful)
    """
    errors = []
    
    try:
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', newline='', encoding='utf-8') as file:
            if not transactions:
                # Write empty file with headers
                writer = csv.writer(file)
                writer.writerow(['date', 'description', 'amount', 'category', 
                               'account_name', 'account_type', 'notes'])
                return errors
            
            # Use first transaction to determine fields
            fieldnames = ['date', 'description', 'amount', 'category', 
                         'account_name', 'account_type', 'notes']
            
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            
            for transaction in transactions:
                writer.writerow({
                    'date': transaction.date.strftime('%Y-%m-%d'),
                    'description': transaction.description,
                    'amount': str(transaction.amount),
                    'category': transaction.category,
                    'account_name': transaction.account_name,  # Map to CSV format
                    'account_type': transaction.transaction_type,
                    'notes': transaction.notes or ''
                })
                
    except Exception as e:
        errors.append(f"Failed to save transactions CSV: {str(e)}")
    
    return errors


def save_assets_csv(assets: List[Asset], file_path: str) -> List[str]:
    """
    Save assets to CSV file
    
    Args:
        assets: List of Asset objects
        file_path: Output CSV file path
    
    Returns:
        List of errors (empty if successful)
    """
    errors = []
    
    try:
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', newline='', encoding='utf-8') as file:
            if not assets:
                # Write empty file with headers
                writer = csv.writer(file)
                writer.writerow(['as_of_date', 'account_name', 'balance', 
                               'account_type', 'currency'])
                return errors
            
            fieldnames = ['as_of_date', 'account_name', 'balance', 
                         'account_type', 'currency']
            
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            
            for asset in assets:
                writer.writerow({
                    'as_of_date': asset.as_of_date.strftime('%Y-%m-%d'),
                    'account_name': asset.account_name,
                    'balance': str(asset.balance),
                    'account_type': asset.account_type,
                    'currency': asset.currency
                })
                
    except Exception as e:
        errors.append(f"Failed to save assets CSV: {str(e)}")
    
    return errors


def save_income_statement_csv(statement_data: Dict[str, Any], file_path: str) -> List[str]:
    """
    Save income statement to CSV file
    
    Args:
        statement_data: Income statement data dictionary
        file_path: Output CSV file path
    
    Returns:
        List of errors (empty if successful)
    """
    errors = []
    
    try:
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Write header
            writer.writerow(['Income Statement', statement_data.get('period', 'Unknown Period')])
            writer.writerow([])  # Empty row
            
            # Write revenue section
            writer.writerow(['REVENUE'])
            revenue = statement_data.get('revenue', {})
            writer.writerow(['Service Revenue', str(revenue.get('service_revenue', 0))])
            writer.writerow(['Other Income', str(revenue.get('other_income', 0))])
            writer.writerow(['Gross Revenue', str(revenue.get('gross_revenue', 0))])
            writer.writerow([])
            
            # Write expenses section
            writer.writerow(['EXPENSES'])
            expenses = statement_data.get('expenses', {})
            writer.writerow(['Fixed Costs', str(expenses.get('fixed_costs', 0))])
            writer.writerow(['Variable Costs', str(expenses.get('variable_costs', 0))])
            writer.writerow(['Tax Expense', str(expenses.get('tax_expense', 0))])
            writer.writerow(['Total Expenses', str(expenses.get('total_expenses', 0))])
            writer.writerow([])
            
            # Write expense breakdown by category
            writer.writerow(['EXPENSE BREAKDOWN'])
            expense_breakdown = statement_data.get('expense_breakdown', {})
            for category, details in expense_breakdown.items():
                amount = details.get('amount', 0) if isinstance(details, dict) else details
                writer.writerow([category, str(amount)])
            writer.writerow([])
            
            # Write net income
            net_income = statement_data.get('net_operating_income', 0)
            writer.writerow(['NET OPERATING INCOME', str(net_income)])
                
    except Exception as e:
        errors.append(f"Failed to save income statement CSV: {str(e)}")
    
    return errors


def validate_csv_format(file_path: str, expected_type: str) -> Tuple[bool, List[str]]:
    """
    Validate CSV file format and headers
    
    Args:
        file_path: Path to CSV file
        expected_type: 'transactions' or 'assets'
    
    Returns:
        Tuple of (is_valid, errors_list)
    """
    errors = []
    
    if not os.path.exists(file_path):
        errors.append(f"File not found: {file_path}")
        return False, errors
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            if expected_type == 'transactions':
                required_headers = ['date', 'description', 'amount', 'category', 'account_name', 'account_type']
            elif expected_type == 'assets':
                required_headers = ['as_of_date', 'account_name', 'balance', 'account_type', 'currency']
            else:
                errors.append(f"Unknown expected type: {expected_type}")
                return False, errors
            
            missing_headers = [h for h in required_headers if h not in reader.fieldnames]
            if missing_headers:
                errors.append(f"Missing required headers: {', '.join(missing_headers)}")
                return False, errors
                
    except UnicodeDecodeError as e:
        errors.append(f"File encoding error: {str(e)}. Please ensure file is UTF-8 encoded.")
        return False, errors
    except Exception as e:
        errors.append(f"File validation error: {str(e)}")
        return False, errors
    
    return True, errors


def _validate_and_parse_transaction_row(
    row: Dict[str, str], 
    row_num: int, 
    validator: TransactionInputValidator,
    valid_categories: List[str],
    user_id: str = None
) -> Transaction:
    """Validate and parse a single transaction CSV row"""
    required_fields = ["date", "description", "amount", "category", "account_name", "account_type"]
    
    # Check required fields
    for field in required_fields:
        if field not in row or not row[field].strip():
            raise ValidationError(f"Missing required field: {field}")
    
    # Validate description
    if not validator.validate_description(row["description"]):
        raise ValidationError(f"Invalid description: {row['description']}")
    
    # Validate amount
    is_valid_amount, amount = validator.validate_amount(row["amount"])
    if not is_valid_amount:
        raise ValidationError(f"Invalid amount: {row['amount']}")
    
    # Validate category
    if not validator.validate_category(row["category"], valid_categories):
        raise ValidationError(f"Invalid category: {row['category']}")
    
    # Parse date
    try:
        date = datetime.strptime(row["date"], "%Y-%m-%d")
    except ValueError:
        raise ValidationError(f"Invalid date format: {row['date']}. Use YYYY-MM-DD.")
    
    # Default transaction type if not provided
    transaction_type = row.get("transaction_type", "Cash")
    if not validator.validate_transaction_type(transaction_type):
        raise ValidationError(f"Invalid transaction type: {transaction_type}")
    
    # Map account_name to account_type for compatibility
    account_type = row.get("account_type", "Cash")
    if not validator.validate_account_type(account_type):
        raise ValidationError(f"Invalid account type: {account_type}")
    
    return Transaction(
        id=str(uuid.uuid4()),
        user_id=user_id or str(uuid.uuid4()),
        date=date,
        description=row["description"].strip(),
        amount=amount,
        category=row["category"],
        account_name=row["account_name"].strip(),
        account_type=account_type,
        transaction_type=transaction_type,
        notes=row.get("notes", "").strip() or None
    )


def _validate_and_parse_asset_row(
    row: Dict[str, str], 
    row_num: int, 
    validator: AssetInputValidator,
    user_id: str = None
) -> Asset:
    """Validate and parse a single asset CSV row"""
    required_fields = ["as_of_date", "account_name", "balance", "account_type"]
    
    # Check required fields
    for field in required_fields:
        if field not in row or not row[field].strip():
            raise ValidationError(f"Missing required field: {field}")
    
    # Validate account name
    if not validator.validate_account_name(row["account_name"]):
        raise ValidationError(f"Invalid account name: {row['account_name']}")
    
    # Validate balance
    is_valid_balance, balance = validator.validate_balance(row["balance"])
    if not is_valid_balance:
        raise ValidationError(f"Invalid balance: {row['balance']}")
    
    # Validate account type
    if not validator.validate_account_type(row["account_type"]):
        raise ValidationError(f"Invalid account type: {row['account_type']}")
    
    # Parse date
    try:
        as_of_date = datetime.strptime(row["as_of_date"], "%Y-%m-%d")
    except ValueError:
        raise ValidationError(f"Invalid date format: {row['as_of_date']}. Use YYYY-MM-DD.")
    
    # Default currency
    currency = row.get("currency", "CNY")
    if currency != "CNY":
        raise ValidationError(f"Invalid currency: {currency}. Only CNY is supported.")
    
    return Asset(
        id=str(uuid.uuid4()),
        user_id=user_id or str(uuid.uuid4()),
        account_name=row["account_name"].strip(),
        balance=balance,
        account_type=row["account_type"],
        as_of_date=as_of_date,
        currency=currency
    )


# New I/O functions for monthly workflow

def load_monthly_assets_csv(file_path: str, as_of_date: datetime) -> Tuple[List['MonthlyAsset'], List[str]]:
    """
    Load monthly assets from simplified CSV format: Account, CNY, USD, Asset Class
    
    Args:
        file_path: Path to CSV file
        as_of_date: Date for asset snapshot
    
    Returns:
        Tuple of (valid_assets_list, errors_list)
    """
    from .models import MonthlyAsset
    
    assets = []
    errors = []
    
    if not os.path.exists(file_path):
        errors.append(f"File not found: {file_path}")
        return assets, errors
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Check required headers
            required_headers = ['Account', 'CNY', 'USD', 'Asset Class']
            missing_headers = [h for h in required_headers if h not in reader.fieldnames]
            if missing_headers:
                errors.append(f"Missing required headers: {', '.join(missing_headers)}")
                return assets, errors
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                try:
                    # Skip empty account names
                    if not row['Account'].strip():
                        continue
                    
                    asset = MonthlyAsset.from_dict(row, as_of_date)
                    assets.append(asset)
                except ValueError as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                except Exception as e:
                    errors.append(f"Row {row_num}: Unexpected error - {str(e)}")
                    
    except UnicodeDecodeError as e:
        errors.append(f"File encoding error: {str(e)}. Please ensure file is UTF-8 encoded.")
    except Exception as e:
        errors.append(f"File reading error: {str(e)}")
    
    return assets, errors


def load_monthly_transactions_csv(file_path: str) -> Tuple[List['MonthlyTransaction'], List[str]]:
    """
    Load monthly transactions from simplified CSV format
    
    Args:
        file_path: Path to CSV file
    
    Returns:
        Tuple of (valid_transactions_list, errors_list)
        
    Note: This is a placeholder implementation. Format to be determined 
    when sample transaction CSV is fixed.
    """
    from .models import MonthlyTransaction
    
    transactions = []
    errors = []
    
    if not os.path.exists(file_path):
        errors.append(f"File not found: {file_path}")
        return transactions, errors
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Expected headers (to be updated when format is determined)
            expected_headers = ['date', 'description', 'amount', 'category', 'account_name', 'currency']
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    transaction = MonthlyTransaction.from_dict(row)
                    transactions.append(transaction)
                except ValueError as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                except Exception as e:
                    errors.append(f"Row {row_num}: Unexpected error - {str(e)}")
                    
    except Exception as e:
        errors.append(f"Error reading transactions file: {str(e)}")
    
    return transactions, errors


def load_exchange_rate_from_file(file_path: str, date: datetime) -> Tuple[Optional['ExchangeRate'], List[str]]:
    """
    Load USD/CNY exchange rate from text file
    
    Args:
        file_path: Path to text file containing exchange rate
        date: Date for the exchange rate
    
    Returns:
        Tuple of (ExchangeRate object or None, errors_list)
    """
    from .models import ExchangeRate
    
    errors = []
    
    try:
        exchange_rate = ExchangeRate.from_text_file(file_path, date)
        return exchange_rate, errors
    except Exception as e:
        errors.append(f"Error loading exchange rate: {str(e)}")
        return None, errors


def save_balance_sheet_csv(balance_sheet_data: dict, file_path: str) -> List[str]:
    """
    Save balance sheet to CSV file in professional format
    
    Args:
        balance_sheet_data: Dictionary containing balance sheet data
        file_path: Output CSV file path
    
    Returns:
        List of error messages (empty if successful)
    """
    errors = []
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            
            # Write balance sheet header
            writer.writerow(['Assets', '', '', 'Liabilities and owner\'s equity', '', ''])
            
            # Assets section
            writer.writerow(['Current assets:', 'CNY', 'USD', 'Current liabilities:', 'CNY', 'USD'])
            
            # Write current assets
            current_assets = balance_sheet_data.get('current_assets', {})
            current_liabilities = balance_sheet_data.get('current_liabilities', {})
            
            max_rows = max(len(current_assets), len(current_liabilities))
            
            asset_items = list(current_assets.items())
            liability_items = list(current_liabilities.items())
            
            for i in range(max_rows):
                asset_row = ['', '', '']  # Default empty asset row
                liability_row = ['', '', '']  # Default empty liability row
                
                if i < len(asset_items):
                    name, values = asset_items[i]
                    asset_row = [name, values.get('cny', ''), values.get('usd', '')]
                
                if i < len(liability_items):
                    name, values = liability_items[i]
                    liability_row = [name, values.get('cny', ''), values.get('usd', '')]
                
                writer.writerow(asset_row + liability_row)
            
            # Write totals and other sections
            writer.writerow(['Total current assets', 
                            balance_sheet_data.get('total_current_assets_cny', ''),
                            balance_sheet_data.get('total_current_assets_usd', ''),
                            'Total current liabilities',
                            balance_sheet_data.get('total_current_liabilities_cny', ''),
                            balance_sheet_data.get('total_current_liabilities_usd', '')])
            
            # Fixed assets and long-term liabilities
            writer.writerow(['Fixed assets:', 'CNY', 'USD', '', '', ''])
            
            fixed_assets = balance_sheet_data.get('fixed_assets', {})
            for name, values in fixed_assets.items():
                writer.writerow([name, values.get('cny', ''), values.get('usd', ''), '', '', ''])
            
            writer.writerow(['Total fixed assets',
                            balance_sheet_data.get('total_fixed_assets_cny', ''),
                            balance_sheet_data.get('total_fixed_assets_usd', ''),
                            'Long-term liabilities:', 'CNY', 'USD'])
            
            # Owner's equity
            writer.writerow(['', '', '', 'Owner\'s equity:', 'CNY', 'USD'])
            
            owner_equity = balance_sheet_data.get('owner_equity', {})
            for owner, amount in owner_equity.items():
                writer.writerow(['', '', '', f'Capital - {owner}', amount.get('cny', ''), amount.get('usd', '')])
            
            writer.writerow(['Total assets',
                            balance_sheet_data.get('total_assets_cny', ''),
                            balance_sheet_data.get('total_assets_usd', ''),
                            'Total owner\'s equity',
                            balance_sheet_data.get('total_owner_equity_cny', ''),
                            balance_sheet_data.get('total_owner_equity_usd', '')])
            
    except Exception as e:
        errors.append(f"Error saving balance sheet: {str(e)}")
    
    return errors


def save_income_statement_csv(income_statement_data: dict, file_path: str) -> List[str]:
    """
    Save income statement to CSV file in professional format
    
    Args:
        income_statement_data: Dictionary containing income statement data
        file_path: Output CSV file path
    
    Returns:
        List of error messages (empty if successful)
    """
    errors = []
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            
            # Revenue section
            writer.writerow(['Revenue', '', ''])
            
            revenues = income_statement_data.get('revenues', {})
            for item, amount in revenues.items():
                writer.writerow([item, amount, ''])
            
            writer.writerow(['Tax Expense', income_statement_data.get('tax_expense', ''), ''])
            writer.writerow(['    Gross Revenue', income_statement_data.get('gross_revenue', ''), ''])
            
            # Expenses section
            writer.writerow(['Expenses', '', ''])
            
            expenses = income_statement_data.get('expenses', {})
            for item, amount in expenses.items():
                writer.writerow([item, amount, ''])
            
            writer.writerow(['    Total Expenses', income_statement_data.get('total_expenses', ''), ''])
            writer.writerow(['    Net Operating Income', income_statement_data.get('net_operating_income', ''), ''])
            
    except Exception as e:
        errors.append(f"Error saving income statement: {str(e)}")
    
    return errors


def save_cash_flow_statement_csv(cash_flow_data: dict, file_path: str) -> List[str]:
    """
    Save cash flow statement to CSV file in professional format
    
    Args:
        cash_flow_data: Dictionary containing cash flow data
        file_path: Output CSV file path
    
    Returns:
        List of error messages (empty if successful)
    """
    errors = []
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            
            # Operating activities
            writer.writerow(['Cash Flow from Operating Activities', '', ''])
            
            operating = cash_flow_data.get('operating_activities', {})
            for item, amount in operating.items():
                writer.writerow([item, amount, ''])
            
            writer.writerow(['Net Cash from Operating Activities', cash_flow_data.get('net_operating_cash', ''), ''])
            
            # Investing activities
            writer.writerow(['Cash Flow from Investing Activities', '', ''])
            
            investing = cash_flow_data.get('investing_activities', {})
            for item, amount in investing.items():
                writer.writerow([item, amount, ''])
            
            writer.writerow(['Net Cash from Investing Activities', cash_flow_data.get('net_investing_cash', ''), ''])
            
            # Financing activities
            writer.writerow(['Cash Flow from Financing Activities', '', ''])
            
            financing = cash_flow_data.get('financing_activities', {})
            for item, amount in financing.items():
                writer.writerow([item, amount, ''])
            
            writer.writerow(['Net Cash from Financing Activities', cash_flow_data.get('net_financing_cash', ''), ''])
            
            # Net change in cash
            writer.writerow(['Net Change in Cash', cash_flow_data.get('net_change_in_cash', ''), ''])
            writer.writerow(['Cash at Beginning of Period', cash_flow_data.get('beginning_cash', ''), ''])
            writer.writerow(['Cash at End of Period', cash_flow_data.get('ending_cash', ''), ''])
            
    except Exception as e:
        errors.append(f"Error saving cash flow statement: {str(e)}")
    
    return errors
