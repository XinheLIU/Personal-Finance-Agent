"""
Cash Flow Presenter

Coordinates between cash flow models and views.
Handles the workflow of processing transactions and generating cash flow statements.
"""

from typing import Any, Dict, List, Tuple
import pandas as pd

from ..models.business.transaction_processor import TransactionProcessor
from ..models.business.cash_flow_generator import CashFlowStatementGenerator
from ..models.domain.category import CategoryMapper


class CashFlowPresenter:
    """Presenter for cash flow statement generation workflow.

    Coordinates between the data processing layer (TransactionProcessor) and
    the business logic layer (CashFlowStatementGenerator) to generate cash flow
    statements for multiple users.

    Attributes:
        category_mapper (CategoryMapper): Maps categories to activity types.
        cashflow_generator (CashFlowStatementGenerator): Generates statements.
    """

    def __init__(self) -> None:
        """Initialize the cash flow presenter with required dependencies."""
        self.category_mapper = CategoryMapper()
        self.cashflow_generator = CashFlowStatementGenerator(self.category_mapper)

    def _generate_statements_for_all_users(
        self, processor: TransactionProcessor
    ) -> Tuple[Dict[str, Dict], List[str]]:
        """Generate cash flow statements for all users and combined.

        This is a private helper method to avoid code duplication between
        DataFrame and file-based processing methods.

        Args:
            processor: TransactionProcessor with loaded transactions.

        Returns:
            Tuple containing:
                - cashflow_statements_dict: Dict mapping entity names to statements
                - users_list: List of individual user names

        Raises:
            ValueError: If no users found in transaction data.
        """
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
        combined_cashflow = self.cashflow_generator.generate_statement(
            processor.transactions, "Combined"
        )
        cashflow_statements["Combined"] = combined_cashflow

        return cashflow_statements, users

    def process_clean_dataframe_and_generate_statements(
        self, cleaned_df: pd.DataFrame
    ) -> Tuple[Dict[str, Dict], List[str]]:
        """Process clean DataFrame and generate cash flow statements for all users.

        This method assumes the DataFrame has been cleaned and validated by DataCleaner
        and any user corrections have been applied.

        Args:
            cleaned_df: Clean DataFrame with columns: Description, Amount, Debit, Credit, User.

        Returns:
            Tuple containing:
                - cashflow_statements_dict: Dict mapping entity names to cash flow statements
                - users_list: List of individual user names (excludes "Combined")

        Raises:
            ValueError: If required columns are missing or no users found in data.

        Note:
            Generates statements for each user individually plus a "Combined" statement.
        """
        # Validate DataFrame has required columns
        required_columns = ['Description', 'Amount', 'Debit', 'Credit', 'User']
        missing_columns = [col for col in required_columns if col not in cleaned_df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Process transactions from clean DataFrame
        processor = TransactionProcessor(dataframe=cleaned_df)
        processor.load_transactions()

        # Generate statements using common helper method
        return self._generate_statements_for_all_users(processor)

    def process_transactions_and_generate_statements(
        self, tmp_file_path: str
    ) -> Tuple[Dict[str, Dict], List[str]]:
        """Process transactions from CSV file and generate cash flow statements.

        Args:
            tmp_file_path: Path to temporary CSV file with transaction data.

        Returns:
            Tuple containing:
                - cashflow_statements_dict: Dict mapping entity names to cash flow statements
                - users_list: List of individual user names (excludes "Combined")

        Raises:
            ValueError: If no users found in transaction data.

        Note:
            Generates statements for each user individually plus a "Combined" statement.
        """
        # Process transactions
        processor = TransactionProcessor(tmp_file_path)
        processor.load_transactions()

        # Generate statements using common helper method
        return self._generate_statements_for_all_users(processor)
    
    def generate_single_statement(self, tmp_file_path: str, entity_name: str) -> Dict[str, Any]:
        """Generate cash flow statement for a single entity.

        Args:
            tmp_file_path: Path to CSV file with transaction data.
            entity_name: Name of specific user or 'Combined' for all users.

        Returns:
            Cash flow statement dictionary for the specified entity.

        Note:
            If entity_name is "Combined", processes all transactions together.
            Otherwise, filters transactions for the specified user.
        """
        processor = TransactionProcessor(tmp_file_path)
        processor.load_transactions()
        
        if entity_name == "Combined":
            transactions = processor.transactions
        else:
            transactions = processor.get_transactions_by_user(entity_name)
        
        return self.cashflow_generator.generate_statement(transactions, entity_name)