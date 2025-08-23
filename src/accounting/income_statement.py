"""
Income Statement Generation for Professional Accounting Module

This module provides comprehensive income statement generation with revenue/expense
categorization, tax calculations, and percentage analysis following professional
accounting standards.
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .models import Transaction, EXPENSE_CATEGORIES


class IncomeStatementGenerator:
    """
    Professional income statement generation service
    
    Generates monthly and YTD income statements with:
    - Revenue categorization (service revenue vs other income)
    - Fixed vs variable cost classification
    - Tax expense calculation
    - Percentage analysis relative to gross revenue
    - Detailed expense breakdown by category
    """
    
    def __init__(self):
        # Fixed cost categories from PRD
        self.fixed_cost_categories = ["房租", "水电费", "保险"]
        
        # Revenue categories (positive amounts)
        self.revenue_categories = ["工资收入", "服务收入", "投资收益", "其他收入"]
        
        # Service revenue specific categories
        self.service_revenue_categories = ["工资收入", "服务收入"]
    
    def generate_monthly_income_statement(
        self, 
        transactions: List[Transaction], 
        month: int, 
        year: int
    ) -> Dict[str, Any]:
        """
        Generate monthly income statement
        
        Args:
            transactions: List of Transaction objects
            month: Target month (1-12)
            year: Target year
        
        Returns:
            Dict containing complete income statement data
        """
        # Filter transactions for the specific month
        month_transactions = [
            t for t in transactions 
            if t.date.month == month and t.date.year == year
        ]
        
        return self._build_income_statement(month_transactions, f"{year}-{month:02d}")
    
    def generate_ytd_income_statement(
        self, 
        transactions: List[Transaction], 
        year: int
    ) -> Dict[str, Any]:
        """
        Generate year-to-date income statement
        
        Args:
            transactions: List of Transaction objects
            year: Target year
        
        Returns:
            Dict containing complete YTD income statement data
        """
        ytd_transactions = [
            t for t in transactions 
            if t.date.year == year
        ]
        
        return self._build_income_statement(ytd_transactions, f"YTD {year}")
    
    def _build_income_statement(
        self, 
        transactions: List[Transaction], 
        period: str
    ) -> Dict[str, Any]:
        """
        Build income statement from filtered transactions
        
        Args:
            transactions: Filtered list of transactions
            period: Period description (e.g., "2024-01" or "YTD 2024")
        
        Returns:
            Complete income statement dictionary
        """
        # Separate revenue (positive amounts) and expenses (negative amounts)
        revenues = [t for t in transactions if t.amount > 0]
        expenses = [t for t in transactions if t.amount < 0]
        
        # Calculate revenue sections
        service_revenue = sum(
            t.amount for t in revenues 
            if t.category in self.service_revenue_categories
        )
        other_income = sum(
            t.amount for t in revenues 
            if t.category not in self.service_revenue_categories
        )
        gross_revenue = service_revenue + other_income
        
        # Categorize expenses (use absolute values for expenses)
        fixed_expenses = sum(
            abs(t.amount) for t in expenses 
            if t.category in self.fixed_cost_categories
        )
        variable_expenses = sum(
            abs(t.amount) for t in expenses 
            if t.category not in self.fixed_cost_categories
        )
        
        # Calculate tax expense
        tax_expense = self._calculate_tax_expense(gross_revenue)
        
        # Calculate totals
        total_expenses = fixed_expenses + variable_expenses + tax_expense
        net_operating_income = gross_revenue - total_expenses
        
        # Helper function for percentage calculations
        def calc_percentage(amount: Decimal, base: Decimal) -> Decimal:
            if base == 0:
                return Decimal("0")
            return ((amount / base) * 100).quantize(Decimal("0.01"), ROUND_HALF_UP)
        
        # Build comprehensive income statement
        return {
            "period": period,
            "total_revenue": gross_revenue,
            "revenue": {
                "service_revenue": service_revenue,
                "service_revenue_pct": calc_percentage(service_revenue, gross_revenue),
                "other_income": other_income,
                "other_income_pct": calc_percentage(other_income, gross_revenue),
                "gross_revenue": gross_revenue
            },
            "expenses": {
                "fixed_costs": fixed_expenses,
                "fixed_costs_pct": calc_percentage(fixed_expenses, gross_revenue),
                "variable_costs": variable_expenses,
                "variable_costs_pct": calc_percentage(variable_expenses, gross_revenue),
                "tax_expense": tax_expense,
                "tax_expense_pct": calc_percentage(tax_expense, gross_revenue),
                "total_expenses": total_expenses,
                "total_expenses_pct": calc_percentage(total_expenses, gross_revenue)
            },
            "net_operating_income": net_operating_income,
            "net_margin_pct": calc_percentage(net_operating_income, gross_revenue),
            "expense_breakdown": self._get_expense_breakdown(expenses, gross_revenue),
            "revenue_breakdown": self._get_revenue_breakdown(revenues, gross_revenue),
            "currency": "CNY",
            "generated_at": datetime.now(),
            "transaction_count": len(transactions)
        }
    
    def _calculate_tax_expense(self, gross_revenue: Decimal) -> Decimal:
        """
        Calculate tax expense based on income
        
        Simplified progressive tax calculation:
        - <= 5,000 CNY: 0% tax
        - 5,001 - 20,000 CNY: 10% tax  
        - > 20,000 CNY: 20% tax
        
        Args:
            gross_revenue: Total gross revenue
        
        Returns:
            Calculated tax expense
        """
        if gross_revenue <= Decimal("5000"):
            return Decimal("0")
        elif gross_revenue <= Decimal("20000"):
            return gross_revenue * Decimal("0.10")
        else:
            return gross_revenue * Decimal("0.20")
    
    def _get_expense_breakdown(
        self, 
        expenses: List[Transaction], 
        gross_revenue: Decimal
    ) -> Dict[str, Dict[str, Decimal]]:
        """
        Get detailed expense breakdown by category
        
        Args:
            expenses: List of expense transactions (negative amounts)
            gross_revenue: Total gross revenue for percentage calculation
        
        Returns:
            Dict mapping category names to amount and percentage data
        """
        breakdown = {}
        
        # Group expenses by category
        category_totals = {}
        for expense in expenses:
            category = expense.category
            if category not in category_totals:
                category_totals[category] = Decimal("0")
            category_totals[category] += abs(expense.amount)
        
        # Calculate percentages for each category
        for category, amount in category_totals.items():
            percentage = Decimal("0")
            if gross_revenue > 0:
                percentage = ((amount / gross_revenue) * 100).quantize(
                    Decimal("0.01"), ROUND_HALF_UP
                )
            
            breakdown[category] = {
                "amount": amount,
                "percentage": percentage,
                "type": "fixed" if category in self.fixed_cost_categories else "variable"
            }
        
        return breakdown
    
    def _get_revenue_breakdown(
        self, 
        revenues: List[Transaction], 
        gross_revenue: Decimal
    ) -> Dict[str, Dict[str, Decimal]]:
        """
        Get detailed revenue breakdown by category
        
        Args:
            revenues: List of revenue transactions (positive amounts)
            gross_revenue: Total gross revenue for percentage calculation
        
        Returns:
            Dict mapping category names to amount and percentage data
        """
        breakdown = {}
        
        # Group revenues by category
        category_totals = {}
        for revenue in revenues:
            category = revenue.category
            if category not in category_totals:
                category_totals[category] = Decimal("0")
            category_totals[category] += revenue.amount
        
        # Calculate percentages for each category
        for category, amount in category_totals.items():
            percentage = Decimal("0")
            if gross_revenue > 0:
                percentage = ((amount / gross_revenue) * 100).quantize(
                    Decimal("0.01"), ROUND_HALF_UP
                )
            
            breakdown[category] = {
                "amount": amount,
                "percentage": percentage,
                "type": "service" if category in self.service_revenue_categories else "other"
            }
        
        return breakdown


def generate_monthly_income_statement(
    transactions: List[Transaction], 
    month: int, 
    year: int
) -> Dict[str, Any]:
    """
    Convenience function for generating monthly income statement
    
    Args:
        transactions: List of Transaction objects
        month: Target month (1-12)
        year: Target year
    
    Returns:
        Complete income statement dictionary
    """
    generator = IncomeStatementGenerator()
    return generator.generate_monthly_income_statement(transactions, month, year)


def generate_ytd_income_statement(
    transactions: List[Transaction], 
    year: int
) -> Dict[str, Any]:
    """
    Convenience function for generating YTD income statement
    
    Args:
        transactions: List of Transaction objects
        year: Target year
    
    Returns:
        Complete YTD income statement dictionary
    """
    generator = IncomeStatementGenerator()
    return generator.generate_ytd_income_statement(transactions, year)


def format_currency(amount: Decimal, currency: str = "CNY") -> str:
    """
    Format currency amount for display
    
    Args:
        amount: Decimal amount to format
        currency: Currency code (default CNY)
    
    Returns:
        Formatted currency string
    """
    if currency == "CNY":
        return f"¥{amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"


def print_income_statement(statement_data: Dict[str, Any]) -> None:
    """
    Print formatted income statement to console
    
    Args:
        statement_data: Income statement dictionary from generator
    """
    period = statement_data["period"]
    currency = statement_data.get("currency", "CNY")
    
    print(f"\n{'='*50}")
    print(f"INCOME STATEMENT - {period}")
    print(f"{'='*50}")
    
    # Revenue section
    revenue = statement_data["revenue"]
    print(f"\nREVENUE:")
    print(f"  Service Revenue:     {format_currency(revenue['service_revenue'], currency):>15} ({revenue['service_revenue_pct']:>5.1f}%)")
    print(f"  Other Income:        {format_currency(revenue['other_income'], currency):>15} ({revenue['other_income_pct']:>5.1f}%)")
    print(f"  {'─'*40}")
    print(f"  Gross Revenue:       {format_currency(revenue['gross_revenue'], currency):>15} (100.0%)")
    
    # Expenses section
    expenses = statement_data["expenses"]
    print(f"\nEXPENSES:")
    print(f"  Fixed Costs:         {format_currency(expenses['fixed_costs'], currency):>15} ({expenses['fixed_costs_pct']:>5.1f}%)")
    print(f"  Variable Costs:      {format_currency(expenses['variable_costs'], currency):>15} ({expenses['variable_costs_pct']:>5.1f}%)")
    print(f"  Tax Expense:         {format_currency(expenses['tax_expense'], currency):>15} ({expenses['tax_expense_pct']:>5.1f}%)")
    print(f"  {'─'*40}")
    print(f"  Total Expenses:      {format_currency(expenses['total_expenses'], currency):>15} ({expenses['total_expenses_pct']:>5.1f}%)")
    
    # Net income
    net_income = statement_data["net_operating_income"]
    net_margin = statement_data["net_margin_pct"]
    print(f"\n  NET OPERATING INCOME: {format_currency(net_income, currency):>14} ({net_margin:>5.1f}%)")
    
    print(f"{'='*50}\n")