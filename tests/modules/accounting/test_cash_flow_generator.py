"""
Test suite for Cash Flow Statement Generation (Model Layer)

Tests Phase 1 of the TDD plan: CashFlowStatementGenerator functionality
Based on the approved TDD plan at .Claude/docs/tdd-plan.md
"""

import pytest
from typing import List, Dict

from src.modules.accounting.models.domain.transaction import Transaction
from src.modules.accounting.models.domain.category import CategoryMapper
from src.modules.accounting.models.business.cash_flow_generator import CashFlowStatementGenerator


class TestCashFlowStatementStructure:
    """Test 1.1-1.3: Basic cash flow statement structure and operating activities"""

    def setup_method(self):
        """Setup test fixtures"""
        self.category_mapper = CategoryMapper()
        self.generator = CashFlowStatementGenerator(self.category_mapper)

    def test_cash_flow_statement_has_required_sections(self):
        """
        Test 1.1: Verify cash flow statement contains Operating, Investing, Financing sections

        Expected structure:
        {
            'Entity': 'User1',
            'Operating Activities': {...},
            'Investing Activities': {...},
            'Financing Activities': {...},
            'Net Change in Cash': <float>
        }
        """
        # Create minimal transaction for testing structure
        transactions = [
            Transaction("Salary", 5000.0, "工资收入", "Bank Account", "User1"),
        ]
        transactions[0].transaction_type = "revenue"

        statement = self.generator.generate_statement(transactions, "User1")

        # Verify top-level structure
        assert "Entity" in statement, "Statement must have 'Entity' field"
        assert statement["Entity"] == "User1"

        # Verify three main sections exist
        assert "Operating Activities" in statement, "Statement must have 'Operating Activities' section"
        assert "Investing Activities" in statement, "Statement must have 'Investing Activities' section"
        assert "Financing Activities" in statement, "Statement must have 'Financing Activities' section"

        # Verify each section has proper subsections
        assert "Details" in statement["Operating Activities"]
        assert "Net Cash from Operating" in statement["Operating Activities"]

        assert "Details" in statement["Investing Activities"]
        assert "Net Cash from Investing" in statement["Investing Activities"]

        assert "Details" in statement["Financing Activities"]
        assert "Net Cash from Financing" in statement["Financing Activities"]

        # Verify net change calculation field
        assert "Net Change in Cash" in statement

    def test_operating_activities_includes_revenue(self):
        """
        Test 1.2: Revenue transactions should appear in Operating Activities

        Revenue should create positive cash flow in Operating Activities
        """
        transactions = [
            Transaction("Salary", 8000.0, "工资收入", "Bank Account", "User1"),
            Transaction("Freelance", 2000.0, "服务收入", "Cash", "User1"),
        ]

        for t in transactions:
            t.transaction_type = "revenue"

        statement = self.generator.generate_statement(transactions, "User1")

        # Check that revenue appears in Operating Activities
        operating_details = statement["Operating Activities"]["Details"]
        assert len(operating_details) > 0, "Operating Activities should have revenue items"

        # Check net operating cash flow is positive from revenue
        net_operating = statement["Operating Activities"]["Net Cash from Operating"]
        assert net_operating == 10000.0, f"Expected 10000.0, got {net_operating}"

        # Verify revenue categories are present
        assert "工资收入" in operating_details or "Salary" in str(operating_details)
        assert "服务收入" in operating_details or "Freelance" in str(operating_details)

    def test_operating_activities_includes_expenses(self):
        """
        Test 1.3: Expense transactions should appear in Operating Activities

        Expenses should create negative cash flow in Operating Activities
        """
        transactions = [
            Transaction("Rent", 2000.0, "房租", "Bank Account", "User1"),
            Transaction("Food", 500.0, "餐饮", "Credit Card", "User1"),
            Transaction("Transport", 300.0, "交通", "Cash", "User1"),
        ]

        for t in transactions:
            t.transaction_type = "expense"

        statement = self.generator.generate_statement(transactions, "User1")

        # Check that expenses appear in Operating Activities
        operating_details = statement["Operating Activities"]["Details"]
        assert len(operating_details) > 0, "Operating Activities should have expense items"

        # Check net operating cash flow is negative from expenses
        net_operating = statement["Operating Activities"]["Net Cash from Operating"]
        # Expenses create negative cash flow: -(2000 + 500 + 300) = -2800
        assert net_operating == -2800.0, f"Expected -2800.0, got {net_operating}"


