"""
Integration Tests for Income Statement & Cash Flow Statement Generation

Tests Phase 2 and Phase 4 of the TDD plan:
- Phase 2: Presenter layer tests for both statements
- Phase 4: End-to-end integration tests

Based on the approved TDD plan at .Claude/docs/tdd-plan.md
"""

import pytest
import pandas as pd
import tempfile
import os
from typing import List, Dict

from src.modules.accounting.models.domain.transaction import Transaction
from src.modules.accounting.models.domain.category import CategoryMapper
from src.modules.accounting.presenters.income_statement_presenter import IncomeStatementPresenter
from src.modules.accounting.presenters.cash_flow_presenter import CashFlowPresenter


class TestCashFlowPresenterDataFrameInput:
    """Test 2.1-2.2: CashFlowPresenter DataFrame input and error handling"""

    def test_cash_flow_presenter_accepts_dataframe(self):
        """
        Test 2.1: CashFlowPresenter should accept DataFrame input like IncomeStatementPresenter

        The presenter should be able to process a clean DataFrame directly
        """
        # Create a sample DataFrame matching the cleaned CSV format
        data = {
            'Description': ['Salary', 'Rent', 'Food'],
            'Amount': [10000.0, 2000.0, 500.0],
            'Debit': ['Bank Account', '房租', '餐饮'],
            'Credit': ['工资收入', 'Bank Account', 'Credit Card'],
            'User': ['User1', 'User1', 'User1']
        }
        df = pd.DataFrame(data)

        # CashFlowPresenter should have a method similar to IncomeStatementPresenter
        presenter = CashFlowPresenter()

        # This method should exist (will fail until implemented)
        cashflow_statements, users = presenter.process_clean_dataframe_and_generate_statements(df)

        # Verify return structure
        assert isinstance(cashflow_statements, dict), "Should return dict of statements"
        assert isinstance(users, list), "Should return list of users"
        assert "User1" in cashflow_statements
        assert "Combined" in cashflow_statements
        assert "User1" in users

    def test_cash_flow_presenter_handles_validation_errors(self):
        """
        Test 2.2: CashFlowPresenter should handle validation errors gracefully

        Invalid data should raise appropriate errors
        """
        presenter = CashFlowPresenter()

        # Test with invalid DataFrame (missing required columns)
        invalid_df = pd.DataFrame({'Invalid': [1, 2, 3]})

        with pytest.raises(Exception) as exc_info:
            presenter.process_clean_dataframe_and_generate_statements(invalid_df)

        # Should raise a meaningful error
        assert "column" in str(exc_info.value).lower() or "required" in str(exc_info.value).lower()


class TestIncomeStatementPresenterGeneratesBothStatements:
    """Test 2.3-2.4: IncomeStatementPresenter should generate both statements"""

    def test_presenter_generates_both_income_and_cash_flow(self):
        """
        Test 2.3: IncomeStatementPresenter should return both income and cash flow statements

        Expected return: (income_statements, cashflow_statements, users)
        This is the key integration change - one presenter generates both
        """
        # Create sample DataFrame
        data = {
            'Description': ['Salary', 'Consulting', 'Rent', 'Food', 'Stock Purchase'],
            'Amount': [15000.0, 5000.0, 3000.0, 1000.0, 8000.0],
            'Debit': ['Bank Account', 'Cash', '房租', '餐饮', '投资支出'],
            'Credit': ['工资收入', '服务收入', 'Bank Account', 'Credit Card', 'Bank Account'],
            'User': ['User1', 'User1', 'User1', 'User1', 'User1']
        }
        df = pd.DataFrame(data)

        presenter = IncomeStatementPresenter()

        # This should now return THREE values instead of two
        result = presenter.process_clean_dataframe_and_generate_statements(df)

        # Unpack the result (should be 3 values now)
        assert len(result) == 3, "Should return 3 values: (income_statements, cashflow_statements, users)"

        income_statements, cashflow_statements, users = result

        # Verify income statements
        assert isinstance(income_statements, dict)
        assert "User1" in income_statements
        assert "Combined" in income_statements
        assert "Total Revenue" in income_statements["User1"]
        assert "Net Income" in income_statements["User1"]

        # Verify cash flow statements
        assert isinstance(cashflow_statements, dict)
        assert "User1" in cashflow_statements
        assert "Combined" in cashflow_statements
        assert "Operating Activities" in cashflow_statements["User1"]
        assert "Net Change in Cash" in cashflow_statements["User1"]

        # Verify users
        assert isinstance(users, list)
        assert "User1" in users

    def test_presenter_integration_both_statements_consistent(self):
        """
        Test 2.4: Income and cash flow statements should be consistent

        Both statements should:
        - Use the same users
        - Process the same transaction data
        - Have consistent net amounts (for simple transactions)
        """
        # Create comprehensive test data
        data = {
            'Description': [
                'User1 Salary', 'User1 Rent', 'User1 Food',
                'User2 Salary', 'User2 Transport'
            ],
            'Amount': [12000.0, 2500.0, 800.0, 10000.0, 500.0],
            'Debit': ['Bank Account', '房租', '餐饮', 'Bank Account', '交通'],
            'Credit': ['工资收入', 'Bank Account', 'Credit Card', '工资收入', 'Cash'],
            'User': ['User1', 'User1', 'User1', 'User2', 'User2']
        }
        df = pd.DataFrame(data)

        presenter = IncomeStatementPresenter()
        income_statements, cashflow_statements, users = \
            presenter.process_clean_dataframe_and_generate_statements(df)

        # Check consistency: same users in both statements
        assert set(income_statements.keys()) == set(cashflow_statements.keys()), \
            "Both statements should have same entities"

        # Check consistency: users list matches
        assert len(users) == 2
        assert "User1" in users
        assert "User2" in users

        # For User1: Check Net Income ≈ Net Operating Cash Flow (simple cash transactions)
        user1_net_income = income_statements["User1"]["Net Income"]
        user1_net_operating_cf = cashflow_statements["User1"]["Operating Activities"]["Net Cash from Operating"]

        # Should be equal for simple operating transactions
        assert abs(user1_net_income - user1_net_operating_cf) < 0.01, \
            f"User1 Net Income ({user1_net_income}) should match Net Operating CF ({user1_net_operating_cf})"

        # Same for User2
        user2_net_income = income_statements["User2"]["Net Income"]
        user2_net_operating_cf = cashflow_statements["User2"]["Operating Activities"]["Net Cash from Operating"]

        assert abs(user2_net_income - user2_net_operating_cf) < 0.01, \
            f"User2 Net Income ({user2_net_income}) should match Net Operating CF ({user2_net_operating_cf})"


