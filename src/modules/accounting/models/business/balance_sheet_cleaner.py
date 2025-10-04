"""
Balance Sheet Data Cleaning & Validation

Cleans and validates account balance CSVs for balance sheet generation.
Expected columns:
 - Account Name
 - Account Type (Cash CNY, Cash USD, Investment, Long-Term Investment)
 - CNY
 - USD
"""

from dataclasses import dataclass
from typing import Tuple, List, Dict
import logging
import re
import pandas as pd

from .data_cleaner import ValidationReport, ValidationError, CleaningAction


logger = logging.getLogger(__name__)


ALLOWED_ACCOUNT_TYPES = {
    'Cash CNY',
    'Cash USD',
    'Investment',
    'Long-Term Investment',
}


@dataclass
class BalanceSheetSchema:
    required_columns: List[str] = (
        'Account Name', 'Account Type', 'CNY', 'USD'
    )
    # Column name variations that should be normalized
    column_mappings: Dict[str, str] = None
    
    def __post_init__(self):
        if self.column_mappings is None:
            self.column_mappings = {
                # Account Name variations
                'Account': 'Account Name',
                'account': 'Account Name',
                'Account Name': 'Account Name',
                'account name': 'Account Name',
                'Name': 'Account Name',
                'name': 'Account Name',
                
                # Account Type variations  
                'Account Type': 'Account Type',
                'account type': 'Account Type',
                'Type': 'Account Type',
                'type': 'Account Type',
                'AccountType': 'Account Type',
                
                # Currency columns are usually consistent
                'CNY': 'CNY',
                'cny': 'CNY',
                'USD': 'USD',
                'usd': 'USD'
            }


