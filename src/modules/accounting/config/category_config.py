"""
Category configuration loader for accounting system

Loads category mappings from JSON configuration files and provides
a clean interface for accessing category mappings.
"""

import json
import os
from typing import Dict, List, Any
from pathlib import Path


class CategoryConfigLoader:
    """Loads and manages category configuration from JSON files"""
    
    def __init__(self, config_file_path: str = None):
        """
        Initialize the category config loader
        
        Args:
            config_file_path: Path to the category mappings JSON file.
                             If None, uses default path.
        """
        if config_file_path is None:
            # Default to the config file in the same directory
            current_dir = Path(__file__).parent
            config_file_path = current_dir / "category_mappings.json"
        
        self.config_file_path = config_file_path
        self._config_data = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                self._config_data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Category configuration file not found: {self.config_file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in category configuration file: {e}")
    
    def get_expense_categories(self) -> Dict[str, str]:
        """
        Get all expense category mappings as a flat dictionary
        
        Returns:
            Dictionary mapping input categories to standardized categories
        """
        if not self._config_data:
            return {}
        
        expense_categories = {}
        expense_config = self._config_data.get("expense_categories", {})
        
        # Flatten all expense category groups into a single dictionary
        for group_name, group_mappings in expense_config.items():
            if isinstance(group_mappings, dict):
                expense_categories.update(group_mappings)
        
        return expense_categories
    
    def get_cashflow_categories(self) -> Dict[str, str]:
        """
        Get all cash flow category mappings as a flat dictionary
        
        Returns:
            Dictionary mapping input categories to cash flow activities
        """
        if not self._config_data:
            return {}
        
        cashflow_categories = {}
        cashflow_config = self._config_data.get("cashflow_categories", {})
        
        # Flatten all cash flow category groups into a single dictionary
        for group_name, group_mappings in cashflow_config.items():
            if isinstance(group_mappings, dict):
                cashflow_categories.update(group_mappings)
        
        return cashflow_categories
    
    def get_revenue_categories(self) -> List[str]:
        """
        Get all revenue categories as a flat list
        
        Returns:
            List of all valid revenue categories
        """
        if not self._config_data:
            return []
        
        revenue_categories = []
        revenue_config = self._config_data.get("revenue_categories", {})
        
        # Combine all revenue category groups into a single list
        for group_name, group_categories in revenue_config.items():
            if isinstance(group_categories, list):
                revenue_categories.extend(group_categories)
        
        return revenue_categories
    
    def get_category_groups(self) -> Dict[str, Any]:
        """
        Get the raw category configuration grouped by type
        
        Returns:
            Dictionary containing the full configuration structure
        """
        return self._config_data or {}
    
    def reload_config(self):
        """Reload configuration from file (useful for development)"""
        self._load_config()
    
    def validate_config(self) -> List[str]:
        """
        Validate the configuration for common issues
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not self._config_data:
            errors.append("No configuration data loaded")
            return errors
        
        # Check required sections
        required_sections = ["expense_categories", "cashflow_categories", "revenue_categories"]
        for section in required_sections:
            if section not in self._config_data:
                errors.append(f"Missing required section: {section}")
        
        # Check for empty mappings
        expense_cats = self.get_expense_categories()
        if not expense_cats:
            errors.append("No expense categories found in configuration")
        
        cashflow_cats = self.get_cashflow_categories()
        if not cashflow_cats:
            errors.append("No cash flow categories found in configuration")
        
        revenue_cats = self.get_revenue_categories()
        if not revenue_cats:
            errors.append("No revenue categories found in configuration")
        
        return errors


# Global configuration loader instance
_config_loader = None


def get_category_config() -> CategoryConfigLoader:
    """
    Get the global category configuration loader instance
    
    Returns:
        CategoryConfigLoader instance
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = CategoryConfigLoader()
    return _config_loader


def reload_category_config():
    """Reload the global category configuration"""
    global _config_loader
    if _config_loader is not None:
        _config_loader.reload_config()
