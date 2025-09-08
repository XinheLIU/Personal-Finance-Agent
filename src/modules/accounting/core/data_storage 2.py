"""
Monthly Data Storage Manager for Accounting Module

Handles persistent storage of monthly transaction and asset data using parquet format.
Implements singleton pattern per month - new uploads overwrite existing monthly data.
"""

import os
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
from decimal import Decimal

from .models import Transaction
from .data_storage_utils import (
    validate_month_format, 
    get_monthly_data_path,
    validate_transactions_data,
    validate_assets_data,
    convert_decimal_columns,
    clean_transactions_for_storage,
    clean_assets_for_storage
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MonthlyDataStorage:
    """
    Manages monthly storage of accounting data in parquet format.
    Implements singleton pattern per month for data consistency.
    """
    
    def __init__(self, base_path: str = "data/accounting/monthly_data"):
        """
        Initialize monthly data storage manager.
        
        Args:
            base_path: Base directory for monthly data storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    def save_monthly_data(
        self, 
        year_month: str, 
        transactions_df: Optional[pd.DataFrame] = None,
        assets_df: Optional[pd.DataFrame] = None,
        overwrite: bool = True
    ) -> Dict[str, bool]:
        """
        Save monthly transactions and assets data to parquet files.
        
        Args:
            year_month: Month in YYYY-MM format
            transactions_df: DataFrame with transaction data
            assets_df: DataFrame with asset data  
            overwrite: Whether to overwrite existing data
            
        Returns:
            Dict with success status for each data type
        """
        if not validate_month_format(year_month):
            raise ValueError(f"Invalid month format: {year_month}. Use YYYY-MM")
            
        results = {"transactions": False, "assets": False}
        monthly_path = get_monthly_data_path(self.base_path, year_month)
        
        # Create monthly directory
        monthly_path.mkdir(parents=True, exist_ok=True)
        
        # Save transactions data
        if transactions_df is not None:
            try:
                # Clean transactions data first (handles problematic amounts, etc.)
                transactions_df_cleaned = clean_transactions_for_storage(transactions_df)
                
                # Validate cleaned transactions data
                validation_errors = validate_transactions_data(transactions_df_cleaned)
                if validation_errors:
                    logger.error(f"Transaction validation errors: {validation_errors}")
                    raise ValueError(f"Transaction validation failed: {validation_errors}")
                
                # Convert decimal columns for parquet compatibility
                transactions_clean = convert_decimal_columns(transactions_df_cleaned)
                
                transactions_path = monthly_path / "transactions.parquet"
                
                # Check if file exists and overwrite policy
                if transactions_path.exists() and not overwrite:
                    logger.warning(f"Transactions file exists for {year_month}, skipping")
                else:
                    transactions_clean.to_parquet(transactions_path, index=False)
                    logger.info(f"Saved transactions data for {year_month}")
                    results["transactions"] = True
                    
            except Exception as e:
                logger.error(f"Failed to save transactions for {year_month}: {e}")
                raise
        
        # Save assets data
        if assets_df is not None:
            try:
                # Clean assets data first (handles problematic amounts, etc.)
                assets_df_cleaned = clean_assets_for_storage(assets_df)
                
                # Validate cleaned assets data
                validation_errors = validate_assets_data(assets_df_cleaned)
                if validation_errors:
                    logger.error(f"Asset validation errors: {validation_errors}")
                    raise ValueError(f"Asset validation failed: {validation_errors}")
                
                # Convert decimal columns for parquet compatibility
                assets_clean = convert_decimal_columns(assets_df_cleaned)
                
                assets_path = monthly_path / "assets.parquet"
                
                # Check if file exists and overwrite policy
                if assets_path.exists() and not overwrite:
                    logger.warning(f"Assets file exists for {year_month}, skipping")
                else:
                    assets_clean.to_parquet(assets_path, index=False)
                    logger.info(f"Saved assets data for {year_month}")
                    results["assets"] = True
                    
            except Exception as e:
                logger.error(f"Failed to save assets for {year_month}: {e}")
                raise
        
        return results
    
    def load_monthly_data(self, year_month: str) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """
        Load monthly transactions and assets data from parquet files.
        
        Args:
            year_month: Month in YYYY-MM format
            
        Returns:
            Tuple of (transactions_df, assets_df), None if file doesn't exist
        """
        if not validate_month_format(year_month):
            raise ValueError(f"Invalid month format: {year_month}. Use YYYY-MM")
            
        monthly_path = get_monthly_data_path(self.base_path, year_month)
        
        transactions_df = None
        assets_df = None
        
        # Load transactions
        transactions_path = monthly_path / "transactions.parquet"
        if transactions_path.exists():
            try:
                transactions_df = pd.read_parquet(transactions_path)
                logger.info(f"Loaded transactions data for {year_month}")
            except Exception as e:
                logger.error(f"Failed to load transactions for {year_month}: {e}")
        
        # Load assets
        assets_path = monthly_path / "assets.parquet"
        if assets_path.exists():
            try:
                assets_df = pd.read_parquet(assets_path)
                logger.info(f"Loaded assets data for {year_month}")
            except Exception as e:
                logger.error(f"Failed to load assets for {year_month}: {e}")
        
        return transactions_df, assets_df
    
    def list_available_months(self) -> List[str]:
        """
        List all available months with stored data.
        
        Returns:
            Sorted list of year-month strings in YYYY-MM format
        """
        available_months = []
        
        if not self.base_path.exists():
            return available_months
            
        for month_dir in self.base_path.iterdir():
            if month_dir.is_dir() and validate_month_format(month_dir.name):
                # Check if contains any data files
                if (month_dir / "transactions.parquet").exists() or (month_dir / "assets.parquet").exists():
                    available_months.append(month_dir.name)
        
        return sorted(available_months)
    
    def get_monthly_data_info(self, year_month: str) -> Dict[str, any]:
        """
        Get information about stored monthly data.
        
        Args:
            year_month: Month in YYYY-MM format
            
        Returns:
            Dictionary with data information
        """
        if not validate_month_format(year_month):
            raise ValueError(f"Invalid month format: {year_month}. Use YYYY-MM")
            
        monthly_path = get_monthly_data_path(self.base_path, year_month)
        info = {
            "year_month": year_month,
            "path": str(monthly_path),
            "exists": monthly_path.exists(),
            "transactions": {
                "exists": False,
                "records": 0,
                "size_bytes": 0,
                "last_modified": None
            },
            "assets": {
                "exists": False,
                "records": 0,
                "size_bytes": 0,
                "last_modified": None
            }
        }
        
        if not monthly_path.exists():
            return info
        
        # Check transactions file
        transactions_path = monthly_path / "transactions.parquet"
        if transactions_path.exists():
            info["transactions"]["exists"] = True
            info["transactions"]["size_bytes"] = transactions_path.stat().st_size
            info["transactions"]["last_modified"] = datetime.fromtimestamp(
                transactions_path.stat().st_mtime
            ).isoformat()
            
            try:
                df = pd.read_parquet(transactions_path)
                info["transactions"]["records"] = len(df)
            except Exception as e:
                logger.error(f"Error reading transactions file: {e}")
        
        # Check assets file
        assets_path = monthly_path / "assets.parquet"
        if assets_path.exists():
            info["assets"]["exists"] = True
            info["assets"]["size_bytes"] = assets_path.stat().st_size
            info["assets"]["last_modified"] = datetime.fromtimestamp(
                assets_path.stat().st_mtime
            ).isoformat()
            
            try:
                df = pd.read_parquet(assets_path)
                info["assets"]["records"] = len(df)
            except Exception as e:
                logger.error(f"Error reading assets file: {e}")
        
        return info
    
    def delete_monthly_data(self, year_month: str, data_type: Optional[str] = None) -> bool:
        """
        Delete monthly data for specified month and type.
        
        Args:
            year_month: Month in YYYY-MM format
            data_type: 'transactions', 'assets', or None for both
            
        Returns:
            True if deletion successful
        """
        if not validate_month_format(year_month):
            raise ValueError(f"Invalid month format: {year_month}. Use YYYY-MM")
            
        monthly_path = get_monthly_data_path(self.base_path, year_month)
        
        if not monthly_path.exists():
            logger.warning(f"No data found for {year_month}")
            return True
        
        try:
            if data_type is None:
                # Delete entire month directory
                import shutil
                shutil.rmtree(monthly_path)
                logger.info(f"Deleted all data for {year_month}")
            elif data_type == "transactions":
                transactions_path = monthly_path / "transactions.parquet"
                if transactions_path.exists():
                    transactions_path.unlink()
                    logger.info(f"Deleted transactions data for {year_month}")
            elif data_type == "assets":
                assets_path = monthly_path / "assets.parquet"
                if assets_path.exists():
                    assets_path.unlink()
                    logger.info(f"Deleted assets data for {year_month}")
            else:
                raise ValueError(f"Invalid data_type: {data_type}")
                
            return True
        except Exception as e:
            logger.error(f"Failed to delete data for {year_month}: {e}")
            return False