"""
Income Statement Presenter

Coordinates between income statement models and views. 
Handles the workflow of processing transactions and generating income statements.

NEW WORKFLOW:
1. CSV Upload (View) → 2. DataCleaner (Model) → 3. User Preview (View) → 
4. TransactionProcessor (Model) → 5. IncomeStatementGenerator (Model)
"""

from typing import Dict, List, Tuple
import pandas as pd

from ..models.business.data_cleaner import DataCleaner, ValidationReport
from ..models.business.transaction_processor import TransactionProcessor
from ..models.business.income_statement_generator import IncomeStatementGenerator
from ..models.domain.category import CategoryMapper


class IncomeStatementPresenter:
    """Presenter for income statement generation workflow"""
    
    def __init__(self):
        self.category_mapper = CategoryMapper()
        self.income_generator = IncomeStatementGenerator(self.category_mapper)
    
    def clean_and_validate_csv(self, csv_file_path: str) -> Tuple[pd.DataFrame, ValidationReport]:
        """
        Step 2 of workflow: Clean and validate CSV data BEFORE user preview.
        
        Args:
            csv_file_path: Path to uploaded CSV file
            
        Returns:
            Tuple of (cleaned_dataframe, validation_report)
        """
        cleaner = DataCleaner(csv_file_path=csv_file_path)
        cleaned_df, validation_report = cleaner.clean_and_validate()
        return cleaned_df, validation_report
    
    def process_clean_dataframe_and_generate_statements(self, 
                                                        cleaned_df: pd.DataFrame) -> Tuple[Dict, List[str]]:
        """
        Step 4-5 of workflow: Process CLEAN DataFrame and generate income statements.
        
        This assumes:
        - DataFrame has been cleaned by DataCleaner
        - User has reviewed and corrected any validation errors in the preview
        
        Args:
            cleaned_df: Clean DataFrame from DataCleaner (possibly user-edited)
            
        Returns:
            Tuple of (income_statements_dict, users_list)
        """
        # Process transactions from clean DataFrame
        processor = TransactionProcessor(dataframe=cleaned_df)
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
    
    def process_transactions_and_generate_statements(self, tmp_file_path: str) -> Tuple[Dict, List[str]]:
        """
        Process transactions from CSV and generate income statements for all users.
        
        LEGACY METHOD: For backward compatibility. 
        NEW CODE should use clean_and_validate_csv() → (user preview) → process_clean_dataframe_and_generate_statements()
        
        Args:
            tmp_file_path: Path to temporary CSV file
            
        Returns:
            Tuple of (income_statements_dict, users_list)
        """
        # NEW WORKFLOW: Clean and validate first
        cleaned_df, validation_report = self.clean_and_validate_csv(tmp_file_path)
        
        # If there are validation errors, raise exception with details
        if validation_report.has_errors():
            error_messages = [error.message for error in validation_report.errors]
            raise ValueError(f"Data validation failed:\n" + "\n".join(error_messages))
        
        # Process clean DataFrame
        return self.process_clean_dataframe_and_generate_statements(cleaned_df)
    
    def generate_single_statement(self, tmp_file_path: str, entity_name: str) -> Dict:
        """
        Generate income statement for a single entity.
        
        LEGACY METHOD: For backward compatibility.
        
        Args:
            tmp_file_path: Path to CSV file
            entity_name: Name of entity or 'Combined' for all users
            
        Returns:
            Income statement dictionary
        """
        # NEW WORKFLOW: Clean and validate first
        cleaned_df, validation_report = self.clean_and_validate_csv(tmp_file_path)
        
        # If there are validation errors, raise exception with details
        if validation_report.has_errors():
            error_messages = [error.message for error in validation_report.errors]
            raise ValueError(f"Data validation failed:\n" + "\n".join(error_messages))
        
        # Process clean DataFrame
        processor = TransactionProcessor(dataframe=cleaned_df)
        processor.load_transactions()
        
        if entity_name == "Combined":
            transactions = processor.transactions
        else:
            transactions = processor.get_transactions_by_user(entity_name)
        
        return self.income_generator.generate_statement(transactions, entity_name)