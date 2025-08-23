"""
Test suite for Professional Accounting Module - Data Models

ACCEPTANCE CRITERIA → TEST MAPPING:
- FR-1.1: Transaction Journal Entry → test_transaction_model_*
- FR-1.2: Asset Portfolio Input → test_asset_model_*
- Data validation requirements → test_data_validation_*
- Currency format validation → test_currency_validation_*

ASSUMPTIONS FOR VALIDATION:
1. Transaction amounts can be positive (income) or negative (expenses)
2. Currency is always Chinese Yuan (¥) with 2 decimal precision
3. Categories must match predefined taxonomy
4. Account types are limited to: Cash, Credit, Debit
5. Asset account types are: checking, savings, investment, retirement
6. Timestamps are stored in UTC format
7. User IDs are UUID strings
8. Required fields cannot be None or empty strings
"""

import pytest
from decimal import Decimal
from datetime import datetime
from typing import Optional
import uuid

# Import actual data models from accounting module
from src.accounting.models import Transaction, Asset, EXPENSE_CATEGORIES


class TestTransactionModel:
    """Test Transaction model validation and functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.base_transaction_data = {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "date": datetime(2024, 1, 15),
            "description": "Coffee purchase",
            "amount": Decimal("25.50"),
            "category": "餐饮",
            "account_type": "Cash",
            "transaction_type": "Cash"
        }
    
    def test_transaction_creation_valid_data(self):
        """Test creating transaction with valid data"""
        transaction = Transaction(**self.base_transaction_data)
        
        assert transaction.id == self.base_transaction_data["id"]
        assert transaction.description == "Coffee purchase"
        assert transaction.amount == Decimal("25.50")
        assert transaction.category == "餐饮"
        assert transaction.account_type == "Cash"
        assert transaction.transaction_type == "Cash"
        assert transaction.notes is None
        assert isinstance(transaction.created_at, datetime)
        assert isinstance(transaction.updated_at, datetime)
    
    def test_transaction_with_optional_notes(self):
        """Test transaction creation with optional notes"""
        data = self.base_transaction_data.copy()
        data["notes"] = "Business meeting coffee"
        
        transaction = Transaction(**data)
        assert transaction.notes == "Business meeting coffee"
    
    @pytest.mark.parametrize("account_type", ["Cash", "Credit", "Debit"])
    def test_transaction_valid_account_types(self, account_type):
        """Test all valid account types"""
        data = self.base_transaction_data.copy()
        data["account_type"] = account_type
        
        transaction = Transaction(**data)
        assert transaction.account_type == account_type
    
    @pytest.mark.parametrize("transaction_type", ["Cash", "Non-Cash"])
    def test_transaction_valid_transaction_types(self, transaction_type):
        """Test all valid transaction types"""
        data = self.base_transaction_data.copy()
        data["transaction_type"] = transaction_type
        
        transaction = Transaction(**data)
        assert transaction.transaction_type == transaction_type
    
    @pytest.mark.parametrize("invalid_account_type", ["credit", "CASH", "Bank", ""])
    def test_transaction_invalid_account_types(self, invalid_account_type):
        """Test invalid account types raise ValueError"""
        data = self.base_transaction_data.copy()
        data["account_type"] = invalid_account_type
        
        with pytest.raises(ValueError, match="Account type must be Cash, Credit, or Debit"):
            Transaction(**data)
    
    @pytest.mark.parametrize("invalid_description", ["", "   ", None])
    def test_transaction_invalid_description(self, invalid_description):
        """Test empty or None descriptions raise ValueError"""
        data = self.base_transaction_data.copy()
        data["description"] = invalid_description
        
        with pytest.raises(ValueError, match="Description cannot be empty"):
            Transaction(**data)
    
    def test_transaction_supports_chinese_description(self):
        """Test Chinese characters in description"""
        data = self.base_transaction_data.copy()
        data["description"] = "星巴克咖啡购买"
        
        transaction = Transaction(**data)
        assert transaction.description == "星巴克咖啡购买"
    
    def test_transaction_supports_negative_amounts(self):
        """Test negative amounts for expenses"""
        data = self.base_transaction_data.copy()
        data["amount"] = Decimal("-100.00")
        
        transaction = Transaction(**data)
        assert transaction.amount == Decimal("-100.00")
    
    def test_transaction_precision_decimal_amounts(self):
        """Test decimal precision handling"""
        data = self.base_transaction_data.copy()
        data["amount"] = Decimal("123.456")
        
        transaction = Transaction(**data)
        assert transaction.amount == Decimal("123.456")


class TestAssetModel:
    """Test Asset model validation and functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.base_asset_data = {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "account_name": "中国银行储蓄账户",
            "balance": Decimal("50000.00"),
            "account_type": "checking",
            "as_of_date": datetime(2024, 1, 31),
            "currency": "CNY"
        }
    
    def test_asset_creation_valid_data(self):
        """Test creating asset with valid data"""
        asset = Asset(**self.base_asset_data)
        
        assert asset.account_name == "中国银行储蓄账户"
        assert asset.balance == Decimal("50000.00")
        assert asset.account_type == "checking"
        assert asset.currency == "CNY"
        assert isinstance(asset.created_at, datetime)
    
    @pytest.mark.parametrize("account_type", ["checking", "savings", "investment", "retirement"])
    def test_asset_valid_account_types(self, account_type):
        """Test all valid asset account types"""
        data = self.base_asset_data.copy()
        data["account_type"] = account_type
        
        asset = Asset(**data)
        assert asset.account_type == account_type
    
    @pytest.mark.parametrize("invalid_account_type", ["CHECKING", "bank", "credit", ""])
    def test_asset_invalid_account_types(self, invalid_account_type):
        """Test invalid account types raise ValueError"""
        data = self.base_asset_data.copy()
        data["account_type"] = invalid_account_type
        
        with pytest.raises(ValueError, match="Account type must be checking, savings, investment, or retirement"):
            Asset(**data)
    
    def test_asset_default_currency_cny(self):
        """Test default currency is CNY"""
        data = self.base_asset_data.copy()
        del data["currency"]
        
        asset = Asset(**data)
        assert asset.currency == "CNY"
    
    def test_asset_currency_validation(self):
        """Test currency must be CNY"""
        data = self.base_asset_data.copy()
        data["currency"] = "USD"
        
        with pytest.raises(ValueError, match="Currency must be CNY"):
            Asset(**data)
    
    @pytest.mark.parametrize("invalid_account_name", ["", "   ", None])
    def test_asset_invalid_account_name(self, invalid_account_name):
        """Test empty or None account names raise ValueError"""
        data = self.base_asset_data.copy()
        data["account_name"] = invalid_account_name
        
        with pytest.raises(ValueError, match="Account name cannot be empty"):
            Asset(**data)
    
    def test_asset_supports_zero_balance(self):
        """Test zero balance is allowed"""
        data = self.base_asset_data.copy()
        data["balance"] = Decimal("0.00")
        
        asset = Asset(**data)
        assert asset.balance == Decimal("0.00")
    
    def test_asset_supports_negative_balance(self):
        """Test negative balance for credit accounts"""
        data = self.base_asset_data.copy()
        data["balance"] = Decimal("-5000.00")
        
        asset = Asset(**data)
        assert asset.balance == Decimal("-5000.00")


