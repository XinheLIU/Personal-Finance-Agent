"""
Test suite for Professional Accounting Module - Income Statement Generation

ACCEPTANCE CRITERIA → TEST MAPPING:
- US-2.1: System generates professional income statement format → test_income_statement_format_*
- Revenue section shows service revenue and other income → test_revenue_section_*
- Tax expenses calculated with percentage of gross revenue → test_tax_calculation_*
- Expenses categorized into fixed and variable costs → test_expense_categorization_*
- Each category shows percentage of gross revenue → test_percentage_analysis_*
- Net operating income calculated correctly → test_net_income_calculation_*

ASSUMPTIONS FOR VALIDATION:
1. Income statements are generated monthly and YTD
2. Revenue categories: Service Revenue, Other Income
3. Fixed costs: 房租, 水电费, 保险
4. Variable costs: All other expense categories
5. Tax rate calculation based on total income
6. Percentages calculated relative to gross revenue
7. Professional format with Chinese and English labels
8. All amounts in Chinese Yuan (¥) with 2 decimal places
"""

import pytest
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class Transaction:
    """Transaction data for testing"""
    description: str
    amount: Decimal
    category: str
    account_type: str
    transaction_type: str
    date: datetime


class IncomeStatementGenerator:
    """Income statement generation service - would be in modules/accounting/statements/"""
    
    def __init__(self):
        self.fixed_cost_categories = ["房租", "水电费", "保险"]
        self.revenue_categories = ["工资收入", "投资收益", "其他收入"]
    
    def generate_monthly_income_statement(self, transactions: List[Transaction], 
                                        month: int, year: int) -> Dict[str, Any]:
        """Generate monthly income statement"""
        # Filter transactions for the specific month
        month_transactions = [
            t for t in transactions 
            if t.date.month == month and t.date.year == year
        ]
        
        return self._build_income_statement(month_transactions, f"{year}-{month:02d}")
    
    def generate_ytd_income_statement(self, transactions: List[Transaction], 
                                    year: int) -> Dict[str, Any]:
        """Generate year-to-date income statement"""
        ytd_transactions = [
            t for t in transactions 
            if t.date.year == year
        ]
        
        return self._build_income_statement(ytd_transactions, f"YTD {year}")
    
    def _build_income_statement(self, transactions: List[Transaction], 
                              period: str) -> Dict[str, Any]:
        """Build income statement from transactions"""
        # Separate revenue and expenses
        revenues = [t for t in transactions if t.amount > 0]
        expenses = [t for t in transactions if t.amount < 0]
        
        # Calculate revenue sections
        service_revenue = sum(
            t.amount for t in revenues 
            if t.category in ["工资收入", "服务收入"]
        )
        other_income = sum(
            t.amount for t in revenues 
            if t.category not in ["工资收入", "服务收入"]
        )
        gross_revenue = service_revenue + other_income
        
        # Categorize expenses
        fixed_expenses = sum(
            abs(t.amount) for t in expenses 
            if t.category in self.fixed_cost_categories
        )
        variable_expenses = sum(
            abs(t.amount) for t in expenses 
            if t.category not in self.fixed_cost_categories
        )
        
        # Calculate tax (simplified - assume 20% on income above threshold)
        tax_expense = self._calculate_tax_expense(gross_revenue)
        
        total_expenses = fixed_expenses + variable_expenses + tax_expense
        net_operating_income = gross_revenue - total_expenses
        
        # Calculate percentages
        def calc_percentage(amount: Decimal, base: Decimal) -> Decimal:
            if base == 0:
                return Decimal("0")
            return ((amount / base) * 100).quantize(Decimal("0.01"), ROUND_HALF_UP)
        
        return {
            "period": period,
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
            "currency": "CNY"
        }
    
    def _calculate_tax_expense(self, gross_revenue: Decimal) -> Decimal:
        """Calculate tax expense based on income"""
        # Simplified tax calculation
        if gross_revenue <= Decimal("5000"):
            return Decimal("0")
        elif gross_revenue <= Decimal("20000"):
            return gross_revenue * Decimal("0.10")
        else:
            return gross_revenue * Decimal("0.20")
    
    def _get_expense_breakdown(self, expenses: List[Transaction], 
                             gross_revenue: Decimal) -> Dict[str, Dict[str, Decimal]]:
        """Get detailed expense breakdown by category"""
        breakdown = {}
        
        # Group expenses by category
        category_totals = {}
        for expense in expenses:
            category = expense.category
            if category not in category_totals:
                category_totals[category] = Decimal("0")
            category_totals[category] += abs(expense.amount)
        
        # Calculate percentages
        for category, amount in category_totals.items():
            percentage = Decimal("0")
            if gross_revenue > 0:
                percentage = ((amount / gross_revenue) * 100).quantize(
                    Decimal("0.01"), ROUND_HALF_UP
                )
            
            breakdown[category] = {
                "amount": amount,
                "percentage": percentage,
                "is_fixed_cost": category in self.fixed_cost_categories
            }
        
        return breakdown


