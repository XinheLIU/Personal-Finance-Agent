"""
Simplified balance sheet generation

Based on the example implementation with straightforward asset categorization and dual-currency support.
"""

import pandas as pd
from typing import Dict, Any
from decimal import Decimal, ROUND_HALF_UP


class BalanceSheetGenerator:
    """A class to generate balance sheet from account data CSV files."""
    
    def __init__(self, exchange_rate: float = 7.0):
        """
        Initialize the balance sheet generator.
        
        Args:
            exchange_rate (float): CNY to USD exchange rate (default: 7 CNY = 1 USD)
        """
        self.exchange_rate = exchange_rate
        self.account_categories = {
            'Cash CNY': 'Current Assets - Cash',
            'Cash USD': 'Current Assets - Cash',
            'Investment': 'Current Assets - Investments',
            'Long-Term Investment': 'Fixed Assets - Long-term investments'
        }
    
    def clean_currency_value(self, value: str) -> float:
        """Clean and convert currency string to float."""
        if pd.isna(value) or value == '' or value == '-':
            return 0.0
        
        # Remove currency symbols and formatting
        cleaned = str(value).replace('¥', '').replace('$', '').replace(',', '').strip()
        
        # Handle empty or dash values
        if cleaned == '' or cleaned == '-':
            return 0.0
        
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    
    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Convert amount between CNY and USD."""
        if from_currency == to_currency:
            return amount
        
        if from_currency == 'CNY' and to_currency == 'USD':
            return amount / self.exchange_rate
        elif from_currency == 'USD' and to_currency == 'CNY':
            return amount * self.exchange_rate
        
        return amount
    
    def format_currency(self, amount: float, currency: str) -> str:
        """Format currency amount for display."""
        if amount == 0:
            return f"{'¥' if currency == 'CNY' else '$'}0.00"
        
        # Round to 2 decimal places
        rounded_amount = float(Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        
        if currency == 'CNY':
            return f"¥{rounded_amount:,.2f}"
        else:
            return f"${rounded_amount:,.2f}"
    
    def process_accounts_data(self, csv_file: str) -> pd.DataFrame:
        """Process the input CSV file and calculate missing currency values."""
        # Read CSV file
        df = pd.read_csv(csv_file)
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Clean currency columns
        df['CNY_clean'] = df['CNY'].apply(self.clean_currency_value)
        df['USD_clean'] = df['USD'].apply(self.clean_currency_value)
        
        # Fill missing values based on exchange rate
        for index, row in df.iterrows():
            cny_val = row['CNY_clean']
            usd_val = row['USD_clean']
            
            if cny_val == 0 and usd_val > 0:
                # Convert USD to CNY
                df.at[index, 'CNY_clean'] = self.convert_currency(usd_val, 'USD', 'CNY')
            elif usd_val == 0 and cny_val > 0:
                # Convert CNY to USD
                df.at[index, 'USD_clean'] = self.convert_currency(cny_val, 'CNY', 'USD')
        
        return df
    
    def categorize_accounts(self, df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Categorize accounts and sum amounts by category."""
        categories = {
            'Current Assets - Cash': {'CNY': 0.0, 'USD': 0.0},
            'Current Assets - Investments': {'CNY': 0.0, 'USD': 0.0},
            'Current Assets - Other': {'CNY': 0.0, 'USD': 0.0},
            'Fixed Assets - Long-term investments': {'CNY': 0.0, 'USD': 0.0}
        }
        
        for _, row in df.iterrows():
            account_type = str(row.get('Account Type', '')).strip()
            cny_amount = row['CNY_clean']
            usd_amount = row['USD_clean']
            
            # Map account type to category
            if account_type in ['Cash CNY', 'Cash USD']:
                category = 'Current Assets - Cash'
            elif account_type == 'Investment':
                category = 'Current Assets - Investments'
            elif account_type == 'Long-Term Investment':
                category = 'Fixed Assets - Long-term investments'
            else:
                category = 'Current Assets - Other'
            
            categories[category]['CNY'] += cny_amount
            categories[category]['USD'] += usd_amount
        
        return categories
    
    def generate_statement(self, csv_file: str) -> Dict[str, Any]:
        """Generate balance sheet statement from CSV file."""
        # Process input data
        df = self.process_accounts_data(csv_file)
        
        # Categorize accounts
        categories = self.categorize_accounts(df)
        
        # Calculate totals
        total_current_cny = (categories['Current Assets - Cash']['CNY'] + 
                           categories['Current Assets - Investments']['CNY'] + 
                           categories['Current Assets - Other']['CNY'])
        total_current_usd = (categories['Current Assets - Cash']['USD'] + 
                           categories['Current Assets - Investments']['USD'] + 
                           categories['Current Assets - Other']['USD'])
        
        total_assets_cny = total_current_cny + categories['Fixed Assets - Long-term investments']['CNY']
        total_assets_usd = total_current_usd + categories['Fixed Assets - Long-term investments']['USD']
        
        # Create balance sheet structure
        balance_sheet = {
            'Current Assets': {
                'Cash': {
                    'CNY': categories['Current Assets - Cash']['CNY'],
                    'USD': categories['Current Assets - Cash']['USD']
                },
                'Investments': {
                    'CNY': categories['Current Assets - Investments']['CNY'],
                    'USD': categories['Current Assets - Investments']['USD']
                },
                'Other': {
                    'CNY': categories['Current Assets - Other']['CNY'],
                    'USD': categories['Current Assets - Other']['USD']
                },
                'Total Current Assets': {
                    'CNY': total_current_cny,
                    'USD': total_current_usd
                }
            },
            'Fixed Assets': {
                'Long-term Investments': {
                    'CNY': categories['Fixed Assets - Long-term investments']['CNY'],
                    'USD': categories['Fixed Assets - Long-term investments']['USD']
                },
                'Total Fixed Assets': {
                    'CNY': categories['Fixed Assets - Long-term investments']['CNY'],
                    'USD': categories['Fixed Assets - Long-term investments']['USD']
                }
            },
            'Total Assets': {
                'CNY': total_assets_cny,
                'USD': total_assets_usd
            }
        }
        
        return balance_sheet


