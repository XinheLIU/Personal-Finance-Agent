"""
Enhanced test suite for Transaction Processing functionality

Tests the third step of the income statement generation workflow:
1. Transaction processing with enhanced prepaid asset handling
2. Transaction type determination and classification  
3. Prepaid asset creation and conversion scenarios
4. Cash flow impact analysis
"""

import pytest
import pandas as pd
import tempfile
import os
from typing import List, Dict

from src.modules.accounting.core.io import TransactionProcessor
from src.modules.accounting.core.models import Transaction, REVENUE_CATEGORIES


class TestTransactionProcessingEnhanced:
    """Enhanced tests for transaction processing with prepaid asset handling"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.processor = TransactionProcessor("")  # Empty path for unit testing
    
    def create_test_csv(self, data: List[List[str]]) -> str:
        """Create a temporary CSV file for testing"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        for row in data:
            temp_file.write(','.join(row) + '\n')
        temp_file.close()
        return temp_file.name
    
    def test_basic_transaction_classification(self):
        """Test basic transaction type classification"""
        # Test revenue transaction
        transaction_type, category, affects_cash_flow, amount = self.processor._determine_transaction_type_and_sign(
            "工资收入", "Bank Account", 8000.0
        )
        assert transaction_type == "expense"  # Since credit is not a revenue category
        
        # Test proper revenue transaction
        transaction_type, category, affects_cash_flow, amount = self.processor._determine_transaction_type_and_sign(
            "Bank Account", "工资收入", 8000.0
        )
        assert transaction_type == "revenue"
        assert category == "工资收入"
        assert amount == 8000.0
    
    def test_expense_transaction_classification(self):
        """Test expense transaction classification"""
        transaction_type, category, affects_cash_flow, amount = self.processor._determine_transaction_type_and_sign(
            "餐饮", "Bank Account", 500.0
        )
        assert transaction_type == "expense"
        assert category == "餐饮"
        assert amount == 500.0
    
    def test_cash_flow_impact_detection(self):
        """Test detection of cash flow impact"""
        # Transaction with cash involvement
        transaction_type, category, affects_cash_flow, amount = self.processor._determine_transaction_type_and_sign(
            "餐饮", "Cash", 500.0
        )
        assert affects_cash_flow == True
        
        # Transaction without cash involvement
        transaction_type, category, affects_cash_flow, amount = self.processor._determine_transaction_type_and_sign(
            "餐饮", "Credit Card", 500.0
        )
        assert affects_cash_flow == False


