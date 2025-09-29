"""
Tests for domain models (MVP refactored structure)

Tests the core domain entities - Transaction, CategoryMapper, etc.
"""

import pytest
from src.modules.accounting.models.domain import (
    Transaction, 
    CategoryMapper, 
    REVENUE_CATEGORIES, 
    get_all_categories
)


class TestTransaction:
    """Test Transaction domain entity"""
    
    def test_transaction_creation(self):
        """Test basic transaction creation"""
        transaction = Transaction(
            description="Test expense",
            amount=100.0,
            debit_category="餐饮",
            credit_account="Cash",
            user="User1"
        )
        
        assert transaction.description == "Test expense"
        assert transaction.amount == 100.0
        assert transaction.debit_category == "餐饮"
        assert transaction.credit_account == "Cash"
        assert transaction.user == "User1"
        assert transaction.transaction_type == "expense"  # default
        assert transaction.affects_cash_flow == True  # default


class TestCategoryMapper:
    """Test CategoryMapper domain entity"""
    
    def test_category_mapper_creation(self):
        """Test CategoryMapper initialization"""
        mapper = CategoryMapper()
        
        assert '餐饮' in mapper.expense_categories
        assert mapper.expense_categories['餐饮'] == 'Food & Dining'
        
        assert '餐饮' in mapper.cashflow_categories
        assert mapper.cashflow_categories['餐饮'] == 'Operating Activities'
    
    def test_get_expense_category(self):
        """Test expense category mapping"""
        mapper = CategoryMapper()
        
        assert mapper.get_expense_category('餐饮') == 'Food & Dining'
        assert mapper.get_expense_category('房租') == 'Rent'
        assert mapper.get_expense_category('Unknown Category') == 'Other Expenses'
    
    def test_get_cashflow_category(self):
        """Test cash flow category mapping"""
        mapper = CategoryMapper()
        
        assert mapper.get_cashflow_category('餐饮') == 'Operating Activities'
        assert mapper.get_cashflow_category('投资收益') == 'Investing Activities'
        assert mapper.get_cashflow_category('Unknown Category') == 'Operating Activities'


class TestCategoryConstants:
    """Test category constants and helper functions"""
    
    def test_revenue_categories(self):
        """Test REVENUE_CATEGORIES constant"""
        assert '工资收入' in REVENUE_CATEGORIES
        assert '服务收入' in REVENUE_CATEGORIES
        assert '投资收益' in REVENUE_CATEGORIES
    
    def test_get_all_categories(self):
        """Test get_all_categories helper function"""
        all_categories = get_all_categories()
        
        # Should include expense categories
        assert '餐饮' in all_categories
        assert '房租' in all_categories
        
        # Should include revenue categories
        assert '工资收入' in all_categories
        assert '服务收入' in all_categories
        
        # Should not have duplicates
        assert len(all_categories) == len(set(all_categories))