class IncomeStatementComparator:
    """Service for comparing income statements - would be in modules/accounting/analytics/"""
    
    def compare_periods(self, current_statement: Dict[str, Any], 
                       previous_statement: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two income statements"""
        current_revenue = current_statement["revenue"]["gross_revenue"]
        previous_revenue = previous_statement["revenue"]["gross_revenue"]
        
        current_expenses = current_statement["expenses"]["total_expenses"]
        previous_expenses = previous_statement["expenses"]["total_expenses"]
        
        current_net = current_statement["net_operating_income"]
        previous_net = previous_statement["net_operating_income"]
        
        return {
            "revenue_change": {
                "amount": current_revenue - previous_revenue,
                "percentage": self._calc_change_percentage(current_revenue, previous_revenue)
            },
            "expense_change": {
                "amount": current_expenses - previous_expenses,
                "percentage": self._calc_change_percentage(current_expenses, previous_expenses)
            },
            "net_income_change": {
                "amount": current_net - previous_net,
                "percentage": self._calc_change_percentage(current_net, previous_net)
            }
        }
    
    def _calc_change_percentage(self, current: Decimal, previous: Decimal) -> Decimal:
        """Calculate percentage change"""
        if previous == 0:
            return Decimal("100") if current > 0 else Decimal("0")
        
        return ((current - previous) / abs(previous) * 100).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )


class TestIncomeStatementGeneration:
    """Test income statement generation functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.generator = IncomeStatementGenerator()
        
        # Sample transactions for testing
        self.sample_transactions = [
            Transaction("Monthly Salary", Decimal("8000.00"), "工资收入", "Debit", "Non-Cash", 
                       datetime(2024, 1, 15)),
            Transaction("Freelance Work", Decimal("2000.00"), "服务收入", "Cash", "Cash", 
                       datetime(2024, 1, 20)),
            Transaction("Investment Dividend", Decimal("500.00"), "投资收益", "Debit", "Non-Cash", 
                       datetime(2024, 1, 25)),
            Transaction("Rent Payment", Decimal("-2000.00"), "房租", "Debit", "Non-Cash", 
                       datetime(2024, 1, 1)),
            Transaction("Utilities", Decimal("-300.00"), "水电费", "Debit", "Non-Cash", 
                       datetime(2024, 1, 5)),
            Transaction("Groceries", Decimal("-800.00"), "餐饮", "Credit", "Non-Cash", 
                       datetime(2024, 1, 10)),
            Transaction("Transportation", Decimal("-200.00"), "交通", "Cash", "Cash", 
                       datetime(2024, 1, 12))
        ]
    
    def test_monthly_income_statement_generation(self):
        """Test generating monthly income statement"""
        statement = self.generator.generate_monthly_income_statement(
            self.sample_transactions, 1, 2024
        )
        
        assert statement["period"] == "2024-01"
        assert statement["currency"] == "CNY"
        
        # Check revenue calculations
        assert statement["revenue"]["service_revenue"] == Decimal("10000.00")  # 8000 + 2000
        assert statement["revenue"]["other_income"] == Decimal("500.00")  # investment
        assert statement["revenue"]["gross_revenue"] == Decimal("10500.00")  # total
        
        # Check expense calculations
        assert statement["expenses"]["fixed_costs"] == Decimal("2300.00")  # rent + utilities
        assert statement["expenses"]["variable_costs"] == Decimal("1000.00")  # groceries + transport
    
    def test_revenue_section_breakdown(self):
        """Test revenue section shows service revenue and other income"""
        statement = self.generator.generate_monthly_income_statement(
            self.sample_transactions, 1, 2024
        )
        
        revenue = statement["revenue"]
        
        # Service revenue (salary + freelance)
        assert revenue["service_revenue"] == Decimal("10000.00")
        assert "service_revenue_pct" in revenue
        
        # Other income (investments)
        assert revenue["other_income"] == Decimal("500.00")
        assert "other_income_pct" in revenue
        
        # Total gross revenue
        assert revenue["gross_revenue"] == Decimal("10500.00")
    
    def test_expense_categorization(self):
        """Test expenses categorized into fixed and variable costs"""
        statement = self.generator.generate_monthly_income_statement(
            self.sample_transactions, 1, 2024
        )
        
        expenses = statement["expenses"]
        
        # Fixed costs (房租, 水电费)
        assert expenses["fixed_costs"] == Decimal("2300.00")  # 2000 + 300
        
        # Variable costs (餐饮, 交通)
        assert expenses["variable_costs"] == Decimal("1000.00")  # 800 + 200
        
        # Tax expense should be calculated
        assert "tax_expense" in expenses
        assert expenses["tax_expense"] > Decimal("0")
    
    def test_percentage_analysis(self):
        """Test each category shows percentage of gross revenue"""
        statement = self.generator.generate_monthly_income_statement(
            self.sample_transactions, 1, 2024
        )
        
        gross_revenue = statement["revenue"]["gross_revenue"]
        
        # Revenue percentages
        expected_service_pct = (Decimal("10000.00") / gross_revenue * 100).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )
        assert statement["revenue"]["service_revenue_pct"] == expected_service_pct
        
        # Expense percentages
        expected_fixed_pct = (Decimal("2300.00") / gross_revenue * 100).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )
        assert statement["expenses"]["fixed_costs_pct"] == expected_fixed_pct
    
    def test_net_operating_income_calculation(self):
        """Test net operating income calculated correctly"""
        statement = self.generator.generate_monthly_income_statement(
            self.sample_transactions, 1, 2024
        )
        
        gross_revenue = statement["revenue"]["gross_revenue"]
        total_expenses = statement["expenses"]["total_expenses"]
        net_income = statement["net_operating_income"]
        
        # Net income = Revenue - Total Expenses
        assert net_income == gross_revenue - total_expenses
        
        # Net margin percentage should be calculated
        expected_margin = (net_income / gross_revenue * 100).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )
        assert statement["net_margin_pct"] == expected_margin
    
    def test_tax_expense_calculation(self):
        """Test tax expenses calculated with percentage analysis"""
        statement = self.generator.generate_monthly_income_statement(
            self.sample_transactions, 1, 2024
        )
        
        tax_expense = statement["expenses"]["tax_expense"]
        tax_percentage = statement["expenses"]["tax_expense_pct"]
        gross_revenue = statement["revenue"]["gross_revenue"]
        
        # Tax should be calculated based on income
        assert tax_expense > Decimal("0")
        
        # Tax percentage should be relative to gross revenue
        expected_tax_pct = (tax_expense / gross_revenue * 100).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )
        assert tax_percentage == expected_tax_pct
    
    @pytest.mark.parametrize("income,expected_tax", [
        (Decimal("3000.00"), Decimal("0.00")),  # Below threshold
        (Decimal("10000.00"), Decimal("1000.00")),  # 10% bracket
        (Decimal("25000.00"), Decimal("5000.00"))  # 20% bracket
    ])
    def test_tax_calculation_brackets(self, income, expected_tax):
        """Test tax calculation for different income brackets"""
        calculated_tax = self.generator._calculate_tax_expense(income)
        assert calculated_tax == expected_tax
    
    def test_expense_breakdown_details(self):
        """Test detailed expense breakdown by category"""
        statement = self.generator.generate_monthly_income_statement(
            self.sample_transactions, 1, 2024
        )
        
        breakdown = statement["expense_breakdown"]
        
        # Check specific categories
        assert "房租" in breakdown
        assert breakdown["房租"]["amount"] == Decimal("2000.00")
        assert breakdown["房租"]["is_fixed_cost"] is True
        
        assert "餐饮" in breakdown
        assert breakdown["餐饮"]["amount"] == Decimal("800.00")
        assert breakdown["餐饮"]["is_fixed_cost"] is False
        
        # All categories should have percentage calculations
        for category, data in breakdown.items():
            assert "percentage" in data
            assert isinstance(data["percentage"], Decimal)


