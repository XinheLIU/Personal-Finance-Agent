"""
Data Storage Utilities and Helpers for Monthly Accounting Data

Provides validation, path management, and data conversion utilities
for the monthly data storage system.
"""

import re
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal
import logging

# Configure logging
logger = logging.getLogger(__name__)


def validate_month_format(year_month: str) -> bool:
    """
    Validate year-month format (YYYY-MM).
    
    Args:
        year_month: String to validate
        
    Returns:
        True if format is valid
    """
    if not isinstance(year_month, str):
        return False
        
    pattern = r'^\d{4}-\d{2}$'
    if not re.match(pattern, year_month):
        return False
    
    try:
        year, month = year_month.split('-')
        year_int = int(year)
        month_int = int(month)
        
        # Basic range validation
        if year_int < 1900 or year_int > 2100:
            return False
        if month_int < 1 or month_int > 12:
            return False
            
        return True
    except (ValueError, IndexError):
        return False


def get_monthly_data_path(base_path: Path, year_month: str) -> Path:
    """
    Get the path for monthly data storage.
    
    Args:
        base_path: Base directory path
        year_month: Month in YYYY-MM format
        
    Returns:
        Path object for monthly data directory
    """
    if not validate_month_format(year_month):
        raise ValueError(f"Invalid month format: {year_month}")
        
    return base_path / year_month


def parse_year_month(year_month: str) -> tuple[int, int]:
    """
    Parse year-month string into integers.
    
    Args:
        year_month: Month in YYYY-MM format
        
    Returns:
        Tuple of (year, month) as integers
    """
    if not validate_month_format(year_month):
        raise ValueError(f"Invalid month format: {year_month}")
        
    year, month = year_month.split('-')
    return int(year), int(month)


def format_year_month(year: int, month: int) -> str:
    """
    Format year and month integers into YYYY-MM string.
    
    Args:
        year: Year as integer
        month: Month as integer (1-12)
        
    Returns:
        Formatted year-month string
    """
    if month < 1 or month > 12:
        raise ValueError(f"Month must be 1-12, got {month}")
        
    return f"{year:04d}-{month:02d}"


def get_current_year_month() -> str:
    """
    Get current year-month in YYYY-MM format.
    
    Returns:
        Current year-month string
    """
    now = datetime.now()
    return format_year_month(now.year, now.month)


def get_recent_months(count: int = 12, from_month: Optional[str] = None) -> List[str]:
    """
    Get list of recent months in reverse chronological order.
    
    Args:
        count: Number of months to return
        from_month: Starting month (default: current month)
        
    Returns:
        List of year-month strings
    """
    if from_month is None:
        from_month = get_current_year_month()
    
    if not validate_month_format(from_month):
        raise ValueError(f"Invalid month format: {from_month}")
    
    months = []
    year, month = parse_year_month(from_month)
    
    for _ in range(count):
        months.append(format_year_month(year, month))
        
        # Move to previous month
        month -= 1
        if month < 1:
            month = 12
            year -= 1
    
    return months


