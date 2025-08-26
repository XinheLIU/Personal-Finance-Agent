"""
Cash Flow Statement Generation for Professional Accounting Module

This module provides cash flow statement generation implementing the direct method,
categorizing cash flows into operating, investing, and financing activities.
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from collections import defaultdict

from .models import Transaction, MonthlyTransaction, EXPENSE_CATEGORIES


class CashFlowGenerator:
    """
    Professional cash flow statement generation service
    
    Generates cash flow statements using the direct method with:
    - Operating Activities (revenue collection, expense payments)
    - Investing Activities (asset purchases/sales, investments)
    - Financing Activities (loans, owner contributions/distributions)
    """
    
    def __init__(self):
        # Operating activities categories (revenue and operating expenses)
        self.operating_revenue_categories = ["工资收入", "服务收入", "其他收入"]
        self.operating_expense_categories = [
            "餐饮", "房租", "水电费", "交通", "日用购物", "保险", "医疗", 
            "教育", "娱乐", "通讯", "服装", "维修", "其他支出"
        ]
        
        # Investing activities categories
        self.investing_categories = ["投资收益", "投资支出", "设备购置", "资产出售"]
        
        # Financing activities categories
        self.financing_categories = ["贷款收入", "还贷支出", "股东投资", "分红支出"]
    
    def generate_cash_flow_statement(
        self, 
        transactions: List[Transaction], 
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Generate cash flow statement for specified period
        
        Args:
            transactions: List of Transaction objects
            start_date: Period start date
            end_date: Period end date
            
        Returns:
            Dict containing complete cash flow statement data
        """
        
        # Filter transactions for the period
        period_transactions = [
            t for t in transactions 
            if start_date <= t.date.date() <= end_date
        ]
        
        # Categorize cash flows
        operating_flows = self._calculate_operating_activities(period_transactions)
        investing_flows = self._calculate_investing_activities(period_transactions)
        financing_flows = self._calculate_financing_activities(period_transactions)
        
        # Calculate net cash flow
        net_operating = sum(operating_flows.values())
        net_investing = sum(investing_flows.values())
        net_financing = sum(financing_flows.values())
        net_cash_flow = net_operating + net_investing + net_financing
        
        return {
            'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'operating_activities': {
                'cash_received_from_customers': operating_flows.get('revenue', Decimal('0')),
                'cash_paid_to_suppliers': operating_flows.get('suppliers', Decimal('0')),
                'cash_paid_for_operating_expenses': operating_flows.get('operating_expenses', Decimal('0')),
                'cash_paid_for_rent': operating_flows.get('rent', Decimal('0')),
                'net_cash_from_operating': net_operating
            },
            'investing_activities': {
                'purchase_of_investments': investing_flows.get('investments_purchased', Decimal('0')),
                'sale_of_investments': investing_flows.get('investments_sold', Decimal('0')),
                'purchase_of_equipment': investing_flows.get('equipment_purchased', Decimal('0')),
                'net_cash_from_investing': net_investing
            },
            'financing_activities': {
                'proceeds_from_loans': financing_flows.get('loan_proceeds', Decimal('0')),
                'repayment_of_loans': financing_flows.get('loan_payments', Decimal('0')),
                'owner_contributions': financing_flows.get('owner_contributions', Decimal('0')),
                'owner_distributions': financing_flows.get('owner_distributions', Decimal('0')),
                'net_cash_from_financing': net_financing
            },
            'net_change_in_cash': net_cash_flow,
            'cash_at_beginning': Decimal('0'),  # Would need historical data
            'cash_at_end': net_cash_flow
        }
    
    def _calculate_operating_activities(self, transactions: List[Transaction]) -> Dict[str, Decimal]:
        """Calculate cash flows from operating activities"""
        flows = {
            'revenue': Decimal('0'),
            'suppliers': Decimal('0'),
            'operating_expenses': Decimal('0'),
            'rent': Decimal('0')
        }
        
        for transaction in transactions:
            if transaction.category in self.operating_revenue_categories:
                if transaction.amount > 0:
                    flows['revenue'] += transaction.amount
            elif transaction.category in self.operating_expense_categories:
                if transaction.amount < 0:  # Expenses are negative
                    if transaction.category == "房租":
                        flows['rent'] += transaction.amount  # Keep negative
                    elif transaction.category in ["日用购物", "餐饮"]:
                        flows['suppliers'] += transaction.amount  # Keep negative
                    else:
                        flows['operating_expenses'] += transaction.amount  # Keep negative
        
        return flows
    
    def _calculate_investing_activities(self, transactions: List[Transaction]) -> Dict[str, Decimal]:
        """Calculate cash flows from investing activities"""
        flows = {
            'investments_purchased': Decimal('0'),
            'investments_sold': Decimal('0'),
            'equipment_purchased': Decimal('0')
        }
        
        for transaction in transactions:
            if transaction.category in self.investing_categories:
                if transaction.category == "投资支出" and transaction.amount < 0:
                    flows['investments_purchased'] += transaction.amount  # Keep negative
                elif transaction.category == "投资收益" and transaction.amount > 0:
                    flows['investments_sold'] += transaction.amount
                elif transaction.category == "设备购置" and transaction.amount < 0:
                    flows['equipment_purchased'] += transaction.amount  # Keep negative
            # Also catch any transactions that mention investment/equipment in description
            elif any(keyword in transaction.description.lower() for keyword in ['投资', '股票', '基金', '设备']):
                if transaction.amount < 0:
                    if any(keyword in transaction.description.lower() for keyword in ['设备', '电脑', '办公']):
                        flows['equipment_purchased'] += transaction.amount
                    else:
                        flows['investments_purchased'] += transaction.amount
                else:
                    flows['investments_sold'] += transaction.amount
        
        return flows
    
    def _calculate_financing_activities(self, transactions: List[Transaction]) -> Dict[str, Decimal]:
        """Calculate cash flows from financing activities"""
        flows = {
            'loan_proceeds': Decimal('0'),
            'loan_payments': Decimal('0'),
            'owner_contributions': Decimal('0'),
            'owner_distributions': Decimal('0')
        }
        
        for transaction in transactions:
            if transaction.category in self.financing_categories:
                if transaction.category == "贷款收入" and transaction.amount > 0:
                    flows['loan_proceeds'] += transaction.amount
                elif transaction.category == "还贷支出" and transaction.amount < 0:
                    flows['loan_payments'] += transaction.amount  # Keep negative
                elif transaction.category == "股东投资" and transaction.amount > 0:
                    flows['owner_contributions'] += transaction.amount
                elif transaction.category == "分红支出" and transaction.amount < 0:
                    flows['owner_distributions'] += transaction.amount  # Keep negative
            # Also catch loan-related transactions by description
            elif any(keyword in transaction.description.lower() for keyword in ['贷款', '还款', 'loan']):
                if transaction.amount > 0:
                    flows['loan_proceeds'] += transaction.amount
                else:
                    flows['loan_payments'] += transaction.amount
        
        return flows

    
    def generate_cash_flow_statement_from_monthly_transactions(
        self, 
        transactions: List[MonthlyTransaction], 
        month: int,
        year: int,
        currency_converter=None
    ) -> Dict[str, Any]:
        """
        Generate cash flow statement from MonthlyTransaction objects
        
        This method is designed for the new monthly workflow
        
        Args:
            transactions: List of MonthlyTransaction objects
            month: Target month (1-12)
            year: Target year
            currency_converter: Optional CurrencyConverter for dual-currency display
            
        Returns:
            Dict containing complete cash flow statement data
        """
        # Filter transactions for the specific month
        month_transactions = [
            t for t in transactions 
            if t.date.month == month and t.date.year == year
        ]
        
        return self._build_cash_flow_from_monthly_transactions(
            month_transactions, f"{year}-{month:02d}", currency_converter
        )
    
    def _build_cash_flow_from_monthly_transactions(
        self, 
        transactions: List[MonthlyTransaction], 
        period: str,
        currency_converter=None
    ) -> Dict[str, Any]:
        """
        Build cash flow statement from MonthlyTransaction objects
        
        Args:
            transactions: List of MonthlyTransaction objects
            period: Period description (e.g., "2024-01")
            currency_converter: Optional CurrencyConverter for dual-currency display
            
        Returns:
            Complete cash flow statement dictionary
        """
        # Categorize cash flows
        operating_flows = self._calculate_operating_activities_monthly(transactions)
        investing_flows = self._calculate_investing_activities_monthly(transactions)
        financing_flows = self._calculate_financing_activities_monthly(transactions)
        
        # Calculate net cash flows
        net_operating = sum(operating_flows.values())
        net_investing = sum(investing_flows.values())
        net_financing = sum(financing_flows.values())
        net_change_in_cash = net_operating + net_investing + net_financing
        
        # Build cash flow statement following professional format
        return {
            'period': period,
            'operating_activities': {
                'Cash received from customers': self._format_cash_amount(operating_flows.get('revenue', Decimal('0')), currency_converter),
                'Cash paid for operating expenses': self._format_cash_amount(operating_flows.get('operating_expenses', Decimal('0')), currency_converter),
                'Cash paid for rent': self._format_cash_amount(operating_flows.get('rent', Decimal('0')), currency_converter),
                'Cash paid to suppliers': self._format_cash_amount(operating_flows.get('suppliers', Decimal('0')), currency_converter),
            },
            'net_operating_cash': self._format_cash_amount(net_operating, currency_converter),
            'investing_activities': {
                'Purchase of investments': self._format_cash_amount(investing_flows.get('investments_purchased', Decimal('0')), currency_converter),
                'Sale of investments': self._format_cash_amount(investing_flows.get('investments_sold', Decimal('0')), currency_converter),
                'Purchase of equipment': self._format_cash_amount(investing_flows.get('equipment_purchased', Decimal('0')), currency_converter),
            },
            'net_investing_cash': self._format_cash_amount(net_investing, currency_converter),
            'financing_activities': {
                'Proceeds from loans': self._format_cash_amount(financing_flows.get('loan_proceeds', Decimal('0')), currency_converter),
                'Repayment of loans': self._format_cash_amount(financing_flows.get('loan_payments', Decimal('0')), currency_converter),
                'Owner contributions': self._format_cash_amount(financing_flows.get('owner_contributions', Decimal('0')), currency_converter),
                'Owner distributions': self._format_cash_amount(financing_flows.get('owner_distributions', Decimal('0')), currency_converter),
            },
            'net_financing_cash': self._format_cash_amount(net_financing, currency_converter),
            'net_change_in_cash': self._format_cash_amount(net_change_in_cash, currency_converter),
            'beginning_cash': self._format_cash_amount(Decimal('0'), currency_converter),  # Would need prior period data
            'ending_cash': self._format_cash_amount(net_change_in_cash, currency_converter),
            'currency': 'CNY',
            'generated_at': datetime.now(),
            'transaction_count': len(transactions)
        }
    
    def _calculate_operating_activities_monthly(self, transactions: List[MonthlyTransaction]) -> Dict[str, Decimal]:
        """Calculate cash flows from operating activities for monthly transactions"""
        flows = {
            'revenue': Decimal('0'),
            'suppliers': Decimal('0'),
            'operating_expenses': Decimal('0'),
            'rent': Decimal('0')
        }
        
        for transaction in transactions:
            if transaction.category in self.operating_revenue_categories:
                if transaction.amount > 0:
                    flows['revenue'] += transaction.amount
            elif transaction.category in self.operating_expense_categories:
                if transaction.amount < 0:  # Expenses are negative
                    if transaction.category == "房租":
                        flows['rent'] += transaction.amount  # Keep negative
                    elif transaction.category in ["日用购物", "餐饮"]:
                        flows['suppliers'] += transaction.amount  # Keep negative
                    else:
                        flows['operating_expenses'] += transaction.amount  # Keep negative
        
        return flows
    
    def _calculate_investing_activities_monthly(self, transactions: List[MonthlyTransaction]) -> Dict[str, Decimal]:
        """Calculate cash flows from investing activities for monthly transactions"""
        flows = {
            'investments_purchased': Decimal('0'),
            'investments_sold': Decimal('0'),
            'equipment_purchased': Decimal('0')
        }
        
        for transaction in transactions:
            if transaction.category in self.investing_categories:
                if transaction.category == "投资支出" and transaction.amount < 0:
                    flows['investments_purchased'] += transaction.amount  # Keep negative
                elif transaction.category == "投资收益" and transaction.amount > 0:
                    flows['investments_sold'] += transaction.amount
                elif transaction.category == "设备购置" and transaction.amount < 0:
                    flows['equipment_purchased'] += transaction.amount  # Keep negative
            # Also catch any transactions that mention investment/equipment in description
            elif any(keyword in transaction.description.lower() for keyword in ['投资', '股票', '基金', '设备']):
                if transaction.amount < 0:
                    if any(keyword in transaction.description.lower() for keyword in ['设备', '电脑', '办公']):
                        flows['equipment_purchased'] += transaction.amount
                    else:
                        flows['investments_purchased'] += transaction.amount
                else:
                    flows['investments_sold'] += transaction.amount
        
        return flows
    
    def _calculate_financing_activities_monthly(self, transactions: List[MonthlyTransaction]) -> Dict[str, Decimal]:
        """Calculate cash flows from financing activities for monthly transactions"""
        flows = {
            'loan_proceeds': Decimal('0'),
            'loan_payments': Decimal('0'),
            'owner_contributions': Decimal('0'),
            'owner_distributions': Decimal('0')
        }
        
        for transaction in transactions:
            if transaction.category in self.financing_categories:
                if transaction.category == "贷款收入" and transaction.amount > 0:
                    flows['loan_proceeds'] += transaction.amount
                elif transaction.category == "还贷支出" and transaction.amount < 0:
                    flows['loan_payments'] += transaction.amount  # Keep negative
                elif transaction.category == "股东投资" and transaction.amount > 0:
                    flows['owner_contributions'] += transaction.amount
                elif transaction.category == "分红支出" and transaction.amount < 0:
                    flows['owner_distributions'] += transaction.amount  # Keep negative
            # Also catch loan-related transactions by description
            elif any(keyword in transaction.description.lower() for keyword in ['贷款', '还贷', 'loan']):
                if transaction.amount > 0:
                    flows['loan_proceeds'] += transaction.amount
                else:
                    flows['loan_payments'] += transaction.amount
        
        return flows
    
    def _format_cash_amount(self, amount: Decimal, currency_converter=None) -> str:
        """
        Format cash flow amount for display, with optional currency conversion
        
        Args:
            amount: Decimal amount to format
            currency_converter: Optional CurrencyConverter for dual-currency display
        
        Returns:
            Formatted amount string
        """
        if currency_converter:
            return currency_converter.format_currency_amount(amount, 'CNY')
        else:
            return f"¥{amount:,.2f}"


