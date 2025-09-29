"""
Enhanced test suite for Income Statement Generation

Tests the fourth step of the income statement generation workflow:
1. Income statement generation with enhanced prepaid asset handling
2. Tax expense separation and proper categorization
3. Prepaid asset exclusion from current period income
4. Complex scenario handling and edge cases
"""

import pytest
import pandas as pd
import tempfile
import os
from typing import List, Dict

from src.modules.accounting.core.models import Transaction, CategoryMapper, REVENUE_CATEGORIES
from src.modules.accounting.core.income_statement import IncomeStatementGenerator
from src.modules.accounting.core.io import TransactionProcessor


class TestIncomeStatementEnhanced:
    """Enhanced tests for income statement generation"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.category_mapper = CategoryMapper()
        self.generator = IncomeStatementGenerator(self.category_mapper)
    
    def test_basic_income_statement_structure(self):
        """Test basic income statement structure and calculations"""
        transactions = [
            Transaction("Salary", 8000.0, "工资收入", "Bank Account", "User1"),
            Transaction("Freelance", 2000.0, "服务收入", "Cash Account", "User1"),
            Transaction("Rent", 2000.0, "房租", "Bank Account", "User1"),
            Transaction("Food", 500.0, "餐饮", "Credit Card", "User1"),
        ]
        
        # Set transaction types properly
        transactions[0].transaction_type = "revenue"
        transactions[1].transaction_type = "revenue"
        transactions[2].transaction_type = "expense"
        transactions[3].transaction_type = "expense"
        
        statement = self.generator.generate_statement(transactions, "User1")
        
        # Check structure
        assert "Entity" in statement
        assert "Revenue" in statement
        assert "Total Revenue" in statement
        assert "Expenses" in statement
        assert "Total Expenses" in statement
        assert "Net Income" in statement
        
        # Check calculations
        assert statement["Total Revenue"] == 10000.0  # 8000 + 2000
        assert statement["Total Expenses"] == 2500.0  # 2000 + 500 (mapped categories)
        assert statement["Net Income"] == 7500.0  # 10000 - 2500


class TestTaxExpenseSeparation:
    """Test tax expense separation and categorization"""
    
    def setup_method(self):
        """Setup test fixtures with tax-aware category mapper"""
        # Extend category mapper to include tax categories
        self.category_mapper = CategoryMapper()
        # Add tax categories to the mapper
        self.category_mapper.expense_categories.update({
            '所得税': 'Income Tax',
            '增值税': 'Value Added Tax',
            '企业所得税': 'Corporate Income Tax',
            '个人所得税': 'Personal Income Tax',
            '营业税': 'Business Tax',
            '税费': 'Tax Expenses',
            '税务罚款': 'Tax Penalties'
        })
        self.generator = IncomeStatementGenerator(self.category_mapper)
    
    def test_tax_expense_categorization(self):
        """Test that tax expenses are properly categorized"""
        transactions = [
            Transaction("Salary", 8000.0, "工资收入", "Bank Account", "User1"),
            Transaction("Income Tax", 800.0, "所得税", "Bank Account", "User1"),
            Transaction("VAT Payment", 500.0, "增值税", "Bank Account", "User1"),
            Transaction("Corporate Tax", 1200.0, "企业所得税", "Bank Account", "User1"),
            Transaction("Regular Expense", 300.0, "餐饮", "Credit Card", "User1"),
        ]
        
        # Set transaction types
        transactions[0].transaction_type = "revenue"
        for i in range(1, 5):
            transactions[i].transaction_type = "expense"
        
        statement = self.generator.generate_statement(transactions, "User1")
        
        # Check that tax expenses are properly mapped
        expenses = statement["Expenses"]
        assert "Income Tax" in expenses
        assert "Value Added Tax" in expenses
        assert "Corporate Income Tax" in expenses
        assert "Food & Dining" in expenses
        
        # Check amounts
        assert expenses["Income Tax"] == 800.0
        assert expenses["Value Added Tax"] == 500.0
        assert expenses["Corporate Income Tax"] == 1200.0
        assert expenses["Food & Dining"] == 300.0
        
        # Check totals
        assert statement["Total Expenses"] == 2800.0  # 800 + 500 + 1200 + 300
        assert statement["Net Income"] == 5200.0  # 8000 - 2800
    
    def test_tax_expense_separation_display(self):
        """Test that tax expenses can be identified separately"""
        transactions = [
            Transaction("Revenue", 10000.0, "工资收入", "Bank Account", "User1"),
            Transaction("Operating Expense", 1000.0, "餐饮", "Credit Card", "User1"),
            Transaction("Income Tax", 1500.0, "所得税", "Bank Account", "User1"),
            Transaction("VAT", 800.0, "增值税", "Bank Account", "User1"),
        ]
        
        # Set transaction types
        transactions[0].transaction_type = "revenue"
        for i in range(1, 4):
            transactions[i].transaction_type = "expense"
        
        statement = self.generator.generate_statement(transactions, "User1")
        
        # Separate tax and non-tax expenses
        tax_expenses = {}
        operating_expenses = {}
        
        for category, amount in statement["Expenses"].items():
            if "Tax" in category:
                tax_expenses[category] = amount
            else:
                operating_expenses[category] = amount
        
        # Check separation
        assert len(tax_expenses) == 2  # Income Tax, Value Added Tax
        assert len(operating_expenses) == 1  # Food & Dining
        
        total_tax = sum(tax_expenses.values())
        total_operating = sum(operating_expenses.values())
        
        assert total_tax == 2300.0  # 1500 + 800
        assert total_operating == 1000.0
        assert total_tax + total_operating == statement["Total Expenses"]
    
    def test_complex_tax_scenario(self):
        """Test complex scenario with multiple tax types and users"""
        transactions = [
            # User1 transactions
            Transaction("User1 Salary", 12000.0, "工资收入", "Bank Account", "User1"),
            Transaction("User1 Income Tax", 1800.0, "个人所得税", "Bank Account", "User1"),
            Transaction("User1 Business Tax", 600.0, "营业税", "Bank Account", "User1"),
            Transaction("User1 Operating Expense", 800.0, "办公支出", "Credit Card", "User1"),
            # User2 transactions
            Transaction("User2 Revenue", 8000.0, "服务收入", "Bank Account", "User2"),
            Transaction("User2 Corporate Tax", 1200.0, "企业所得税", "Bank Account", "User2"),
            Transaction("User2 Operating Expense", 500.0, "餐饮", "Credit Card", "User2"),
        ]
        
        # Set transaction types
        transactions[0].transaction_type = "revenue"
        transactions[4].transaction_type = "revenue"
        for i in [1, 2, 3, 5, 6]:
            transactions[i].transaction_type = "expense"
        
        # Test User1 statement
        user1_transactions = [t for t in transactions if t.user == "User1"]
        user1_statement = self.generator.generate_statement(user1_transactions, "User1")
        
        # Check User1 tax expenses
        user1_tax_total = (
            user1_statement["Expenses"].get("Personal Income Tax", 0) +
            user1_statement["Expenses"].get("Business Tax", 0)
        )
        assert user1_tax_total == 2400.0  # 1800 + 600
        
        # Test User2 statement
        user2_transactions = [t for t in transactions if t.user == "User2"]
        user2_statement = self.generator.generate_statement(user2_transactions, "User2")
        
        # Check User2 tax expenses
        user2_tax_total = user2_statement["Expenses"].get("Corporate Income Tax", 0)
        assert user2_tax_total == 1200.0


class TestPrepaidAssetHandling:
    """Test prepaid asset handling in income statement generation"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.category_mapper = CategoryMapper()
        self.generator = IncomeStatementGenerator(self.category_mapper)
    
    def test_prepaid_asset_exclusion(self):
        """Test that prepaid asset transactions are excluded from income statement"""
        transactions = [
            Transaction("Revenue", 10000.0, "工资收入", "Bank Account", "User1"),
            Transaction("Regular Expense", 1000.0, "餐饮", "Credit Card", "User1"),
            Transaction("Prepaid Payment", 6000.0, "Prepaid Rent", "Bank Account", "User1"),  # Should be excluded
            Transaction("Prepaid Usage", 500.0, "房租", "Prepaid Rent", "User1"),  # Should be included
        ]
        
        # Set transaction types
        transactions[0].transaction_type = "revenue"
        transactions[1].transaction_type = "expense"
        transactions[2].transaction_type = "prepaid_asset"  # This should be excluded
        transactions[3].transaction_type = "expense"  # This should be included
        
        statement = self.generator.generate_statement(transactions, "User1")
        
        # Check that prepaid asset is excluded
        assert statement["Total Revenue"] == 10000.0  # Only revenue
        # Should only include regular expense (1000) + prepaid usage (500)
        assert statement["Total Expenses"] == 1500.0  # 1000 + 500, excludes 6000 prepaid payment
        assert statement["Net Income"] == 8500.0  # 10000 - 1500
        
        # Verify prepaid payment is not in expenses
        expense_descriptions = list(statement["Expenses"].keys())
        assert "Prepaid Rent" not in expense_descriptions
        assert "Rent" in expense_descriptions  # Converted prepaid expense should be there
    
    def test_prepaid_asset_conversion_included(self):
        """Test that prepaid asset conversions are properly included as expenses"""
        transactions = [
            Transaction("Revenue", 8000.0, "工资收入", "Bank Account", "User1"),
            # Prepaid asset creation (should be excluded from income statement)
            Transaction("Annual Insurance", 2400.0, "Prepaid Insurance", "Bank Account", "User1"),
            # Monthly prepaid conversions (should be included as expenses)
            Transaction("Jan Insurance", 200.0, "保险费", "Prepaid Insurance", "User1"),
            Transaction("Feb Insurance", 200.0, "保险费", "Prepaid Insurance", "User1"),
            Transaction("Mar Insurance", 200.0, "保险费", "Prepaid Insurance", "User1"),
        ]
        
        # Set transaction types
        transactions[0].transaction_type = "revenue"
        transactions[1].transaction_type = "prepaid_asset"  # Excluded
        transactions[2].transaction_type = "expense"  # Included
        transactions[3].transaction_type = "expense"  # Included
        transactions[4].transaction_type = "expense"  # Included
        
        statement = self.generator.generate_statement(transactions, "User1")
        
        # Check calculations
        assert statement["Total Revenue"] == 8000.0
        assert statement["Total Expenses"] == 600.0  # 200 * 3 months, excludes 2400 prepaid payment
        assert statement["Net Income"] == 7400.0  # 8000 - 600
        
        # Check that insurance expenses are properly categorized
        insurance_expense = statement["Expenses"].get("Insurance", 0)
        assert insurance_expense == 600.0  # 3 months of 200 each
    
    def test_complex_prepaid_scenario(self):
        """Test complex scenario with multiple prepaid assets"""
        transactions = [
            # Revenue
            Transaction("Salary", 15000.0, "工资收入", "Bank Account", "User1"),
            Transaction("Consulting", 5000.0, "服务收入", "Cash", "User1"),
            
            # Prepaid asset creations (should be excluded)
            Transaction("Prepaid Rent", 12000.0, "Prepaid Rent", "Bank Account", "User1"),
            Transaction("Prepaid Insurance", 2400.0, "Prepaid Insurance", "Bank Account", "User1"),
            Transaction("Prepaid Supplies", 1200.0, "Prepaid Office Supplies", "Bank Account", "User1"),
            
            # Prepaid conversions (should be included as expenses)
            Transaction("Monthly Rent", 1000.0, "房租", "Prepaid Rent", "User1"),
            Transaction("Monthly Insurance", 200.0, "保险费", "Prepaid Insurance", "User1"),
            Transaction("Office Supplies Used", 100.0, "办公支出", "Prepaid Office Supplies", "User1"),
            
            # Regular expenses
            Transaction("Utilities", 500.0, "水电", "Bank Account", "User1"),
            Transaction("Food", 800.0, "餐饮", "Credit Card", "User1"),
        ]
        
        # Set transaction types
        transactions[0].transaction_type = "revenue"
        transactions[1].transaction_type = "revenue"
        transactions[2].transaction_type = "prepaid_asset"  # Excluded
        transactions[3].transaction_type = "prepaid_asset"  # Excluded
        transactions[4].transaction_type = "prepaid_asset"  # Excluded
        transactions[5].transaction_type = "expense"  # Included
        transactions[6].transaction_type = "expense"  # Included
        transactions[7].transaction_type = "expense"  # Included
        transactions[8].transaction_type = "expense"  # Included
        transactions[9].transaction_type = "expense"  # Included
        
        statement = self.generator.generate_statement(transactions, "User1")
        
        # Check calculations
        assert statement["Total Revenue"] == 20000.0  # 15000 + 5000
        # Expenses: 1000 (rent) + 200 (insurance) + 100 (supplies) + 500 (utilities) + 800 (food) = 2600
        assert statement["Total Expenses"] == 2600.0
        assert statement["Net Income"] == 17400.0  # 20000 - 2600
        
        # Verify prepaid payments are excluded
        total_prepaid_payments = 12000 + 2400 + 1200  # 15600
        # If prepaid payments were included, total expenses would be 2600 + 15600 = 18200
        assert statement["Total Expenses"] != 18200  # Confirms exclusion


