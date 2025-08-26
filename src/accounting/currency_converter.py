"""
Currency Conversion Utilities for Accounting Module

Handles USD/CNY conversion for dual-currency financial statements.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional
from datetime import datetime

from .models import ExchangeRate, MonthlyAsset


class CurrencyConverter:
    """
    Utility class for currency conversion operations
    """
    
    def __init__(self, exchange_rate: ExchangeRate):
        self.exchange_rate = exchange_rate
    
    def cny_to_usd(self, cny_amount: Decimal) -> Decimal:
        """Convert CNY to USD with proper rounding"""
        usd_amount = cny_amount / self.exchange_rate.rate
        return usd_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def usd_to_cny(self, usd_amount: Decimal) -> Decimal:
        """Convert USD to CNY with proper rounding"""
        cny_amount = usd_amount * self.exchange_rate.rate
        return cny_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def normalize_asset_currencies(self, assets: List[MonthlyAsset]) -> List[MonthlyAsset]:
        """
        Normalize asset currencies - if either CNY or USD is missing, calculate from the other
        
        Args:
            assets: List of MonthlyAsset objects
            
        Returns:
            List of MonthlyAsset objects with both currencies populated
        """
        normalized_assets = []
        
        for asset in assets:
            cny_balance = asset.cny_balance
            usd_balance = asset.usd_balance
            
            # If CNY is 0 but USD has value, calculate CNY from USD
            if cny_balance == 0 and usd_balance > 0:
                cny_balance = self.usd_to_cny(usd_balance)
            
            # If USD is 0 but CNY has value, calculate USD from CNY
            elif usd_balance == 0 and cny_balance > 0:
                usd_balance = self.cny_to_usd(cny_balance)
            
            # Create normalized asset
            normalized_asset = MonthlyAsset(
                account_name=asset.account_name,
                cny_balance=cny_balance,
                usd_balance=usd_balance,
                asset_class=asset.asset_class,
                as_of_date=asset.as_of_date
            )
            normalized_assets.append(normalized_asset)
        
        return normalized_assets
    
    def calculate_totals_by_class(self, assets: List[MonthlyAsset]) -> Dict[str, Dict[str, Decimal]]:
        """
        Calculate total balances by asset class in both currencies
        
        Args:
            assets: List of MonthlyAsset objects
            
        Returns:
            Dictionary with asset class totals: {class: {'cny': total, 'usd': total}}
        """
        totals = {}
        
        for asset in assets:
            asset_class = asset.asset_class
            
            if asset_class not in totals:
                totals[asset_class] = {'cny': Decimal('0'), 'usd': Decimal('0')}
            
            totals[asset_class]['cny'] += asset.cny_balance
            totals[asset_class]['usd'] += asset.usd_balance
        
        return totals
    
    def format_currency_amount(self, amount: Decimal, currency: str, include_symbol: bool = True) -> str:
        """
        Format currency amount for display
        
        Args:
            amount: Decimal amount
            currency: 'CNY' or 'USD'
            include_symbol: Whether to include currency symbol
            
        Returns:
            Formatted string (e.g., "¥1,234.56" or "$1,234.56")
        """
        # Format with commas and 2 decimal places
        formatted_amount = f"{amount:,.2f}"
        
        if include_symbol:
            if currency == 'CNY':
                return f"¥{formatted_amount}"
            elif currency == 'USD':
                return f"${formatted_amount}"
        
        return formatted_amount
    
    def get_conversion_summary(self) -> Dict[str, str]:
        """
        Get summary information about the current exchange rate
        
        Returns:
            Dictionary with conversion rate and date information
        """
        return {
            'rate': str(self.exchange_rate.rate),
            'date': self.exchange_rate.date.strftime('%Y-%m-%d'),
            'description': f"1 USD = {self.exchange_rate.rate} CNY"
        }


def load_exchange_rate_from_file(file_path: str, date: datetime) -> ExchangeRate:
    """
    Helper function to load exchange rate from text file
    
    Args:
        file_path: Path to text file containing exchange rate
        date: Date for the exchange rate
        
    Returns:
        ExchangeRate object
    """
    return ExchangeRate.from_text_file(file_path, date)


def create_currency_converter(exchange_rate_file: str, date: datetime) -> CurrencyConverter:
    """
    Helper function to create CurrencyConverter from exchange rate file
    
    Args:
        exchange_rate_file: Path to exchange rate text file
        date: Date for the exchange rate
        
    Returns:
        CurrencyConverter object
    """
    exchange_rate = load_exchange_rate_from_file(exchange_rate_file, date)
    return CurrencyConverter(exchange_rate)