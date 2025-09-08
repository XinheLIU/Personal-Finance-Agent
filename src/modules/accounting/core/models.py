"""
Simplified data models for accounting module

Based on the example implementation, focusing on essential functionality
for income statement and cash flow generation.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Transaction:
    """Represents a single transaction"""
    description: str
    amount: float
    debit_category: str
    credit_account: str
    user: str
    transaction_type: str = "expense"  # revenue, expense, prepaid_asset
    affects_cash_flow: bool = True     # whether this transaction affects cash flow
    

class CategoryMapper:
    """Maps transaction categories to financial statement categories"""
    
    def __init__(self):
        # Define category mappings for income statement
        self.expense_categories = {
            '餐饮': 'Food & Dining',
            '通勤': 'Transportation', 
            '人情/旅行支出': 'Travel & Entertainment',
            '日用购物': 'General Shopping',
            '个人消费': 'Personal Expenses',
            '运动和健康': 'Health & Wellness',
            '水电': 'Utilities',
            '宠物': 'Pet Expenses',
            '房租': 'Rent',
            '保险': 'Insurance',
            '交通': 'Transportation',
            '服饰': 'Clothing',
            '教育/买书': 'Education',
            '买药/医疗': 'Medical',
            '社交吃饭': 'Social Dining',
            '办公支出': 'Office Expenses'
        }
        
        # Define category mappings for cash flow statement
        self.cashflow_categories = {
            '餐饮': 'Operating Activities',
            '通勤': 'Operating Activities',
            '人情/旅行支出': 'Operating Activities', 
            '日用购物': 'Operating Activities',
            '个人消费': 'Operating Activities',
            '运动和健康': 'Operating Activities',
            '水电': 'Operating Activities',
            '宠物': 'Operating Activities',
            '房租': 'Operating Activities',
            '保险': 'Operating Activities',
            '交通': 'Operating Activities',
            '服饰': 'Operating Activities',
            '教育/买书': 'Operating Activities',
            '买药/医疗': 'Operating Activities',
            '社交吃饭': 'Operating Activities',
            '办公支出': 'Operating Activities',
            # Investment categories
            '投资收益': 'Investing Activities',
            '投资支出': 'Investing Activities',
            '设备购置': 'Investing Activities',
            # Financing categories
            '贷款收入': 'Financing Activities',
            '还贷支出': 'Financing Activities',
            '股东投资': 'Financing Activities',
            '分红支出': 'Financing Activities'
        }
    
    def get_expense_category(self, category: str) -> str:
        return self.expense_categories.get(category, 'Other Expenses')
    
    def get_cashflow_category(self, category: str) -> str:
        return self.cashflow_categories.get(category, 'Operating Activities')


# Revenue categories
REVENUE_CATEGORIES = ['工资收入', '服务收入', '投资收益', '其他收入', 'Service Revenue', 'Investment Income', 'Other Income']

def get_all_categories() -> List[str]:
    """Get flattened list of all valid categories"""
    mapper = CategoryMapper()
    all_categories = list(mapper.expense_categories.keys())
    all_categories.extend(REVENUE_CATEGORIES)
    return all_categories