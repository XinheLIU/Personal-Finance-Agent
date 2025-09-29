"""
Transaction processing business logic

Handles the processing of raw transaction data from CSV files.
"""

import pandas as pd
import re
import os
from typing import List, Tuple

from ..domain.transaction import Transaction
from ..domain.category import REVENUE_CATEGORIES


class TransactionProcessor:
    """Processes raw transaction data"""
    
    def __init__(self, csv_file_path: str):
        self.csv_file_path = csv_file_path
        self.transactions: List[Transaction] = []
    
    def _clean_amount(self, amount_str: str) -> float:
        """Clean and convert amount string to float"""
        if pd.isna(amount_str) or amount_str == '':
            return 0.0
        
        # Remove currency symbols and commas
        cleaned = re.sub(r'[¥,￥$]', '', str(amount_str))
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def _determine_transaction_type_and_sign(self, debit: str, credit: str, amount: float) -> Tuple[str, str, bool, float]:
        """
        Determine transaction type and impacts based on Credit/Debit columns
        
        Returns: (transaction_type, category, affects_cash_flow, amount)
        
        Accounting Logic:
        1. Cash involved → affects cash flow
        2. Revenue account credited → revenue transaction  
        3. Expense account debited → expense transaction
        4. Asset/liability conversions → may not affect current income/cash flow
        """
        
        debit = debit.strip()
        credit = credit.strip()
        cash_involved = credit.lower() in ["cash", "现金"] or debit.lower() in ["cash", "现金"]
        
        # Revenue transaction: Credit is a revenue account
        if credit in REVENUE_CATEGORIES:
            return "revenue", credit, cash_involved, abs(amount)
        
        # Prepaid expense being used (converted to expense): Debit = expense, Credit = prepaid
        elif "prepaid" in credit.lower() or "pre-paid" in credit.lower():
            # This converts prepaid asset to current expense - affects income statement only
            return "expense", debit, False, abs(amount)
        
        # Cash payment for future expense: Debit = prepaid, Credit = cash  
        elif "prepaid" in debit.lower() or "pre-paid" in debit.lower():
            # This creates prepaid asset - affects cash flow only, not current income
            return "prepaid_asset", debit, cash_involved, abs(amount)
        
        # Regular expense: Debit = expense, Credit = cash (or other account)
        else:
            return "expense", debit, cash_involved, abs(amount)
    
    def _validate_csv_data(self, df: pd.DataFrame) -> None:
        """Validate CSV data before processing"""
        required_columns = ['Description', 'Amount', 'Debit', 'Credit', 'User']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Check if we have any data rows (not just headers)
        if len(df) == 0:
            raise ValueError("CSV file contains no data rows")

    def load_transactions(self) -> None:
        """Load transactions from CSV file with proper Credit/Debit handling"""
        try:
            # Read CSV with encoding handling for BOM characters
            df = pd.read_csv(self.csv_file_path, encoding='utf-8-sig')
            
            # Handle empty dataframes
            if df.empty:
                return
            
            # Clean column names (remove any extra spaces and BOM characters)
            df.columns = df.columns.str.strip()
            
            # Remove completely empty rows
            df = df.dropna(how='all')
            
            # Validate data structure
            self._validate_csv_data(df)
            
            for _, row in df.iterrows():
                # Convert all fields to strings safely to prevent type errors
                description = str(row.get('Description', '')).strip() if pd.notna(row.get('Description')) else ''
                debit = str(row.get('Debit', '')).strip() if pd.notna(row.get('Debit')) else ''
                credit = str(row.get('Credit', '')).strip() if pd.notna(row.get('Credit')) else ''
                user = str(row.get('User', '')).strip() if pd.notna(row.get('User')) else ''
                
                # Skip rows with no description or empty essential fields
                if not description and not debit and not credit:
                    continue
                
                raw_amount = self._clean_amount(row.get('Amount', 0))
                
                # Skip transactions with zero amounts
                if raw_amount == 0:
                    continue
                
                # Determine transaction type, category, cash flow impact, and amount
                transaction_type, category, affects_cash_flow, corrected_amount = self._determine_transaction_type_and_sign(
                    debit, credit, raw_amount
                )
                
                transaction = Transaction(
                    description=description,
                    amount=corrected_amount,
                    debit_category=category,
                    credit_account=credit,
                    user=user
                )
                
                # Add metadata for transaction type and cash flow impact
                transaction.transaction_type = transaction_type
                transaction.affects_cash_flow = affects_cash_flow
                
                self.transactions.append(transaction)
                
        except pd.errors.EmptyDataError:
            # Handle empty CSV files gracefully
            return
        except Exception as e:
            raise Exception(f"Error loading transactions: {e}")
    
    def get_transactions_by_user(self, user: str) -> List[Transaction]:
        """Get all transactions for a specific user"""
        return [t for t in self.transactions if t.user == user]
    
    def get_all_users(self) -> List[str]:
        """Get list of all unique users"""
        return list(set(t.user for t in self.transactions if t.user))