def print_balance_sheet(statement: Dict[str, Any]):
    """Print formatted balance sheet"""
    print(f"\n{'='*50}")
    print(f"BALANCE SHEET")
    print(f"{'='*50}")
    
    print("\nASSETS:")
    print("\nCurrent Assets:")
    print(f"                        CNY        USD")
    print(f"  Cash:                ¥{statement['Current Assets']['Cash']['CNY']:,.2f}   ${statement['Current Assets']['Cash']['USD']:,.2f}")
    print(f"  Investments:         ¥{statement['Current Assets']['Investments']['CNY']:,.2f}   ${statement['Current Assets']['Investments']['USD']:,.2f}")
    if statement['Current Assets']['Other']['CNY'] > 0 or statement['Current Assets']['Other']['USD'] > 0:
        print(f"  Other:               ¥{statement['Current Assets']['Other']['CNY']:,.2f}   ${statement['Current Assets']['Other']['USD']:,.2f}")
    print(f"  {'─'*40}")
    print(f"  Total Current:       ¥{statement['Current Assets']['Total Current Assets']['CNY']:,.2f}   ${statement['Current Assets']['Total Current Assets']['USD']:,.2f}")
    
    print("\nFixed Assets:")
    print(f"  Long-term Invest:    ¥{statement['Fixed Assets']['Long-term Investments']['CNY']:,.2f}   ${statement['Fixed Assets']['Long-term Investments']['USD']:,.2f}")
    print(f"  {'─'*40}")
    print(f"  Total Fixed:         ¥{statement['Fixed Assets']['Total Fixed Assets']['CNY']:,.2f}   ${statement['Fixed Assets']['Total Fixed Assets']['USD']:,.2f}")
    
    print(f"\nTOTAL ASSETS:          ¥{statement['Total Assets']['CNY']:,.2f}   ${statement['Total Assets']['USD']:,.2f}")
    print(f"{'='*50}")