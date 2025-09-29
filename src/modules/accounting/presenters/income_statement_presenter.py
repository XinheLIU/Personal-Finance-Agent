"""
Income Statement Presenter

Coordinates between income statement models and views. 
Handles the workflow of processing transactions and generating income statements.
"""

from typing import Dict, List, Tuple

from ..models.business.transaction_processor import TransactionProcessor
from ..models.business.income_statement_generator import IncomeStatementGenerator
from ..models.domain.category import CategoryMapper


class IncomeStatementPresenter:
    """Presenter for income statement generation workflow"""
    
    def __init__(self):
        self.category_mapper = CategoryMapper()
        self.income_generator = IncomeStatementGenerator(self.category_mapper)
    
    def process_transactions_and_generate_statements(self, tmp_file_path: str) -> Tuple[Dict, List[str]]:
        """
        Process transactions from CSV and generate income statements for all users.
        
        Args:
            tmp_file_path: Path to temporary CSV file
            
        Returns:
            Tuple of (income_statements_dict, users_list)
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
        
        # Individual user statements
        for user in users:
            user_transactions = processor.get_transactions_by_user(user)
            income_stmt = self.income_generator.generate_statement(user_transactions, user)
            income_statements[user] = income_stmt
        
        # Combined statement
        combined_income = self.income_generator.generate_statement(processor.transactions, "Combined")
        income_statements["Combined"] = combined_income
        
        return income_statements, users
    
    def generate_single_statement(self, tmp_file_path: str, entity_name: str) -> Dict:
        """
        Generate income statement for a single entity.
        
        Args:
            tmp_file_path: Path to CSV file
            entity_name: Name of entity or 'Combined' for all users
            
        Returns:
            Income statement dictionary
        """
        processor = TransactionProcessor(tmp_file_path)
        processor.load_transactions()
        
        if entity_name == "Combined":
            transactions = processor.transactions
        else:
            transactions = processor.get_transactions_by_user(entity_name)
        
        return self.income_generator.generate_statement(transactions, entity_name)