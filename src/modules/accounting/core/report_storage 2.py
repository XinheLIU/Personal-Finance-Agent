"""
Report Storage Manager for Monthly Accounting Statements

Handles persistent storage of generated financial statements (income, cash flow, balance sheet)
with singleton pattern per month and refresh capability.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from decimal import Decimal

from .data_storage_utils import validate_month_format, get_monthly_data_path

# Configure logging
logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal objects"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


class MonthlyReportStorage:
    """
    Manages monthly storage of generated financial statements.
    Supports income statement, cash flow statement, and balance sheet.
    """
    
    STATEMENT_TYPES = ["income_statement", "cash_flow", "balance_sheet"]
    
    def __init__(self, base_path: str = "data/accounting/monthly_reports"):
        """
        Initialize monthly report storage manager.
        
        Args:
            base_path: Base directory for monthly reports storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    def save_statement(
        self, 
        year_month: str,
        statement_type: str,
        statement_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save a financial statement for a specific month.
        
        Args:
            year_month: Month in YYYY-MM format
            statement_type: Type of statement (income_statement, cash_flow, balance_sheet)
            statement_data: Statement data dictionary
            metadata: Optional metadata (generation params, etc.)
            
        Returns:
            True if save successful
        """
        if not validate_month_format(year_month):
            raise ValueError(f"Invalid month format: {year_month}. Use YYYY-MM")
            
        if statement_type not in self.STATEMENT_TYPES:
            raise ValueError(f"Invalid statement type: {statement_type}. Must be one of {self.STATEMENT_TYPES}")
        
        try:
            monthly_path = get_monthly_data_path(self.base_path, year_month)
            monthly_path.mkdir(parents=True, exist_ok=True)
            
            # Prepare statement with metadata
            statement_with_meta = {
                "year_month": year_month,
                "statement_type": statement_type,
                "generated_at": datetime.now().isoformat(),
                "data": statement_data,
                "metadata": metadata or {}
            }
            
            # Save as JSON file
            statement_path = monthly_path / f"{statement_type}.json"
            with open(statement_path, 'w', encoding='utf-8') as f:
                json.dump(statement_with_meta, f, cls=DecimalEncoder, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {statement_type} for {year_month}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save {statement_type} for {year_month}: {e}")
            return False
    
    def load_statement(
        self, 
        year_month: str, 
        statement_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Load a financial statement for a specific month.
        
        Args:
            year_month: Month in YYYY-MM format
            statement_type: Type of statement
            
        Returns:
            Statement data dictionary or None if not found
        """
        if not validate_month_format(year_month):
            raise ValueError(f"Invalid month format: {year_month}. Use YYYY-MM")
            
        if statement_type not in self.STATEMENT_TYPES:
            raise ValueError(f"Invalid statement type: {statement_type}")
        
        monthly_path = get_monthly_data_path(self.base_path, year_month)
        statement_path = monthly_path / f"{statement_type}.json"
        
        if not statement_path.exists():
            return None
        
        try:
            with open(statement_path, 'r', encoding='utf-8') as f:
                statement_data = json.load(f)
            
            logger.info(f"Loaded {statement_type} for {year_month}")
            return statement_data
            
        except Exception as e:
            logger.error(f"Failed to load {statement_type} for {year_month}: {e}")
            return None
    
    def list_available_statements(self, statement_type: Optional[str] = None) -> Dict[str, List[str]]:
        """
        List all available statements by month.
        
        Args:
            statement_type: Filter by statement type (optional)
            
        Returns:
            Dictionary mapping months to available statement types
        """
        available = {}
        
        if not self.base_path.exists():
            return available
        
        for month_dir in self.base_path.iterdir():
            if month_dir.is_dir() and validate_month_format(month_dir.name):
                month_statements = []
                
                for stmt_type in self.STATEMENT_TYPES:
                    if statement_type is None or stmt_type == statement_type:
                        statement_path = month_dir / f"{stmt_type}.json"
                        if statement_path.exists():
                            month_statements.append(stmt_type)
                
                if month_statements:
                    available[month_dir.name] = month_statements
        
        return available
    
    def get_statement_info(self, year_month: str, statement_type: str) -> Dict[str, Any]:
        """
        Get information about a stored statement.
        
        Args:
            year_month: Month in YYYY-MM format
            statement_type: Type of statement
            
        Returns:
            Dictionary with statement information
        """
        if not validate_month_format(year_month):
            raise ValueError(f"Invalid month format: {year_month}")
            
        monthly_path = get_monthly_data_path(self.base_path, year_month)
        statement_path = monthly_path / f"{statement_type}.json"
        
        info = {
            "year_month": year_month,
            "statement_type": statement_type,
            "exists": statement_path.exists(),
            "path": str(statement_path),
            "size_bytes": 0,
            "last_modified": None,
            "generated_at": None
        }
        
        if statement_path.exists():
            info["size_bytes"] = statement_path.stat().st_size
            info["last_modified"] = datetime.fromtimestamp(
                statement_path.stat().st_mtime
            ).isoformat()
            
            # Try to get generation time from file content
            try:
                with open(statement_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    info["generated_at"] = data.get("generated_at")
            except Exception as e:
                logger.warning(f"Could not read generation time for {statement_path}: {e}")
        
        return info
    
    def delete_statement(
        self, 
        year_month: str, 
        statement_type: Optional[str] = None
    ) -> bool:
        """
        Delete statements for a specific month.
        
        Args:
            year_month: Month in YYYY-MM format
            statement_type: Type of statement, or None for all types
            
        Returns:
            True if deletion successful
        """
        if not validate_month_format(year_month):
            raise ValueError(f"Invalid month format: {year_month}")
            
        monthly_path = get_monthly_data_path(self.base_path, year_month)
        
        if not monthly_path.exists():
            logger.warning(f"No reports found for {year_month}")
            return True
        
        try:
            if statement_type is None:
                # Delete all statements for the month
                for stmt_type in self.STATEMENT_TYPES:
                    statement_path = monthly_path / f"{stmt_type}.json"
                    if statement_path.exists():
                        statement_path.unlink()
                        logger.info(f"Deleted {stmt_type} for {year_month}")
                
                # Remove directory if empty
                if not any(monthly_path.iterdir()):
                    monthly_path.rmdir()
                    logger.info(f"Removed empty directory for {year_month}")
            else:
                # Delete specific statement type
                if statement_type not in self.STATEMENT_TYPES:
                    raise ValueError(f"Invalid statement type: {statement_type}")
                    
                statement_path = monthly_path / f"{statement_type}.json"
                if statement_path.exists():
                    statement_path.unlink()
                    logger.info(f"Deleted {statement_type} for {year_month}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete statements for {year_month}: {e}")
            return False
    
    def refresh_statement(
        self, 
        year_month: str, 
        statement_type: str,
        statement_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Refresh (overwrite) an existing statement.
        
        Args:
            year_month: Month in YYYY-MM format
            statement_type: Type of statement
            statement_data: New statement data
            metadata: Optional metadata
            
        Returns:
            True if refresh successful
        """
        # This is the same as save_statement (overwrites by design)
        return self.save_statement(year_month, statement_type, statement_data, metadata)
    
    def export_statements_to_csv(
        self, 
        year_month: str, 
        output_path: Optional[Path] = None
    ) -> Dict[str, str]:
        """
        Export all statements for a month to CSV files.
        
        Args:
            year_month: Month in YYYY-MM format
            output_path: Output directory path (default: monthly reports path)
            
        Returns:
            Dictionary mapping statement types to output file paths
        """
        if not validate_month_format(year_month):
            raise ValueError(f"Invalid month format: {year_month}")
        
        if output_path is None:
            output_path = get_monthly_data_path(self.base_path, year_month)
        else:
            output_path = Path(output_path)
            
        output_path.mkdir(parents=True, exist_ok=True)
        
        exported_files = {}
        
        for statement_type in self.STATEMENT_TYPES:
            statement_data = self.load_statement(year_month, statement_type)
            
            if statement_data is None:
                continue
                
            try:
                # Extract the main data from the statement
                data = statement_data.get("data", {})
                
                # Convert to DataFrame based on statement structure
                if statement_type == "income_statement":
                    df = self._income_statement_to_df(data)
                elif statement_type == "cash_flow":
                    df = self._cash_flow_to_df(data)
                elif statement_type == "balance_sheet":
                    df = self._balance_sheet_to_df(data)
                else:
                    # Generic conversion
                    df = pd.json_normalize(data)
                
                # Export to CSV
                csv_path = output_path / f"{year_month}_{statement_type}.csv"
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                
                exported_files[statement_type] = str(csv_path)
                logger.info(f"Exported {statement_type} to {csv_path}")
                
            except Exception as e:
                logger.error(f"Failed to export {statement_type} for {year_month}: {e}")
        
        return exported_files

    def load_monthly_statements(self, year_month: str) -> Dict[str, Any]:
        """Load all available statements for a month with normalized keys.

        Returns a dict with keys: 'income_statement', 'balance_sheet',
        and 'cash_flow_statement' when present.
        """
        if not validate_month_format(year_month):
            raise ValueError(f"Invalid month format: {year_month}")

        results: Dict[str, Any] = {}
        for stmt_type in self.STATEMENT_TYPES:
            data = self.load_statement(year_month, stmt_type)
            if data is None:
                continue
            # Normalize naming for UI consistency
            if stmt_type == "cash_flow":
                results["cash_flow_statement"] = data
            else:
                results[stmt_type] = data

        return results
    
    def _income_statement_to_df(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Convert income statement data to DataFrame"""
        rows = []
        
        # Add revenue section
        if "revenue" in data:
            for item, amount in data["revenue"].items():
                rows.append({"Category": "Revenue", "Item": item, "Amount": amount})
        
        # Add expense sections
        for section_name, section_data in data.items():
            if section_name != "revenue" and isinstance(section_data, dict):
                for item, amount in section_data.items():
                    rows.append({"Category": section_name.title(), "Item": item, "Amount": amount})
        
        return pd.DataFrame(rows)
    
    def _cash_flow_to_df(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Convert cash flow statement data to DataFrame"""
        rows = []
        
        for section_name, section_data in data.items():
            if isinstance(section_data, dict):
                for item, amount in section_data.items():
                    rows.append({"Section": section_name.title(), "Item": item, "Amount": amount})
        
        return pd.DataFrame(rows)
    
    def _balance_sheet_to_df(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Convert balance sheet data to DataFrame"""
        rows = []
        
        for section_name, section_data in data.items():
            if isinstance(section_data, dict):
                for item, amount in section_data.items():
                    rows.append({"Section": section_name.title(), "Item": item, "Amount": amount})
        
        return pd.DataFrame(rows)