class TestOperatingActivitiesCalculations:
    """Test 1.4: Net operating cash flow calculation"""

    def setup_method(self):
        """Setup test fixtures"""
        self.category_mapper = CategoryMapper()
        self.generator = CashFlowStatementGenerator(self.category_mapper)

    def test_net_operating_cash_flow_calculation(self):
        """
        Test 1.4: Net Operating Cash Flow = Revenue - Expenses

        When no accruals, net operating cash flow should match net income
        """
        transactions = [
            # Revenue
            Transaction("Salary", 10000.0, "工资收入", "Bank Account", "User1"),
            Transaction("Consulting", 3000.0, "服务收入", "Cash", "User1"),

            # Operating expenses
            Transaction("Rent", 2000.0, "房租", "Bank Account", "User1"),
            Transaction("Food", 800.0, "餐饮", "Credit Card", "User1"),
            Transaction("Utilities", 500.0, "水电", "Bank Account", "User1"),
        ]

        # Set transaction types
        transactions[0].transaction_type = "revenue"
        transactions[1].transaction_type = "revenue"
        for i in range(2, 5):
            transactions[i].transaction_type = "expense"

        statement = self.generator.generate_statement(transactions, "User1")

        # Calculate expected
        total_revenue = 10000.0 + 3000.0  # 13000
        total_expenses = 2000.0 + 800.0 + 500.0  # 3300
        expected_net_operating_cf = total_revenue - total_expenses  # 9700

        # Verify calculation
        net_operating_cf = statement["Operating Activities"]["Net Cash from Operating"]
        assert net_operating_cf == expected_net_operating_cf, \
            f"Expected {expected_net_operating_cf}, got {net_operating_cf}"


class TestInvestingActivities:
    """Test 1.5: Investing activities - investment purchases"""

    def setup_method(self):
        """Setup test fixtures"""
        self.category_mapper = CategoryMapper()
        self.generator = CashFlowStatementGenerator(self.category_mapper)

    def test_investing_activities_investment_purchases(self):
        """
        Test 1.5: Investment transactions should appear in Investing Activities

        Investment purchases should create negative cash flow in Investing Activities
        """
        transactions = [
            Transaction("Stock Purchase", 5000.0, "投资支出", "Bank Account", "User1"),
            Transaction("Property Investment", 100000.0, "房产投资", "Bank Account", "User1"),
        ]

        for t in transactions:
            t.transaction_type = "expense"  # Investments are expense-type but in different category

        statement = self.generator.generate_statement(transactions, "User1")

        # Check investing activities section
        investing_details = statement["Investing Activities"]["Details"]
        assert len(investing_details) > 0, "Investing Activities should have investment items"

        # Check net investing cash flow is negative (cash outflow)
        net_investing = statement["Investing Activities"]["Net Cash from Investing"]
        # Expected: -(5000 + 100000) = -105000
        assert net_investing == -105000.0, f"Expected -105000.0, got {net_investing}"


class TestFinancingActivities:
    """Test 1.6: Financing activities - loans and debt"""

    def setup_method(self):
        """Setup test fixtures"""
        self.category_mapper = CategoryMapper()
        self.generator = CashFlowStatementGenerator(self.category_mapper)

    def test_financing_activities_loan_receipt(self):
        """
        Test 1.6: Loan transactions should appear in Financing Activities

        Loan receipts should create positive cash flow
        Debt repayments should create negative cash flow
        """
        transactions = [
            Transaction("Loan Receipt", 20000.0, "借款", "Bank Account", "User1"),
            Transaction("Debt Repayment", 5000.0, "还款", "Bank Account", "User1"),
        ]

        # Loan receipt is revenue-type in financing category
        transactions[0].transaction_type = "revenue"
        # Debt repayment is expense-type in financing category
        transactions[1].transaction_type = "expense"

        statement = self.generator.generate_statement(transactions, "User1")

        # Check financing activities section
        financing_details = statement["Financing Activities"]["Details"]
        assert len(financing_details) > 0, "Financing Activities should have loan/debt items"

        # Check net financing cash flow
        net_financing = statement["Financing Activities"]["Net Cash from Financing"]
        # Expected: 20000 (inflow) - 5000 (outflow) = 15000
        assert net_financing == 15000.0, f"Expected 15000.0, got {net_financing}"