def generate_cash_flow_statement(transactions: List[Transaction], start_date: date, end_date: date) -> Dict[str, Any]:
    """
    Convenience function to generate cash flow statement
    
    Args:
        transactions: List of Transaction objects
        start_date: Period start date
        end_date: Period end date
        
    Returns:
        Dict containing complete cash flow statement data
    """
    generator = CashFlowGenerator()
    return generator.generate_cash_flow_statement(transactions, start_date, end_date)


def format_currency(amount: Decimal) -> str:
    """Format decimal amount as CNY currency"""
    return f"¥{amount:,.2f}"


def print_cash_flow_statement(cash_flow_data: Dict[str, Any]) -> str:
    """
    Format cash flow statement data for console output
    
    Args:
        cash_flow_data: Cash flow data from generate_cash_flow_statement()
        
    Returns:
        Formatted string representation of the cash flow statement
    """
    data = cash_flow_data
    output = []
    
    output.append(f"CASH FLOW STATEMENT - {data['period']}")
    output.append("=" * 60)
    
    # Operating Activities
    output.append("\nCASH FLOWS FROM OPERATING ACTIVITIES:")
    output.append(f"  Cash received from customers:          {format_currency(data['operating_activities']['cash_received_from_customers'])}")
    output.append(f"  Cash paid to suppliers:                {format_currency(data['operating_activities']['cash_paid_to_suppliers'])}")
    output.append(f"  Cash paid for operating expenses:      {format_currency(data['operating_activities']['cash_paid_for_operating_expenses'])}")
    output.append(f"  Cash paid for rent:                    {format_currency(data['operating_activities']['cash_paid_for_rent'])}")
    output.append(f"  Net cash from operating activities:    {format_currency(data['operating_activities']['net_cash_from_operating'])}")
    
    # Investing Activities
    output.append(f"\nCASH FLOWS FROM INVESTING ACTIVITIES:")
    output.append(f"  Purchase of investments:               {format_currency(data['investing_activities']['purchase_of_investments'])}")
    output.append(f"  Sale of investments:                   {format_currency(data['investing_activities']['sale_of_investments'])}")
    output.append(f"  Purchase of equipment:                 {format_currency(data['investing_activities']['purchase_of_equipment'])}")
    output.append(f"  Net cash from investing activities:    {format_currency(data['investing_activities']['net_cash_from_investing'])}")
    
    # Financing Activities
    output.append(f"\nCASH FLOWS FROM FINANCING ACTIVITIES:")
    output.append(f"  Proceeds from loans:                   {format_currency(data['financing_activities']['proceeds_from_loans'])}")
    output.append(f"  Repayment of loans:                    {format_currency(data['financing_activities']['repayment_of_loans'])}")
    output.append(f"  Owner contributions:                   {format_currency(data['financing_activities']['owner_contributions'])}")
    output.append(f"  Owner distributions:                   {format_currency(data['financing_activities']['owner_distributions'])}")
    output.append(f"  Net cash from financing activities:    {format_currency(data['financing_activities']['net_cash_from_financing'])}")
    
    # Summary
    output.append(f"\nNET CHANGE IN CASH:                      {format_currency(data['net_change_in_cash'])}")
    output.append(f"Cash at beginning of period:             {format_currency(data['cash_at_beginning'])}")
    output.append(f"Cash at end of period:                   {format_currency(data['cash_at_end'])}")
    output.append("=" * 60)
    
    return "\n".join(output)