"""
Category domain entities

Defines category mappings and constants for financial statement categorization.
Uses configuration files for maintainable category management.
"""

from typing import Dict, List
from ...config import get_category_config


class CategoryMapper:
    """Maps transaction categories to financial statement categories"""
    
    def __init__(self, config_loader=None):
        """
        Initialize CategoryMapper with category configuration
        
        Args:
            config_loader: Optional CategoryConfigLoader instance.
                          If None, uses the global configuration loader.
        """
        if config_loader is None:
            config_loader = get_category_config()
        
        self.config_loader = config_loader
        
        # Load category mappings from configuration
        self.expense_categories = self.config_loader.get_expense_categories()
        self.cashflow_categories = self.config_loader.get_cashflow_categories()
    
    def get_expense_category(self, category: str) -> str:
        return self.expense_categories.get(category, 'Other Expenses')
    
    def get_cashflow_category(self, category: str) -> str:
        return self.cashflow_categories.get(category, 'Operating Activities')


def get_revenue_categories() -> List[str]:
    """Get revenue categories from configuration"""
    config_loader = get_category_config()
    return config_loader.get_revenue_categories()


# For backward compatibility, create REVENUE_CATEGORIES as a property
def _get_revenue_categories():
    """Get revenue categories (cached for performance)"""
    if not hasattr(_get_revenue_categories, '_cache'):
        _get_revenue_categories._cache = get_revenue_categories()
    return _get_revenue_categories._cache


# Backward compatibility - REVENUE_CATEGORIES as a list
REVENUE_CATEGORIES = _get_revenue_categories()


def get_all_categories() -> List[str]:
    """Get flattened list of all valid categories"""
    mapper = CategoryMapper()
    all_categories = list(mapper.expense_categories.keys())
    all_categories.extend(get_revenue_categories())
    return all_categories