class TestNetChangeInCash:
    """Test 1.7: Net change in cash calculation"""

    def setup_method(self):
        """Setup test fixtures"""
        self.category_mapper = CategoryMapper()
        self.generator = CashFlowStatementGenerator(self.category_mapper)

    def test_net_change_in_cash_calculation(self):
        """
        Test 1.7: Net Change in Cash = Operating + Investing + Financing

        Comprehensive test with all three activity types
        """
        transactions = [
            # Operating activities
            Transaction("Salary", 15000.0, "工资收入", "Bank Account", "User1"),
            Transaction("Rent", 3000.0, "房租", "Bank Account", "User1"),
            Transaction("Food", 1000.0, "餐饮", "Credit Card", "User1"),

            # Investing activities
            Transaction("Stock Purchase", 5000.0, "投资支出", "Bank Account", "User1"),

            # Financing activities
            Transaction("Loan Receipt", 10000.0, "借款", "Bank Account", "User1"),
        ]

        # Set transaction types
        transactions[0].transaction_type = "revenue"
        transactions[1].transaction_type = "expense"
        transactions[2].transaction_type = "expense"
        transactions[3].transaction_type = "expense"
        transactions[4].transaction_type = "revenue"

        statement = self.generator.generate_statement(transactions, "User1")

        # Calculate expected
        net_operating = 15000.0 - 3000.0 - 1000.0  # 11000
        net_investing = -5000.0  # -5000
        net_financing = 10000.0  # 10000
        expected_net_change = net_operating + net_investing + net_financing  # 16000

        # Verify each section
        assert statement["Operating Activities"]["Net Cash from Operating"] == net_operating
        assert statement["Investing Activities"]["Net Cash from Investing"] == net_investing
        assert statement["Financing Activities"]["Net Cash from Financing"] == net_financing

        # Verify total net change
        assert statement["Net Change in Cash"] == expected_net_change, \
            f"Expected {expected_net_change}, got {statement['Net Change in Cash']}"


class TestMultiUserCashFlow:
    """Test 1.8: Multi-user cash flow generation"""

    def setup_method(self):
        """Setup test fixtures"""
        self.category_mapper = CategoryMapper()
        self.generator = CashFlowStatementGenerator(self.category_mapper)

    def test_multi_user_cash_flow_generation(self):
        """
        Test 1.8: Generate separate cash flow statements for multiple users

        Each user should have their own statement with correct entity name
        """
        # User1 transactions
        user1_transactions = [
            Transaction("User1 Salary", 10000.0, "工资收入", "Bank Account", "User1"),
            Transaction("User1 Rent", 2000.0, "房租", "Bank Account", "User1"),
        ]
        user1_transactions[0].transaction_type = "revenue"
        user1_transactions[1].transaction_type = "expense"

        # User2 transactions
        user2_transactions = [
            Transaction("User2 Salary", 12000.0, "工资收入", "Bank Account", "User2"),
            Transaction("User2 Food", 1500.0, "餐饮", "Credit Card", "User2"),
        ]
        user2_transactions[0].transaction_type = "revenue"
        user2_transactions[1].transaction_type = "expense"

        # Generate separate statements
        user1_statement = self.generator.generate_statement(user1_transactions, "User1")
        user2_statement = self.generator.generate_statement(user2_transactions, "User2")

        # Verify entity names
        assert user1_statement["Entity"] == "User1"
        assert user2_statement["Entity"] == "User2"

        # Verify User1 calculations
        assert user1_statement["Operating Activities"]["Net Cash from Operating"] == 8000.0  # 10000 - 2000
        assert user1_statement["Net Change in Cash"] == 8000.0

        # Verify User2 calculations
        assert user2_statement["Operating Activities"]["Net Cash from Operating"] == 10500.0  # 12000 - 1500
        assert user2_statement["Net Change in Cash"] == 10500.0

        # Combined statement
        all_transactions = user1_transactions + user2_transactions
        combined_statement = self.generator.generate_statement(all_transactions, "Combined")

        assert combined_statement["Entity"] == "Combined"
        # Combined net change = 8000 + 10500 = 18500
        assert combined_statement["Net Change in Cash"] == 18500.0


