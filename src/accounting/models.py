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
        account_name: str,
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
        self.account_name = account_name
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
            'account_name': self.account_name,
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
            account_name=data['account_name'],
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


# New simplified models for monthly workflow

class MonthlyAsset:
    """
    Simplified asset model for monthly processing workflow
    
    Matches the sample CSV format: Account, CNY, USD, Asset Class
    """
    
    def __init__(
        self,
        account_name: str,
        cny_balance: Decimal,
        usd_balance: Decimal,
        asset_class: str,
        as_of_date: datetime
    ):
        self.account_name = account_name
        self.cny_balance = cny_balance
        self.usd_balance = usd_balance
        self.asset_class = asset_class
        self.as_of_date = as_of_date
        
        self._validate()
    
    def _validate(self):
        """Validate asset data"""
        if not self.account_name or not self.account_name.strip():
            raise ValueError("Account name cannot be empty")
        
        valid_classes = ["Cash", "Investments", "Long-term investments"]
        if self.asset_class not in valid_classes:
            raise ValueError(f"Asset class must be one of: {', '.join(valid_classes)}")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for CSV export"""
        return {
            'Account': self.account_name,
            'CNY': float(self.cny_balance),
            'USD': float(self.usd_balance),
            'Asset Class': self.asset_class
        }
    
    @classmethod
    def from_dict(cls, data: dict, as_of_date: datetime) -> 'MonthlyAsset':
        """Create from dictionary (CSV import)"""
        # Handle currency formatting (remove ¥, $, commas)
        cny_str = str(data.get('CNY', '0')).replace('¥', '').replace(',', '').strip()
        usd_str = str(data.get('USD', '0')).replace('$', '').replace(',', '').strip()
        
        # Handle empty values
        cny_balance = Decimal('0') if not cny_str else Decimal(cny_str)
        usd_balance = Decimal('0') if not usd_str else Decimal(usd_str)
        
        return cls(
            account_name=data['Account'],
            cny_balance=cny_balance,
            usd_balance=usd_balance,
            asset_class=data['Asset Class'],
            as_of_date=as_of_date
        )


class ExchangeRate:
    """
    USD/CNY exchange rate for currency conversion
    """
    
    def __init__(self, rate: Decimal, date: datetime):
        self.rate = rate
        self.date = date
        self._validate()
    
    def _validate(self):
        """Validate exchange rate"""
        if self.rate <= 0:
            raise ValueError("Exchange rate must be positive")
    
    def cny_to_usd(self, cny_amount: Decimal) -> Decimal:
        """Convert CNY to USD"""
        return cny_amount / self.rate
    
    def usd_to_cny(self, usd_amount: Decimal) -> Decimal:
        """Convert USD to CNY"""
        return usd_amount * self.rate
    
    @classmethod
    def from_text_file(cls, file_path: str, date: datetime) -> 'ExchangeRate':
        """Load exchange rate from text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                rate_str = f.read().strip()
                rate = Decimal(rate_str)
                return cls(rate=rate, date=date)
        except (FileNotFoundError, ValueError) as e:
            raise ValueError(f"Could not load exchange rate from {file_path}: {e}")


class MonthlyTransaction:
    """
    Simplified transaction model for monthly processing
    
    Note: Format to be determined based on corrected sample CSV
    """
    
    def __init__(
        self,
        date: datetime,
        description: str,
        amount: Decimal,
        category: str,
        account_name: str,
        currency: str = "CNY",
        notes: Optional[str] = None
    ):
        self.date = date
        self.description = description
        self.amount = amount
        self.category = category
        self.account_name = account_name
        self.currency = currency
        self.notes = notes
        
        self._validate()
    
    def _validate(self):
        """Validate transaction data"""
        if not self.description or not self.description.strip():
            raise ValueError("Description cannot be empty")
        
        if self.currency not in ["CNY", "USD"]:
            raise ValueError("Currency must be CNY or USD")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for CSV export"""
        return {
            'date': self.date.strftime('%Y-%m-%d'),
            'description': self.description,
            'amount': float(self.amount),
            'category': self.category,
            'account_name': self.account_name,
            'currency': self.currency,
            'notes': self.notes or ''
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MonthlyTransaction':
        """Create from dictionary (CSV import)"""
        return cls(
            date=datetime.fromisoformat(data['date']) if isinstance(data['date'], str) else data['date'],
            description=data['description'],
            amount=Decimal(str(data['amount'])),
            category=data['category'],
            account_name=data['account_name'],
            currency=data.get('currency', 'CNY'),
            notes=data.get('notes')
        )


class OwnerEquity:
    """
    Multi-user owner equity model
    """
    
    def __init__(self, owner_name: str, equity_amount: Decimal):
        self.owner_name = owner_name
        self.equity_amount = equity_amount
        
        self._validate()
    
    def _validate(self):
        """Validate owner equity"""
        if not self.owner_name or not self.owner_name.strip():
            raise ValueError("Owner name cannot be empty")
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'owner_name': self.owner_name,
            'equity_amount': float(self.equity_amount)
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'OwnerEquity':
        """Create from dictionary"""
        return cls(
            owner_name=data['owner_name'],
            equity_amount=Decimal(str(data['equity_amount']))
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