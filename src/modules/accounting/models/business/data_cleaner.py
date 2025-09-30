"""
Data Cleaning & Validation Business Logic

Handles automated data cleaning and validation BEFORE user preview.
This ensures users see clean, validated data and only need to fix business logic issues.
"""

import pandas as pd
import re
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass, field

# Set up logger for DataCleaner
logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """Represents a single validation error"""
    row_number: int
    column: str
    error_type: str
    message: str


@dataclass
class CleaningAction:
    """Represents a single cleaning action taken"""
    action_type: str  # 'remove_empty_rows', 'remove_empty_columns', 'normalize_currency', etc.
    description: str
    count: int = 0
    details: str = ""


@dataclass
class ValidationReport:
    """Contains all validation results and cleaning actions"""
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    cleaning_actions: List[CleaningAction] = field(default_factory=list)
    
    def has_errors(self) -> bool:
        """Check if there are any critical errors"""
        return len(self.errors) > 0
    
    def get_summary(self) -> str:
        """Get human-readable summary"""
        if not self.has_errors() and not self.warnings:
            return "✅ All validation checks passed"
        
        summary = []
        if self.errors:
            summary.append(f"❌ {len(self.errors)} error(s) found")
        if self.warnings:
            summary.append(f"⚠️ {len(self.warnings)} warning(s) found")
        return " | ".join(summary)
    
    def get_cleaning_summary(self) -> str:
        """Get summary of cleaning actions performed"""
        if not self.cleaning_actions:
            return "ℹ️ No cleaning actions needed"
        
        summary = []
        for action in self.cleaning_actions:
            if action.count > 0:
                summary.append(f"🧹 {action.description}: {action.count}")
        
        return " | ".join(summary) if summary else "ℹ️ No cleaning actions needed"