def validate_transactions_data(df: pd.DataFrame) -> List[str]:
    """
    Validate transactions DataFrame for storage.
    
    Args:
        df: Transactions DataFrame
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    if df is None or df.empty:
        errors.append("Transactions DataFrame is empty")
        return errors
    
    # Required columns check
    required_columns = ['Description', 'Amount', 'Debit', 'Credit', 'User']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        errors.append(f"Missing required columns: {missing_columns}")
    
    # Check for completely empty rows first
    if df.isnull().all(axis=1).any():
        errors.append("Contains completely empty rows")
    
    # More robust Amount validation - check for non-numeric values that can't be cleaned
    if 'Amount' in df.columns:
        # Try to clean amounts first (same logic as TransactionProcessor)
        problematic_amounts = []
        for idx, amount_val in enumerate(df['Amount']):
            if pd.isna(amount_val) or amount_val == '':
                continue  # Skip empty values, they're handled as 0.0
            
            # Try to clean the amount (remove currency symbols, etc.)
            try:
                cleaned = re.sub(r'[¥,￥$]', '', str(amount_val))
                float(cleaned)
            except (ValueError, TypeError):
                # Only add to errors if it's truly non-cleanable
                if str(amount_val).strip() != '' and str(amount_val).strip().lower() not in ['nan', 'none', 'null']:
                    problematic_amounts.append(f"Row {idx+1}: '{amount_val}'")
        
        if problematic_amounts:
            # Only error if there are many problematic amounts (> 10% of data)
            if len(problematic_amounts) > len(df) * 0.1:
                errors.append(f"Too many non-cleanable amounts found in {len(problematic_amounts)} rows: {problematic_amounts[:3]}...")
            # For fewer problematic amounts, just warn (they'll be cleaned to 0.0)
    
    return errors


def validate_assets_data(df: pd.DataFrame) -> List[str]:
    """
    Validate assets DataFrame for storage.
    
    Args:
        df: Assets DataFrame
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    if df is None or df.empty:
        errors.append("Assets DataFrame is empty")
        return errors
    
    # Required columns check (flexible based on asset data structure)
    # Basic validation for common asset columns
    if 'Amount' in df.columns or 'Value' in df.columns or 'Balance' in df.columns:
        # Check numeric columns
        numeric_cols = [col for col in ['Amount', 'Value', 'Balance'] if col in df.columns]
        for col in numeric_cols:
            try:
                pd.to_numeric(df[col], errors='coerce')
            except Exception:
                errors.append(f"{col} column contains invalid numeric values")
    
    # Check for completely empty rows
    if df.isnull().all(axis=1).any():
        errors.append("Contains completely empty rows")
    
    return errors


