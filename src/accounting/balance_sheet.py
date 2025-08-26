"""
Balance Sheet Generation for Professional Accounting Module

This module provides balance sheet generation from transaction and asset data,
implementing standard accounting practices with assets, liabilities, and equity.
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from collections import defaultdict

from .models import Transaction, Asset, MonthlyAsset


class BalanceSheetGenerator:
    """
    Enhanced balance sheet generator for monthly workflow
    
    Generates professional balance sheets with:
    - Dual currency support (CNY/USD)
    - Multi-user owner equity
    - Professional accounting format
    """
    
    def __init__(self, currency_converter):
        """
        Initialize with currency converter
        
        Args:
            currency_converter: CurrencyConverter instance for USD/CNY conversion
        """
        self.currency_converter = currency_converter
    
    def generate_balance_sheet(
        self, 
        assets: List['MonthlyAsset'],
        owner_equity: Dict[str, Decimal],
        as_of_date: date
    ) -> Dict[str, Any]:
        """
        Generate balance sheet from monthly assets and owner equity
        
        Args:
            assets: List of MonthlyAsset objects
            owner_equity: Dictionary of owner name -> equity amount (in CNY)
            as_of_date: Date for balance sheet
            
        Returns:
            Dict containing complete balance sheet data with dual currency
        """
        
        # Normalize assets to ensure both currencies are populated
        normalized_assets = self.currency_converter.normalize_asset_currencies(assets)
        
        # Calculate totals by asset class
        asset_totals = self.currency_converter.calculate_totals_by_class(normalized_assets)
        
        # Categorize assets into balance sheet sections
        current_assets_cny = Decimal('0')
        current_assets_usd = Decimal('0')
        fixed_assets_cny = Decimal('0')
        fixed_assets_usd = Decimal('0')
        
        current_assets_detail = {}
        fixed_assets_detail = {}
        
        for asset_class, totals in asset_totals.items():
            if asset_class == 'Cash':
                current_assets_cny += totals['cny']
                current_assets_usd += totals['usd']
                current_assets_detail['Cash'] = {
                    'cny': self.currency_converter.format_currency_amount(totals['cny'], 'CNY'),
                    'usd': self.currency_converter.format_currency_amount(totals['usd'], 'USD')
                }
            elif asset_class == 'Investments':
                current_assets_cny += totals['cny']
                current_assets_usd += totals['usd']
                current_assets_detail['Investments'] = {
                    'cny': self.currency_converter.format_currency_amount(totals['cny'], 'CNY'),
                    'usd': self.currency_converter.format_currency_amount(totals['usd'], 'USD')
                }
            elif asset_class == 'Long-term investments':
                fixed_assets_cny += totals['cny']
                fixed_assets_usd += totals['usd']
                fixed_assets_detail['Long-term investments'] = {
                    'cny': self.currency_converter.format_currency_amount(totals['cny'], 'CNY'),
                    'usd': self.currency_converter.format_currency_amount(totals['usd'], 'USD')
                }
        
        # Calculate total assets
        total_assets_cny = current_assets_cny + fixed_assets_cny
        total_assets_usd = current_assets_usd + fixed_assets_usd
        
        # Calculate total owner equity
        total_owner_equity_cny = sum(owner_equity.values())
        total_owner_equity_usd = self.currency_converter.cny_to_usd(total_owner_equity_cny)
        
        # Format owner equity
        formatted_owner_equity = {}
        for owner, equity_cny in owner_equity.items():
            equity_usd = self.currency_converter.cny_to_usd(equity_cny)
            formatted_owner_equity[owner] = {
                'cny': self.currency_converter.format_currency_amount(equity_cny, 'CNY'),
                'usd': self.currency_converter.format_currency_amount(equity_usd, 'USD')
            }
        
        return {
            'as_of_date': as_of_date.strftime('%Y-%m-%d'),
            'current_assets': current_assets_detail,
            'total_current_assets_cny': self.currency_converter.format_currency_amount(current_assets_cny, 'CNY'),
            'total_current_assets_usd': self.currency_converter.format_currency_amount(current_assets_usd, 'USD'),
            'fixed_assets': fixed_assets_detail,
            'total_fixed_assets_cny': self.currency_converter.format_currency_amount(fixed_assets_cny, 'CNY'),
            'total_fixed_assets_usd': self.currency_converter.format_currency_amount(fixed_assets_usd, 'USD'),
            'total_assets_cny': self.currency_converter.format_currency_amount(total_assets_cny, 'CNY'),
            'total_assets_usd': self.currency_converter.format_currency_amount(total_assets_usd, 'USD'),
            'current_liabilities': {},  # No liabilities in sample data
            'total_current_liabilities_cny': self.currency_converter.format_currency_amount(Decimal('0'), 'CNY'),
            'total_current_liabilities_usd': self.currency_converter.format_currency_amount(Decimal('0'), 'USD'),
            'owner_equity': formatted_owner_equity,
            'total_owner_equity_cny': self.currency_converter.format_currency_amount(total_owner_equity_cny, 'CNY'),
            'total_owner_equity_usd': self.currency_converter.format_currency_amount(total_owner_equity_usd, 'USD'),
            'exchange_rate': self.currency_converter.get_conversion_summary()
        }
    
    def extract_owner_equity_from_assets(self, assets: List['MonthlyAsset']) -> Dict[str, Decimal]:
        """
        Extract owner equity information from asset account names
        
        This is a heuristic based on the sample data where owner names appear in account names
        
        Args:
            assets: List of MonthlyAsset objects
            
        Returns:
            Dictionary of owner name -> total equity amount (in CNY)
        """
        owner_equity = {}
        
        # Sum all assets to get total equity (assuming no liabilities for now)
        total_equity_cny = sum(asset.cny_balance for asset in assets)
        
        # Extract owner information from account names (heuristic based on sample)
        owner_accounts = {}
        
        for asset in assets:
            account_name = asset.account_name.upper()
            
            # Look for owner indicators in account names
            if 'XH' in account_name:
                if 'XH' not in owner_accounts:
                    owner_accounts['XH'] = Decimal('0')
                owner_accounts['XH'] += asset.cny_balance
            elif 'YY' in account_name:
                if 'YY' not in owner_accounts:
                    owner_accounts['YY'] = Decimal('0')
                owner_accounts['YY'] += asset.cny_balance
        
        # If we found owner-specific accounts, use those
        if owner_accounts:
            return owner_accounts
        else:
            # Otherwise split equally (placeholder logic)
            return {
                'XH': total_equity_cny / 2,
                'YY': total_equity_cny / 2
            }


def generate_balance_sheet(transactions: List[Transaction], assets: List[Asset], as_of_date: date) -> Dict[str, Any]:
    """
    Convenience function to generate balance sheet
    
    Args:
        transactions: List of Transaction objects
        assets: List of Asset objects (can be empty)
        as_of_date: Date for balance sheet
        
    Returns:
        Dict containing complete balance sheet data
    """
    generator = BalanceSheetGenerator()
    return generator.generate_balance_sheet(transactions, assets or [], as_of_date)


def format_currency(amount: Decimal) -> str:
    """Format decimal amount as CNY currency"""
    return f"¥{amount:,.2f}"


def print_balance_sheet(balance_sheet_data: Dict[str, Any]) -> str:
    """
    Format balance sheet data for console output
    
    Args:
        balance_sheet_data: Balance sheet data from generate_balance_sheet()
        
    Returns:
        Formatted string representation of the balance sheet
    """
    data = balance_sheet_data
    output = []
    
    output.append(f"BALANCE SHEET - As of {data['as_of_date']}")
    output.append("=" * 50)
    
    # Assets section
    output.append("\nASSETS:")
    output.append(f"  Current Assets:")
    output.append(f"    Cash and Equivalents:     {format_currency(data['assets']['current_assets']['cash_and_equivalents'])}")
    output.append(f"    Accounts Receivable:      {format_currency(data['assets']['current_assets']['accounts_receivable'])}")
    output.append(f"    Total Current Assets:     {format_currency(data['assets']['current_assets']['total_current_assets'])}")
    
    output.append(f"  Fixed Assets:")
    output.append(f"    Investments:              {format_currency(data['assets']['fixed_assets']['investments'])}")
    output.append(f"    Equipment:                {format_currency(data['assets']['fixed_assets']['equipment'])}")
    output.append(f"    Total Fixed Assets:       {format_currency(data['assets']['fixed_assets']['total_fixed_assets'])}")
    
    output.append(f"  TOTAL ASSETS:               {format_currency(data['assets']['total_assets'])}")
    
    # Liabilities section
    output.append(f"\nLIABILITIES:")
    output.append(f"  Current Liabilities:")
    output.append(f"    Accounts Payable:         {format_currency(data['liabilities']['current_liabilities']['accounts_payable'])}")
    output.append(f"    Credit Cards:             {format_currency(data['liabilities']['current_liabilities']['credit_cards'])}")
    output.append(f"    Total Current Liab.:      {format_currency(data['liabilities']['current_liabilities']['total_current_liabilities'])}")
    
    output.append(f"  Long-term Liabilities:")
    output.append(f"    Loans:                    {format_currency(data['liabilities']['long_term_liabilities']['loans'])}")
    output.append(f"    Total Long-term Liab.:    {format_currency(data['liabilities']['long_term_liabilities']['total_long_term_liabilities'])}")
    
    output.append(f"  TOTAL LIABILITIES:          {format_currency(data['liabilities']['total_liabilities'])}")
    
    # Equity section
    output.append(f"\nOWNER'S EQUITY:")
    output.append(f"  Retained Earnings:          {format_currency(data['equity']['retained_earnings'])}")
    output.append(f"  TOTAL EQUITY:               {format_currency(data['equity']['total_equity'])}")
    
    output.append(f"\nTOTAL LIAB. & EQUITY:       {format_currency(data['total_liab_and_equity'])}")
    output.append("=" * 50)
    
    return "\n".join(output)