"""
Data models for Professional Accounting Module

This module defines the core data structures for transactions and assets
as specified in the PRD, with comprehensive validation and Chinese language support.
"""

from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional
import uuid


class Transaction:
    """
    Transaction model as specified in PRD
    
    Represents a financial transaction with comprehensive validation
    for personal accounting use cases.
    """
    
    def __init__(
        self,
        id: str,
        user_id: str,
        date: datetime,
        description: str,
        amount: Decimal,
        category: str,
        account_type: str,
        transaction_type: str,
        notes: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.user_id = user_id
        self.date = date
        self.description = description
        self.amount = amount
        self.category = category
        self.account_type = account_type
        self.transaction_type = transaction_type
        self.notes = notes
        self.created_at = created_at or datetime.now(timezone.utc).replace(tzinfo=None)
        self.updated_at = updated_at or datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Validate all fields according to PRD requirements
        self._validate()
    
    def _validate(self):
        """Validate transaction data according to PRD requirements"""
        if not self.description or not self.description.strip():
            raise ValueError("Description cannot be empty")
        
        if self.account_type not in ["Cash", "Credit", "Debit"]:
            raise ValueError("Account type must be Cash, Credit, or Debit")
        
        if self.transaction_type not in ["Cash", "Non-Cash"]:
            raise ValueError("Transaction type must be Cash or Non-Cash")
        
        if not self.category or not self.category.strip():
            raise ValueError("Category cannot be empty")
    
    def to_dict(self) -> dict:
        """Convert transaction to dictionary for CSV export"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.strftime('%Y-%m-%d'),
            'description': self.description,
            'amount': float(self.amount),
            'category': self.category,
            'account_type': self.account_type,
            'transaction_type': self.transaction_type,
            'notes': self.notes or '',
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Transaction':
        """Create transaction from dictionary (CSV import)"""
        return cls(
            id=data['id'],
            user_id=data['user_id'],
            date=datetime.fromisoformat(data['date']) if isinstance(data['date'], str) else data['date'],
            description=data['description'],
            amount=Decimal(str(data['amount'])),
            category=data['category'],
            account_type=data['account_type'],
            transaction_type=data['transaction_type'],
            notes=data.get('notes'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )


class Asset:
    """
    Asset model as specified in PRD
    
    Represents account balances and positions with support for
    multiple account types and month-over-month tracking.
    """
    
    def __init__(
        self,
        id: str,
        user_id: str,
        account_name: str,
        balance: Decimal,
        account_type: str,
        as_of_date: datetime,
        currency: str = "CNY",
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.user_id = user_id
        self.account_name = account_name
        self.balance = balance
        self.account_type = account_type
        self.as_of_date = as_of_date
        self.currency = currency
        self.created_at = created_at or datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Validate all fields according to PRD requirements
        self._validate()
    
    def _validate(self):
        """Validate asset data according to PRD requirements"""
        if not self.account_name or not self.account_name.strip():
            raise ValueError("Account name cannot be empty")
        
        if self.account_type not in ["checking", "savings", "investment", "retirement"]:
            raise ValueError("Account type must be checking, savings, investment, or retirement")
        
        if self.currency != "CNY":
            raise ValueError("Currency must be CNY")
    
    def to_dict(self) -> dict:
        """Convert asset to dictionary for CSV export"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'account_name': self.account_name,
            'balance': float(self.balance),
            'account_type': self.account_type,
            'as_of_date': self.as_of_date.strftime('%Y-%m-%d'),
            'currency': self.currency,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Asset':
        """Create asset from dictionary (CSV import)"""
        return cls(
            id=data['id'],
            user_id=data['user_id'],
            account_name=data['account_name'],
            balance=Decimal(str(data['balance'])),
            account_type=data['account_type'],
            as_of_date=datetime.fromisoformat(data['as_of_date']) if isinstance(data['as_of_date'], str) else data['as_of_date'],
            currency=data.get('currency', 'CNY'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        )


# Category taxonomy from PRD - Chinese language support
EXPENSE_CATEGORIES = {
    "fixed_costs": ["房租", "水电费", "保险"],
    "food_dining": ["餐饮", "买菜/杭州日常餐饮"],
    "transportation": ["交通", "通勤"],
    "daily_shopping": ["日用购物", "服饰"],
    "personal": ["个人消费", "教育/买书"],
    "health_fitness": ["运动和健康", "买药/医疗"],
    "social_entertainment": ["人情/旅行支出", "社交吃饭"],
    "pets": ["宠物"],
    "work_related": ["办公支出"]
}

# Revenue categories from income statement generator
REVENUE_CATEGORIES = ["工资收入", "服务收入", "投资收益", "其他收入"]


def get_all_categories() -> list[str]:
    """Get flattened list of all valid categories"""
    all_categories = []
    for category_list in EXPENSE_CATEGORIES.values():
        all_categories.extend(category_list)
    # Add revenue categories
    all_categories.extend(REVENUE_CATEGORIES)
    return all_categories


def validate_category(category: str) -> bool:
    """Check if category is in the valid taxonomy"""
    return category in get_all_categories()


def get_category_group(category: str) -> Optional[str]:
    """Get the category group (key) for a specific category"""
    for group, categories in EXPENSE_CATEGORIES.items():
        if category in categories:
            return group
    return None