class DataCleaner:
    """
    Automated data cleaning and validation for CSV transaction data.
    
    This is the first step after CSV upload - cleans and validates data
    BEFORE showing it to the user for preview/editing.
    """
    
    REQUIRED_COLUMNS = ['Description', 'Amount', 'Debit', 'Credit', 'User']
    
    def __init__(self, csv_file_path: str = None, dataframe: pd.DataFrame = None):
        """
        Initialize with either a CSV file path or a DataFrame.
        
        Args:
            csv_file_path: Path to CSV file
            dataframe: Pre-loaded DataFrame (alternative to csv_file_path)
        """
        if csv_file_path is None and dataframe is None:
            raise ValueError("Must provide either csv_file_path or dataframe")
        
        self.csv_file_path = csv_file_path
        self._raw_df = dataframe
        self.cleaned_df: pd.DataFrame = None
        self.validation_report = ValidationReport()
    
    def _load_csv(self) -> pd.DataFrame:
        """Load CSV file with proper encoding handling"""
        try:
            # Handle UTF-8 with BOM (common in Excel exports)
            df = pd.read_csv(self.csv_file_path, encoding='utf-8-sig')
            return df
        except pd.errors.EmptyDataError:
            return pd.DataFrame()
        except Exception as e:
            raise Exception(f"Error reading CSV file: {e}")
    
    def _remove_empty_rows_and_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove completely empty rows and columns, and rows without amounts"""
        original_rows = len(df)
        original_cols = len(df.columns)
        
        # Remove rows where ALL values are NaN
        df_before_empty_rows = df.copy()
        df = df.dropna(how='all')
        empty_rows_removed = len(df_before_empty_rows) - len(df)
        
        if empty_rows_removed > 0:
            logger.info(f"Removed {empty_rows_removed} completely empty rows")
            self.validation_report.cleaning_actions.append(
                CleaningAction(
                    action_type="remove_empty_rows",
                    description="Removed completely empty rows",
                    count=empty_rows_removed,
                    details="Rows with all NaN/empty values"
                )
            )
        
        # Remove rows with no amount (meaningless transactions)
        if 'Amount' in df.columns:
            df_before_no_amount = df.copy()
            # Remove rows where Amount is NaN, empty string, or zero
            df = df[
                df['Amount'].notna() & 
                (df['Amount'] != '') & 
                (df['Amount'] != 0) &
                (df['Amount'] != '0') &
                (df['Amount'] != '0.0') &
                (df['Amount'] != '0.00')
            ]
            no_amount_removed = len(df_before_no_amount) - len(df)
            
            if no_amount_removed > 0:
                logger.info(f"Removed {no_amount_removed} rows with no amount (meaningless transactions)")
                self.validation_report.cleaning_actions.append(
                    CleaningAction(
                        action_type="remove_no_amount_rows",
                        description="Removed rows with no amount",
                        count=no_amount_removed,
                        details="Transactions without amounts are meaningless"
                    )
                )
        
        # Remove columns where ALL values are NaN
        df_before_empty_cols = df.copy()
        df = df.dropna(axis=1, how='all')
        empty_cols_removed = len(df_before_empty_cols.columns) - len(df.columns)
        
        if empty_cols_removed > 0:
            logger.info(f"Removed {empty_cols_removed} completely empty columns")
            self.validation_report.cleaning_actions.append(
                CleaningAction(
                    action_type="remove_empty_columns",
                    description="Removed completely empty columns",
                    count=empty_cols_removed,
                    details="Columns with all NaN/empty values"
                )
            )
        
        total_rows_removed = original_rows - len(df)
        total_cols_removed = original_cols - len(df.columns)
        
        if total_rows_removed > 0 or total_cols_removed > 0:
            logger.info(f"Data cleaning summary: {original_rows}→{len(df)} rows ({total_rows_removed} removed), "
                       f"{original_cols}→{len(df.columns)} columns ({total_cols_removed} removed)")
        
        return df
    
    def _normalize_currency_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize currency values in Amount column.
        
        Handles:
        - Chinese yuan symbols: ¥, ￥
        - Dollar signs: $
        - Comma separators: 1,000.00 → 1000.00
        - Whitespace
        """
        if 'Amount' not in df.columns:
            return df
        
        currency_cleaned_count = 0
        
        def clean_amount(value):
            nonlocal currency_cleaned_count
            if pd.isna(value) or value == '':
                return value  # Keep NaN as-is for validation
            
            original_value = str(value)
            # Convert to string and remove currency symbols and commas
            cleaned = re.sub(r'[¥￥$,\s]', '', original_value)
            
            # Check if we actually cleaned something
            if cleaned != original_value:
                currency_cleaned_count += 1
            
            # Try to convert to float
            try:
                return float(cleaned)
            except ValueError:
                return value  # Keep original if can't convert (for validation error)
        
        df['Amount'] = df['Amount'].apply(clean_amount)
        
        if currency_cleaned_count > 0:
            logger.info(f"Normalized currency symbols in {currency_cleaned_count} amount values")
            self.validation_report.cleaning_actions.append(
                CleaningAction(
                    action_type="normalize_currency",
                    description="Normalized currency symbols",
                    count=currency_cleaned_count,
                    details="Removed ¥, $, commas from amounts"
                )
            )
        
        return df
    
    def _strip_whitespace(self, df: pd.DataFrame) -> pd.DataFrame:
        """Strip leading/trailing whitespace from all text fields"""
        # Clean column names first
        original_columns = df.columns.tolist()
        df.columns = df.columns.str.strip()
        cleaned_columns = df.columns.tolist()
        
        if original_columns != cleaned_columns:
            logger.info("Cleaned whitespace from column names")
            self.validation_report.cleaning_actions.append(
                CleaningAction(
                    action_type="clean_column_names",
                    description="Cleaned column names",
                    count=1,
                    details="Removed leading/trailing whitespace from headers"
                )
            )
        
        # Strip whitespace from string columns
        whitespace_cleaned_count = 0
        for col in df.columns:
            if df[col].dtype == 'object':  # String columns
                original_values = df[col].copy()
                df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
                # Count how many values were actually changed
                changed_values = sum(1 for orig, new in zip(original_values, df[col]) 
                                   if isinstance(orig, str) and isinstance(new, str) and orig != new)
                whitespace_cleaned_count += changed_values
        
        if whitespace_cleaned_count > 0:
            logger.info(f"Cleaned whitespace from {whitespace_cleaned_count} text values")
            self.validation_report.cleaning_actions.append(
                CleaningAction(
                    action_type="clean_whitespace",
                    description="Cleaned text whitespace",
                    count=whitespace_cleaned_count,
                    details="Removed leading/trailing spaces from text fields"
                )
            )
        
        return df
    
    def _validate_required_columns(self, df: pd.DataFrame) -> None:
        """Validate that all required columns exist"""
        missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        
        if missing_columns:
            error = ValidationError(
                row_number=0,
                column=', '.join(missing_columns),
                error_type='missing_column',
                message=f"Missing required columns: {', '.join(missing_columns)}"
            )
            self.validation_report.errors.append(error)
    
    def _validate_required_fields(self, df: pd.DataFrame) -> None:
        """
        Validate required field completion.
        
        Business Rule: If a row has an Amount, it MUST have both Debit AND Credit accounts.
        """
        if 'Amount' not in df.columns:
            return
        
        for idx, row in df.iterrows():
            amount = row.get('Amount')
            debit = row.get('Debit', '')
            credit = row.get('Credit', '')
            
            # Skip completely empty rows
            if pd.isna(amount) and pd.isna(debit) and pd.isna(credit):
                continue
            
            # If amount exists, must have both debit and credit
            if pd.notna(amount) and amount != '' and amount != 0:
                if pd.isna(debit) or str(debit).strip() == '':
                    error = ValidationError(
                        row_number=idx + 2,  # +2 because: 0-indexed + header row
                        column='Debit',
                        error_type='missing_required_field',
                        message=f"Row {idx + 2}: Missing Debit account (required when Amount is present)"
                    )
                    self.validation_report.errors.append(error)
                
                if pd.isna(credit) or str(credit).strip() == '':
                    error = ValidationError(
                        row_number=idx + 2,
                        column='Credit',
                        error_type='missing_required_field',
                        message=f"Row {idx + 2}: Missing Credit account (required when Amount is present)"
                    )
                    self.validation_report.errors.append(error)
    
    def _validate_data_types(self, df: pd.DataFrame) -> None:
        """Validate that data types are correct"""
        if 'Amount' not in df.columns:
            return
        
        for idx, row in df.iterrows():
            amount = row.get('Amount')
            
            # Skip empty amounts
            if pd.isna(amount) or amount == '':
                continue
            
            # Check if amount is numeric
            try:
                float(amount)
            except (ValueError, TypeError):
                error = ValidationError(
                    row_number=idx + 2,
                    column='Amount',
                    error_type='invalid_data_type',
                    message=f"Row {idx + 2}: Amount must be a number (got '{amount}')"
                )
                self.validation_report.errors.append(error)
    
    def _validate_business_rules(self, df: pd.DataFrame) -> None:
        """
        Validate business logic rules.
        
        Note: This is basic validation. Complex business rules are handled
        in TransactionProcessor after user has reviewed/corrected the data.
        """
        # Could add rules like:
        # - Revenue categories should have positive amounts (warning, not error)
        # - Certain account types should only appear in debit or credit
        # For now, we keep this simple and let TransactionProcessor handle complex logic
        pass
    
    def clean_and_validate(self) -> Tuple[pd.DataFrame, ValidationReport]:
        """
        Main method: Clean and validate data.
        
        Returns:
            Tuple of (cleaned_dataframe, validation_report)
        """
        # Step 1: Load data
        if self._raw_df is None:
            self._raw_df = self._load_csv()
        
        df = self._raw_df.copy()
        
        # Step 2: Cleaning operations (automated, no user intervention)
        df = self._remove_empty_rows_and_columns(df)
        df = self._strip_whitespace(df)
        df = self._normalize_currency_values(df)
        
        # Step 3: Validation (collect errors for user review)
        self._validate_required_columns(df)
        
        # Only validate data if we have required columns
        if not self.validation_report.has_errors():
            self._validate_required_fields(df)
            self._validate_data_types(df)
            self._validate_business_rules(df)
        
        # Store results
        self.cleaned_df = df
        
        return df, self.validation_report
    
    def get_cleaned_dataframe(self) -> pd.DataFrame:
        """Get the cleaned DataFrame (after running clean_and_validate)"""
        if self.cleaned_df is None:
            raise RuntimeError("Must call clean_and_validate() first")
        return self.cleaned_df
    
    def get_validation_errors_as_dict(self) -> Dict[str, List[str]]:
        """
        Get validation errors organized by type for UI display.
        
        Returns:
            Dict with error types as keys and lists of messages as values
        """
        errors_by_type = {}
        
        for error in self.validation_report.errors:
            if error.error_type not in errors_by_type:
                errors_by_type[error.error_type] = []
            errors_by_type[error.error_type].append(error.message)
        
        return errors_by_type
