"""
Cash Flow Presenter

Coordinates between cash flow models and views.
Handles the workflow of processing transactions and generating cash flow statements.
"""

from typing import Dict, List, Tuple

from ..models.business.transaction_processor import TransactionProcessor
from ..models.business.cash_flow_generator import CashFlowStatementGenerator
from ..models.domain.category import CategoryMapper


class CashFlowPresenter:
    """Presenter for cash flow statement generation workflow"""
    
    def __init__(self):
        self.category_mapper = CategoryMapper()
        self.cashflow_generator = CashFlowStatementGenerator(self.category_mapper)
    
    def process_transactions_and_generate_statements(self, tmp_file_path: str) -> Tuple[Dict, List[str]]:
        """
        Process transactions from CSV and generate cash flow statements for all users.
        
        Args:
            tmp_file_path: Path to temporary CSV file
            
        Returns:
            Tuple of (cashflow_statements_dict, users_list)
        """
        # Process transactions
        processor = TransactionProcessor(tmp_file_path)
        processor.load_transactions()
        
        # Get users
        users = processor.get_all_users()
        if not users:
            raise ValueError("No users found in transaction data")
        
        # Generate statements for all users
        cashflow_statements = {}
        
        # Individual user statements
        for user in users:
            user_transactions = processor.get_transactions_by_user(user)
            cashflow_stmt = self.cashflow_generator.generate_statement(user_transactions, user)
            cashflow_statements[user] = cashflow_stmt
        
        # Combined statement
        combined_cashflow = self.cashflow_generator.generate_statement(processor.transactions, "Combined")
        cashflow_statements["Combined"] = combined_cashflow
        
        return cashflow_statements, users
    
    def generate_single_statement(self, tmp_file_path: str, entity_name: str) -> Dict:
        """
        Generate cash flow statement for a single entity.
        
        Args:
            tmp_file_path: Path to CSV file
            entity_name: Name of entity or 'Combined' for all users
            
        Returns:
            Cash flow statement dictionary
        """
        processor = TransactionProcessor(tmp_file_path)
        processor.load_transactions()
        
        if entity_name == "Combined":
            transactions = processor.transactions
        else:
            transactions = processor.get_transactions_by_user(entity_name)
        
        return self.cashflow_generator.generate_statement(transactions, entity_name)