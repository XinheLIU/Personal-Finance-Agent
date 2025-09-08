"""
Category Translation Module for Accounting System
Handles Chinese-English category mapping and data translation
"""

from typing import Dict, List, Optional, Set
import logging

logger = logging.getLogger(__name__)


class CategoryTranslator:
    """
    Translates between Chinese and English accounting categories.
    Ensures consistent category mapping for bilingual data processing.
    """
    
    # Standard Chinese to English category mapping
    CATEGORY_MAPPING = {
        # Essential/Fixed Expenses - 刚性消费
        "房租": "Rent",
        "水电": "Utilities",
        "通勤": "Transportation",
        
        # Food & Living - 生活支出  
        "餐饮": "Food & Dining",
        "日用购物": "General Shopping",
        
        # Flexible Expenses - 弹性消费
        "运动和健康": "Health & Wellness", 
        "宠物": "Pet Expenses",
        "小孩支出": "Personal Expenses",
        "个人消费": "Personal Expenses",
        "旅行/孩子支出": "Travel & Entertainment",
        "人情/应酬支出": "Travel & Entertainment",
        
        # Aggregated Categories
        "刚性消费": "Essential Expenses",
        "弹性消费": "Flexible Expenses",
        
        # Revenue Categories
        "工资收入": "Service Revenue",
        "服务收入": "Service Revenue",
        "其他收入": "Other Revenue"
    }
    
    # Reverse mapping for English to Chinese
    REVERSE_MAPPING = {v: k for k, v in CATEGORY_MAPPING.items() if v not in ["Personal Expenses", "Travel & Entertainment", "Service Revenue"]}
    
    # Handle multiple Chinese categories mapping to same English category
    REVERSE_MAPPING.update({
        "Personal Expenses": "个人消费",  # Default choice
        "Travel & Entertainment": "旅行/孩子支出",  # Default choice
        "Service Revenue": "工资收入"  # Default choice
    })
    
    # Standard English categories used in income statements
    STANDARD_EXPENSE_CATEGORIES = {
        "Rent", "Utilities", "Transportation", "Food & Dining", 
        "General Shopping", "Health & Wellness", "Pet Expenses",
        "Personal Expenses", "Travel & Entertainment", "Other Expenses",
        "Essential Expenses", "Flexible Expenses"
    }
    
    STANDARD_REVENUE_CATEGORIES = {
        "Service Revenue", "Other Revenue"
    }
    
    def __init__(self):
        """Initialize the category translator with validation."""
        self._validate_mappings()
        logger.info("CategoryTranslator initialized with %d category mappings", 
                   len(self.CATEGORY_MAPPING))
    
    def translate_to_english(self, chinese_category: str) -> str:
        """
        Translate Chinese category to English standard category.
        
        Args:
            chinese_category: Chinese category name
            
        Returns:
            English category name, or original if no mapping found
        """
        if not chinese_category:
            return ""
            
        # Direct mapping
        if chinese_category in self.CATEGORY_MAPPING:
            return self.CATEGORY_MAPPING[chinese_category]
        
        # If already in English, validate and return
        if chinese_category in self.STANDARD_EXPENSE_CATEGORIES or \
           chinese_category in self.STANDARD_REVENUE_CATEGORIES:
            return chinese_category
        
        # Log unmapped category for future enhancement
        logger.warning(f"Unknown Chinese category: {chinese_category}")
        return chinese_category
    
    def translate_to_chinese(self, english_category: str) -> str:
        """
        Translate English category to Chinese category.
        
        Args:
            english_category: English category name
            
        Returns:
            Chinese category name, or original if no mapping found
        """
        if not english_category:
            return ""
            
        # Direct reverse mapping
        if english_category in self.REVERSE_MAPPING:
            return self.REVERSE_MAPPING[english_category]
        
        # If already in Chinese, return as-is
        if english_category in self.CATEGORY_MAPPING:
            return english_category
        
        # Log unmapped category
        logger.warning(f"Unknown English category: {english_category}")
        return english_category
    
    def translate_category_dict(self, category_dict: Dict[str, float], 
                              to_language: str = "english") -> Dict[str, float]:
        """
        Translate all keys in a category dictionary.
        
        Args:
            category_dict: Dictionary with category keys and numeric values
            to_language: Target language ("english" or "chinese")
            
        Returns:
            Dictionary with translated category keys
        """
        if not category_dict:
            return {}
        
        translated = {}
        translate_func = (self.translate_to_english if to_language.lower() == "english" 
                         else self.translate_to_chinese)
        
        for category, value in category_dict.items():
            translated_category = translate_func(category)
            
            # Aggregate values if multiple Chinese categories map to same English
            if translated_category in translated:
                translated[translated_category] += value
            else:
                translated[translated_category] = value
        
        return translated
    
    def get_category_suggestions(self, partial_category: str, 
                               language: str = "chinese") -> List[str]:
        """
        Get category suggestions for partial input.
        
        Args:
            partial_category: Partial category name
            language: Source language ("chinese" or "english")
            
        Returns:
            List of matching categories
        """
        partial_lower = partial_category.lower()
        
        if language.lower() == "chinese":
            candidates = self.CATEGORY_MAPPING.keys()
        else:
            candidates = list(self.STANDARD_EXPENSE_CATEGORIES) + \
                        list(self.STANDARD_REVENUE_CATEGORIES)
        
        # Simple substring matching
        suggestions = [cat for cat in candidates 
                      if partial_lower in cat.lower()]
        
        return sorted(suggestions)
    
    def validate_category(self, category: str, 
                         language: str = "auto") -> Dict[str, any]:
        """
        Validate category and provide translation info.
        
        Args:
            category: Category to validate
            language: Expected language ("chinese", "english", "auto")
            
        Returns:
            Validation result with translation info
        """
        result = {
            "category": category,
            "is_valid": False,
            "detected_language": None,
            "english_translation": None,
            "chinese_translation": None,
            "suggestions": []
        }
        
        if not category:
            return result
        
        # Detect language and validate
        is_chinese = category in self.CATEGORY_MAPPING
        is_english = (category in self.STANDARD_EXPENSE_CATEGORIES or 
                     category in self.STANDARD_REVENUE_CATEGORIES)
        
        if is_chinese:
            result["detected_language"] = "chinese"
            result["is_valid"] = True
            result["english_translation"] = self.translate_to_english(category)
            result["chinese_translation"] = category
        elif is_english:
            result["detected_language"] = "english"
            result["is_valid"] = True
            result["english_translation"] = category
            result["chinese_translation"] = self.translate_to_chinese(category)
        else:
            # Provide suggestions for invalid categories
            chinese_suggestions = self.get_category_suggestions(category, "chinese")
            english_suggestions = self.get_category_suggestions(category, "english")
            result["suggestions"] = chinese_suggestions + english_suggestions
        
        return result
    
    def get_standard_categories(self, category_type: str = "all") -> Dict[str, Set[str]]:
        """
        Get standard categories by type.
        
        Args:
            category_type: "expense", "revenue", or "all"
            
        Returns:
            Dictionary with Chinese and English category sets
        """
        categories = {"chinese": set(), "english": set()}
        
        if category_type.lower() in ["expense", "all"]:
            # Add expense categories
            expense_chinese = {k for k, v in self.CATEGORY_MAPPING.items() 
                             if v in self.STANDARD_EXPENSE_CATEGORIES}
            categories["chinese"].update(expense_chinese)
            categories["english"].update(self.STANDARD_EXPENSE_CATEGORIES)
        
        if category_type.lower() in ["revenue", "all"]:
            # Add revenue categories
            revenue_chinese = {k for k, v in self.CATEGORY_MAPPING.items() 
                             if v in self.STANDARD_REVENUE_CATEGORIES}
            categories["chinese"].update(revenue_chinese)
            categories["english"].update(self.STANDARD_REVENUE_CATEGORIES)
        
        return categories
    
    def _validate_mappings(self):
        """Validate internal category mappings for consistency."""
        # Check for duplicate English categories (except known multi-mappings)
        english_counts = {}
        for chinese, english in self.CATEGORY_MAPPING.items():
            english_counts[english] = english_counts.get(english, 0) + 1
        
        multi_mapped = [cat for cat, count in english_counts.items() if count > 1]
        expected_multi = {"Personal Expenses", "Travel & Entertainment", "Service Revenue"}
        
        unexpected_multi = set(multi_mapped) - expected_multi
        if unexpected_multi:
            logger.warning(f"Unexpected multi-mapped categories: {unexpected_multi}")
        
        # Validate reverse mapping completeness
        missing_reverse = set(self.CATEGORY_MAPPING.values()) - set(self.REVERSE_MAPPING.keys())
        if missing_reverse:
            logger.warning(f"Missing reverse mappings: {missing_reverse}")
        
        logger.info("Category mapping validation completed")