class TestIncomeStatementIntegration:
    """Integration tests for income statement generation with full workflow"""
    
    def test_complete_workflow_with_csv(self):
        """Test complete workflow from CSV to income statement with all features"""
        comprehensive_data = [
            ["Description", "Amount", "Debit", "Credit", "User"],
            # Revenue transactions
            ["Salary", "15000.00", "Bank Account", "工资收入", "User1"],
            ["Freelance Income", "3000.00", "Cash", "服务收入", "User1"],
            
            # Tax expenses
            ["Income Tax Payment", "2000.00", "所得税", "Bank Account", "User1"],
            ["VAT Payment", "800.00", "增值税", "Bank Account", "User1"],
            
            # Prepaid asset creation
            ["Annual Insurance", "2400.00", "Prepaid Insurance", "Bank Account", "User1"],
            ["Office Rent Prepaid", "12000.00", "Prepaid Rent", "Bank Account", "User1"],
            
            # Prepaid asset conversions
            ["Monthly Insurance", "200.00", "保险费", "Prepaid Insurance", "User1"],
            ["Monthly Rent", "1000.00", "房租", "Prepaid Rent", "User1"],
            
            # Regular operating expenses
            ["Office Supplies", "300.00", "办公支出", "Credit Card", "User1"],
            ["Business Meals", "500.00", "餐饮", "Credit Card", "User1"],
            ["Transportation", "200.00", "交通", "Cash", "User1"],
            
            # User2 transactions
            ["User2 Salary", "12000.00", "Bank Account", "工资收入", "User2"],
            ["User2 Tax", "1500.00", "个人所得税", "Bank Account", "User2"],
            ["User2 Expenses", "800.00", "餐饮", "Credit Card", "User2"],
        ]
        
        csv_file = self.create_test_csv(comprehensive_data)
        
        try:
            # Process transactions
            processor = TransactionProcessor(csv_file)
            processor.load_transactions()
            
            # Generate income statements
            generator = IncomeStatementGenerator(CategoryMapper())
            
            # Enhance category mapper with tax categories
            generator.category_mapper.expense_categories.update({
                '所得税': 'Income Tax',
                '增值税': 'Value Added Tax',
                '个人所得税': 'Personal Income Tax'
            })
            
            # User1 statement
            user1_transactions = processor.get_transactions_by_user("User1")
            user1_statement = generator.generate_statement(user1_transactions, "User1")
            
            # User2 statement
            user2_transactions = processor.get_transactions_by_user("User2")
            user2_statement = generator.generate_statement(user2_transactions, "User2")
            
            # Combined statement
            combined_statement = generator.generate_statement(processor.transactions, "Combined")
            
            # Verify User1 statement
            assert user1_statement["Total Revenue"] == 18000.0  # 15000 + 3000
            
            # User1 expenses should exclude prepaid payments but include conversions
            # Expected: 2000 (tax) + 800 (vat) + 200 (insurance) + 1000 (rent) + 300 (supplies) + 500 (meals) + 200 (transport)
            expected_user1_expenses = 5000.0
            assert user1_statement["Total Expenses"] == expected_user1_expenses
            assert user1_statement["Net Income"] == 13000.0  # 18000 - 5000
            
            # Verify User2 statement
            assert user2_statement["Total Revenue"] == 12000.0
            # User2 expenses: 1500 (tax) + 800 (meals)
            assert user2_statement["Total Expenses"] == 2300.0
            assert user2_statement["Net Income"] == 9700.0  # 12000 - 2300
            
            # Verify combined statement
            assert combined_statement["Total Revenue"] == 30000.0  # 18000 + 12000
            assert combined_statement["Total Expenses"] == 7300.0  # 5000 + 2300
            assert combined_statement["Net Income"] == 22700.0  # 30000 - 7300
            
            # Check tax expense separation in User1
            user1_tax_expenses = {k: v for k, v in user1_statement["Expenses"].items() if "Tax" in k}
            assert len(user1_tax_expenses) >= 2  # Income Tax, Value Added Tax
            
        finally:
            os.unlink(csv_file)
    
    def test_edge_cases_and_error_handling(self):
        """Test edge cases in income statement generation"""
        edge_case_data = [
            ["Description", "Amount", "Debit", "Credit", "User"],
            # Zero amounts (should be filtered)
            ["Zero Transaction", "0.00", "餐饮", "Bank Account", "User1"],
            # Very large amounts
            ["Large Revenue", "1000000.00", "Bank Account", "工资收入", "User1"],
            ["Large Expense", "500000.00", "设备购买", "Bank Account", "User1"],
            # Unicode characters
            ["中文描述", "1000.00", "餐饮", "银行账户", "用户1"],
            # Mixed currency formats
            ["Currency Test", "¥2,500.00", "交通", "Bank Account", "User1"],
        ]
        
        csv_file = self.create_test_csv(edge_case_data)
        
        try:
            processor = TransactionProcessor(csv_file)
            processor.load_transactions()
            
            generator = IncomeStatementGenerator(CategoryMapper())
            statement = generator.generate_statement(processor.transactions, "Test")
            
            # Should handle all cases without errors
            assert isinstance(statement, dict)
            assert "Total Revenue" in statement
            assert "Total Expenses" in statement
            assert "Net Income" in statement
            
            # Check that zero transactions were filtered
            assert statement["Total Revenue"] == 1000000.0  # Only the large revenue
            
        finally:
            os.unlink(csv_file)
    
    def create_test_csv(self, data: List[List[str]]) -> str:
        """Create a temporary CSV file for testing"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        for row in data:
            temp_file.write(','.join(row) + '\n')
        temp_file.close()
        return temp_file.name


class TestIncomeStatementDisplayAndFormatting:
    """Test income statement display and formatting functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.category_mapper = CategoryMapper()
        self.generator = IncomeStatementGenerator(self.category_mapper)
    
    def test_currency_formatting(self):
        """Test currency formatting in income statement"""
        from src.modules.accounting.core.income_statement import format_currency
        
        test_amounts = [
            (1000.0, "¥1,000.00"),
            (1500.50, "¥1,500.50"),
            (0.0, "¥0.00"),
            (-500.0, "¥-500.00"),
            (1000000.0, "¥1,000,000.00")
        ]
        
        for amount, expected in test_amounts:
            result = format_currency(amount)
            assert result == expected
    
    def test_print_income_statement_functionality(self):
        """Test print income statement functionality"""
        from src.modules.accounting.core.income_statement import print_income_statement
        
        sample_statement = {
            "Entity": "Test User",
            "Total Revenue": 15000.0,
            "Total Expenses": 5000.0,
            "Net Income": 10000.0,
            "Revenue": {
                "工资收入": 12000.0,
                "服务收入": 3000.0
            },
            "Expenses": {
                "Rent": 2000.0,
                "Food & Dining": 1500.0,
                "Income Tax": 1000.0,
                "Transportation": 500.0
            }
        }
        
        # Should not raise any exceptions
        try:
            print_income_statement(sample_statement)
            success = True
        except Exception:
            success = False
        
        assert success, "print_income_statement should not raise exceptions"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
