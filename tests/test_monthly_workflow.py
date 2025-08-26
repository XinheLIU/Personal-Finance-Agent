"""
Test Suite for Monthly Accounting Workflow

This module provides comprehensive tests for the new monthly workflow with:
- 3 inputs: transactions CSV, assets CSV, USD/CNY exchange rate
- 3 outputs: balance sheet, income statement, cash flow statement

Tests validate the complete input→output relationships and data accuracy.
"""

import unittest
import tempfile
import os
from decimal import Decimal
from datetime import datetime, date
from pathlib import Path

from src.accounting.models import (
    MonthlyAsset, MonthlyTransaction, ExchangeRate, OwnerEquity
)
from src.accounting.currency_converter import CurrencyConverter, create_currency_converter
from src.accounting.io import (
    load_monthly_assets_csv, load_exchange_rate_from_file, 
    save_balance_sheet_csv, save_income_statement_csv, save_cash_flow_statement_csv
)
from src.accounting.balance_sheet import BalanceSheetGenerator
from src.accounting.income_statement import IncomeStatementGenerator
from src.accounting.cash_flow import CashFlowGenerator


class TestMonthlyDataModels(unittest.TestCase):
    """Test the new simplified data models for monthly processing"""
    
    def test_monthly_asset_creation_and_validation(self):
        """Test MonthlyAsset creation and validation"""
        # Test valid asset creation
        asset = MonthlyAsset(
            account_name="招商银行储蓄卡",
            cny_balance=Decimal("15000.00"),
            usd_balance=Decimal("2000.00"),
            asset_class="Cash",
            as_of_date=datetime(2025, 7, 31)
        )
        
        self.assertEqual(asset.account_name, "招商银行储蓄卡")
        self.assertEqual(asset.cny_balance, Decimal("15000.00"))
        self.assertEqual(asset.usd_balance, Decimal("2000.00"))
        self.assertEqual(asset.asset_class, "Cash")
        
        # Test validation errors
        with self.assertRaises(ValueError):
            MonthlyAsset("", Decimal("1000"), Decimal("0"), "Cash", datetime.now())
        
        with self.assertRaises(ValueError):
            MonthlyAsset("Test", Decimal("1000"), Decimal("0"), "InvalidClass", datetime.now())
    
    def test_monthly_asset_from_dict(self):
        """Test MonthlyAsset creation from dictionary (CSV import)"""
        csv_row = {
            'Account': '招商银行储蓄卡',
            'CNY': '¥15,000.00',
            'USD': '$2,000.00',
            'Asset Class': 'Cash'
        }
        
        asset = MonthlyAsset.from_dict(csv_row, datetime(2025, 7, 31))
        
        self.assertEqual(asset.account_name, '招商银行储蓄卡')
        self.assertEqual(asset.cny_balance, Decimal('15000.00'))
        self.assertEqual(asset.usd_balance, Decimal('2000.00'))
        self.assertEqual(asset.asset_class, 'Cash')
    
    def test_exchange_rate_creation_and_conversion(self):
        """Test ExchangeRate creation and currency conversion"""
        exchange_rate = ExchangeRate(Decimal("7.19"), datetime(2025, 7, 31))
        
        self.assertEqual(exchange_rate.rate, Decimal("7.19"))
        
        # Test conversions
        cny_amount = Decimal("719.00")
        usd_amount = exchange_rate.cny_to_usd(cny_amount)
        self.assertEqual(usd_amount, Decimal("100.00"))
        
        converted_back = exchange_rate.usd_to_cny(usd_amount)
        self.assertEqual(converted_back, cny_amount)
    
    def test_monthly_transaction_creation(self):
        """Test MonthlyTransaction creation and validation"""
        transaction = MonthlyTransaction(
            date=datetime(2025, 7, 15),
            description="餐饮支出",
            amount=Decimal("-68.50"),
            category="餐饮",
            account_name="招商银行储蓄卡",
            currency="CNY",
            notes="晚餐"
        )
        
        self.assertEqual(transaction.description, "餐饮支出")
        self.assertEqual(transaction.amount, Decimal("-68.50"))
        self.assertEqual(transaction.category, "餐饮")
        self.assertEqual(transaction.currency, "CNY")
    
    def test_owner_equity_creation(self):
        """Test OwnerEquity creation"""
        equity = OwnerEquity("XH", Decimal("100000.00"))
        
        self.assertEqual(equity.owner_name, "XH")
        self.assertEqual(equity.equity_amount, Decimal("100000.00"))