class TestCategoryTaxonomy:
    """Test category taxonomy validation"""
    
    def test_expense_categories_structure(self):
        """Test expense categories match PRD specification"""
        assert "fixed_costs" in EXPENSE_CATEGORIES
        assert "food_dining" in EXPENSE_CATEGORIES
        assert "transportation" in EXPENSE_CATEGORIES
        assert "daily_shopping" in EXPENSE_CATEGORIES
        assert "personal" in EXPENSE_CATEGORIES
        assert "health_fitness" in EXPENSE_CATEGORIES
        assert "social_entertainment" in EXPENSE_CATEGORIES
        assert "pets" in EXPENSE_CATEGORIES
        assert "work_related" in EXPENSE_CATEGORIES
    
    def test_expense_categories_content(self):
        """Test specific categories contain expected items"""
        assert "房租" in EXPENSE_CATEGORIES["fixed_costs"]
        assert "餐饮" in EXPENSE_CATEGORIES["food_dining"]
        assert "交通" in EXPENSE_CATEGORIES["transportation"]
    
    def test_all_categories_are_lists(self):
        """Test all categories are lists of strings"""
        for category_name, items in EXPENSE_CATEGORIES.items():
            assert isinstance(items, list)
            for item in items:
                assert isinstance(item, str)
                assert item.strip()  # Not empty
    
    def test_valid_transaction_categories(self):
        """Test transactions can use any valid category"""
        all_categories = []
        for category_list in EXPENSE_CATEGORIES.values():
            all_categories.extend(category_list)
        
        # Test with a few categories
        test_categories = ["房租", "餐饮", "交通", "宠物"]
        
        for category in test_categories:
            assert category in all_categories
            
            # Should be able to create transaction with this category
            data = {
                "id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
                "date": datetime(2024, 1, 15),
                "description": f"Test transaction for {category}",
                "amount": Decimal("100.00"),
                "category": category,
                "account_type": "Cash",
                "transaction_type": "Cash"
            }
            
            transaction = Transaction(**data)
            assert transaction.category == category


class TestDataValidation:
    """Test comprehensive data validation scenarios"""
    
    def test_uuid_format_validation(self):
        """Test UUID format for IDs"""
        # Valid UUID
        valid_uuid = str(uuid.uuid4())
        
        data = {
            "id": valid_uuid,
            "user_id": str(uuid.uuid4()),
            "date": datetime(2024, 1, 15),
            "description": "Test",
            "amount": Decimal("100.00"),
            "category": "餐饮",
            "account_type": "Cash",
            "transaction_type": "Cash"
        }
        
        transaction = Transaction(**data)
        assert transaction.id == valid_uuid
    
    def test_datetime_timezone_handling(self):
        """Test datetime handling for different timezone scenarios"""
        # Test UTC datetime
        utc_date = datetime(2024, 1, 15, 12, 0, 0)
        
        data = {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "date": utc_date,
            "description": "Test",
            "amount": Decimal("100.00"),
            "category": "餐饮",
            "account_type": "Cash",
            "transaction_type": "Cash"
        }
        
        transaction = Transaction(**data)
        assert transaction.date == utc_date
        
        # Test that created_at is set automatically
        assert transaction.created_at is not None
        assert isinstance(transaction.created_at, datetime)
    
    @pytest.mark.parametrize("amount,expected", [
        ("0.00", Decimal("0.00")),
        ("123.45", Decimal("123.45")),
        ("-567.89", Decimal("-567.89")),
        ("0.01", Decimal("0.01")),
        ("99999.99", Decimal("99999.99"))
    ])
    def test_currency_amount_validation(self, amount, expected):
        """Test various currency amount formats"""
        data = {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "date": datetime(2024, 1, 15),
            "description": "Test",
            "amount": Decimal(amount),
            "category": "餐饮",
            "account_type": "Cash",
            "transaction_type": "Cash"
        }
        
        transaction = Transaction(**data)
        assert transaction.amount == expected