"""
Test suite for Professional Accounting Module - Consolidated Reports

ACCEPTANCE CRITERIA → TEST MAPPING:
- US-3.1: System combines multiple user transactions → test_multi_user_transaction_consolidation_*
- Consolidated income statement for all users → test_consolidated_income_statement_*
- Consolidated asset portfolio view → test_consolidated_asset_portfolio_*
- Individual vs. household reporting options → test_individual_vs_household_*

ASSUMPTIONS FOR VALIDATION:
1. Multi-user households have shared income and expenses
2. Asset consolidation sums all account balances by type
3. Individual reports show single user data
4. Household reports aggregate all family members
5. User separation maintained for detailed analysis
6. Shared categories (rent, utilities) vs individual categories (personal expenses)
7. Consolidated reports support same features as individual reports
8. Data privacy maintained - users only see their own data unless authorized
"""

import pytest
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ReportType(Enum):
    """Report type enumeration"""
    INDIVIDUAL = "individual"
    HOUSEHOLD = "household"
    CONSOLIDATED = "consolidated"


@dataclass
class User:
    """User data structure"""
    id: str
    name: str
    household_id: Optional[str] = None


@dataclass
class Transaction:
    """Transaction with user association"""
    id: str
    user_id: str
    description: str
    amount: Decimal
    category: str
    account_type: str
    date: datetime
    is_shared: bool = False  # Whether expense is shared among household members


@dataclass
class Asset:
    """Asset with user association"""
    id: str
    user_id: str
    account_name: str
    balance: Decimal
    account_type: str
    as_of_date: datetime