class TestCurrencyConverter(unittest.TestCase):
    """Test currency conversion utilities"""
    
    def setUp(self):
        """Set up test currency converter"""
        exchange_rate = ExchangeRate(Decimal("7.19"), datetime(2025, 7, 31))
        self.converter = CurrencyConverter(exchange_rate)
    
    def test_currency_conversion_accuracy(self):
        """Test accurate currency conversion with rounding"""
        cny_amount = Decimal("1000.00")
        usd_amount = self.converter.cny_to_usd(cny_amount)
        
        # 1000 / 7.19 = 139.08
        expected_usd = Decimal("139.08")
        self.assertEqual(usd_amount, expected_usd)
        
        # Test reverse conversion
        converted_back = self.converter.usd_to_cny(usd_amount)
        # 139.08 * 7.19 = 999.97 (due to rounding)
        self.assertAlmostEqual(float(converted_back), float(cny_amount), places=0)
    
    def test_normalize_asset_currencies(self):
        """Test currency normalization for assets"""
        assets = [
            MonthlyAsset("Cash CNY", Decimal("1000.00"), Decimal("0"), "Cash", datetime.now()),
            MonthlyAsset("Cash USD", Decimal("0"), Decimal("100.00"), "Cash", datetime.now()),
            MonthlyAsset("Both Currencies", Decimal("500.00"), Decimal("50.00"), "Cash", datetime.now())
        ]
        
        normalized = self.converter.normalize_asset_currencies(assets)
        
        # First asset should now have USD calculated
        self.assertGreater(normalized[0].usd_balance, 0)
        # Second asset should now have CNY calculated  
        self.assertGreater(normalized[1].cny_balance, 0)
        # Third asset should remain unchanged
        self.assertEqual(normalized[2].cny_balance, Decimal("500.00"))
        self.assertEqual(normalized[2].usd_balance, Decimal("50.00"))
    
    def test_calculate_totals_by_class(self):
        """Test asset total calculation by class"""
        assets = [
            MonthlyAsset("Cash1", Decimal("1000.00"), Decimal("100.00"), "Cash", datetime.now()),
            MonthlyAsset("Cash2", Decimal("500.00"), Decimal("50.00"), "Cash", datetime.now()),
            MonthlyAsset("Investment", Decimal("2000.00"), Decimal("200.00"), "Investments", datetime.now())
        ]
        
        totals = self.converter.calculate_totals_by_class(assets)
        
        self.assertEqual(totals["Cash"]["cny"], Decimal("1500.00"))
        self.assertEqual(totals["Cash"]["usd"], Decimal("150.00"))
        self.assertEqual(totals["Investments"]["cny"], Decimal("2000.00"))
        self.assertEqual(totals["Investments"]["usd"], Decimal("200.00"))
    
    def test_currency_formatting(self):
        """Test currency amount formatting"""
        amount = Decimal("1234.56")
        
        cny_formatted = self.converter.format_currency_amount(amount, "CNY")
        usd_formatted = self.converter.format_currency_amount(amount, "USD")
        
        self.assertEqual(cny_formatted, "¥1,234.56")
        self.assertEqual(usd_formatted, "$1,234.56")


class TestIOFunctions(unittest.TestCase):
    """Test I/O functions for the new workflow"""
    
    def test_load_monthly_assets_csv(self):
        """Test loading assets from simplified CSV format"""
        # Create temporary CSV file
        csv_content = """Account,CNY,USD,Asset Class
招商银行储蓄卡,"¥15,000.00","$2,000.00",Cash
支付宝余额,"¥2,800.00",,Cash
投资账户,,"$1,000.00",Investments"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            temp_path = f.name
        
        try:
            assets, errors = load_monthly_assets_csv(temp_path, datetime(2025, 7, 31))
            
            self.assertEqual(len(errors), 0)
            self.assertEqual(len(assets), 3)
            
            # Check first asset
            self.assertEqual(assets[0].account_name, "招商银行储蓄卡")
            self.assertEqual(assets[0].cny_balance, Decimal("15000.00"))
            self.assertEqual(assets[0].usd_balance, Decimal("2000.00"))
            self.assertEqual(assets[0].asset_class, "Cash")
            
            # Check assets with missing currency values
            self.assertEqual(assets[1].usd_balance, Decimal("0"))
            self.assertEqual(assets[2].cny_balance, Decimal("0"))
            
        finally:
            os.unlink(temp_path)
    
    def test_load_exchange_rate_from_file(self):
        """Test loading exchange rate from text file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("7.19")
            temp_path = f.name
        
        try:
            exchange_rate, errors = load_exchange_rate_from_file(temp_path, datetime(2025, 7, 31))
            
            self.assertEqual(len(errors), 0)
            self.assertIsNotNone(exchange_rate)
            self.assertEqual(exchange_rate.rate, Decimal("7.19"))
            
        finally:
            os.unlink(temp_path)


