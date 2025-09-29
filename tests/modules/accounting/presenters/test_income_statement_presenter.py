"""
Tests for Income Statement Presenter (MVP refactored structure)

Tests the presentation layer coordination logic.
"""

import pytest
import tempfile
import os
import pandas as pd
from unittest.mock import patch, MagicMock

from src.modules.accounting.presenters.income_statement_presenter import IncomeStatementPresenter


class TestIncomeStatementPresenter:
    """Test Income Statement Presenter"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.presenter = IncomeStatementPresenter()
    
    def create_test_csv(self, data):
        """Helper to create temporary CSV file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            df = pd.DataFrame(data)
            df.to_csv(f.name, index=False)
            return f.name
    
    def test_presenter_initialization(self):
        """Test presenter initializes correctly"""
        assert self.presenter.category_mapper is not None
        assert self.presenter.income_generator is not None
    
    def test_process_transactions_and_generate_statements(self):
        """Test complete transaction processing workflow"""
        # Create test data
        test_data = [
            {
                'Description': 'Salary',
                'Amount': 5000.0,
                'Debit': '工资收入',
                'Credit': 'Cash',
                'User': 'User1'
            },
            {
                'Description': 'Food expense',
                'Amount': -200.0,
                'Debit': '餐饮',
                'Credit': 'Cash',
                'User': 'User1'
            }
        ]
        
        csv_path = self.create_test_csv(test_data)
        
        try:
            # Process through presenter
            income_statements, users = self.presenter.process_transactions_and_generate_statements(csv_path)
            
            # Verify results
            assert 'User1' in users
            assert 'User1' in income_statements
            assert 'Combined' in income_statements
            
            user1_statement = income_statements['User1']
            assert user1_statement['Entity'] == 'User1'
            assert user1_statement['Total Revenue'] > 0
            assert user1_statement['Total Expenses'] > 0
            
        finally:
            # Cleanup
            os.unlink(csv_path)
    
    def test_generate_single_statement(self):
        """Test single statement generation"""
        # Create test data
        test_data = [
            {
                'Description': 'Salary',
                'Amount': 3000.0,
                'Debit': '工资收入',
                'Credit': 'Cash',
                'User': 'TestUser'
            }
        ]
        
        csv_path = self.create_test_csv(test_data)
        
        try:
            # Generate single statement
            statement = self.presenter.generate_single_statement(csv_path, 'TestUser')
            
            # Verify results
            assert statement['Entity'] == 'TestUser'
            assert statement['Total Revenue'] == 3000.0
            assert '工资收入' in statement['Revenue']
            
        finally:
            # Cleanup
            os.unlink(csv_path)
    
    def test_empty_file_handling(self):
        """Test handling of empty CSV file"""
        csv_path = self.create_test_csv([])
        
        try:
            with pytest.raises(ValueError, match="No users found"):
                self.presenter.process_transactions_and_generate_statements(csv_path)
        finally:
            os.unlink(csv_path)