class ConsolidatedReportGenerator:
    """Consolidated reporting service - would be in modules/accounting/statements/"""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.shared_categories = ["房租", "水电费", "保险", "internet", "shared_utilities"]
    
    def register_user(self, user: User):
        """Register a user in the system"""
        self.users[user.id] = user
    
    def generate_household_income_statement(self, household_id: str, 
                                          transactions: List[Transaction], 
                                          month: int, year: int) -> Dict[str, Any]:
        """Generate consolidated income statement for household"""
        # Get all users in household
        household_users = [
            user for user in self.users.values() 
            if user.household_id == household_id
        ]
        
        # Filter transactions for household members
        household_transactions = [
            t for t in transactions 
            if t.user_id in [u.id for u in household_users]
            and t.date.month == month and t.date.year == year
        ]
        
        return self._build_consolidated_income_statement(
            household_transactions, f"Household {household_id} - {year}-{month:02d}"
        )
    
    def generate_individual_vs_household_comparison(self, household_id: str,
                                                  transactions: List[Transaction],
                                                  month: int, year: int) -> Dict[str, Any]:
        """Generate comparison between individual and household reports"""
        household_users = [
            user for user in self.users.values() 
            if user.household_id == household_id
        ]
        
        # Generate individual reports for each user
        individual_reports = {}
        for user in household_users:
            user_transactions = [
                t for t in transactions 
                if t.user_id == user.id
                and t.date.month == month and t.date.year == year
            ]
            individual_reports[user.id] = self._build_consolidated_income_statement(
                user_transactions, f"{user.name} - {year}-{month:02d}"
            )
        
        # Generate household consolidated report
        household_report = self.generate_household_income_statement(
            household_id, transactions, month, year
        )
        
        return {
            "household_report": household_report,
            "individual_reports": individual_reports,
            "summary": self._generate_comparison_summary(individual_reports, household_report)
        }
    
    def consolidate_asset_portfolio(self, household_id: str, 
                                  assets: List[Asset]) -> Dict[str, Any]:
        """Generate consolidated asset portfolio for household"""
        household_users = [
            user for user in self.users.values() 
            if user.household_id == household_id
        ]
        
        # Filter assets for household members
        household_assets = [
            asset for asset in assets 
            if asset.user_id in [u.id for u in household_users]
        ]
        
        # Group by account type and calculate totals
        consolidated_by_type = {}
        individual_breakdown = {}
        
        for asset in household_assets:
            account_type = asset.account_type
            
            # Consolidated totals
            if account_type not in consolidated_by_type:
                consolidated_by_type[account_type] = {
                    "total_balance": Decimal("0"),
                    "account_count": 0,
                    "accounts": []
                }
            
            consolidated_by_type[account_type]["total_balance"] += asset.balance
            consolidated_by_type[account_type]["account_count"] += 1
            consolidated_by_type[account_type]["accounts"].append({
                "account_name": asset.account_name,
                "balance": asset.balance,
                "user_id": asset.user_id,
                "user_name": self.users[asset.user_id].name
            })
            
            # Individual breakdown
            if asset.user_id not in individual_breakdown:
                individual_breakdown[asset.user_id] = {
                    "user_name": self.users[asset.user_id].name,
                    "total_assets": Decimal("0"),
                    "by_type": {}
                }
            
            individual_breakdown[asset.user_id]["total_assets"] += asset.balance
            
            if account_type not in individual_breakdown[asset.user_id]["by_type"]:
                individual_breakdown[asset.user_id]["by_type"][account_type] = Decimal("0")
            
            individual_breakdown[asset.user_id]["by_type"][account_type] += asset.balance
        
        # Calculate household totals
        total_household_assets = sum(
            data["total_balance"] for data in consolidated_by_type.values()
        )
        
        return {
            "household_id": household_id,
            "total_assets": total_household_assets,
            "consolidated_by_type": consolidated_by_type,
            "individual_breakdown": individual_breakdown,
            "asset_allocation": self._calculate_asset_allocation(consolidated_by_type, total_household_assets)
        }
    
    def generate_multi_user_transaction_analysis(self, household_id: str,
                                               transactions: List[Transaction],
                                               month: int, year: int) -> Dict[str, Any]:
        """Analyze transaction patterns across multiple users"""
        household_users = [
            user for user in self.users.values() 
            if user.household_id == household_id
        ]
        
        month_transactions = [
            t for t in transactions 
            if t.user_id in [u.id for u in household_users]
            and t.date.month == month and t.date.year == year
        ]
        
        # Separate shared vs individual expenses
        shared_expenses = [t for t in month_transactions if t.is_shared or t.category in self.shared_categories]
        individual_expenses = [t for t in month_transactions if not t.is_shared and t.category not in self.shared_categories]
        
        # Analyze by user
        user_analysis = {}
        for user in household_users:
            user_transactions = [t for t in month_transactions if t.user_id == user.id]
            user_shared = [t for t in user_transactions if t.is_shared or t.category in self.shared_categories]
            user_individual = [t for t in user_transactions if not t.is_shared and t.category not in self.shared_categories]
            
            user_analysis[user.id] = {
                "user_name": user.name,
                "total_spending": sum(abs(t.amount) for t in user_transactions if t.amount < 0),
                "shared_spending": sum(abs(t.amount) for t in user_shared if t.amount < 0),
                "individual_spending": sum(abs(t.amount) for t in user_individual if t.amount < 0),
                "income": sum(t.amount for t in user_transactions if t.amount > 0),
                "transaction_count": len(user_transactions)
            }
        
        return {
            "period": f"{year}-{month:02d}",
            "household_summary": {
                "total_shared_expenses": sum(abs(t.amount) for t in shared_expenses if t.amount < 0),
                "total_individual_expenses": sum(abs(t.amount) for t in individual_expenses if t.amount < 0),
                "total_household_income": sum(t.amount for t in month_transactions if t.amount > 0),
                "shared_expense_categories": list(set(t.category for t in shared_expenses)),
                "individual_expense_categories": list(set(t.category for t in individual_expenses))
            },
            "user_analysis": user_analysis,
            "expense_sharing_analysis": self._analyze_expense_sharing(shared_expenses, household_users)
        }
    
    def _build_consolidated_income_statement(self, transactions: List[Transaction], 
                                           period: str) -> Dict[str, Any]:
        """Build income statement from consolidated transactions"""
        # Separate revenue and expenses
        revenues = [t for t in transactions if t.amount > 0]
        expenses = [t for t in transactions if t.amount < 0]
        
        # Calculate totals
        total_revenue = sum(t.amount for t in revenues)
        total_expenses = sum(abs(t.amount) for t in expenses)
        net_income = total_revenue - total_expenses
        
        # Categorize expenses
        expense_by_category = {}
        for expense in expenses:
            category = expense.category
            if category not in expense_by_category:
                expense_by_category[category] = Decimal("0")
            expense_by_category[category] += abs(expense.amount)
        
        # Calculate percentages
        def calc_percentage(amount: Decimal, base: Decimal) -> Decimal:
            return (amount / base * 100).quantize(Decimal("0.01")) if base > 0 else Decimal("0")
        
        return {
            "period": period,
            "revenue": {
                "total_revenue": total_revenue,
                "revenue_sources": self._analyze_revenue_sources(revenues)
            },
            "expenses": {
                "total_expenses": total_expenses,
                "by_category": expense_by_category,
                "category_percentages": {
                    cat: calc_percentage(amount, total_revenue) 
                    for cat, amount in expense_by_category.items()
                }
            },
            "net_income": net_income,
            "net_margin": calc_percentage(net_income, total_revenue)
        }
    
    def _analyze_revenue_sources(self, revenues: List[Transaction]) -> Dict[str, Decimal]:
        """Analyze revenue sources"""
        revenue_sources = {}
        for revenue in revenues:
            category = revenue.category
            if category not in revenue_sources:
                revenue_sources[category] = Decimal("0")
            revenue_sources[category] += revenue.amount
        return revenue_sources
    
    def _calculate_asset_allocation(self, consolidated_by_type: Dict[str, Any], 
                                  total_assets: Decimal) -> Dict[str, Decimal]:
        """Calculate asset allocation percentages"""
        if total_assets == 0:
            return {}
        
        allocation = {}
        for account_type, data in consolidated_by_type.items():
            allocation[account_type] = (data["total_balance"] / total_assets * 100).quantize(
                Decimal("0.01")
            )
        return allocation
    
    def _generate_comparison_summary(self, individual_reports: Dict[str, Any], 
                                   household_report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comparison summary between individual and household reports"""
        # Sum individual totals
        total_individual_revenue = sum(
            report["revenue"]["total_revenue"] for report in individual_reports.values()
        )
        total_individual_expenses = sum(
            report["expenses"]["total_expenses"] for report in individual_reports.values()
        )
        
        household_revenue = household_report["revenue"]["total_revenue"]
        household_expenses = household_report["expenses"]["total_expenses"]
        
        return {
            "revenue_reconciliation": {
                "sum_of_individual": total_individual_revenue,
                "household_total": household_revenue,
                "difference": household_revenue - total_individual_revenue
            },
            "expense_reconciliation": {
                "sum_of_individual": total_individual_expenses,
                "household_total": household_expenses,
                "difference": household_expenses - total_individual_expenses
            },
            "individual_contributions": {
                user_id: {
                    "revenue_percentage": (report["revenue"]["total_revenue"] / household_revenue * 100).quantize(Decimal("0.01")) if household_revenue > 0 else Decimal("0"),
                    "expense_percentage": (report["expenses"]["total_expenses"] / household_expenses * 100).quantize(Decimal("0.01")) if household_expenses > 0 else Decimal("0")
                }
                for user_id, report in individual_reports.items()
            }
        }
    
    def _analyze_expense_sharing(self, shared_expenses: List[Transaction], 
                               household_users: List[User]) -> Dict[str, Any]:
        """Analyze how shared expenses are distributed among users"""
        sharing_analysis = {}
        
        for category in set(t.category for t in shared_expenses):
            category_expenses = [t for t in shared_expenses if t.category == category]
            total_category_amount = sum(abs(t.amount) for t in category_expenses)
            
            user_contributions = {}
            for user in household_users:
                user_category_expenses = [t for t in category_expenses if t.user_id == user.id]
                user_contribution = sum(abs(t.amount) for t in user_category_expenses)
                user_contributions[user.id] = {
                    "user_name": user.name,
                    "amount": user_contribution,
                    "percentage": (user_contribution / total_category_amount * 100).quantize(Decimal("0.01")) if total_category_amount > 0 else Decimal("0")
                }
            
            sharing_analysis[category] = {
                "total_amount": total_category_amount,
                "user_contributions": user_contributions
            }
        
        return sharing_analysis


class TestMultiUserTransactionConsolidation:
    """Test multi-user transaction consolidation functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.generator = ConsolidatedReportGenerator()
        
        # Create test users
        self.user1 = User("user1", "Alice", "household1")
        self.user2 = User("user2", "Bob", "household1")
        self.user3 = User("user3", "Carol", "household2")  # Different household
        
        self.generator.register_user(self.user1)
        self.generator.register_user(self.user2)
        self.generator.register_user(self.user3)
        
        # Sample transactions
        self.sample_transactions = [
            # Household 1 - Alice
            Transaction("tx1", "user1", "Alice Salary", Decimal("8000.00"), "工资收入", "Debit", datetime(2024, 1, 15)),
            Transaction("tx2", "user1", "Rent Payment", Decimal("-1000.00"), "房租", "Debit", datetime(2024, 1, 1), is_shared=True),
            Transaction("tx3", "user1", "Alice Food", Decimal("-300.00"), "餐饮", "Cash", datetime(2024, 1, 10)),
            # Household 1 - Bob  
            Transaction("tx4", "user2", "Bob Salary", Decimal("7000.00"), "工资收入", "Debit", datetime(2024, 1, 15)),
            Transaction("tx5", "user2", "Utilities", Decimal("-200.00"), "水电费", "Debit", datetime(2024, 1, 5), is_shared=True),
            Transaction("tx6", "user2", "Bob Food", Decimal("-250.00"), "餐饮", "Cash", datetime(2024, 1, 12)),
            # Household 2 - Carol (different household)
            Transaction("tx7", "user3", "Carol Salary", Decimal("6000.00"), "工资收入", "Debit", datetime(2024, 1, 15)),
            Transaction("tx8", "user3", "Carol Rent", Decimal("-1500.00"), "房租", "Debit", datetime(2024, 1, 1))
        ]
    
    def test_multi_user_transaction_filtering(self):
        """Test filtering transactions for specific household"""
        analysis = self.generator.generate_multi_user_transaction_analysis(
            "household1", self.sample_transactions, 1, 2024
        )
        
        # Should only include Alice and Bob's transactions
        user_analysis = analysis["user_analysis"]
        assert "user1" in user_analysis
        assert "user2" in user_analysis
        assert "user3" not in user_analysis  # Different household
        
        # Check user names
        assert user_analysis["user1"]["user_name"] == "Alice"
        assert user_analysis["user2"]["user_name"] == "Bob"
    
    def test_shared_vs_individual_expense_separation(self):
        """Test separation of shared vs individual expenses"""
        analysis = self.generator.generate_multi_user_transaction_analysis(
            "household1", self.sample_transactions, 1, 2024
        )
        
        household_summary = analysis["household_summary"]
        
        # Shared expenses: Rent (1000) + Utilities (200) = 1200
        assert household_summary["total_shared_expenses"] == Decimal("1200.00")
        
        # Individual expenses: Alice Food (300) + Bob Food (250) = 550
        assert household_summary["total_individual_expenses"] == Decimal("550.00")
        
        # Total household income: Alice (8000) + Bob (7000) = 15000
        assert household_summary["total_household_income"] == Decimal("15000.00")
    
    def test_user_spending_analysis(self):
        """Test individual user spending analysis within household"""
        analysis = self.generator.generate_multi_user_transaction_analysis(
            "household1", self.sample_transactions, 1, 2024
        )
        
        alice_analysis = analysis["user_analysis"]["user1"]
        bob_analysis = analysis["user_analysis"]["user2"]
        
        # Alice: total spending = rent (1000) + food (300) = 1300
        assert alice_analysis["total_spending"] == Decimal("1300.00")
        assert alice_analysis["shared_spending"] == Decimal("1000.00")  # Just rent
        assert alice_analysis["individual_spending"] == Decimal("300.00")  # Food
        assert alice_analysis["income"] == Decimal("8000.00")
        
        # Bob: total spending = utilities (200) + food (250) = 450
        assert bob_analysis["total_spending"] == Decimal("450.00")
        assert bob_analysis["shared_spending"] == Decimal("200.00")  # Utilities
        assert bob_analysis["individual_spending"] == Decimal("250.00")  # Food
        assert bob_analysis["income"] == Decimal("7000.00")
    
    def test_expense_sharing_analysis(self):
        """Test analysis of how shared expenses are distributed"""
        analysis = self.generator.generate_multi_user_transaction_analysis(
            "household1", self.sample_transactions, 1, 2024
        )
        
        sharing_analysis = analysis["expense_sharing_analysis"]
        
        # Check rent sharing (only Alice paid)
        rent_sharing = sharing_analysis["房租"]
        assert rent_sharing["total_amount"] == Decimal("1000.00")
        assert rent_sharing["user_contributions"]["user1"]["amount"] == Decimal("1000.00")
        assert rent_sharing["user_contributions"]["user1"]["percentage"] == Decimal("100.00")
        assert rent_sharing["user_contributions"]["user2"]["amount"] == Decimal("0.00")
        
        # Check utilities sharing (only Bob paid)
        utilities_sharing = sharing_analysis["水电费"]
        assert utilities_sharing["total_amount"] == Decimal("200.00")
        assert utilities_sharing["user_contributions"]["user2"]["amount"] == Decimal("200.00")
        assert utilities_sharing["user_contributions"]["user2"]["percentage"] == Decimal("100.00")


class TestConsolidatedIncomeStatement:
    """Test consolidated income statement generation"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.generator = ConsolidatedReportGenerator()
        
        self.user1 = User("user1", "Alice", "household1")
        self.user2 = User("user2", "Bob", "household1")
        
        self.generator.register_user(self.user1)
        self.generator.register_user(self.user2)
        
        self.household_transactions = [
            # Combined income
            Transaction("tx1", "user1", "Alice Salary", Decimal("8000.00"), "工资收入", "Debit", datetime(2024, 1, 15)),
            Transaction("tx2", "user2", "Bob Salary", Decimal("7000.00"), "工资收入", "Debit", datetime(2024, 1, 15)),
            Transaction("tx3", "user1", "Investment", Decimal("500.00"), "投资收益", "Debit", datetime(2024, 1, 20)),
            # Combined expenses
            Transaction("tx4", "user1", "Rent", Decimal("-2000.00"), "房租", "Debit", datetime(2024, 1, 1)),
            Transaction("tx5", "user2", "Utilities", Decimal("-300.00"), "水电费", "Debit", datetime(2024, 1, 5)),
            Transaction("tx6", "user1", "Groceries", Decimal("-800.00"), "餐饮", "Cash", datetime(2024, 1, 10)),
            Transaction("tx7", "user2", "Transportation", Decimal("-200.00"), "交通", "Cash", datetime(2024, 1, 12))
        ]
    
    def test_consolidated_income_statement_generation(self):
        """Test generating consolidated household income statement"""
        statement = self.generator.generate_household_income_statement(
            "household1", self.household_transactions, 1, 2024
        )
        
        assert statement["period"] == "Household household1 - 2024-01"
        
        # Total revenue: 8000 + 7000 + 500 = 15500
        assert statement["revenue"]["total_revenue"] == Decimal("15500.00")
        
        # Total expenses: 2000 + 300 + 800 + 200 = 3300
        assert statement["expenses"]["total_expenses"] == Decimal("3300.00")
        
        # Net income: 15500 - 3300 = 12200
        assert statement["net_income"] == Decimal("12200.00")
    
    def test_consolidated_revenue_sources_analysis(self):
        """Test analysis of consolidated revenue sources"""
        statement = self.generator.generate_household_income_statement(
            "household1", self.household_transactions, 1, 2024
        )
        
        revenue_sources = statement["revenue"]["revenue_sources"]
        
        # Salary income: 8000 + 7000 = 15000
        assert revenue_sources["工资收入"] == Decimal("15000.00")
        
        # Investment income: 500
        assert revenue_sources["投资收益"] == Decimal("500.00")
    
    def test_consolidated_expense_categorization(self):
        """Test consolidated expense categorization"""
        statement = self.generator.generate_household_income_statement(
            "household1", self.household_transactions, 1, 2024
        )
        
        expenses_by_category = statement["expenses"]["by_category"]
        
        assert expenses_by_category["房租"] == Decimal("2000.00")
        assert expenses_by_category["水电费"] == Decimal("300.00")
        assert expenses_by_category["餐饮"] == Decimal("800.00")
        assert expenses_by_category["交通"] == Decimal("200.00")
    
    def test_consolidated_percentage_calculations(self):
        """Test percentage calculations in consolidated statement"""
        statement = self.generator.generate_household_income_statement(
            "household1", self.household_transactions, 1, 2024
        )
        
        category_percentages = statement["expenses"]["category_percentages"]
        total_revenue = statement["revenue"]["total_revenue"]
        
        # Rent percentage: 2000/15500 * 100 = 12.90%
        expected_rent_pct = (Decimal("2000.00") / total_revenue * 100).quantize(Decimal("0.01"))
        assert category_percentages["房租"] == expected_rent_pct
        
        # Net margin: 12200/15500 * 100 = 78.71%
        expected_margin = (statement["net_income"] / total_revenue * 100).quantize(Decimal("0.01"))
        assert statement["net_margin"] == expected_margin


class TestConsolidatedAssetPortfolio:
    """Test consolidated asset portfolio functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.generator = ConsolidatedReportGenerator()
        
        self.user1 = User("user1", "Alice", "household1")
        self.user2 = User("user2", "Bob", "household1")
        
        self.generator.register_user(self.user1)
        self.generator.register_user(self.user2)
        
        self.sample_assets = [
            # Alice's assets
            Asset("a1", "user1", "Alice Checking", Decimal("5000.00"), "checking", datetime(2024, 1, 31)),
            Asset("a2", "user1", "Alice Savings", Decimal("25000.00"), "savings", datetime(2024, 1, 31)),
            Asset("a3", "user1", "Alice 401k", Decimal("80000.00"), "retirement", datetime(2024, 1, 31)),
            # Bob's assets
            Asset("a4", "user2", "Bob Checking", Decimal("3000.00"), "checking", datetime(2024, 1, 31)),
            Asset("a5", "user2", "Bob Investment", Decimal("50000.00"), "investment", datetime(2024, 1, 31)),
        ]
    
    def test_asset_portfolio_consolidation(self):
        """Test consolidation of household asset portfolio"""
        portfolio = self.generator.consolidate_asset_portfolio(
            "household1", self.sample_assets
        )
        
        assert portfolio["household_id"] == "household1"
        
        # Total assets: 5000 + 25000 + 80000 + 3000 + 50000 = 163000
        assert portfolio["total_assets"] == Decimal("163000.00")
        
        # Check consolidated by type
        consolidated = portfolio["consolidated_by_type"]
        
        # Checking: Alice (5000) + Bob (3000) = 8000
        assert consolidated["checking"]["total_balance"] == Decimal("8000.00")
        assert consolidated["checking"]["account_count"] == 2
        
        # Savings: Alice only = 25000
        assert consolidated["savings"]["total_balance"] == Decimal("25000.00")
        assert consolidated["savings"]["account_count"] == 1
        
        # Investment: Bob only = 50000
        assert consolidated["investment"]["total_balance"] == Decimal("50000.00")
        
        # Retirement: Alice only = 80000
        assert consolidated["retirement"]["total_balance"] == Decimal("80000.00")
    
    def test_individual_asset_breakdown(self):
        """Test individual asset breakdown within household"""
        portfolio = self.generator.consolidate_asset_portfolio(
            "household1", self.sample_assets
        )
        
        individual_breakdown = portfolio["individual_breakdown"]
        
        # Alice's breakdown
        alice_assets = individual_breakdown["user1"]
        assert alice_assets["user_name"] == "Alice"
        assert alice_assets["total_assets"] == Decimal("110000.00")  # 5000 + 25000 + 80000
        assert alice_assets["by_type"]["checking"] == Decimal("5000.00")
        assert alice_assets["by_type"]["savings"] == Decimal("25000.00")
        assert alice_assets["by_type"]["retirement"] == Decimal("80000.00")
        
        # Bob's breakdown
        bob_assets = individual_breakdown["user2"]
        assert bob_assets["user_name"] == "Bob"
        assert bob_assets["total_assets"] == Decimal("53000.00")  # 3000 + 50000
        assert bob_assets["by_type"]["checking"] == Decimal("3000.00")
        assert bob_assets["by_type"]["investment"] == Decimal("50000.00")
    
    def test_asset_allocation_calculations(self):
        """Test asset allocation percentage calculations"""
        portfolio = self.generator.consolidate_asset_portfolio(
            "household1", self.sample_assets
        )
        
        allocation = portfolio["asset_allocation"]
        total_assets = portfolio["total_assets"]
        
        # Checking allocation: 8000/163000 * 100 = 4.91%
        expected_checking = (Decimal("8000.00") / total_assets * 100).quantize(Decimal("0.01"))
        assert allocation["checking"] == expected_checking
        
        # Retirement allocation: 80000/163000 * 100 = 49.08%
        expected_retirement = (Decimal("80000.00") / total_assets * 100).quantize(Decimal("0.01"))
        assert allocation["retirement"] == expected_retirement
        
        # All allocations should sum to 100%
        total_allocation = sum(allocation.values())
        assert abs(total_allocation - Decimal("100.00")) < Decimal("0.01")  # Allow for rounding
    
    def test_account_details_in_consolidation(self):
        """Test that account details are preserved in consolidation"""
        portfolio = self.generator.consolidate_asset_portfolio(
            "household1", self.sample_assets
        )
        
        checking_accounts = portfolio["consolidated_by_type"]["checking"]["accounts"]
        
        # Should have 2 checking accounts
        assert len(checking_accounts) == 2
        
        # Find Alice's account
        alice_account = next(acc for acc in checking_accounts if acc["user_id"] == "user1")
        assert alice_account["account_name"] == "Alice Checking"
        assert alice_account["balance"] == Decimal("5000.00")
        assert alice_account["user_name"] == "Alice"
        
        # Find Bob's account
        bob_account = next(acc for acc in checking_accounts if acc["user_id"] == "user2")
        assert bob_account["account_name"] == "Bob Checking"
        assert bob_account["balance"] == Decimal("3000.00")
        assert bob_account["user_name"] == "Bob"


class TestIndividualVsHouseholdReporting:
    """Test individual vs household reporting functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.generator = ConsolidatedReportGenerator()
        
        self.user1 = User("user1", "Alice", "household1")
        self.user2 = User("user2", "Bob", "household1")
        
        self.generator.register_user(self.user1)
        self.generator.register_user(self.user2)
        
        self.comparison_transactions = [
            # Alice transactions
            Transaction("tx1", "user1", "Alice Salary", Decimal("8000.00"), "工资收入", "Debit", datetime(2024, 1, 15)),
            Transaction("tx2", "user1", "Alice Food", Decimal("-400.00"), "餐饮", "Cash", datetime(2024, 1, 10)),
            # Bob transactions
            Transaction("tx3", "user2", "Bob Salary", Decimal("6000.00"), "工资收入", "Debit", datetime(2024, 1, 15)),
            Transaction("tx4", "user2", "Bob Transport", Decimal("-200.00"), "交通", "Cash", datetime(2024, 1, 12)),
            # Shared expense
            Transaction("tx5", "user1", "Shared Rent", Decimal("-2000.00"), "房租", "Debit", datetime(2024, 1, 1), is_shared=True)
        ]
    
    def test_individual_report_generation(self):
        """Test individual report generation for household members"""
        comparison = self.generator.generate_individual_vs_household_comparison(
            "household1", self.comparison_transactions, 1, 2024
        )
        
        individual_reports = comparison["individual_reports"]
        
        # Alice's individual report
        alice_report = individual_reports["user1"]
        assert alice_report["revenue"]["total_revenue"] == Decimal("8000.00")
        assert alice_report["expenses"]["total_expenses"] == Decimal("2400.00")  # 400 + 2000
        assert alice_report["net_income"] == Decimal("5600.00")
        
        # Bob's individual report
        bob_report = individual_reports["user2"]
        assert bob_report["revenue"]["total_revenue"] == Decimal("6000.00")
        assert bob_report["expenses"]["total_expenses"] == Decimal("200.00")
        assert bob_report["net_income"] == Decimal("5800.00")
    
    def test_household_vs_individual_reconciliation(self):
        """Test reconciliation between household and sum of individual reports"""
        comparison = self.generator.generate_individual_vs_household_comparison(
            "household1", self.comparison_transactions, 1, 2024
        )
        
        summary = comparison["summary"]
        household_report = comparison["household_report"]
        
        # Revenue reconciliation
        revenue_reconciliation = summary["revenue_reconciliation"]
        assert revenue_reconciliation["sum_of_individual"] == Decimal("14000.00")  # 8000 + 6000
        assert revenue_reconciliation["household_total"] == Decimal("14000.00")
        assert revenue_reconciliation["difference"] == Decimal("0.00")  # Should match
        
        # Expense reconciliation
        expense_reconciliation = summary["expense_reconciliation"]
        assert expense_reconciliation["sum_of_individual"] == Decimal("2600.00")  # 2400 + 200
        assert expense_reconciliation["household_total"] == Decimal("2600.00")
        assert expense_reconciliation["difference"] == Decimal("0.00")  # Should match
    
    def test_individual_contribution_analysis(self):
        """Test analysis of individual contributions to household totals"""
        comparison = self.generator.generate_individual_vs_household_comparison(
            "household1", self.comparison_transactions, 1, 2024
        )
        
        summary = comparison["summary"]
        contributions = summary["individual_contributions"]
        
        # Alice's contributions
        alice_contributions = contributions["user1"]
        # Alice revenue: 8000/14000 = 57.14%
        expected_alice_revenue_pct = (Decimal("8000.00") / Decimal("14000.00") * 100).quantize(Decimal("0.01"))
        assert alice_contributions["revenue_percentage"] == expected_alice_revenue_pct
        
        # Alice expenses: 2400/2600 = 92.31%
        expected_alice_expense_pct = (Decimal("2400.00") / Decimal("2600.00") * 100).quantize(Decimal("0.01"))
        assert alice_contributions["expense_percentage"] == expected_alice_expense_pct
        
        # Bob's contributions
        bob_contributions = contributions["user2"]
        # Bob revenue: 6000/14000 = 42.86%
        expected_bob_revenue_pct = (Decimal("6000.00") / Decimal("14000.00") * 100).quantize(Decimal("0.01"))
        assert bob_contributions["revenue_percentage"] == expected_bob_revenue_pct
    
    def test_household_report_completeness(self):
        """Test that household report includes all household member data"""
        comparison = self.generator.generate_individual_vs_household_comparison(
            "household1", self.comparison_transactions, 1, 2024
        )
        
        household_report = comparison["household_report"]
        
        # Should include all transaction data
        assert household_report["revenue"]["total_revenue"] == Decimal("14000.00")
        assert household_report["expenses"]["total_expenses"] == Decimal("2600.00")
        assert household_report["net_income"] == Decimal("11400.00")
        
        # Should have all expense categories
        expenses_by_category = household_report["expenses"]["by_category"]
        assert "餐饮" in expenses_by_category
        assert "交通" in expenses_by_category
        assert "房租" in expenses_by_category
        
        assert expenses_by_category["餐饮"] == Decimal("400.00")
        assert expenses_by_category["交通"] == Decimal("200.00")
        assert expenses_by_category["房租"] == Decimal("2000.00")


class TestConsolidatedReportEdgeCases:
    """Test edge cases in consolidated reporting"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.generator = ConsolidatedReportGenerator()
        
        self.user1 = User("user1", "Alice", "household1")
        self.generator.register_user(self.user1)
    
    def test_single_user_household(self):
        """Test consolidated reporting for single-user household"""
        single_user_transactions = [
            Transaction("tx1", "user1", "Salary", Decimal("5000.00"), "工资收入", "Debit", datetime(2024, 1, 15)),
            Transaction("tx2", "user1", "Rent", Decimal("-1500.00"), "房租", "Debit", datetime(2024, 1, 1))
        ]
        
        statement = self.generator.generate_household_income_statement(
            "household1", single_user_transactions, 1, 2024
        )
        
        # Should work same as individual report
        assert statement["revenue"]["total_revenue"] == Decimal("5000.00")
        assert statement["expenses"]["total_expenses"] == Decimal("1500.00")
        assert statement["net_income"] == Decimal("3500.00")
    
    def test_empty_household(self):
        """Test consolidated reporting for household with no transactions"""
        empty_statement = self.generator.generate_household_income_statement(
            "household1", [], 1, 2024
        )
        
        assert empty_statement["revenue"]["total_revenue"] == Decimal("0.00")
        assert empty_statement["expenses"]["total_expenses"] == Decimal("0.00")
        assert empty_statement["net_income"] == Decimal("0.00")
    
    def test_nonexistent_household(self):
        """Test reporting for non-existent household"""
        statement = self.generator.generate_household_income_statement(
            "nonexistent", [], 1, 2024
        )
        
        # Should return empty statement
        assert statement["revenue"]["total_revenue"] == Decimal("0.00")
        assert statement["expenses"]["total_expenses"] == Decimal("0.00")
    
    def test_mixed_household_transactions(self):
        """Test household with transactions from different households"""
        self.user2 = User("user2", "Bob", "household2")  # Different household
        self.generator.register_user(self.user2)
        
        mixed_transactions = [
            Transaction("tx1", "user1", "Alice Income", Decimal("3000.00"), "工资收入", "Debit", datetime(2024, 1, 15)),
            Transaction("tx2", "user2", "Bob Income", Decimal("4000.00"), "工资收入", "Debit", datetime(2024, 1, 15)),  # Different household
        ]
        
        household1_statement = self.generator.generate_household_income_statement(
            "household1", mixed_transactions, 1, 2024
        )
        
        # Should only include Alice's transactions
        assert household1_statement["revenue"]["total_revenue"] == Decimal("3000.00")