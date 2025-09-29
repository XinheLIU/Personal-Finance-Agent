"""
Test suite for comprehensive English category support in accounting system

Tests that the CategoryMapper correctly handles English category inputs
for both expenses and revenue, ensuring no unexpected fallbacks to "Other Expenses".
"""

import pytest
from src.modules.accounting.models.domain.category import CategoryMapper, REVENUE_CATEGORIES
from src.modules.accounting.models.domain.transaction import Transaction
from src.modules.accounting.models.business.income_statement_generator import IncomeStatementGenerator


class TestEnglishCategorySupport:
    """Test comprehensive English category support"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.category_mapper = CategoryMapper()
        self.generator = IncomeStatementGenerator(self.category_mapper)
    
    def test_english_expense_categories(self):
        """Test that common English expense categories are properly mapped"""
        
        # Test cases: (input_category, expected_mapped_category)
        test_cases = [
            # Food categories
            ('Food', 'Food & Dining'),
            ('Dining', 'Food & Dining'), 
            ('Groceries', 'Food & Dining'),
            ('Restaurant', 'Food & Dining'),
            ('Meals', 'Food & Dining'),
            
            # Transportation categories
            ('Transport', 'Transportation'),
            ('Transportation', 'Transportation'),
            ('Gas', 'Transportation'),
            ('Fuel', 'Transportation'),
            ('Car Payment', 'Transportation'),
            ('Car', 'Transportation'),
            ('Bus', 'Transportation'),
            ('Taxi', 'Transportation'),
            ('Uber', 'Transportation'),
            
            # Entertainment categories
            ('Travel', 'Travel & Entertainment'),
            ('Entertainment', 'Travel & Entertainment'),
            ('Movies', 'Travel & Entertainment'),
            ('Vacation', 'Travel & Entertainment'),
            ('Hotel', 'Travel & Entertainment'),
            
            # Medical categories
            ('Healthcare', 'Medical'),
            ('Medical', 'Medical'),
            ('Doctor', 'Medical'),
            ('Hospital', 'Medical'),
            ('Pharmacy', 'Medical'),
            ('Medicine', 'Medical'),
            ('Dental', 'Medical'),
            
            # Insurance categories
            ('Insurance', 'Insurance'),
            ('Health Insurance', 'Insurance'),
            ('Car Insurance', 'Insurance'),
            ('Life Insurance', 'Insurance'),
            
            # Office categories
            ('Office', 'Office Expenses'),
            ('Supplies', 'Office Expenses'),
            ('Office Supplies', 'Office Expenses'),
            ('Stationery', 'Office Expenses'),
            
            # Education categories
            ('Education', 'Education'),
            ('School', 'Education'),
            ('Books', 'Education'),
            ('Tuition', 'Education'),
            ('Course', 'Education'),
            
            # Clothing categories
            ('Clothing', 'Clothing'),
            ('Clothes', 'Clothing'),
            ('Apparel', 'Clothing'),
            ('Fashion', 'Clothing'),
            
            # Utilities categories
            ('Utilities', 'Utilities'),
            ('Electric', 'Utilities'),
            ('Electricity', 'Utilities'),
            ('Water', 'Utilities'),
            ('Internet', 'Utilities'),
            ('Phone', 'Utilities'),
            ('Phone Bill', 'Utilities'),
            ('Mobile', 'Utilities'),
            ('Cable', 'Utilities'),
            
            # Housing categories
            ('Rent', 'Rent'),
            ('Mortgage', 'Rent'),
            ('Housing', 'Rent'),
            ('Apartment', 'Rent'),
            
            # Shopping categories
            ('Shopping', 'General Shopping'),
            ('Purchase', 'General Shopping'),
            ('Retail', 'General Shopping'),
            
            # Personal categories
            ('Personal', 'Personal Expenses'),
            ('Personal Care', 'Personal Expenses'),
            ('Beauty', 'Personal Expenses'),
            
            # Health & Wellness categories
            ('Gym', 'Health & Wellness'),
            ('Fitness', 'Health & Wellness'),
            ('Sports', 'Health & Wellness'),
            ('Wellness', 'Health & Wellness'),
            
            # Pet categories
            ('Pet', 'Pet Expenses'),
            ('Pets', 'Pet Expenses'),
            ('Veterinary', 'Pet Expenses'),
            ('Vet', 'Pet Expenses'),
            
            # Social categories
            ('Social', 'Social Dining'),
            ('Socializing', 'Social Dining'),
        ]
        
        for input_category, expected_category in test_cases:
            mapped_category = self.category_mapper.get_expense_category(input_category)
            assert mapped_category == expected_category, \
                f"Category '{input_category}' should map to '{expected_category}', but got '{mapped_category}'"
    
    def test_english_revenue_categories(self):
        """Test that English revenue categories are properly recognized"""
        
        english_revenue_categories = [
            'Service Revenue', 'Investment Income', 'Other Income',
            'Salary', 'Wages', 'Income', 'Revenue', 'Sales', 'Earnings',
            'Freelance', 'Consulting', 'Bonus', 'Commission', 'Tips',
            'Interest', 'Dividends', 'Rental Income', 'Business Income'
        ]
        
        for category in english_revenue_categories:
            assert category in REVENUE_CATEGORIES, \
                f"Revenue category '{category}' should be in REVENUE_CATEGORIES"
    
    def test_english_tax_categories(self):
        """Test that English tax categories are properly mapped"""
        
        tax_test_cases = [
            ('Tax Expense', 'Tax Expense'),
            ('Tax Expenses', 'Tax Expenses'),
            ('Income Tax', 'Income Tax'),
            ('Value Added Tax', 'Value Added Tax'),
            ('VAT', 'Value Added Tax'),
            ('Corporate Tax', 'Corporate Income Tax'),
            ('Corporate Income Tax', 'Corporate Income Tax'),
            ('Personal Income Tax', 'Personal Income Tax'),
            ('Business Tax', 'Business Tax'),
            ('Tax Penalties', 'Tax Penalties'),
            ('Provident Fund', 'Provident Fund Tax'),
            ('Social Security Tax', 'Social Security Tax'),
            ('Payroll Tax', 'Payroll Tax'),
        ]
        
        for input_category, expected_category in tax_test_cases:
            mapped_category = self.category_mapper.get_expense_category(input_category)
            assert mapped_category == expected_category, \
                f"Tax category '{input_category}' should map to '{expected_category}', but got '{mapped_category}'"
    
    def test_income_statement_with_english_categories(self):
        """Test income statement generation with mixed English categories"""
        
        transactions = [
            # Revenue transactions (English)
            Transaction("Monthly salary", 5000.00, "Salary", "Bank", "User1"),
            Transaction("Freelance work", 1500.00, "Freelance", "Bank", "User1"),
            Transaction("Investment returns", 200.00, "Dividends", "Investment Account", "User1"),
            
            # Expense transactions (English)
            Transaction("Lunch", 25.00, "Food", "Cash", "User1"),
            Transaction("Bus fare", 5.00, "Transport", "Cash", "User1"),
            Transaction("Movie tickets", 30.00, "Entertainment", "Credit Card", "User1"),
            Transaction("Doctor visit", 100.00, "Healthcare", "Insurance", "User1"),
            Transaction("Grocery shopping", 80.00, "Groceries", "Credit Card", "User1"),
            Transaction("Phone bill", 50.00, "Phone Bill", "Bank", "User1"),
            Transaction("Car payment", 300.00, "Car Payment", "Bank", "User1"),
            Transaction("Income tax", 800.00, "Income Tax", "Bank", "User1"),
            Transaction("Gym membership", 60.00, "Gym", "Credit Card", "User1"),
        ]
        
        # Set transaction types
        for i in [0, 1, 2]:  # Revenue transactions
            transactions[i].transaction_type = "revenue"
        for i in range(3, len(transactions)):  # Expense transactions
            transactions[i].transaction_type = "expense"
        
        statement = self.generator.generate_statement(transactions, "User1")
        
        # Verify totals
        expected_revenue = 5000.0 + 1500.0 + 200.0  # 6700
        expected_expenses = 25.0 + 5.0 + 30.0 + 100.0 + 80.0 + 50.0 + 300.0 + 800.0 + 60.0  # 1450
        
        assert statement["Total Revenue"] == expected_revenue
        assert statement["Total Expenses"] == expected_expenses
        assert statement["Net Income"] == expected_revenue - expected_expenses
        
        # Verify no expenses went to "Other Expenses"
        assert "Other Expenses" not in statement["Expenses"], \
            f"No expenses should go to 'Other Expenses', but found: {statement['Expenses'].get('Other Expenses', 0)}"
        
        # Verify specific category mappings in the result
        expenses = statement["Expenses"]
        assert expenses["Food & Dining"] == 25.0 + 80.0  # Food + Groceries
        assert expenses["Transportation"] == 5.0 + 300.0  # Bus + Car Payment
        assert expenses["Travel & Entertainment"] == 30.0  # Movies
        assert expenses["Medical"] == 100.0  # Healthcare
        assert expenses["Utilities"] == 50.0  # Phone Bill
        assert expenses["Income Tax"] == 800.0  # Tax
        assert expenses["Health & Wellness"] == 60.0  # Gym
        
        # Verify revenue categories
        revenue = statement["Revenue"]
        assert revenue["Salary"] == 5000.0
        assert revenue["Freelance"] == 1500.0
        assert revenue["Dividends"] == 200.0
    
    def test_mixed_language_transaction_processing(self):
        """Test processing transactions with mixed Chinese and English categories"""
        
        transactions = [
            # Chinese categories
            Transaction("午餐", 30.00, "餐饮", "现金", "User1"),
            Transaction("地铁", 10.00, "通勤", "交通卡", "User1"),
            Transaction("工资", 8000.00, "工资收入", "银行", "User1"),
            
            # English categories
            Transaction("Dinner", 50.00, "Food", "Credit Card", "User1"),
            Transaction("Taxi", 20.00, "Transport", "Cash", "User1"),
            Transaction("Bonus", 1000.00, "Bonus", "Bank", "User1"),
            
            # Mixed description + English category (user's original case)
            Transaction("公积金", 4069.00, "Tax Expense", "Cash", "User1"),
        ]
        
        # Set transaction types
        transactions[2].transaction_type = "revenue"  # 工资
        transactions[5].transaction_type = "revenue"  # Bonus
        for i in [0, 1, 3, 4, 6]:  # All others are expenses
            transactions[i].transaction_type = "expense"
        
        statement = self.generator.generate_statement(transactions, "User1")
        
        # Verify no fallback to "Other Expenses"
        assert "Other Expenses" not in statement["Expenses"], \
            f"Mixed language processing failed - expenses went to 'Other Expenses': {statement['Expenses']}"
        
        # Verify proper categorization
        expenses = statement["Expenses"]
        assert expenses["Food & Dining"] == 30.0 + 50.0  # 餐饮 + Food
        assert expenses["Transportation"] == 10.0 + 20.0  # 通勤 + Transport
        assert expenses["Tax Expense"] == 4069.0  # User's specific case
        
        revenue = statement["Revenue"]
        assert revenue["工资收入"] == 8000.0  # Chinese salary
        assert revenue["Bonus"] == 1000.0  # English bonus
    
    def test_no_common_categories_fallback_to_other_expenses(self):
        """Test that no common English categories fall back to 'Other Expenses'"""
        
        # List of categories that users commonly input in English
        common_english_categories = [
            'Food', 'Dining', 'Groceries', 'Restaurant', 'Meals',
            'Transport', 'Transportation', 'Gas', 'Car', 'Bus', 'Taxi',
            'Travel', 'Entertainment', 'Movies', 'Hotel',
            'Healthcare', 'Medical', 'Doctor', 'Hospital',
            'Insurance', 'Education', 'Clothing', 'Utilities',
            'Rent', 'Shopping', 'Personal', 'Gym', 'Pet'
        ]
        
        fallback_categories = []
        
        for category in common_english_categories:
            mapped = self.category_mapper.get_expense_category(category)
            if mapped == "Other Expenses":
                fallback_categories.append(category)
        
        assert len(fallback_categories) == 0, \
            f"These common English categories incorrectly fall back to 'Other Expenses': {fallback_categories}"
    
    def test_user_specific_english_tax_case(self):
        """Test the user's specific case: 公积金 with 'Tax Expense' category"""
        
        transaction = Transaction(
            description="公积金",
            amount=4069.00,
            debit_category="Tax Expense",  # User input in English
            credit_account="Cash",
            user="XH"
        )
        transaction.transaction_type = "expense"
        
        statement = self.generator.generate_statement([transaction], "XH")
        
        # Verify proper categorization
        assert "Tax Expense" in statement["Expenses"]
        assert statement["Expenses"]["Tax Expense"] == 4069.0
        assert "Other Expenses" not in statement["Expenses"]
        assert statement["Total Expenses"] == 4069.0


