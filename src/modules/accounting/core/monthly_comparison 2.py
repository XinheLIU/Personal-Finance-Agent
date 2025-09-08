"""
Monthly Comparison Engine for Accounting Statements

Provides 12-month rolling comparison of stored financial statements
with trend analysis, percentage changes, and data aggregation.
"""

import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from decimal import Decimal
import logging

from .report_storage import MonthlyReportStorage
from .data_storage_utils import get_recent_months, validate_month_format

# Configure logging
logger = logging.getLogger(__name__)


class MonthlyComparisonEngine:
    """
    Engine for comparing financial statements across multiple months.
    Provides trend analysis and aggregated comparisons.
    """
    
    def __init__(self, report_storage: Optional[MonthlyReportStorage] = None):
        """
        Initialize monthly comparison engine.
        
        Args:
            report_storage: Report storage instance (creates new if None)
        """
        self.report_storage = report_storage or MonthlyReportStorage()
    
    def get_comparison_data(
        self, 
        statement_type: str, 
        months: Optional[List[str]] = None,
        count: int = 12
    ) -> Dict[str, Any]:
        """
        Get comparison data using income statement schema format.
        
        Args:
            statement_type: Type of statement (income_statement, cash_flow, balance_sheet)
            months: List of months to compare (default: last 12 months)
            count: Number of recent months if months not specified
            
        Returns:
            Dictionary with comparison data in income statement format
        """
        if months is None:
            # Prefer actual available months for this statement type
            available_map = self.report_storage.list_available_statements(statement_type)
            if available_map:
                months_available = sorted(available_map.keys())
                months = months_available[-count:]
            else:
                # Fallback to recent months if storage is empty
                months = get_recent_months(count)
        
        # Validate months
        for month in months:
            if not validate_month_format(month):
                raise ValueError(f"Invalid month format: {month}")
        
        comparison_data = {
            "comparison_type": "monthly_comparison",
            "statement_type": statement_type,
            "months": months,
            "data": {},  # Will contain month -> income_statement_format data
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_months": len(months),
                "available_months": [],
                "missing_months": []
            }
        }
        
        # Load data for each month and convert to standard format
        for month in months:
            statement_data = self.report_storage.load_statement(month, statement_type)
            
            if statement_data is not None:
                # Extract the actual statement data (matches income statement format)
                month_statement = statement_data.get("data", {})
                
                # Ensure standard income statement schema structure
                standardized_data = self._standardize_to_income_statement_format(month_statement, month)
                comparison_data["data"][month] = standardized_data
                comparison_data["metadata"]["available_months"].append(month)
            else:
                comparison_data["metadata"]["missing_months"].append(month)
        
        logger.info(f"Loaded {statement_type} data for {len(comparison_data['metadata']['available_months'])} months")
        return comparison_data
    
    def calculate_monthly_trends(
        self, 
        comparison_data: Dict[str, Any],
        metric_path: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Calculate month-over-month trends for comparison data.
        
        Args:
            comparison_data: Data from get_comparison_data()
            metric_path: Path to specific metric (e.g., ['revenue', 'total'])
            
        Returns:
            Dictionary with trend analysis
        """
        months = comparison_data["months"]
        available_data = comparison_data["data"]
        
        trend_analysis = {
            "statement_type": comparison_data["statement_type"],
            "metric_path": metric_path,
            "trends": {},
            "summary": {
                "total_periods": 0,
                "growth_periods": 0,
                "decline_periods": 0,
                "flat_periods": 0,
                "average_change_pct": 0.0,
                "max_growth_pct": 0.0,
                "max_decline_pct": 0.0
            }
        }
        
        # Sort months chronologically
        sorted_months = sorted([m for m in months if m in available_data])
        
        if len(sorted_months) < 2:
            logger.warning("Need at least 2 months of data for trend analysis")
            return trend_analysis
        
        changes = []
        
        for i in range(1, len(sorted_months)):
            prev_month = sorted_months[i-1]
            curr_month = sorted_months[i]
            
            prev_value = self._extract_metric_value(available_data[prev_month], metric_path)
            curr_value = self._extract_metric_value(available_data[curr_month], metric_path)
            
            if prev_value is not None and curr_value is not None:
                if prev_value != 0:
                    change_pct = ((curr_value - prev_value) / abs(prev_value)) * 100
                else:
                    change_pct = 100.0 if curr_value > 0 else -100.0 if curr_value < 0 else 0.0
                
                trend_analysis["trends"][curr_month] = {
                    "previous_month": prev_month,
                    "previous_value": float(prev_value),
                    "current_value": float(curr_value),
                    "absolute_change": float(curr_value - prev_value),
                    "percentage_change": round(change_pct, 2),
                    "trend_direction": "growth" if change_pct > 0 else "decline" if change_pct < 0 else "flat"
                }
                
                changes.append(change_pct)
        
        # Calculate summary statistics
        if changes:
            trend_analysis["summary"]["total_periods"] = len(changes)
            trend_analysis["summary"]["growth_periods"] = len([c for c in changes if c > 0])
            trend_analysis["summary"]["decline_periods"] = len([c for c in changes if c < 0])
            trend_analysis["summary"]["flat_periods"] = len([c for c in changes if c == 0])
            trend_analysis["summary"]["average_change_pct"] = round(sum(changes) / len(changes), 2)
            trend_analysis["summary"]["max_growth_pct"] = round(max(changes) if changes else 0, 2)
            trend_analysis["summary"]["max_decline_pct"] = round(min(changes) if changes else 0, 2)
        
        return trend_analysis
    
    def create_comparison_table(
        self, 
        comparison_data: Dict[str, Any],
        metrics: Optional[List[List[str]]] = None
    ) -> pd.DataFrame:
        """
        Create a comparison table DataFrame from comparison data.
        
        Args:
            comparison_data: Data from get_comparison_data()
            metrics: List of metric paths to include (default: extract all)
            
        Returns:
            DataFrame with months as columns and metrics as rows
        """
        months = sorted([m for m in comparison_data["months"] if m in comparison_data["data"]])
        
        if not months:
            return pd.DataFrame()
        
        # Auto-extract metrics if not provided
        if metrics is None:
            metrics = self._extract_all_metrics(comparison_data["data"])
        
        # Create table data
        table_data = {}
        
        for month in months:
            month_data = comparison_data["data"][month]
            month_values = {}
            
            for metric_path in metrics:
                value = self._extract_metric_value(month_data, metric_path)
                metric_label = " > ".join(metric_path) if isinstance(metric_path, list) else str(metric_path)
                month_values[metric_label] = float(value) if value is not None else None
            
            table_data[month] = month_values
        
        # Create DataFrame
        df = pd.DataFrame(table_data)
        df.index.name = "Metric"
        
        return df
    
    def calculate_year_over_year_comparison(
        self, 
        statement_type: str,
        current_month: str,
        metrics: Optional[List[List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Calculate year-over-year comparison for specific metrics.
        
        Args:
            statement_type: Type of statement
            current_month: Current month in YYYY-MM format
            metrics: List of metric paths to compare
            
        Returns:
            Dictionary with YoY comparison data
        """
        if not validate_month_format(current_month):
            raise ValueError(f"Invalid month format: {current_month}")
        
        # Calculate previous year month
        year, month = current_month.split('-')
        prev_year_month = f"{int(year) - 1}-{month}"
        
        # Load data for both months
        current_data = self.report_storage.load_statement(current_month, statement_type)
        prev_year_data = self.report_storage.load_statement(prev_year_month, statement_type)
        
        yoy_comparison = {
            "statement_type": statement_type,
            "current_month": current_month,
            "previous_year_month": prev_year_month,
            "current_data_available": current_data is not None,
            "previous_year_data_available": prev_year_data is not None,
            "comparisons": {}
        }
        
        if current_data is None or prev_year_data is None:
            logger.warning(f"Missing data for YoY comparison: current={current_data is not None}, prev_year={prev_year_data is not None}")
            return yoy_comparison
        
        current_values = current_data.get("data", {})
        prev_year_values = prev_year_data.get("data", {})
        
        # Auto-extract metrics if not provided
        if metrics is None:
            metrics = self._extract_all_metrics({"current": current_values, "prev": prev_year_values})
        
        # Calculate comparisons
        for metric_path in metrics:
            current_value = self._extract_metric_value(current_values, metric_path)
            prev_year_value = self._extract_metric_value(prev_year_values, metric_path)
            
            metric_label = " > ".join(metric_path) if isinstance(metric_path, list) else str(metric_path)
            
            if current_value is not None and prev_year_value is not None:
                absolute_change = current_value - prev_year_value
                
                if prev_year_value != 0:
                    percentage_change = (absolute_change / abs(prev_year_value)) * 100
                else:
                    percentage_change = 100.0 if current_value > 0 else -100.0 if current_value < 0 else 0.0
                
                yoy_comparison["comparisons"][metric_label] = {
                    "current_value": float(current_value),
                    "previous_year_value": float(prev_year_value),
                    "absolute_change": float(absolute_change),
                    "percentage_change": round(percentage_change, 2),
                    "trend": "growth" if percentage_change > 0 else "decline" if percentage_change < 0 else "flat"
                }
        
        return yoy_comparison
    
    def get_summary_statistics(
        self, 
        statement_type: str, 
        months: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get summary statistics across multiple months.
        
        Args:
            statement_type: Type of statement
            months: List of months (default: last 12 months)
            
        Returns:
            Dictionary with summary statistics
        """
        comparison_data = self.get_comparison_data(statement_type, months)
        available_months = comparison_data["metadata"]["available_months"]
        
        if not available_months:
            return {"error": "No data available for summary statistics"}
        
        summary = {
            "statement_type": statement_type,
            "period": f"{min(available_months)} to {max(available_months)}",
            "total_months": len(available_months),
            "metrics": {}
        }
        
        # Extract all metrics and calculate statistics
        all_metrics = self._extract_all_metrics(comparison_data["data"])
        
        for metric_path in all_metrics:
            values = []
            for month in available_months:
                value = self._extract_metric_value(comparison_data["data"][month], metric_path)
                if value is not None:
                    values.append(float(value))
            
            if values:
                metric_label = " > ".join(metric_path) if isinstance(metric_path, list) else str(metric_path)
                summary["metrics"][metric_label] = {
                    "count": len(values),
                    "mean": round(sum(values) / len(values), 2),
                    "min": round(min(values), 2),
                    "max": round(max(values), 2),
                    "std": round(pd.Series(values).std(), 2) if len(values) > 1 else 0,
                    "total": round(sum(values), 2)
                }
        
        return summary
    
    def _extract_metric_value(self, data: Dict[str, Any], metric_path: Optional[List[str]]) -> Optional[float]:
        """Extract a specific metric value from nested data structure"""
        if metric_path is None:
            return None
        
        try:
            current = data
            for key in metric_path:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None
            
            # Convert to float if possible
            if isinstance(current, (int, float, Decimal)):
                return float(current)
            elif isinstance(current, str):
                try:
                    return float(current)
                except ValueError:
                    return None
            else:
                return None
                
        except Exception:
            return None
    
    def _extract_all_metrics(self, data_dict: Dict[str, Any]) -> List[List[str]]:
        """Extract all possible metric paths from data structure"""
        metrics = set()
        
        for month_data in data_dict.values():
            if isinstance(month_data, dict):
                metrics.update(self._get_nested_paths(month_data))
        
        return [list(path) for path in sorted(metrics)]
    
    def _get_nested_paths(self, data: Dict[str, Any], prefix: tuple = ()) -> set:
        """Recursively get all paths in nested dictionary"""
        paths = set()
        
        for key, value in data.items():
            current_path = prefix + (key,)
            
            if isinstance(value, dict):
                # Add intermediate path if it has numeric values
                if any(isinstance(v, (int, float, Decimal, str)) for v in value.values()):
                    paths.update(self._get_nested_paths(value, current_path))
            elif isinstance(value, (int, float, Decimal)) or (isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit()):
                paths.add(current_path)
        
        return paths

    
    def _standardize_to_income_statement_format(self, month_data: Dict[str, Any], month: str) -> Dict[str, Any]:
        """
        Convert month data to standardized income statement format.
        
        Args:
            month_data: Raw month data from storage
            month: Month string for metadata
            
        Returns:
            Standardized data matching income statement schema
        """
        # If already in correct format, return as-is
        if all(key in month_data for key in ["Entity", "Revenue", "Total Revenue", "Expenses", "Total Expenses", "Net Income"]):
            return month_data
        
        # Convert legacy or alternative formats to standard schema
        standardized = {
            "Entity": month_data.get("Entity", "Combined"),
            "Revenue": {},
            "Total Revenue": 0.0,
            "Expenses": {},
            "Total Expenses": 0.0,
            "Net Income": 0.0
        }
        
        # Handle various data structures
        if "Revenue" in month_data and isinstance(month_data["Revenue"], dict):
            standardized["Revenue"] = month_data["Revenue"]
            standardized["Total Revenue"] = sum(month_data["Revenue"].values())
        
        if "Expenses" in month_data and isinstance(month_data["Expenses"], dict):
            standardized["Expenses"] = month_data["Expenses"]
            standardized["Total Expenses"] = sum(month_data["Expenses"].values())
        
        # Handle direct totals
        if "Total Revenue" in month_data:
            standardized["Total Revenue"] = float(month_data["Total Revenue"])
        
        if "Total Expenses" in month_data:
            standardized["Total Expenses"] = float(month_data["Total Expenses"])
        
        # Calculate net income
        standardized["Net Income"] = standardized["Total Revenue"] - standardized["Total Expenses"]
        
        # Handle legacy category structures
        if not standardized["Expenses"] and not standardized["Revenue"]:
            # Try to extract from other structures
            for key, value in month_data.items():
                if key in ["Entity", "Total Revenue", "Total Expenses", "Net Income"]:
                    continue
                    
                if isinstance(value, (int, float, Decimal)):
                    # Assume expenses for now (can be enhanced with category detection)
                    standardized["Expenses"][key] = float(value)
                    standardized["Total Expenses"] += float(value)
        
        # Recalculate net income
        standardized["Net Income"] = standardized["Total Revenue"] - standardized["Total Expenses"]
        
        return standardized
    
    def generate_income_statement_comparison(self, months: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate monthly comparison using pure income statement format.
        
        Args:
            months: List of months to compare
            
        Returns:
            Income statement format comparison data
        """
        from .data_storage import MonthlyDataStorage
        from .income_statement import IncomeStatementGenerator
        from .models import CategoryMapper
        
        # Use data storage directly for most current data
        storage = MonthlyDataStorage()
        generator = IncomeStatementGenerator(CategoryMapper())
        
        if months is None:
            months = storage.list_available_months()[-12:]  # Last 12 months
        
        comparison_data = {
            "comparison_type": "income_statement_comparison",
            "months": months,
            "data": {},
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "source": "direct_data_storage",
                "total_months": len(months)
            }
        }
        
        # Generate income statement for each month from raw data
        for month in months:
            transactions_df, assets_df = storage.load_monthly_data(month)
            
            if transactions_df is not None:
                # Convert DataFrame to Transaction objects
                from .models import Transaction
                from decimal import Decimal
                
                transactions = []
                for _, row in transactions_df.iterrows():
                    transaction = Transaction(
                        date=row['date'],
                        description=row['description'],
                        amount=Decimal(str(row['amount'])),
                        debit_category=row['category'],
                        account_name=row.get('account_name', 'Default'),
                        account_type=row.get('account_type', 'Cash'),
                        notes=row.get('notes', '')
                    )
                    transactions.append(transaction)
                
                # Generate income statement
                income_statement = generator.generate_statement(transactions, "Combined")
                comparison_data["data"][month] = income_statement
            else:
                logger.warning(f"No transaction data found for {month}")
        
        return comparison_data
