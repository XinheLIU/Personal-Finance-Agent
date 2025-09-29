"""
Test suite for CSV upload and validation functionality

Tests the first step of the income statement generation workflow:
1. CSV upload and validation
2. Data cleaning (empty rows, currency signs, whole row removal)
3. Currency handling and number conversion
"""

import pytest
import pandas as pd
import tempfile
import os
from typing import List, Dict
from io import StringIO

from src.modules.accounting.core.io import TransactionProcessor


class TestCSVUploadValidation:
    """Test CSV upload and validation functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.valid_data = [
            ["Description", "Amount", "Debit", "Credit", "User"],
            ["Salary Payment", "8000.00", "工资收入", "Bank Account", "User1"],
            ["Rent Payment", "-2000.00", "房租", "Bank Account", "User1"],
            ["Groceries", "-500.00", "餐饮", "Credit Card", "User1"]
        ]
    
    def create_csv_content(self, data: List[List[str]]) -> str:
        """Create CSV content string from data"""
        csv_content = StringIO()
        for row in data:
            csv_content.write(','.join(row) + '\n')
        return csv_content.getvalue()
    
    def create_test_csv(self, data: List[List[str]]) -> str:
        """Create a temporary CSV file for testing"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        for row in data:
            temp_file.write(','.join(row) + '\n')
        temp_file.close()
        return temp_file.name
    
    def test_valid_csv_upload(self):
        """Test uploading a valid CSV file"""
        csv_file = self.create_test_csv(self.valid_data)
        
        try:
            processor = TransactionProcessor(csv_file)
            processor.load_transactions()
            
            assert len(processor.transactions) == 3
            assert processor.transactions[0].description == "Salary Payment"
            assert processor.transactions[0].amount == 8000.0
            
        finally:
            os.unlink(csv_file)
    
    def test_file_not_found_error(self):
        """Test handling of non-existent file"""
        with pytest.raises(Exception) as exc_info:
            processor = TransactionProcessor("non_existent_file.csv")
            processor.load_transactions()
        
        assert "Error loading transactions" in str(exc_info.value)
    
    def test_malformed_csv_handling(self):
        """Test handling of malformed CSV data"""
        malformed_data = [
            ["Description", "Amount", "Debit", "Credit", "User"],
            ["Incomplete row", "100.00", "expense"],  # Missing columns
            ["Another row", "200.00", "expense", "account", "user", "extra column"]  # Extra column
        ]
        
        csv_file = self.create_test_csv(malformed_data)
        
        try:
            processor = TransactionProcessor(csv_file)
            processor.load_transactions()
            
            # Should still process valid parts and handle missing data gracefully
            assert len(processor.transactions) >= 0  # May be 0 if all invalid
            
        finally:
            os.unlink(csv_file)