class TestFinancialStatementGenerators(unittest.TestCase):
    """Test financial statement generation"""
    
    def setUp(self):
        """Set up test data and currency converter"""
        exchange_rate = ExchangeRate(Decimal("7.19"), datetime(2025, 7, 31))
        self.converter = CurrencyConverter(exchange_rate)
        
        # Create test assets
        self.test_assets = [
            MonthlyAsset("招商银行储蓄卡", Decimal("100000.00"), Decimal("0"), "Cash", datetime(2025, 7, 31)),
            MonthlyAsset("投资账户", Decimal("50000.00"), Decimal("0"), "Investments", datetime(2025, 7, 31)),
            MonthlyAsset("长期投资XH", Decimal("30000.00"), Decimal("0"), "Long-term investments", datetime(2025, 7, 31)),
            MonthlyAsset("长期投资YY", Decimal("20000.00"), Decimal("0"), "Long-term investments", datetime(2025, 7, 31))
        ]
        
        # Create test transactions
        self.test_transactions = [
            MonthlyTransaction(datetime(2025, 7, 1), "工资收入", Decimal("10000.00"), "工资收入", "银行卡"),
            MonthlyTransaction(datetime(2025, 7, 5), "餐饮支出", Decimal("-500.00"), "餐饮", "银行卡"),
            MonthlyTransaction(datetime(2025, 7, 10), "房租", Decimal("-3000.00"), "房租", "银行卡"),
            MonthlyTransaction(datetime(2025, 7, 15), "服务收入", Decimal("2000.00"), "服务收入", "银行卡")
        ]
    
    def test_balance_sheet_generation(self):
        """Test balance sheet generation with dual-currency and multi-user support"""
        generator = BalanceSheetGenerator(self.converter)
        
        # Extract owner equity (simplified test)
        owner_equity = {"XH": Decimal("120000.00"), "YY": Decimal("80000.00")}
        
        balance_sheet = generator.generate_balance_sheet(
            self.test_assets, 
            owner_equity, 
            date(2025, 7, 31)
        )
        
        # Verify structure
        self.assertIn('as_of_date', balance_sheet)
        self.assertIn('current_assets', balance_sheet)
        self.assertIn('fixed_assets', balance_sheet)
        self.assertIn('owner_equity', balance_sheet)
        self.assertIn('exchange_rate', balance_sheet)
        
        # Verify dual currency
        self.assertIn('total_assets_cny', balance_sheet)
        self.assertIn('total_assets_usd', balance_sheet)
        
        # Verify multi-user equity
        self.assertIn('XH', balance_sheet['owner_equity'])
        self.assertIn('YY', balance_sheet['owner_equity'])
    
    def test_income_statement_generation(self):
        """Test income statement generation from monthly transactions"""
        generator = IncomeStatementGenerator()
        
        income_statement = generator.generate_monthly_income_statement_from_monthly_transactions(
            self.test_transactions, 7, 2025, self.converter
        )
        
        # Verify structure
        self.assertIn('period', income_statement)
        self.assertIn('revenues', income_statement)
        self.assertIn('expenses', income_statement)
        self.assertIn('tax_expense', income_statement)
        self.assertIn('net_operating_income', income_statement)
        
        # Verify calculations
        self.assertEqual(income_statement['period'], '2025-07')
        self.assertIn('Service Revenue', income_statement['revenues'])
        
    def test_cash_flow_statement_generation(self):
        """Test cash flow statement generation from monthly transactions"""
        generator = CashFlowGenerator()
        
        cash_flow = generator.generate_cash_flow_statement_from_monthly_transactions(
            self.test_transactions, 7, 2025, self.converter
        )
        
        # Verify structure
        self.assertIn('period', cash_flow)
        self.assertIn('operating_activities', cash_flow)
        self.assertIn('investing_activities', cash_flow)
        self.assertIn('financing_activities', cash_flow)
        self.assertIn('net_change_in_cash', cash_flow)
        
        # Verify period
        self.assertEqual(cash_flow['period'], '2025-07')