class TestPrepaidAssetHandling:
    """Comprehensive tests for prepaid asset handling"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.processor = TransactionProcessor("")
    
    def test_prepaid_asset_creation(self):
        """Test prepaid asset creation scenario"""
        # Cash payment for future expense: Debit = prepaid, Credit = cash
        transaction_type, category, affects_cash_flow, amount = self.processor._determine_transaction_type_and_sign(
            "Prepaid Rent", "Cash", 6000.0
        )
        
        assert transaction_type == "prepaid_asset"
        assert category == "Prepaid Rent"
        assert affects_cash_flow == True  # Cash was used
        assert amount == 6000.0
    
    def test_prepaid_asset_conversion_to_expense(self):
        """Test prepaid asset conversion to current expense"""
        # Prepaid expense being used: Debit = expense, Credit = prepaid
        transaction_type, category, affects_cash_flow, amount = self.processor._determine_transaction_type_and_sign(
            "房租", "Prepaid Rent", 2000.0
        )
        
        assert transaction_type == "expense"
        assert category == "房租"
        assert affects_cash_flow == False  # No cash involved in conversion
        assert amount == 2000.0
    
    def test_prepaid_asset_variations(self):
        """Test different variations of prepaid asset naming"""
        prepaid_variations = [
            "Prepaid Insurance",
            "Pre-paid Utilities", 
            "prepaid rent",
            "Prepaid Office Supplies"
        ]
        
        for prepaid_name in prepaid_variations:
            transaction_type, category, affects_cash_flow, amount = self.processor._determine_transaction_type_and_sign(
                prepaid_name, "Bank Account", 1000.0
            )
            assert transaction_type == "prepaid_asset"
            assert category == prepaid_name
    
    def test_prepaid_expense_conversion_variations(self):
        """Test different variations of prepaid expense conversion"""
        conversion_scenarios = [
            ("保险费", "Prepaid Insurance"),
            ("水电费", "Pre-paid Utilities"),
            ("房租", "prepaid rent"),
            ("办公用品", "Prepaid Office Supplies")
        ]
        
        for expense_category, prepaid_account in conversion_scenarios:
            transaction_type, category, affects_cash_flow, amount = self.processor._determine_transaction_type_and_sign(
                expense_category, prepaid_account, 500.0
            )
            assert transaction_type == "expense"
            assert category == expense_category
            assert affects_cash_flow == False
    
    def test_prepaid_asset_complete_workflow(self):
        """Test complete prepaid asset workflow from creation to expense"""
        # Create test data with complete prepaid workflow
        prepaid_workflow_data = [
            ["Description", "Amount", "Debit", "Credit", "User"],
            # Step 1: Pay for 12 months rent in advance
            ["Prepaid Rent Payment", "24000.00", "Prepaid Rent", "Bank Account", "User1"],
            # Step 2: Monthly rent expense (convert prepaid to expense)
            ["January Rent", "2000.00", "房租", "Prepaid Rent", "User1"],
            # Step 3: February rent expense
            ["February Rent", "2000.00", "房租", "Prepaid Rent", "User1"],
            # Step 4: Regular expense (not prepaid)
            ["Utilities", "-500.00", "水电", "Bank Account", "User1"],
        ]
        
        csv_file = self.create_test_csv(prepaid_workflow_data)
        
        try:
            processor = TransactionProcessor(csv_file)
            processor.load_transactions()
            
            assert len(processor.transactions) == 4
            
            # Check transaction types
            transactions_by_desc = {t.description: t for t in processor.transactions}
            
            # Prepaid asset creation
            prepaid_payment = transactions_by_desc["Prepaid Rent Payment"]
            assert prepaid_payment.transaction_type == "prepaid_asset"
            assert prepaid_payment.affects_cash_flow == True
            
            # Prepaid to expense conversions
            jan_rent = transactions_by_desc["January Rent"]
            assert jan_rent.transaction_type == "expense"
            assert jan_rent.affects_cash_flow == False
            
            feb_rent = transactions_by_desc["February Rent"] 
            assert feb_rent.transaction_type == "expense"
            assert feb_rent.affects_cash_flow == False
            
            # Regular expense
            utilities = transactions_by_desc["Utilities"]
            assert utilities.transaction_type == "expense"
            assert utilities.affects_cash_flow == True  # Cash involved
            
        finally:
            os.unlink(csv_file)
    
    def create_test_csv(self, data: List[List[str]]) -> str:
        """Create a temporary CSV file for testing"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        for row in data:
            temp_file.write(','.join(row) + '\n')
        temp_file.close()
        return temp_file.name