def clean_transactions_for_storage(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean transaction data for storage, handling problematic amounts.
    
    Args:
        df: Raw transactions DataFrame
        
    Returns:
        Cleaned DataFrame ready for storage
    """
    df_cleaned = df.copy()
    
    if 'Amount' in df_cleaned.columns:
        # Clean amounts using the same logic as TransactionProcessor
        def clean_amount(amount_str):
            if pd.isna(amount_str) or amount_str == '':
                return 0.0
            
            # Remove currency symbols and commas
            cleaned = re.sub(r'[¥,￥$]', '', str(amount_str))
            try:
                return float(cleaned)
            except ValueError:
                logger.warning(f"Could not convert amount '{amount_str}' to float, using 0.0")
                return 0.0
        
        df_cleaned['Amount'] = df_cleaned['Amount'].apply(clean_amount)
    
    # Clean other string columns
    string_columns = ['Description', 'Debit', 'Credit', 'User']
    for col in string_columns:
        if col in df_cleaned.columns:
            df_cleaned[col] = df_cleaned[col].astype(str).str.strip()
            # Replace 'nan' strings with empty strings
            df_cleaned[col] = df_cleaned[col].replace(['nan', 'None', 'null'], '')
    
    # Remove completely empty rows
    df_cleaned = df_cleaned.dropna(how='all')
    
    return df_cleaned


def clean_assets_for_storage(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean asset data for storage, handling problematic numeric values.
    
    Args:
        df: Raw assets DataFrame
        
    Returns:
        Cleaned DataFrame ready for storage
    """
    df_cleaned = df.copy()
    
    # Clean numeric columns (CNY, USD, Amount, Value, Balance)
    numeric_columns = ['CNY', 'USD', 'Amount', 'Value', 'Balance']
    for col in numeric_columns:
        if col in df_cleaned.columns:
            def clean_amount(amount_str):
                if pd.isna(amount_str) or amount_str == '':
                    return 0.0
                
                # Remove currency symbols and commas
                cleaned = re.sub(r'[¥,￥$]', '', str(amount_str))
                try:
                    return float(cleaned)
                except ValueError:
                    logger.warning(f"Could not convert {col} '{amount_str}' to float, using 0.0")
                    return 0.0
            
            df_cleaned[col] = df_cleaned[col].apply(clean_amount)
    
    # Clean string columns
    string_columns = ['Account Type', 'Account']
    for col in string_columns:
        if col in df_cleaned.columns:
            df_cleaned[col] = df_cleaned[col].astype(str).str.strip()
            # Replace 'nan' strings with empty strings
            df_cleaned[col] = df_cleaned[col].replace(['nan', 'None', 'null'], '')
    
    # Remove completely empty rows
    df_cleaned = df_cleaned.dropna(how='all')
    
    return df_cleaned


def convert_decimal_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert Decimal columns to float for parquet compatibility.
    
    Args:
        df: DataFrame with potential Decimal columns
        
    Returns:
        DataFrame with Decimal columns converted to float
    """
    df_converted = df.copy()
    
    for col in df_converted.columns:
        if df_converted[col].dtype == 'object':
            # Check if column contains Decimal objects
            sample_values = df_converted[col].dropna().iloc[:5] if len(df_converted) > 0 else []
            if any(isinstance(val, Decimal) for val in sample_values):
                try:
                    df_converted[col] = df_converted[col].apply(
                        lambda x: float(x) if isinstance(x, Decimal) else x
                    )
                    logger.info(f"Converted Decimal column '{col}' to float")
                except Exception as e:
                    logger.warning(f"Failed to convert Decimal column '{col}': {e}")
    
    return df_converted


def csv_to_dataframe(csv_content: str, file_type: str = "transactions") -> pd.DataFrame:
    """
    Convert CSV content string to DataFrame with appropriate validation.
    
    Args:
        csv_content: CSV content as string
        file_type: Type of data ('transactions' or 'assets')
        
    Returns:
        Validated DataFrame
    """
    try:
        # Read CSV from string
        from io import StringIO
        df = pd.read_csv(StringIO(csv_content))
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Validate based on file type
        if file_type == "transactions":
            errors = validate_transactions_data(df)
        else:
            errors = validate_assets_data(df)
        
        if errors:
            raise ValueError(f"Data validation failed: {errors}")
        
        return df
        
    except Exception as e:
        logger.error(f"Failed to convert CSV to DataFrame: {e}")
        raise


def dataframe_to_summary(df: pd.DataFrame, data_type: str = "data") -> Dict[str, Any]:
    """
    Generate summary information about a DataFrame.
    
    Args:
        df: DataFrame to summarize
        data_type: Type of data for context
        
    Returns:
        Dictionary with summary information
    """
    if df is None or df.empty:
        return {
            "rows": 0,
            "columns": 0,
            "data_type": data_type,
            "empty": True
        }
    
    summary = {
        "rows": len(df),
        "columns": len(df.columns),
        "data_type": data_type,
        "empty": False,
        "column_names": list(df.columns),
        "memory_usage_bytes": df.memory_usage(deep=True).sum(),
        "has_nulls": df.isnull().any().any(),
        "null_counts": df.isnull().sum().to_dict()
    }
    
    # Add numeric column statistics
    numeric_cols = df.select_dtypes(include=['number']).columns
    if len(numeric_cols) > 0:
        summary["numeric_columns"] = list(numeric_cols)
        summary["numeric_summary"] = df[numeric_cols].describe().to_dict()
    
    return summary


def ensure_monthly_directory_structure(base_path: Path) -> None:
    """
    Ensure the monthly directory structure exists.
    
    Args:
        base_path: Base path for monthly data
    """
    base_path.mkdir(parents=True, exist_ok=True)
    
    # Create README if it doesn't exist
    readme_path = base_path / "README.md"
    if not readme_path.exists():
        readme_content = """# Monthly Accounting Data Storage

This directory contains monthly accounting data stored in parquet format.

## Structure
```
YYYY-MM/
├── transactions.parquet  # Monthly transaction data
└── assets.parquet       # Monthly asset data
```

## Data Format
- **Transactions**: CSV data converted to parquet with validation
- **Assets**: Asset balance and valuation data
- **Singleton Pattern**: One dataset per month, new uploads overwrite existing

## Usage
Data is managed through the MonthlyDataStorage class in src/accounting/data_storage.py
"""
        readme_path.write_text(readme_content)
        logger.info(f"Created README at {readme_path}")


def get_storage_statistics(base_path: Path) -> Dict[str, Any]:
    """
    Get statistics about stored monthly data.
    
    Args:
        base_path: Base path for monthly data
        
    Returns:
        Dictionary with storage statistics
    """
    stats = {
        "total_months": 0,
        "total_files": 0,
        "total_size_bytes": 0,
        "months_with_transactions": 0,
        "months_with_assets": 0,
        "oldest_month": None,
        "newest_month": None,
        "monthly_breakdown": []
    }
    
    if not base_path.exists():
        return stats
    
    months = []
    for month_dir in base_path.iterdir():
        if month_dir.is_dir() and validate_month_format(month_dir.name):
            month_info = {
                "month": month_dir.name,
                "has_transactions": (month_dir / "transactions.parquet").exists(),
                "has_assets": (month_dir / "assets.parquet").exists(),
                "transactions_size": 0,
                "assets_size": 0
            }
            
            # Get file sizes
            trans_path = month_dir / "transactions.parquet"
            if trans_path.exists():
                month_info["transactions_size"] = trans_path.stat().st_size
                stats["months_with_transactions"] += 1
                stats["total_files"] += 1
            
            assets_path = month_dir / "assets.parquet"
            if assets_path.exists():
                month_info["assets_size"] = assets_path.stat().st_size
                stats["months_with_assets"] += 1
                stats["total_files"] += 1
            
            month_info["total_size"] = month_info["transactions_size"] + month_info["assets_size"]
            stats["total_size_bytes"] += month_info["total_size"]
            
            if month_info["has_transactions"] or month_info["has_assets"]:
                months.append(month_dir.name)
                stats["monthly_breakdown"].append(month_info)
    
    stats["total_months"] = len(months)
    if months:
        stats["oldest_month"] = min(months)
        stats["newest_month"] = max(months)
    
    return stats

# =============================================================================
# Bulk Data Processing and Translation Utilities
# =============================================================================

def parse_user_expense_table(table_content: str) -> Dict[str, Any]:
    """
    Parse user expense table format (User-Category-Month matrix).
    
    Example input format:
    User        Jan-25    Feb-25    Mar-25
    YY    房租    ¥11,512.80    ¥11,512.80    ¥11,512.80
    XH    餐饮    ¥3,243.94    ¥2,240.63    ¥1,854.87
    
    Args:
        table_content: Multi-line string with expense table
        
    Returns:
        Dictionary with parsed data structure
    """
    from .category_translator import CategoryTranslator
    
    translator = CategoryTranslator()
    lines = [line.strip() for line in table_content.strip().split('\n') if line.strip()]
    
    if not lines:
        raise ValueError("Empty table content")
    
    # Parse header row (months)
    header = lines[0].split()
    if len(header) < 3:  # Minimum: User, Category, Month1
        raise ValueError("Invalid header format. Expected: User Category Month1 Month2 ...")
    
    months = header[2:]  # Skip 'User' and first category column
    
    # Validate month formats and standardize
    standardized_months = []
    for month in months:
        try:
            # Handle various month formats (Jan-25, 2025-01, etc.)
            if '-' in month and len(month.split('-')[1]) == 2:
                # Format: Jan-25 or 01-25
                month_part, year_part = month.split('-')
                
                # Convert month names to numbers if needed
                month_mapping = {
                    'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                    'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08', 
                    'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                }
                
                if month_part in month_mapping:
                    month_num = month_mapping[month_part]
                else:
                    month_num = month_part.zfill(2)
                
                standardized_month = f"20{year_part}-{month_num}"
            else:
                standardized_month = month
                
            # Validate format
            if not validate_month_format(standardized_month):
                raise ValueError(f"Invalid month format: {month}")
                
            standardized_months.append(standardized_month)
            
        except Exception as e:
            raise ValueError(f"Error parsing month '{month}': {e}")
    
    # Parse data rows
    parsed_data = {
        "months": standardized_months,
        "users": {},
        "categories": set(),
        "total_records": 0
    }
    
    current_user = None
    for line_idx, line in enumerate(lines[1:], 2):
        parts = line.split()
        if len(parts) < len(standardized_months) + 2:
            logger.warning(f"Line {line_idx}: Insufficient data columns, skipping")
            continue
        
        user = parts[0]
        category_chinese = parts[1]
        amounts = parts[2:]
        
        # Update current user
        if user != current_user:
            current_user = user
            if user not in parsed_data["users"]:
                parsed_data["users"][user] = {}
        
        # Translate category to English
        category_english = translator.translate_to_english(category_chinese)
        parsed_data["categories"].add(category_english)
        
        # Parse amounts for each month
        month_amounts = {}
        for month, amount_str in zip(standardized_months, amounts):
            try:
                # Clean amount string (remove ¥, commas, etc.)
                cleaned_amount = amount_str.replace('¥', '').replace(',', '').strip()
                amount = float(cleaned_amount) if cleaned_amount else 0.0
                month_amounts[month] = amount
                parsed_data["total_records"] += 1
            except ValueError as e:
                logger.error(f"Error parsing amount '{amount_str}' for {user}-{category_chinese}: {e}")
                month_amounts[month] = 0.0
        
        # Store in parsed data structure
        if category_english not in parsed_data["users"][user]:
            parsed_data["users"][user]["categories"] = {}
        
        parsed_data["users"][user][category_english] = month_amounts
    
    parsed_data["categories"] = sorted(list(parsed_data["categories"]))
    logger.info(f"Parsed expense table: {len(parsed_data['users'])} users, "
                f"{len(parsed_data['categories'])} categories, "
                f"{len(standardized_months)} months")
    
    return parsed_data


def convert_parsed_data_to_transactions(parsed_data: Dict[str, Any]) -> List[pd.DataFrame]:
    """
    Convert parsed user expense table to monthly transaction DataFrames.
    
    Args:
        parsed_data: Result from parse_user_expense_table()
        
    Returns:
        List of DataFrames, one per month with transaction data
    """
    from datetime import datetime
    from decimal import Decimal
    
    monthly_dataframes = []
    
    for month in parsed_data["months"]:
        transactions = []
        
        for user, user_data in parsed_data["users"].items():
            for category, month_amounts in user_data.items():
                if category == "categories":  # Skip metadata
                    continue
                    
                amount = month_amounts.get(month, 0.0)
                if amount == 0.0:  # Skip zero amounts
                    continue
                
                # Create transaction record with proper schema
                transaction = {
                    "date": f"{month}-01",  # Use first day of month
                    "Description": f"{category} - {user}",  # Capital D for schema compatibility
                    "Amount": -abs(amount),  # Expenses are negative
                    "Debit": category,  # Category goes in Debit column
                    "Credit": f"{user}_Account",  # Account goes in Credit column  
                    "User": user,  # User column
                    "category": category,  # Keep lowercase for internal use
                    "account_name": f"{user}_Account",
                    "account_type": "Cash",
                    "notes": f"Bulk upload - {user} {category}"
                }
                transactions.append(transaction)
        
        # Create DataFrame for this month
        if transactions:
            df = pd.DataFrame(transactions)
            df["year_month"] = month
            monthly_dataframes.append((month, df))
            
    logger.info(f"Converted to {len(monthly_dataframes)} monthly transaction DataFrames")
    return monthly_dataframes


def aggregate_users_to_combined_entity(parsed_data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """
    Aggregate multiple users into combined entity following income statement format.
    
    Args:
        parsed_data: Result from parse_user_expense_table()
        
    Returns:
        Dictionary with aggregated data by month
    """
    from .category_translator import CategoryTranslator
    
    translator = CategoryTranslator()
    aggregated_data = {}
    
    for month in parsed_data["months"]:
        month_data = {
            "Entity": "Combined",
            "Revenue": {},
            "Total Revenue": 0.0,
            "Expenses": {},
            "Total Expenses": 0.0,
            "Net Income": 0.0
        }
        
        # Aggregate expenses across all users
        for user, user_data in parsed_data["users"].items():
            for category, month_amounts in user_data.items():
                if category == "categories":  # Skip metadata
                    continue
                    
                amount = month_amounts.get(month, 0.0)
                if amount == 0.0:
                    continue
                
                # Determine if revenue or expense (assume all amounts are expenses for now)
                if category in translator.STANDARD_REVENUE_CATEGORIES:
                    month_data["Revenue"][category] = month_data["Revenue"].get(category, 0.0) + amount
                    month_data["Total Revenue"] += amount
                else:
                    month_data["Expenses"][category] = month_data["Expenses"].get(category, 0.0) + amount
                    month_data["Total Expenses"] += amount
        
        # Calculate net income
        month_data["Net Income"] = month_data["Total Revenue"] - month_data["Total Expenses"]
        
        aggregated_data[month] = month_data
        
    logger.info(f"Aggregated data for {len(aggregated_data)} months")
    return aggregated_data


def validate_bulk_upload_data(parsed_data: Dict[str, Any]) -> List[str]:
    """
    Validate bulk upload data for consistency and completeness.
    
    Args:
        parsed_data: Result from parse_user_expense_table()
        
    Returns:
        List of validation errors (empty if valid)
    """
    from .category_translator import CategoryTranslator
    
    errors = []
    translator = CategoryTranslator()
    
    # Validate basic structure
    if not parsed_data.get("months"):
        errors.append("No months found in data")
    
    if not parsed_data.get("users"):
        errors.append("No users found in data")
    
    if not parsed_data.get("categories"):
        errors.append("No categories found in data")
    
    # Validate months
    for month in parsed_data.get("months", []):
        if not validate_month_format(month):
            errors.append(f"Invalid month format: {month}")
    
    # Validate categories
    unknown_categories = []
    for category in parsed_data.get("categories", []):
        validation = translator.validate_category(category)
        if not validation["is_valid"]:
            unknown_categories.append(category)
    
    if unknown_categories:
        errors.append(f"Unknown categories: {unknown_categories}")
    
    # Validate data completeness
    total_records = parsed_data.get("total_records", 0)
    expected_records = (len(parsed_data.get("users", {})) * 
                       len(parsed_data.get("categories", [])) * 
                       len(parsed_data.get("months", [])))
    
    if total_records < expected_records * 0.5:  # Allow for some missing data
        errors.append(f"Data appears incomplete: {total_records}/{expected_records} records")
    
    return errors


def preview_bulk_upload_conversion(table_content: str, max_preview_records: int = 20) -> Dict[str, Any]:
    """
    Preview bulk upload conversion without saving to storage.
    
    Args:
        table_content: Raw table content
        max_preview_records: Maximum records to show in preview
        
    Returns:
        Dictionary with preview information
    """
    try:
        # Parse the data
        parsed_data = parse_user_expense_table(table_content)
        
        # Validate
        validation_errors = validate_bulk_upload_data(parsed_data)
        
        # Convert to transactions (limited preview)
        monthly_dfs = convert_parsed_data_to_transactions(parsed_data)
        
        # Aggregate data
        aggregated_data = aggregate_users_to_combined_entity(parsed_data)
        
        # Create preview
        preview = {
            "status": "success" if not validation_errors else "validation_errors",
            "validation_errors": validation_errors,
            "summary": {
                "total_months": len(parsed_data["months"]),
                "total_users": len(parsed_data["users"]),
                "total_categories": len(parsed_data["categories"]),
                "total_records": parsed_data["total_records"],
                "months": parsed_data["months"],
                "users": list(parsed_data["users"].keys()),
                "categories": parsed_data["categories"]
            },
            "sample_transactions": [],
            "sample_aggregated": {}
        }
        
        # Add sample transactions
        for month, df in monthly_dfs[:2]:  # First 2 months
            sample_transactions = df.head(max_preview_records).to_dict('records')
            preview["sample_transactions"].extend([
                {"month": month, "transaction": tx} for tx in sample_transactions
            ])
        
        # Add sample aggregated data
        for month in list(aggregated_data.keys())[:2]:  # First 2 months
            preview["sample_aggregated"][month] = aggregated_data[month]
        
        return preview
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "validation_errors": [],
            "summary": {},
            "sample_transactions": [],
            "sample_aggregated": {}
        }