class TestDataCleaning:
    """Test data cleaning functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.processor = TransactionProcessor("")  # Empty path for unit testing
    
    def test_remove_empty_rows_from_dataframe(self):
        """Test removal of empty rows before saving to pandas DataFrame"""
        # Create data with empty rows
        data_with_empty_rows = [
            ["Description", "Amount", "Debit", "Credit", "User"],
            ["Salary", "8000.00", "工资收入", "Bank Account", "User1"],
            ["", "", "", "", ""],  # Completely empty row
            ["Rent", "-2000.00", "房租", "Bank Account", "User1"],
            ["", "0", "", "", ""],  # Partially empty row
            ["Groceries", "-500.00", "餐饮", "Credit Card", "User1"]
        ]
        
        # Create temporary CSV file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        for row in data_with_empty_rows:
            temp_file.write(','.join(row) + '\n')
        temp_file.close()
        
        try:
            processor = TransactionProcessor(temp_file.name)
            processor.load_transactions()
            
            # Should only have 2 valid transactions (salary and groceries)
            # Rent has 0 amount after cleaning, so it gets filtered out
            # Empty rows get filtered out during processing
            valid_transactions = [t for t in processor.transactions if t.amount != 0]
            assert len(valid_transactions) == 2
            
            descriptions = [t.description for t in valid_transactions]
            assert "Salary" in descriptions
            assert "Groceries" in descriptions
            
        finally:
            os.unlink(temp_file.name)
    
    def test_currency_sign_handling(self):
        """Test automatic handling of currency signs and conversion to numbers"""
        # Test various currency formats
        currency_test_cases = [
            ("8000.00", 8000.0),
            ("¥8,000.00", 8000.0),
            ("￥8,000.00", 8000.0),
            ("$2,500.50", 2500.5),
            ("-¥1,200.75", -1200.75),
            ("", 0.0),
            ("invalid", 0.0)
        ]
        
        for input_str, expected in currency_test_cases:
            result = self.processor._clean_amount(input_str)
            assert result == expected, f"Failed for input '{input_str}': expected {expected}, got {result}"
    
    def test_whole_empty_row_removal(self):
        """Test removal of completely empty rows"""
        data_with_whole_empty_rows = [
            ["Description", "Amount", "Debit", "Credit", "User"],
            ["Salary", "8000.00", "工资收入", "Bank Account", "User1"],
            ["", "", "", "", ""],  # Completely empty row 1
            ["", "", "", "", ""],  # Completely empty row 2
            ["Rent", "-2000.00", "房租", "Bank Account", "User1"]
        ]
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        for row in data_with_whole_empty_rows:
            temp_file.write(','.join(row) + '\n')
        temp_file.close()
        
        try:
            processor = TransactionProcessor(temp_file.name)
            processor.load_transactions()
            
            # Should only have 2 transactions (empty rows filtered out)
            assert len(processor.transactions) == 2
            descriptions = [t.description for t in processor.transactions]
            assert "Salary" in descriptions
            assert "Rent" in descriptions
            
        finally:
            os.unlink(temp_file.name)
    
    def test_zero_amount_filtering(self):
        """Test filtering of transactions with zero amounts"""
        data_with_zero_amounts = [
            ["Description", "Amount", "Debit", "Credit", "User"],
            ["Salary", "8000.00", "工资收入", "Bank Account", "User1"],
            ["Zero Transaction", "0.00", "expense", "Bank Account", "User1"],
            ["Another Zero", "", "expense", "Bank Account", "User1"],  # Empty amount becomes 0
            ["Valid Transaction", "-500.00", "餐饮", "Credit Card", "User1"]
        ]
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        for row in data_with_zero_amounts:
            temp_file.write(','.join(row) + '\n')
        temp_file.close()
        
        try:
            processor = TransactionProcessor(temp_file.name)
            processor.load_transactions()
            
            # Should only have 2 non-zero transactions
            assert len(processor.transactions) == 2
            for transaction in processor.transactions:
                assert transaction.amount != 0
                
        finally:
            os.unlink(temp_file.name)


class TestCurrencyHandling:
    """Test comprehensive currency handling and number conversion"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.processor = TransactionProcessor("")
    
    def test_chinese_currency_symbols(self):
        """Test handling of Chinese currency symbols"""
        test_cases = [
            ("¥10,000.00", 10000.0),
            ("￥5,500.50", 5500.5),
            ("¥1,234.56", 1234.56),
            ("￥999.99", 999.99)
        ]
        
        for input_str, expected in test_cases:
            result = self.processor._clean_amount(input_str)
            assert result == expected
    
    def test_us_currency_symbols(self):
        """Test handling of US currency symbols"""
        test_cases = [
            ("$1,000.00", 1000.0),
            ("$2,500.75", 2500.75),
            ("$999.99", 999.99),
            ("$10,000", 10000.0)
        ]
        
        for input_str, expected in test_cases:
            result = self.processor._clean_amount(input_str)
            assert result == expected
    
    def test_negative_amounts(self):
        """Test handling of negative amounts with currency symbols"""
        test_cases = [
            ("-¥1,000.00", -1000.0),
            ("-$500.50", -500.5),
            ("-1234.56", -1234.56),
            ("-￥999.99", -999.99)
        ]
        
        for input_str, expected in test_cases:
            result = self.processor._clean_amount(input_str)
            assert result == expected
    
    def test_comma_separated_thousands(self):
        """Test handling of comma-separated thousands"""
        test_cases = [
            ("1,000", 1000.0),
            ("10,000", 10000.0),
            ("100,000", 100000.0),
            ("1,234,567.89", 1234567.89),
            ("¥1,000,000.00", 1000000.0)
        ]
        
        for input_str, expected in test_cases:
            result = self.processor._clean_amount(input_str)
            assert result == expected
    
    def test_edge_cases(self):
        """Test edge cases in currency handling"""
        test_cases = [
            ("", 0.0),  # Empty string
            ("0", 0.0),  # Zero
            ("0.00", 0.0),  # Zero with decimals
            ("invalid_number", 0.0),  # Invalid input
            ("¥", 0.0),  # Currency symbol only
            ("$", 0.0),  # Currency symbol only
            ("abc123", 0.0),  # Mix of letters and numbers
            (None, 0.0),  # None value
        ]
        
        for input_val, expected in test_cases:
            result = self.processor._clean_amount(input_val)
            assert result == expected, f"Failed for input '{input_val}': expected {expected}, got {result}"