class TestEndToEndCSVToBothStatements:
    """Test 4.1: End-to-end workflow from CSV to both statements"""

    def test_e2e_csv_to_both_statements(self):
        """
        Test 4.1: Complete workflow from CSV upload to displaying both statements

        Steps:
        1. Upload CSV
        2. Clean and validate
        3. Generate both income and cash flow statements
        4. Display both statements side-by-side
        """
        # Create comprehensive test CSV
        csv_content = """Description,Amount,Debit,Credit,User
Salary,¥15000.00,Bank Account,工资收入,User1
Freelance Income,¥3000.00,Cash,服务收入,User1
Rent,¥3000.00,房租,Bank Account,User1
Food,¥1500.00,餐饮,Credit Card,User1
Transportation,¥500.00,交通,Cash,User1
Stock Purchase,¥5000.00,投资支出,Bank Account,User1
Loan Receipt,¥10000.00,Bank Account,借款,User1"""

        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as f:
            f.write(csv_content)
            csv_path = f.name

        try:
            # Step 1: Upload and process CSV
            presenter = IncomeStatementPresenter()

            # Step 2: Clean and validate
            cleaned_df, validation_report = presenter.clean_and_validate_csv(csv_path)

            # Verify cleaning succeeded
            assert validation_report is not None
            assert len(cleaned_df) == 7, "Should have 7 transactions"

            # Step 3: Generate both statements
            income_statements, cashflow_statements, users = \
                presenter.process_clean_dataframe_and_generate_statements(cleaned_df)

            # Verify income statement
            assert "User1" in income_statements
            user1_income = income_statements["User1"]
            assert user1_income["Total Revenue"] == 18000.0  # 15000 + 3000
            # Operating expenses: 3000 + 1500 + 500 = 5000
            # Note: Stock purchase and loan are non-operating
            assert user1_income["Net Income"] > 0

            # Verify cash flow statement
            assert "User1" in cashflow_statements
            user1_cashflow = cashflow_statements["User1"]

            # Operating activities: revenue - operating expenses
            assert user1_cashflow["Operating Activities"]["Net Cash from Operating"] > 0

            # Investing activities: stock purchase (negative)
            assert user1_cashflow["Investing Activities"]["Net Cash from Investing"] < 0

            # Financing activities: loan receipt (positive)
            assert user1_cashflow["Financing Activities"]["Net Cash from Financing"] > 0

            # Net change in cash
            assert "Net Change in Cash" in user1_cashflow

        finally:
            os.unlink(csv_path)


class TestBothStatementsUseSameTransactions:
    """Test 4.2: Both statements should use same transaction objects"""

    def test_both_statements_use_same_transactions(self):
        """
        Test 4.2: Verify no re-parsing, both statements use same Transaction list

        Both generators should receive the same transaction objects,
        ensuring data consistency
        """
        # Create test data
        data = {
            'Description': ['Salary', 'Rent', 'Investment'],
            'Amount': [10000.0, 2000.0, 5000.0],
            'Debit': ['Bank Account', '房租', '投资支出'],
            'Credit': ['工资收入', 'Bank Account', 'Bank Account'],
            'User': ['User1', 'User1', 'User1']
        }
        df = pd.DataFrame(data)

        presenter = IncomeStatementPresenter()
        income_statements, cashflow_statements, users = \
            presenter.process_clean_dataframe_and_generate_statements(df)

        # Both statements should be generated from the same data
        # Verify by checking that transaction counts are consistent

        # Income statement should process 3 transactions (revenue + expenses)
        user1_income = income_statements["User1"]
        assert user1_income["Total Revenue"] == 10000.0  # Only salary is revenue

        # Cash flow should also process same 3 transactions
        user1_cashflow = cashflow_statements["User1"]

        # All three transactions should affect cash:
        # - Salary: +10000 (operating)
        # - Rent: -2000 (operating)
        # - Investment: -5000 (investing)
        expected_net_change = 10000.0 - 2000.0 - 5000.0  # 3000
        assert user1_cashflow["Net Change in Cash"] == expected_net_change