class TestErrorHandling:
    """Test error handling for edge cases"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.category_mapper = CategoryMapper()
    
    def test_empty_and_none_categories(self):
        """Test handling of empty and None category inputs"""
        
        assert self.category_mapper.get_expense_category("") == "Other Expenses"
        assert self.category_mapper.get_expense_category(None) == "Other Expenses"
    
    def test_case_sensitivity(self):
        """Test that category mapping is case-sensitive (as expected)"""
        
        # Current implementation is case-sensitive
        assert self.category_mapper.get_expense_category("food") == "Other Expenses"  # lowercase
        assert self.category_mapper.get_expense_category("Food") == "Food & Dining"  # proper case
        assert self.category_mapper.get_expense_category("FOOD") == "Other Expenses"  # uppercase
    
    def test_unknown_categories_fallback(self):
        """Test that truly unknown categories fall back to 'Other Expenses'"""
        
        unknown_categories = [
            "Unknown Category", "Random Stuff", "Weird Expense",
            "NotACategory", "Some Random Text"
        ]
        
        for category in unknown_categories:
            mapped = self.category_mapper.get_expense_category(category)
            assert mapped == "Other Expenses", \
                f"Unknown category '{category}' should fall back to 'Other Expenses', but got '{mapped}'"


if __name__ == "__main__":
    # Run a quick verification
    test_instance = TestEnglishCategorySupport()
    test_instance.setup_method()
    
    try:
        test_instance.test_english_expense_categories()
        test_instance.test_english_revenue_categories()
        test_instance.test_english_tax_categories()
        test_instance.test_no_common_categories_fallback_to_other_expenses()
        test_instance.test_user_specific_english_tax_case()
        print("✅ All quick tests passed! English category support is working correctly.")
    except Exception as e:
        print(f"❌ Test failed: {e}")
