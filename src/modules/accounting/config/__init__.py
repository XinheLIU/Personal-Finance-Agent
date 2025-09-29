"""
Configuration module for accounting system

Provides configuration loading and management for category mappings,
system settings, and other configurable aspects of the accounting system.
"""

from .category_config import CategoryConfigLoader, get_category_config, reload_category_config

__all__ = [
    'CategoryConfigLoader',
    'get_category_config', 
    'reload_category_config'
]