class TestComplexTransactionScenarios:
    """Test complex transaction scenarios with mixed types"""
    
    def setup_method(self):
        """Setup test fixtures"""
        pass
    
    def test_mixed_transaction_types_processing(self):
        """Test processing of mixed transaction types"""
        mixed_transaction_data = [
            ["Description", "Amount", "Debit", "Credit", "User"],
            # Revenue transactions
            ["Salary", "8000.00", "Bank Account", "工资收入", "User1"],
            ["Freelance Income", "2000.00", "Cash", "服务收入", "User1"],
            # Regular expenses  
            ["Rent", "-2000.00", "房租", "Bank Account", "User1"],
            ["Groceries", "-500.00", "餐饮", "Credit Card", "User1"],
            # Prepaid asset creation
            ["Insurance Payment", "1200.00", "Prepaid Insurance", "Bank Account", "User1"],
            # Prepaid asset conversion
            ["Monthly Insurance", "100.00", "保险费", "Prepaid Insurance", "User1"],
            # Investment (different user)
            ["Stock Purchase", "-5000.00", "投资", "Bank Account", "User2"],
        ]
        
        csv_file = self.create_test_csv(mixed_transaction_data)
        
        try:
            processor = TransactionProcessor(csv_file)
            processor.load_transactions()
            
            # Should process all valid transactions
            assert len(processor.transactions) == 7
            
            # Check users
            users = processor.get_all_users()
            assert "User1" in users
            assert "User2" in users
            assert len(users) == 2
            
            # Check transaction types distribution
            transaction_types = [t.transaction_type for t in processor.transactions]
            assert "revenue" in transaction_types
            assert "expense" in transaction_types  
            assert "prepaid_asset" in transaction_types
            
            # Check cash flow impacts
            cash_flow_impacts = [t.affects_cash_flow for t in processor.transactions]
            assert True in cash_flow_impacts  # Some affect cash flow
            assert False in cash_flow_impacts  # Some don't (prepaid conversions)
            
        finally:
            os.unlink(csv_file)
    
    def test_multi_user_prepaid_scenarios(self):
        """Test prepaid scenarios across multiple users"""
        multi_user_prepaid_data = [
            ["Description", "Amount", "Debit", "Credit", "User"],
            # User1 prepaid scenarios
            ["User1 Prepaid Rent", "12000.00", "Prepaid Rent", "Bank Account", "User1"],
            ["User1 Jan Rent", "1000.00", "房租", "Prepaid Rent", "User1"],
            # User2 prepaid scenarios
            ["User2 Prepaid Insurance", "2400.00", "Prepaid Insurance", "Bank Account", "User2"],
            ["User2 Monthly Insurance", "200.00", "保险费", "Prepaid Insurance", "User2"],
            # Shared household expenses
            ["Shared Utilities", "-300.00", "水电", "Bank Account", "Household"],
        ]
        
        csv_file = self.create_test_csv(multi_user_prepaid_data)
        
        try:
            processor = TransactionProcessor(csv_file)
            processor.load_transactions()
            
            # Check user-specific transactions
            user1_transactions = processor.get_transactions_by_user("User1")
            user2_transactions = processor.get_transactions_by_user("User2")
            household_transactions = processor.get_transactions_by_user("Household")
            
            assert len(user1_transactions) == 2
            assert len(user2_transactions) == 2 
            assert len(household_transactions) == 1
            
            # Check prepaid assets for each user
            user1_prepaid = [t for t in user1_transactions if t.transaction_type == "prepaid_asset"]
            user2_prepaid = [t for t in user2_transactions if t.transaction_type == "prepaid_asset"]
            
            assert len(user1_prepaid) == 1
            assert len(user2_prepaid) == 1
            
        finally:
            os.unlink(csv_file)
    
    def create_test_csv(self, data: List[List[str]]) -> str:
        """Create a temporary CSV file for testing"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        for row in data:
            temp_file.write(','.join(row) + '\n')
        temp_file.close()
        return temp_file.name


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling in transaction processing"""
    
    def test_invalid_prepaid_scenarios(self):
        """Test handling of invalid or edge case prepaid scenarios"""
        processor = TransactionProcessor("")
        
        # Test edge cases that might be misclassified
        edge_cases = [
            # Description contains "prepaid" but not in debit/credit
            ("Prepaid card purchase", "Bank Account", 100.0),
            # Empty strings
            ("", "", 0.0),
            # Mixed case
            ("PREPAID RENT", "bank account", 1000.0),
        ]
        
        for debit, credit, amount in edge_cases:
            transaction_type, category, affects_cash_flow, corrected_amount = processor._determine_transaction_type_and_sign(
                debit, credit, amount
            )
            # Should handle gracefully without errors
            assert transaction_type in ["revenue", "expense", "prepaid_asset"]
            assert isinstance(affects_cash_flow, bool)
            assert isinstance(corrected_amount, (int, float))
    
    def test_zero_amount_prepaid_handling(self):
        """Test handling of zero-amount prepaid transactions"""
        zero_prepaid_data = [
            ["Description", "Amount", "Debit", "Credit", "User"],
            ["Zero Prepaid", "0.00", "Prepaid Rent", "Bank Account", "User1"],
            ["Prepaid Conversion Zero", "0.00", "房租", "Prepaid Rent", "User1"],
        ]
        
        csv_file = self.create_test_csv(zero_prepaid_data)
        
        try:
            processor = TransactionProcessor(csv_file)
            processor.load_transactions()
            
            # Zero amount transactions should be filtered out
            assert len(processor.transactions) == 0
            
        finally:
            os.unlink(csv_file)
    
    def test_large_amount_prepaid_handling(self):
        """Test handling of very large prepaid amounts"""
        large_amount_data = [
            ["Description", "Amount", "Debit", "Credit", "User"],
            ["Large Prepaid", "1000000.00", "Prepaid Facility", "Bank Account", "User1"],
            ["Large Conversion", "100000.00", "设施费", "Prepaid Facility", "User1"],
        ]
        
        csv_file = self.create_test_csv(large_amount_data)
        
        try:
            processor = TransactionProcessor(csv_file)
            processor.load_transactions()
            
            assert len(processor.transactions) == 2
            
            # Check large amounts are handled correctly
            large_prepaid = processor.transactions[0]
            assert large_prepaid.amount == 1000000.0
            assert large_prepaid.transaction_type == "prepaid_asset"
            
            large_conversion = processor.transactions[1]
            assert large_conversion.amount == 100000.0
            assert large_conversion.transaction_type == "expense"
            
        finally:
            os.unlink(csv_file)
    
    def create_test_csv(self, data: List[List[str]]) -> str:
        """Create a temporary CSV file for testing"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        for row in data:
            temp_file.write(','.join(row) + '\n')
        temp_file.close()
        return temp_file.name


class TestTransactionProcessorIntegration:
    """Integration tests for TransactionProcessor with prepaid handling"""
    
    def test_full_processor_workflow_with_prepaid(self):
        """Test complete processor workflow including prepaid assets"""
        comprehensive_data = [
            ["Description", "Amount", "Debit", "Credit", "User"],
            # Revenue
            ["Salary", "8000.00", "Bank Account", "工资收入", "User1"],
            ["Consulting", "3000.00", "Cash", "服务收入", "User1"],
            # Regular expenses
            ["Rent", "-2000.00", "房租", "Bank Account", "User1"],
            ["Food", "-800.00", "餐饮", "Credit Card", "User1"],
            # Prepaid asset workflow
            ["Annual Insurance", "2400.00", "Prepaid Insurance", "Bank Account", "User1"],
            ["Jan Insurance", "200.00", "保险费", "Prepaid Insurance", "User1"],
            ["Feb Insurance", "200.00", "保险费", "Prepaid Insurance", "User1"],
            # Different user
            ["User2 Salary", "7000.00", "Bank Account", "工资收入", "User2"],
            ["User2 Prepaid", "1200.00", "Prepaid Utilities", "Bank Account", "User2"],
        ]
        
        csv_file = self.create_test_csv(comprehensive_data)
        
        try:
            processor = TransactionProcessor(csv_file)
            processor.load_transactions()
            
            # Comprehensive checks
            assert len(processor.transactions) == 9
            
            # Check transaction type distribution
            by_type = {}
            for t in processor.transactions:
                by_type[t.transaction_type] = by_type.get(t.transaction_type, 0) + 1
            
            assert by_type.get("revenue", 0) == 2  # 2 revenue transactions
            assert by_type.get("expense", 0) == 4  # 4 expense transactions (2 regular + 2 prepaid conversions)
            assert by_type.get("prepaid_asset", 0) == 2  # 2 prepaid asset creations
            
            # Check cash flow impact distribution
            cash_flow_count = sum(1 for t in processor.transactions if t.affects_cash_flow)
            non_cash_flow_count = sum(1 for t in processor.transactions if not t.affects_cash_flow)
            
            assert cash_flow_count == 7  # Revenue, regular expenses, prepaid creations
            assert non_cash_flow_count == 2  # Prepaid conversions
            
            # Check user separation
            users = processor.get_all_users()
            assert len(users) == 2
            assert "User1" in users
            assert "User2" in users
            
            # Check user-specific data
            user1_transactions = processor.get_transactions_by_user("User1")
            user2_transactions = processor.get_transactions_by_user("User2")
            
            assert len(user1_transactions) == 7
            assert len(user2_transactions) == 2
            
        finally:
            os.unlink(csv_file)
    
    def create_test_csv(self, data: List[List[str]]) -> str:
        """Create a temporary CSV file for testing"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        for row in data:
            temp_file.write(','.join(row) + '\n')
        temp_file.close()
        return temp_file.name


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
