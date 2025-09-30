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
    
    def __init__(self, csv_file_path: str = None, dataframe: pd.DataFrame = None):
        """
        Initialize with either a CSV file path or a clean DataFrame.
        
        Args:
            csv_file_path: Path to CSV file (for backward compatibility)
            dataframe: Pre-cleaned DataFrame from DataCleaner (preferred)
        """
        if csv_file_path is None and dataframe is None:
            raise ValueError("Must provide either csv_file_path or dataframe")
        
        self.csv_file_path = csv_file_path
        self._dataframe = dataframe
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
        5. Reimbursements (Cash debited, Expense credited) → negative expense (expense reduction)
        """
        cash_involved = credit.lower() in ["cash", "现金"] or debit.lower() in ["cash", "现金"]
        
        # Revenue transaction: Credit is a revenue account
        if credit in REVENUE_CATEGORIES:
            return "revenue", credit, cash_involved, abs(amount)
        
        # Reimbursement: Debit = Cash, Credit = Expense category (cash inflow reduces expense)
        # Example: 报销 ¥1,509.00 Cash 通勤 (got cash back for transportation)
        elif debit.lower() in ["cash", "现金"] and credit not in REVENUE_CATEGORIES:
            # This is cash received that reduces a previous expense
            # Treat as negative expense (expense reduction)
            return "expense", credit, cash_involved, -abs(amount)
        
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
        """
        Load transactions from clean DataFrame into Transaction domain objects.
        
        Expects DataFrame to be already cleaned and validated by DataCleaner.
        For backward compatibility, also supports loading directly from CSV.
        """
        try:
            # Load DataFrame from either source
            if self._dataframe is not None:
                df = self._dataframe
            elif self.csv_file_path:
                # Backward compatibility: Load from CSV
                # NOTE: Ideally, this should go through DataCleaner first
                df = pd.read_csv(self.csv_file_path, encoding='utf-8-sig')
                df.columns = df.columns.str.strip()
                df = df.dropna(how='all')
            else:
                return
            
            # Handle empty dataframes
            if df.empty:
                return
            
            for _, row in df.iterrows():
                # Extract fields (data should already be clean from DataCleaner)
                description = str(row.get('Description', '')).strip() if pd.notna(row.get('Description')) else ''
                debit = str(row.get('Debit', '')).strip() if pd.notna(row.get('Debit')) else ''
                credit = str(row.get('Credit', '')).strip() if pd.notna(row.get('Credit')) else ''
                user = str(row.get('User', '')).strip() if pd.notna(row.get('User')) else ''
                
                # Skip rows with no essential data
                if not description and not debit and not credit:
                    continue
                
                # Get amount (should already be numeric from DataCleaner)
                try:
                    raw_amount = float(row.get('Amount', 0)) if pd.notna(row.get('Amount')) else 0.0
                except (ValueError, TypeError):
                    # Fallback to cleaning if data came from CSV directly
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
                
        except Exception as e:
            raise Exception(f"Error loading transactions: {e}")
    
    def get_transactions_by_user(self, user: str) -> List[Transaction]:
        """Get all transactions for a specific user"""
        return [t for t in self.transactions if t.user == user]
    
    def get_all_users(self) -> List[str]:
        """Get list of all unique users"""
        return list(set(t.user for t in self.transactions if t.user))