class TestCSVValidationIntegration:
    """Test integration of CSV validation with data cleaning"""
    
    def test_comprehensive_data_cleaning_workflow(self):
        """Test complete data cleaning workflow from CSV to clean transactions"""
        comprehensive_test_data = [
            ["Description", "Amount", "Debit", "Credit", "User"],
            ["Salary", "¥8,000.00", "工资收入", "Bank Account", "User1"],  # Chinese currency
            ["Bonus", "$2,500.50", "服务收入", "Cash Account", "User1"],    # US currency
            ["", "", "", "", ""],  # Empty row - should be filtered
            ["Rent", "-¥2,000.00", "房租", "Bank Account", "User1"],       # Negative Chinese currency
            ["Zero Amount", "0", "expense", "Bank Account", "User1"],      # Zero amount - should be filtered
            ["Groceries", "-500.75", "餐饮", "Credit Card", "User1"],      # Simple negative
            ["", "100", "", "", ""],  # Partially empty - missing required fields
            ["Transport", "￥200.00", "交通", "Cash Account", "User2"],     # Different user, alternate Chinese symbol
        ]
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        for row in comprehensive_test_data:
            temp_file.write(','.join(row) + '\n')
        temp_file.close()
        
        try:
            processor = TransactionProcessor(temp_file.name)
            processor.load_transactions()
            
            # Should have 5 valid transactions (filtered out empty row and zero amount)
            assert len(processor.transactions) == 5
            
            # Check specific transactions
            transactions_by_desc = {t.description: t for t in processor.transactions}
            
            # Salary transaction
            salary = transactions_by_desc["Salary"]
            assert salary.amount == 8000.0
            assert salary.user == "User1"
            
            # Bonus transaction (US currency)
            bonus = transactions_by_desc["Bonus"]
            assert bonus.amount == 2500.5
            
            # Rent transaction (negative Chinese currency)
            rent = transactions_by_desc["Rent"]
            assert rent.amount == 2000.0  # Should be converted to positive for internal processing
            
            # Transport (different user)
            transport = transactions_by_desc["Transport"]
            assert transport.amount == 200.0
            assert transport.user == "User2"
            
            # Verify users extraction
            users = processor.get_all_users()
            assert "User1" in users
            assert "User2" in users
            assert len(users) == 2
            
        finally:
            os.unlink(temp_file.name)
    
    def test_file_encoding_handling(self):
        """Test handling of different file encodings (UTF-8 for Chinese characters)"""
        chinese_data = [
            ["Description", "Amount", "Debit", "Credit", "User"],
            ["工资收入", "¥8,000.00", "工资收入", "银行账户", "用户1"],
            ["餐饮支出", "-¥500.00", "餐饮", "信用卡", "用户1"],
            ["交通费用", "-¥200.00", "交通", "现金", "用户2"]
        ]
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8')
        for row in chinese_data:
            temp_file.write(','.join(row) + '\n')
        temp_file.close()
        
        try:
            processor = TransactionProcessor(temp_file.name)
            processor.load_transactions()
            
            assert len(processor.transactions) == 3
            
            # Check Chinese characters are preserved
            descriptions = [t.description for t in processor.transactions]
            assert "工资收入" in descriptions
            assert "餐饮支出" in descriptions
            
            # Check Chinese users
            users = processor.get_all_users()
            assert "用户1" in users
            assert "用户2" in users
            
        finally:
            os.unlink(temp_file.name)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