class TestYTDIncomeStatement:
    """Test year-to-date income statement functionality"""
    
    def setup_method(self):
        """Setup test fixtures with multi-month data"""
        self.generator = IncomeStatementGenerator()
        
        # Create transactions across multiple months
        self.multi_month_transactions = [
            # January
            Transaction("Jan Salary", Decimal("8000.00"), "工资收入", "Debit", "Non-Cash", 
                       datetime(2024, 1, 15)),
            Transaction("Jan Rent", Decimal("-2000.00"), "房租", "Debit", "Non-Cash", 
                       datetime(2024, 1, 1)),
            # February
            Transaction("Feb Salary", Decimal("8500.00"), "工资收入", "Debit", "Non-Cash", 
                       datetime(2024, 2, 15)),
            Transaction("Feb Rent", Decimal("-2000.00"), "房租", "Debit", "Non-Cash", 
                       datetime(2024, 2, 1)),
            Transaction("Feb Freelance", Decimal("1500.00"), "服务收入", "Cash", "Cash", 
                       datetime(2024, 2, 20)),
            # March
            Transaction("Mar Salary", Decimal("8000.00"), "工资收入", "Debit", "Non-Cash", 
                       datetime(2024, 3, 15))
        ]
    
    def test_ytd_income_statement_generation(self):
        """Test generating YTD income statement"""
        statement = self.generator.generate_ytd_income_statement(
            self.multi_month_transactions, 2024
        )
        
        assert statement["period"] == "YTD 2024"
        
        # Should aggregate all transactions for the year
        total_revenue = Decimal("26000.00")  # 8000 + 8500 + 1500 + 8000
        assert statement["revenue"]["gross_revenue"] == total_revenue
        
        # Should aggregate expenses
        total_rent = Decimal("4000.00")  # 2000 + 2000
        assert statement["expense_breakdown"]["房租"]["amount"] == total_rent
    
    def test_ytd_multi_month_aggregation(self):
        """Test proper aggregation across multiple months"""
        statement = self.generator.generate_ytd_income_statement(
            self.multi_month_transactions, 2024
        )
        
        # Service revenue: 8000 + 8500 + 8000 (salaries) + 1500 (freelance)
        assert statement["revenue"]["service_revenue"] == Decimal("26000.00")
        
        # Fixed costs: 2000 + 2000 (rent)
        assert statement["expenses"]["fixed_costs"] == Decimal("4000.00")
        
        # Net income should be calculated correctly
        net_income = statement["net_operating_income"]
        expected_net = statement["revenue"]["gross_revenue"] - statement["expenses"]["total_expenses"]
        assert net_income == expected_net
    
    def test_ytd_percentage_calculations(self):
        """Test YTD percentage calculations are accurate"""
        statement = self.generator.generate_ytd_income_statement(
            self.multi_month_transactions, 2024
        )
        
        gross_revenue = statement["revenue"]["gross_revenue"]
        
        # Service revenue percentage
        service_revenue = statement["revenue"]["service_revenue"]
        expected_pct = (service_revenue / gross_revenue * 100).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )
        assert statement["revenue"]["service_revenue_pct"] == expected_pct
        
        # Fixed costs percentage
        fixed_costs = statement["expenses"]["fixed_costs"]
        expected_fixed_pct = (fixed_costs / gross_revenue * 100).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )
        assert statement["expenses"]["fixed_costs_pct"] == expected_fixed_pct


