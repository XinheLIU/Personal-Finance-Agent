"""
Balance Sheet Presenter

Coordinates between balance sheet cleaner and generator.

Workflow:
1) Clean & validate balance sheet CSV (BalanceSheetDataCleaner)
2) Generate balance sheet (BalanceSheetGenerator)
"""

from typing import Tuple, Dict, Any
import pandas as pd

from ..models.business.balance_sheet_cleaner import BalanceSheetDataCleaner
from ..core.balance_sheet import BalanceSheetGenerator


class BalanceSheetPresenter:
    """Presenter for balance sheet generation workflow."""

    def __init__(self, exchange_rate: float = 7.0) -> None:
        self.generator = BalanceSheetGenerator(exchange_rate=exchange_rate)

    def clean_and_validate_csv(self, csv_file_path: str):
        cleaner = BalanceSheetDataCleaner(csv_file_path=csv_file_path)
        return cleaner.clean_and_validate()

    def process_clean_dataframe_and_generate_statement(self, cleaned_df: pd.DataFrame) -> Dict[str, Any]:
        # Generator currently expects a CSV path; extend it to support DataFrame directly if needed
        # Here we mimic the generator's internal flow using its public methods
        # to avoid rewriting file I/O.
        # Convert cleaned_df to the expected internal shape: ensure CNY_clean/USD_clean exist
        # by reusing generator's processing on a temp CSV is heavyweight; instead ensure columns match
        df = cleaned_df.copy()
        # If the generator relies on process_accounts_data, we will route via a temp CSV path.
        # For now, rely on generator.categorize_accounts expecting CNY_clean/USD_clean;
        # create them if absent using the generator's clean rules implicitly (cleaner already normalized)
        if 'CNY_clean' not in df.columns and 'CNY' in df.columns:
            df['CNY_clean'] = df['CNY'].fillna(0).astype(float)
        if 'USD_clean' not in df.columns and 'USD' in df.columns:
            df['USD_clean'] = df['USD'].fillna(0).astype(float)

        categories = self.generator.categorize_accounts(df)

        total_current_cny = (
            categories['Current Assets - Cash']['CNY']
            + categories['Current Assets - Investments']['CNY']
            + categories['Current Assets - Other']['CNY']
        )
        total_current_usd = (
            categories['Current Assets - Cash']['USD']
            + categories['Current Assets - Investments']['USD']
            + categories['Current Assets - Other']['USD']
        )
        total_assets_cny = total_current_cny + categories['Fixed Assets - Long-term investments']['CNY']
        total_assets_usd = total_current_usd + categories['Fixed Assets - Long-term investments']['USD']

        balance_sheet = {
            'Current Assets': {
                'Cash': {
                    'CNY': categories['Current Assets - Cash']['CNY'],
                    'USD': categories['Current Assets - Cash']['USD'],
                },
                'Investments': {
                    'CNY': categories['Current Assets - Investments']['CNY'],
                    'USD': categories['Current Assets - Investments']['USD'],
                },
                'Other': {
                    'CNY': categories['Current Assets - Other']['CNY'],
                    'USD': categories['Current Assets - Other']['USD'],
                },
                'Total Current Assets': {
                    'CNY': total_current_cny,
                    'USD': total_current_usd,
                },
            },
            'Fixed Assets': {
                'Long-term Investments': {
                    'CNY': categories['Fixed Assets - Long-term investments']['CNY'],
                    'USD': categories['Fixed Assets - Long-term investments']['USD'],
                },
                'Total Fixed Assets': {
                    'CNY': categories['Fixed Assets - Long-term investments']['CNY'],
                    'USD': categories['Fixed Assets - Long-term investments']['USD'],
                },
            },
            'Total Assets': {
                'CNY': total_assets_cny,
                'USD': total_assets_usd,
            },
        }

        return balance_sheet