class TestEdgeCases:
    """Test 1.9-1.10: Edge cases and consistency checks"""

    def setup_method(self):
        """Setup test fixtures"""
        self.category_mapper = CategoryMapper()
        self.generator = CashFlowStatementGenerator(self.category_mapper)

    def test_empty_transactions_returns_zero_cash_flow(self):
        """
        Test 1.9: Handle empty transaction list gracefully

        Should return valid statement structure with zero amounts
        """
        transactions = []

        statement = self.generator.generate_statement(transactions, "EmptyUser")

        # Verify structure exists
        assert "Entity" in statement
        assert statement["Entity"] == "EmptyUser"

        # Verify all sections are zero
        assert statement["Operating Activities"]["Net Cash from Operating"] == 0.0
        assert statement["Investing Activities"]["Net Cash from Investing"] == 0.0
        assert statement["Financing Activities"]["Net Cash from Financing"] == 0.0
        assert statement["Net Change in Cash"] == 0.0

        # Verify details are empty
        assert len(statement["Operating Activities"]["Details"]) == 0
        assert len(statement["Investing Activities"]["Details"]) == 0
        assert len(statement["Financing Activities"]["Details"]) == 0

    def test_net_operating_cash_flow_matches_net_income(self):
        """
        Test 1.10: When no accruals, Net Operating Cash Flow should approximately equal Net Income

        This test verifies consistency between cash flow and income statement
        For simple cash-based transactions, they should match
        """
        from src.modules.accounting.models.business.income_statement_generator import IncomeStatementGenerator

        transactions = [
            # Simple revenue and expenses (no accruals, no prepaid)
            Transaction("Salary", 15000.0, "工资收入", "Bank Account", "User1"),
            Transaction("Consulting", 5000.0, "服务收入", "Cash", "User1"),
            Transaction("Rent", 3000.0, "房租", "Bank Account", "User1"),
            Transaction("Food", 1500.0, "餐饮", "Credit Card", "User1"),
            Transaction("Utilities", 500.0, "水电", "Bank Account", "User1"),
        ]

        # Set transaction types
        transactions[0].transaction_type = "revenue"
        transactions[1].transaction_type = "revenue"
        for i in range(2, 5):
            transactions[i].transaction_type = "expense"

        # Generate both statements
        cash_flow_statement = self.generator.generate_statement(transactions, "User1")

        income_generator = IncomeStatementGenerator(self.category_mapper)
        income_statement = income_generator.generate_statement(transactions, "User1")

        # Compare net operating cash flow with net income
        net_operating_cf = cash_flow_statement["Operating Activities"]["Net Cash from Operating"]
        net_income = income_statement["Net Income"]

        # They should be equal for simple cash-based transactions
        assert abs(net_operating_cf - net_income) < 0.01, \
            f"Net Operating Cash Flow ({net_operating_cf}) should match Net Income ({net_income})"

        # Expected values
        expected_revenue = 15000.0 + 5000.0  # 20000
        expected_expenses = 3000.0 + 1500.0 + 500.0  # 5000
        expected_net = expected_revenue - expected_expenses  # 15000

        assert net_operating_cf == expected_net
        assert net_income == expected_net


if __name__ == "__main__":
    pytest.main([__file__, "-v"])