class TestIncomeStatementComparison:
    """Test income statement comparison functionality"""
    
    def setup_method(self):
        """Setup test fixtures for comparison"""
        self.generator = IncomeStatementGenerator()
        self.comparator = IncomeStatementComparator()
        
        # Current month transactions
        self.current_transactions = [
            Transaction("Salary", Decimal("10000.00"), "工资收入", "Debit", "Non-Cash", 
                       datetime(2024, 2, 15)),
            Transaction("Rent", Decimal("-2200.00"), "房租", "Debit", "Non-Cash", 
                       datetime(2024, 2, 1))
        ]
        
        # Previous month transactions
        self.previous_transactions = [
            Transaction("Salary", Decimal("8000.00"), "工资收入", "Debit", "Non-Cash", 
                       datetime(2024, 1, 15)),
            Transaction("Rent", Decimal("-2000.00"), "房租", "Debit", "Non-Cash", 
                       datetime(2024, 1, 1))
        ]
    
    def test_revenue_change_comparison(self):
        """Test revenue change comparison between periods"""
        current_statement = self.generator.generate_monthly_income_statement(
            self.current_transactions, 2, 2024
        )
        previous_statement = self.generator.generate_monthly_income_statement(
            self.previous_transactions, 1, 2024
        )
        
        comparison = self.comparator.compare_periods(current_statement, previous_statement)
        
        # Revenue increased from 8000 to 10000
        assert comparison["revenue_change"]["amount"] == Decimal("2000.00")
        assert comparison["revenue_change"]["percentage"] == Decimal("25.00")  # 25% increase
    
    def test_expense_change_comparison(self):
        """Test expense change comparison between periods"""
        current_statement = self.generator.generate_monthly_income_statement(
            self.current_transactions, 2, 2024
        )
        previous_statement = self.generator.generate_monthly_income_statement(
            self.previous_transactions, 1, 2024
        )
        
        comparison = self.comparator.compare_periods(current_statement, previous_statement)
        
        # Check that expense change is calculated
        assert "expense_change" in comparison
        assert "amount" in comparison["expense_change"]
        assert "percentage" in comparison["expense_change"]
    
    def test_net_income_change_comparison(self):
        """Test net income change comparison"""
        current_statement = self.generator.generate_monthly_income_statement(
            self.current_transactions, 2, 2024
        )
        previous_statement = self.generator.generate_monthly_income_statement(
            self.previous_transactions, 1, 2024
        )
        
        comparison = self.comparator.compare_periods(current_statement, previous_statement)
        
        # Net income change should be calculated
        assert "net_income_change" in comparison
        assert isinstance(comparison["net_income_change"]["amount"], Decimal)
        assert isinstance(comparison["net_income_change"]["percentage"], Decimal)
    
    def test_zero_previous_revenue_comparison(self):
        """Test comparison when previous revenue is zero"""
        # Create zero revenue scenario
        zero_revenue_transactions = [
            Transaction("Expense", Decimal("-1000.00"), "餐饮", "Cash", "Cash", 
                       datetime(2024, 1, 15))
        ]
        
        current_statement = self.generator.generate_monthly_income_statement(
            self.current_transactions, 2, 2024
        )
        zero_statement = self.generator.generate_monthly_income_statement(
            zero_revenue_transactions, 1, 2024
        )
        
        comparison = self.comparator.compare_periods(current_statement, zero_statement)
        
        # Should handle zero division gracefully
        assert comparison["revenue_change"]["percentage"] == Decimal("100")


