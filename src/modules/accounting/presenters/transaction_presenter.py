"""
Transaction Presenter

Coordinates between transaction models and views.
Handles the workflow of processing and coordinating both income and cash flow statements.
"""

from typing import Dict, List, Tuple

from ..models.business.transaction_processor import TransactionProcessor
from ..models.business.income_statement_generator import IncomeStatementGenerator
from ..models.business.cash_flow_generator import CashFlowStatementGenerator
from ..models.domain.category import CategoryMapper


class TransactionPresenter:
    """Presenter for coordinated transaction processing workflow"""
    
    def __init__(self):
        self.category_mapper = CategoryMapper()
        self.income_generator = IncomeStatementGenerator(self.category_mapper)
        self.cashflow_generator = CashFlowStatementGenerator(self.category_mapper)
    
    def process_transaction_statements(self, tmp_file_path: str) -> Tuple[Dict, Dict, List[str]]:
        """
        Process transactions and generate both income and cash flow statements for all users.
        
        This method replaces the original processors.py:process_transaction_statements()
        
        Args:
            tmp_file_path: Path to temporary CSV file
            
        Returns:
            Tuple of (income_statements, cashflow_statements, users)
        """
        # Process transactions
        processor = TransactionProcessor(tmp_file_path)
        processor.load_transactions()
        
        # Get users
        users = processor.get_all_users()
        if not users:
            raise ValueError("No users found in transaction data")
        
        # Generate statements for all users
        income_statements = {}
        cashflow_statements = {}
        
        # Individual user statements
        for user in users:
            user_transactions = processor.get_transactions_by_user(user)
            
            # Generate income statement
            income_stmt = self.income_generator.generate_statement(user_transactions, user)
            income_statements[user] = income_stmt
            
            # Generate cash flow statement  
            cashflow_stmt = self.cashflow_generator.generate_statement(user_transactions, user)
            cashflow_statements[user] = cashflow_stmt
        
        # Combined statements
        combined_income = self.income_generator.generate_statement(processor.transactions, "Combined")
        combined_cashflow = self.cashflow_generator.generate_statement(processor.transactions, "Combined")
        income_statements["Combined"] = combined_income
        cashflow_statements["Combined"] = combined_cashflow
        
        return income_statements, cashflow_statements, users