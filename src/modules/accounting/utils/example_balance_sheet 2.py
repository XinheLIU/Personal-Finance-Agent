import pandas as pd
import re
from typing import Dict, List, Tuple
from decimal import Decimal, ROUND_HALF_UP


class BalanceSheetGenerator:
    """
    A class to generate balance sheet from account data CSV files.
    """
    
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
        """
        Clean and convert currency string to float.
        
        Args:
            value (str): Currency value string
            
        Returns:
            float: Cleaned numeric value
        """
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
        """
        Convert amount between CNY and USD.
        
        Args:
            amount (float): Amount to convert
            from_currency (str): Source currency ('CNY' or 'USD')
            to_currency (str): Target currency ('CNY' or 'USD')
            
        Returns:
            float: Converted amount
        """
        if from_currency == to_currency:
            return amount
        
        if from_currency == 'CNY' and to_currency == 'USD':
            return amount / self.exchange_rate
        elif from_currency == 'USD' and to_currency == 'CNY':
            return amount * self.exchange_rate
        
        return amount
    
    def format_currency(self, amount: float, currency: str) -> str:
        """
        Format currency amount for display.
        
        Args:
            amount (float): Amount to format
            currency (str): Currency type ('CNY' or 'USD')
            
        Returns:
            str: Formatted currency string
        """
        if amount == 0:
            return f"{'¥' if currency == 'CNY' else '$'}0.00"
        
        # Round to 2 decimal places
        rounded_amount = float(Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        
        if currency == 'CNY':
            return f"¥{rounded_amount:,.2f}"
        else:
            return f"${rounded_amount:,.2f}"
    
    def process_accounts_data(self, csv_file: str) -> pd.DataFrame:
        """
        Process the input CSV file and calculate missing currency values.
        
        Args:
            csv_file (str): Path to input CSV file
            
        Returns:
            pd.DataFrame: Processed account data
        """
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
        """
        Categorize accounts and sum amounts by category.
        
        Args:
            df (pd.DataFrame): Processed account data
            
        Returns:
            Dict: Categorized account totals
        """
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
    
    def generate_balance_sheet_text(self, categories: Dict[str, Dict[str, float]]) -> str:
        """
        Generate formatted balance sheet text.
        
        Args:
            categories (Dict): Categorized account totals
            
        Returns:
            str: Formatted balance sheet
        """
        output_lines = ["**Assets**", "", ""]
        
        # Current Assets
        output_lines.extend([
            "Current assets:",
            "CNY\tUSD",
            f"Cash\t{self.format_currency(categories['Current Assets - Cash']['CNY'], 'CNY')}\t{self.format_currency(categories['Current Assets - Cash']['USD'], 'USD')}",
            f"Investments\t{self.format_currency(categories['Current Assets - Investments']['CNY'], 'CNY')}\t{self.format_currency(categories['Current Assets - Investments']['USD'], 'USD')}",
            f"Accounts receivable\t¥0.00\t$0.00",
            f"Pre-paid expenses\t¥0.00\t$0.00"
        ])
        
        # Add other current assets if any
        if categories['Current Assets - Other']['CNY'] > 0 or categories['Current Assets - Other']['USD'] > 0:
            output_lines.append(f"Other\t{self.format_currency(categories['Current Assets - Other']['CNY'], 'CNY')}\t{self.format_currency(categories['Current Assets - Other']['USD'], 'USD')}")
        else:
            output_lines.append("Other\t-\t$0.00")
        
        # Total current assets
        total_current_cny = (categories['Current Assets - Cash']['CNY'] + 
                           categories['Current Assets - Investments']['CNY'] + 
                           categories['Current Assets - Other']['CNY'])
        total_current_usd = (categories['Current Assets - Cash']['USD'] + 
                           categories['Current Assets - Investments']['USD'] + 
                           categories['Current Assets - Other']['USD'])
        
        output_lines.extend([
            f"Total current assets\t{self.format_currency(total_current_cny, 'CNY')}\t{self.format_currency(total_current_usd, 'USD')}",
            ""
        ])
        
        # Fixed Assets
        output_lines.extend([
            "Fixed assets:",
            "CNY\tUSD",
            f"Property and equipment\t¥0.00\t-",
            f"Long-term investments\t{self.format_currency(categories['Fixed Assets - Long-term investments']['CNY'], 'CNY')}\t{self.format_currency(categories['Fixed Assets - Long-term investments']['USD'], 'USD')}",
            f"Less accumulated depreciation\t¥0.00\t-",
            f"Total fixed assets\t{self.format_currency(categories['Fixed Assets - Long-term investments']['CNY'], 'CNY')}\t{self.format_currency(categories['Fixed Assets - Long-term investments']['USD'], 'USD')}",
            "", ""
        ])
        
        # Other Assets
        output_lines.extend([
            "Other assets:",
            "CNY\tUSD",
            "\t¥0.00\t-",
            "Total other assets\t¥0.00\t-",
            ""
        ])
        
        # Total Assets
        total_assets_cny = total_current_cny + categories['Fixed Assets - Long-term investments']['CNY']
        total_assets_usd = total_current_usd + categories['Fixed Assets - Long-term investments']['USD']
        
        output_lines.extend([
            "**Total assets**",
            f"**{self.format_currency(total_assets_cny, 'CNY')}**\t**{self.format_currency(total_assets_usd, 'USD')}**"
        ])
        
        return "\n".join(output_lines)
    
    def generate_balance_sheet_csv(self, categories: Dict[str, Dict[str, float]], output_file: str):
        """
        Generate balance sheet CSV file.
        
        Args:
            categories (Dict): Categorized account totals
            output_file (str): Output CSV file path
        """
        # Prepare data for CSV
        data = []
        
        # Current Assets
        data.extend([
            ["**Assets**", "", ""],
            ["", "", ""],
            ["Current assets:", "", ""],
            ["", "CNY", "USD"],
            ["Cash", self.format_currency(categories['Current Assets - Cash']['CNY'], 'CNY'), 
             self.format_currency(categories['Current Assets - Cash']['USD'], 'USD')],
            ["Investments", self.format_currency(categories['Current Assets - Investments']['CNY'], 'CNY'), 
             self.format_currency(categories['Current Assets - Investments']['USD'], 'USD')],
            ["Accounts receivable", "¥0.00", "$0.00"],
            ["Pre-paid expenses", "¥0.00", "$0.00"],
            ["Other", "-" if categories['Current Assets - Other']['CNY'] == 0 else self.format_currency(categories['Current Assets - Other']['CNY'], 'CNY'), 
             "$0.00" if categories['Current Assets - Other']['USD'] == 0 else self.format_currency(categories['Current Assets - Other']['USD'], 'USD')]
        ])
        
        # Total current assets
        total_current_cny = (categories['Current Assets - Cash']['CNY'] + 
                           categories['Current Assets - Investments']['CNY'] + 
                           categories['Current Assets - Other']['CNY'])
        total_current_usd = (categories['Current Assets - Cash']['USD'] + 
                           categories['Current Assets - Investments']['USD'] + 
                           categories['Current Assets - Other']['USD'])
        
        data.append(["Total current assets", self.format_currency(total_current_cny, 'CNY'), 
                    self.format_currency(total_current_usd, 'USD')])
        
        # Fixed Assets
        data.extend([
            ["", "", ""],
            ["Fixed assets:", "", ""],
            ["", "CNY", "USD"],
            ["Property and equipment", "¥0.00", "-"],
            ["Long-term investments", self.format_currency(categories['Fixed Assets - Long-term investments']['CNY'], 'CNY'), 
             self.format_currency(categories['Fixed Assets - Long-term investments']['USD'], 'USD')],
            ["Less accumulated depreciation", "¥0.00", "-"],
            ["Total fixed assets", self.format_currency(categories['Fixed Assets - Long-term investments']['CNY'], 'CNY'), 
             self.format_currency(categories['Fixed Assets - Long-term investments']['USD'], 'USD')]
        ])
        
        # Other Assets
        data.extend([
            ["", "", ""],
            ["Other assets:", "", ""],
            ["", "CNY", "USD"],
            ["", "¥0.00", "-"],
            ["Total other assets", "¥0.00", "-"]
        ])
        
        # Total Assets
        total_assets_cny = total_current_cny + categories['Fixed Assets - Long-term investments']['CNY']
        total_assets_usd = total_current_usd + categories['Fixed Assets - Long-term investments']['USD']
        
        data.extend([
            ["", "", ""],
            ["**Total assets**", f"**{self.format_currency(total_assets_cny, 'CNY')}**", 
             f"**{self.format_currency(total_assets_usd, 'USD')}**"]
        ])
        
        # Create DataFrame and save to CSV
        df_output = pd.DataFrame(data, columns=['Item', 'CNY', 'USD'])
        df_output.to_csv(output_file, index=False)
        print(f"Balance sheet saved to {output_file}")
    
    def generate_balance_sheet(self, input_csv: str, output_csv: str = "balance_sheet.csv") -> str:
        """
        Main method to generate balance sheet from input CSV.
        
        Args:
            input_csv (str): Input CSV file path
            output_csv (str): Output CSV file path
            
        Returns:
            str: Formatted balance sheet text
        """
        # Process input data
        df = self.process_accounts_data(input_csv)
        
        # Categorize accounts
        categories = self.categorize_accounts(df)
        
        # Generate balance sheet text
        balance_sheet_text = self.generate_balance_sheet_text(categories)
        
        # Generate CSV output
        self.generate_balance_sheet_csv(categories, output_csv)
        
        return balance_sheet_text


def main():
    """
    Main function to demonstrate usage.
    """
    # Example usage
    generator = BalanceSheetGenerator(exchange_rate=7.0)
    
    # Generate balance sheet
    try:
        balance_sheet = generator.generate_balance_sheet("assets.csv", "balance_sheet.csv")
        print("Generated Balance Sheet:")
        print("=" * 50)
        print(balance_sheet)
    except FileNotFoundError:
        print("Error: Input CSV not found.")
        print("Please make sure the file exists in the current directory.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()