class TestIncomeStatementEdgeCases:
    """Test edge cases for income statement generation"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.generator = IncomeStatementGenerator()
    
    def test_no_transactions_period(self):
        """Test income statement with no transactions"""
        statement = self.generator.generate_monthly_income_statement([], 1, 2024)
        
        assert statement["revenue"]["gross_revenue"] == Decimal("0")
        assert statement["expenses"]["total_expenses"] == Decimal("0")
        assert statement["net_operating_income"] == Decimal("0")
        assert statement["net_margin_pct"] == Decimal("0")
    
    def test_only_revenue_no_expenses(self):
        """Test income statement with only revenue"""
        revenue_only = [
            Transaction("Salary", Decimal("5000.00"), "工资收入", "Debit", "Non-Cash", 
                       datetime(2024, 1, 15))
        ]
        
        statement = self.generator.generate_monthly_income_statement(revenue_only, 1, 2024)
        
        assert statement["revenue"]["gross_revenue"] == Decimal("5000.00")
        assert statement["expenses"]["variable_costs"] == Decimal("0")
        assert statement["expenses"]["fixed_costs"] == Decimal("0")
        # At exactly 5000 CNY, tax expense should be 0 (per tax bracket logic)
        assert statement["expenses"]["tax_expense"] == Decimal("0")
    
    def test_only_expenses_no_revenue(self):
        """Test income statement with only expenses"""
        expenses_only = [
            Transaction("Rent", Decimal("-2000.00"), "房租", "Debit", "Non-Cash", 
                       datetime(2024, 1, 1)),
            Transaction("Food", Decimal("-500.00"), "餐饮", "Cash", "Cash", 
                       datetime(2024, 1, 10))
        ]
        
        statement = self.generator.generate_monthly_income_statement(expenses_only, 1, 2024)
        
        assert statement["revenue"]["gross_revenue"] == Decimal("0")
        assert statement["expenses"]["fixed_costs"] == Decimal("2000.00")
        assert statement["expenses"]["variable_costs"] == Decimal("500.00")
        assert statement["net_operating_income"] == Decimal("-2500.00")  # Negative income
    
    def test_decimal_precision_handling(self):
        """Test proper decimal precision in calculations"""
        precise_transactions = [
            Transaction("Salary", Decimal("8333.33"), "工资收入", "Debit", "Non-Cash", 
                       datetime(2024, 1, 15)),
            Transaction("Rent", Decimal("-1666.67"), "房租", "Debit", "Non-Cash", 
                       datetime(2024, 1, 1))
        ]
        
        statement = self.generator.generate_monthly_income_statement(
            precise_transactions, 1, 2024
        )
        
        # All percentages should be rounded to 2 decimal places
        for key, value in statement["revenue"].items():
            if key.endswith("_pct"):
                assert value.as_tuple().exponent >= -2  # Max 2 decimal places
        
        for key, value in statement["expenses"].items():
            if key.endswith("_pct"):
                assert value.as_tuple().exponent >= -2