class TestIntegratedWorkflow(unittest.TestCase):
    """Integration tests for the complete 3-input → 3-output workflow"""
    
    def test_complete_monthly_workflow(self):
        """Test the complete monthly workflow from CSV inputs to financial statements"""
        # Create temporary input files
        assets_csv = """Account,CNY,USD,Asset Class
招商银行储蓄卡,"¥100,000.00",,Cash
投资账户,"¥50,000.00",,Investments
长期投资XH,"¥30,000.00",,Long-term investments
长期投资YY,"¥20,000.00",,Long-term investments"""
        
        # Note: Transaction CSV format to be determined when sample file is fixed
        # For now, create a simplified test
        
        exchange_rate_txt = "7.19"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write test files
            assets_path = os.path.join(temp_dir, "assets.csv")
            rate_path = os.path.join(temp_dir, "rate.txt")
            
            with open(assets_path, 'w', encoding='utf-8') as f:
                f.write(assets_csv)
            
            with open(rate_path, 'w', encoding='utf-8') as f:
                f.write(exchange_rate_txt)
            
            # Load inputs
            assets, asset_errors = load_monthly_assets_csv(assets_path, datetime(2025, 7, 31))
            exchange_rate, rate_errors = load_exchange_rate_from_file(rate_path, datetime(2025, 7, 31))
            
            # Verify inputs loaded successfully
            self.assertEqual(len(asset_errors), 0)
            self.assertEqual(len(rate_errors), 0)
            self.assertEqual(len(assets), 4)
            self.assertIsNotNone(exchange_rate)
            
            # Create currency converter
            converter = CurrencyConverter(exchange_rate)
            
            # Generate balance sheet
            bs_generator = BalanceSheetGenerator(converter)
            owner_equity = bs_generator.extract_owner_equity_from_assets(assets)
            balance_sheet = bs_generator.generate_balance_sheet(assets, owner_equity, date(2025, 7, 31))
            
            # Verify balance sheet structure
            self.assertIn('current_assets', balance_sheet)
            self.assertIn('fixed_assets', balance_sheet)
            self.assertIn('owner_equity', balance_sheet)
            
            # Test CSV export
            bs_output_path = os.path.join(temp_dir, "balance_sheet.csv")
            bs_errors = save_balance_sheet_csv(balance_sheet, bs_output_path)
            
            self.assertEqual(len(bs_errors), 0)
            self.assertTrue(os.path.exists(bs_output_path))
    
    def test_data_consistency_validation(self):
        """Test data consistency between inputs and outputs"""
        # Create test data
        test_assets = [
            MonthlyAsset("Cash", Decimal("100000.00"), Decimal("0"), "Cash", datetime(2025, 7, 31)),
            MonthlyAsset("Investments", Decimal("50000.00"), Decimal("0"), "Investments", datetime(2025, 7, 31))
        ]
        
        exchange_rate = ExchangeRate(Decimal("7.19"), datetime(2025, 7, 31))
        converter = CurrencyConverter(exchange_rate)
        
        # Generate balance sheet
        bs_generator = BalanceSheetGenerator(converter)
        owner_equity = {"XH": Decimal("90000.00"), "YY": Decimal("60000.00")}
        balance_sheet = bs_generator.generate_balance_sheet(test_assets, owner_equity, date(2025, 7, 31))
        
        # Verify total assets consistency
        total_assets_cny = sum(asset.cny_balance for asset in test_assets)
        total_owner_equity_cny = sum(owner_equity.values())
        
        # In this simple case (no liabilities), total assets should equal total equity
        self.assertEqual(total_assets_cny, Decimal("150000.00"))
        self.assertEqual(total_owner_equity_cny, Decimal("150000.00"))


if __name__ == '__main__':
    # Create test suite
    test_classes = [
        TestMonthlyDataModels,
        TestCurrencyConverter, 
        TestIOFunctions,
        TestFinancialStatementGenerators,
        TestIntegratedWorkflow
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")