class TestMultiUserIntegration:
    """Test 4.3: Multi-user integration for both statements"""

    def test_multi_user_both_statements(self):
        """
        Test 4.3: Individual users sum to Combined for both statements

        Combined statement should equal sum of individual statements
        """
        # Create multi-user CSV
        csv_content = """Description,Amount,Debit,Credit,User
User1 Salary,¥12000.00,Bank Account,工资收入,User1
User1 Rent,¥2000.00,房租,Bank Account,User1
User1 Food,¥800.00,餐饮,Credit Card,User1
User2 Salary,¥10000.00,Bank Account,工资收入,User2
User2 Transport,¥500.00,交通,Cash,User2
User2 Investment,¥3000.00,投资支出,Bank Account,User2"""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as f:
            f.write(csv_content)
            csv_path = f.name

        try:
            presenter = IncomeStatementPresenter()
            cleaned_df, _ = presenter.clean_and_validate_csv(csv_path)

            income_statements, cashflow_statements, users = \
                presenter.process_clean_dataframe_and_generate_statements(cleaned_df)

            # Verify multi-user structure
            assert len(users) == 2
            assert "User1" in users
            assert "User2" in users
            assert "User1" in income_statements
            assert "User2" in income_statements
            assert "Combined" in income_statements
            assert "User1" in cashflow_statements
            assert "User2" in cashflow_statements
            assert "Combined" in cashflow_statements

            # Income Statement: Check Combined = User1 + User2
            user1_net_income = income_statements["User1"]["Net Income"]
            user2_net_income = income_statements["User2"]["Net Income"]
            combined_net_income = income_statements["Combined"]["Net Income"]

            assert abs(combined_net_income - (user1_net_income + user2_net_income)) < 0.01, \
                "Combined net income should equal sum of individual users"

            # Cash Flow: Check Combined = User1 + User2
            user1_net_change = cashflow_statements["User1"]["Net Change in Cash"]
            user2_net_change = cashflow_statements["User2"]["Net Change in Cash"]
            combined_net_change = cashflow_statements["Combined"]["Net Change in Cash"]

            assert abs(combined_net_change - (user1_net_change + user2_net_change)) < 0.01, \
                "Combined net change in cash should equal sum of individual users"

        finally:
            os.unlink(csv_path)


class TestStorageIntegration:
    """Test 4.4: Storage integration for both statements"""

    def test_storage_saves_both_statements(self):
        """
        Test 4.4: Verify both JSON files created with correct structure

        When saving, should create:
        - {YYYY-MM}/income_statement.json
        - {YYYY-MM}/cash_flow.json

        Both in the same directory with proper structure
        """
        from src.modules.accounting.core.io import MonthlyReportStorage
        import json

        # Create sample statements
        income_statement = {
            "Entity": "User1",
            "Total Revenue": 10000.0,
            "Revenue": {"工资收入": 10000.0},
            "Total Expenses": 2000.0,
            "Expenses": {"Rent": 2000.0},
            "Net Income": 8000.0
        }

        cashflow_statement = {
            "Entity": "User1",
            "Operating Activities": {
                "Details": {"工资收入": 10000.0, "Rent": -2000.0},
                "Net Cash from Operating": 8000.0
            },
            "Investing Activities": {
                "Details": {},
                "Net Cash from Investing": 0.0
            },
            "Financing Activities": {
                "Details": {},
                "Net Cash from Financing": 0.0
            },
            "Net Change in Cash": 8000.0
        }

        # Create temporary storage directory
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = MonthlyReportStorage(base_path=temp_dir)
            year_month = "2025-01"

            # Save both statements
            metadata = {
                "entity": "User1",
                "generated_at": "2025-01-15T10:00:00",
                "source": "test"
            }

            # This should work (may need to implement save_statement method)
            storage.save_statement(year_month, "income_statement", income_statement, metadata)
            storage.save_statement(year_month, "cash_flow", cashflow_statement, metadata)

            # Verify files exist
            income_file = os.path.join(temp_dir, year_month, "income_statement_User1.json")
            cashflow_file = os.path.join(temp_dir, year_month, "cash_flow_User1.json")

            assert os.path.exists(income_file), f"Income statement file should exist at {income_file}"
            assert os.path.exists(cashflow_file), f"Cash flow statement file should exist at {cashflow_file}"

            # Verify file contents
            with open(income_file, 'r', encoding='utf-8') as f:
                saved_income = json.load(f)
                assert saved_income["statement"]["Net Income"] == 8000.0

            with open(cashflow_file, 'r', encoding='utf-8') as f:
                saved_cashflow = json.load(f)
                assert saved_cashflow["statement"]["Net Change in Cash"] == 8000.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])