class BalanceSheetDataCleaner:
    """Cleaner/validator for balance sheet CSVs."""

    def __init__(self, csv_file_path: str | None = None, dataframe: pd.DataFrame | None = None):
        if csv_file_path is None and dataframe is None:
            raise ValueError("Must provide either csv_file_path or dataframe")
        self.csv_file_path = csv_file_path
        self._raw_df = dataframe
        self.cleaned_df: pd.DataFrame | None = None
        self.validation_report = ValidationReport()

    def _load_csv(self) -> pd.DataFrame:
        try:
            return pd.read_csv(self.csv_file_path, encoding='utf-8-sig')
        except pd.errors.EmptyDataError:
            return pd.DataFrame()
        except Exception as e:
            raise Exception(f"Error reading CSV file: {e}")

    def _remove_empty_rows_and_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        original_rows = len(df)
        original_cols = len(df.columns)

        df_before_empty_rows = df.copy()
        df = df.dropna(how='all')
        empty_rows_removed = len(df_before_empty_rows) - len(df)
        if empty_rows_removed > 0:
            self.validation_report.cleaning_actions.append(
                CleaningAction(
                    action_type="remove_empty_rows",
                    description="Removed completely empty rows",
                    count=empty_rows_removed,
                    details="Rows with all NaN/empty values",
                )
            )

        df_before_empty_cols = df.copy()
        df = df.dropna(axis=1, how='all')
        empty_cols_removed = len(df_before_empty_cols.columns) - len(df.columns)
        if empty_cols_removed > 0:
            self.validation_report.cleaning_actions.append(
                CleaningAction(
                    action_type="remove_empty_columns",
                    description="Removed completely empty columns",
                    count=empty_cols_removed,
                    details="Columns with all NaN/empty values",
                )
            )

        if empty_rows_removed > 0 or empty_cols_removed > 0:
            logger.info(
                f"Data cleaning summary: {original_rows}→{len(df)} rows, "
                f"{original_cols}→{len(df.columns)} columns",
            )
        return df

    def _normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names to standard schema."""
        schema = BalanceSheetSchema()
        original_columns = df.columns.tolist()
        new_columns = []
        normalized_count = 0
        
        for col in df.columns:
            stripped_col = str(col).strip()
            if stripped_col in schema.column_mappings:
                normalized_col = schema.column_mappings[stripped_col]
                new_columns.append(normalized_col)
                if normalized_col != stripped_col:
                    normalized_count += 1
            else:
                new_columns.append(stripped_col)
        
        df.columns = new_columns
        
        if normalized_count > 0:
            self.validation_report.cleaning_actions.append(
                CleaningAction(
                    action_type="normalize_column_names",
                    description="Normalized column names",
                    count=normalized_count,
                    details=f"Mapped variations like 'Account' → 'Account Name'",
                )
            )
        
        return df

    def _strip_whitespace(self, df: pd.DataFrame) -> pd.DataFrame:
        # String values only (columns already handled in _normalize_column_names)
        whitespace_cleaned = 0
        for col in df.columns:
            if df[col].dtype == 'object':
                before = df[col].copy()
                df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
                whitespace_cleaned += sum(
                    1 for a, b in zip(before, df[col])
                    if isinstance(a, str) and isinstance(b, str) and a != b
                )
        if whitespace_cleaned > 0:
            self.validation_report.cleaning_actions.append(
                CleaningAction(
                    action_type="clean_whitespace",
                    description="Cleaned text whitespace",
                    count=whitespace_cleaned,
                    details="Removed leading/trailing spaces from text fields",
                )
            )
        return df

    def _normalize_currency_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        currency_cleaned_count = 0

        def clean_amount(value):
            nonlocal currency_cleaned_count
            if pd.isna(value) or value == '':
                return value
            original = str(value)
            cleaned = re.sub(r'[¥￥$,\s]', '', original)
            if cleaned != original:
                currency_cleaned_count += 1
            try:
                return float(cleaned)
            except ValueError:
                return value

        if 'CNY' in df.columns:
            df['CNY'] = df['CNY'].apply(clean_amount)
        if 'USD' in df.columns:
            df['USD'] = df['USD'].apply(clean_amount)

        if currency_cleaned_count > 0:
            self.validation_report.cleaning_actions.append(
                CleaningAction(
                    action_type="normalize_currency",
                    description="Normalized currency symbols for CNY/USD",
                    count=currency_cleaned_count,
                    details="Removed ¥, $, commas",
                )
            )
        return df

    def _validate_required_columns(self, df: pd.DataFrame) -> None:
        schema = BalanceSheetSchema()
        missing = [c for c in schema.required_columns if c not in df.columns]
        if missing:
            self.validation_report.errors.append(
                ValidationError(
                    row_number=0,
                    column=", ".join(missing),
                    error_type="missing_column",
                    message=f"Missing required columns: {', '.join(missing)}",
                )
            )

    def _validate_required_fields(self, df: pd.DataFrame) -> None:
        for idx, row in df.iterrows():
            name = row.get('Account Name', '')
            acc_type = row.get('Account Type', '')
            if pd.isna(name) or str(name).strip() == '':
                self.validation_report.errors.append(
                    ValidationError(
                        row_number=idx + 2,
                        column='Account Name',
                        error_type='missing_required_field',
                        message=f"Row {idx + 2}: Missing Account Name",
                    )
                )
            if pd.isna(acc_type) or str(acc_type).strip() == '':
                self.validation_report.errors.append(
                    ValidationError(
                        row_number=idx + 2,
                        column='Account Type',
                        error_type='missing_required_field',
                        message=f"Row {idx + 2}: Missing Account Type",
                    )
                )

    def _validate_data_types(self, df: pd.DataFrame) -> None:
        for idx, row in df.iterrows():
            for col in ['CNY', 'USD']:
                val = row.get(col)
                if pd.isna(val) or val == '' or val == '-':
                    continue
                try:
                    float(val)
                except (ValueError, TypeError):
                    self.validation_report.errors.append(
                        ValidationError(
                            row_number=idx + 2,
                            column=col,
                            error_type='invalid_data_type',
                            message=f"Row {idx + 2}: {col} must be numeric (got '{val}')",
                        )
                    )

    def _validate_business_rules(self, df: pd.DataFrame) -> None:
        for idx, row in df.iterrows():
            cny = row.get('CNY')
            usd = row.get('USD')
            if (pd.isna(cny) or cny in ['', '-'] or float(cny) == 0.0) and (
                pd.isna(usd) or usd in ['', '-'] or float(usd) == 0.0
            ):
                self.validation_report.errors.append(
                    ValidationError(
                        row_number=idx + 2,
                        column='CNY/USD',
                        error_type='missing_required_field',
                        message=f"Row {idx + 2}: At least one of CNY or USD must be provided",
                    )
                )

            acc_type = str(row.get('Account Type', '')).strip()
            if acc_type and acc_type not in ALLOWED_ACCOUNT_TYPES:
                self.validation_report.warnings.append(
                    ValidationError(
                        row_number=idx + 2,
                        column='Account Type',
                        error_type='invalid_value',
                        message=f"Row {idx + 2}: Account Type '{acc_type}' is not in allowed types",
                    )
                )

    def clean_and_validate(self) -> Tuple[pd.DataFrame, ValidationReport]:
        if self._raw_df is None:
            self._raw_df = self._load_csv()

        df = self._raw_df.copy()
        df = self._remove_empty_rows_and_columns(df)
        df = self._normalize_column_names(df)  # Normalize column names before validation
        df = self._strip_whitespace(df)
        self._validate_required_columns(df)

        # Only proceed with column-specific ops if columns exist
        if not self.validation_report.has_errors():
            df = self._normalize_currency_columns(df)
            self._validate_required_fields(df)
            self._validate_data_types(df)
            self._validate_business_rules(df)

        self.cleaned_df = df
        return df, self.validation_report


