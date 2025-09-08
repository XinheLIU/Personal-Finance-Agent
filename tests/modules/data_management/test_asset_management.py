"""
Test suite for Professional Accounting Module - Asset Management

ACCEPTANCE CRITERIA → TEST MAPPING:
- US-1.2: User can manually enter account balances by institution → test_manual_asset_entry_*
- System supports various account types (checking, savings, investment) → test_account_type_validation_*
- User can upload asset data via CSV/Excel → test_asset_bulk_import_*
- System validates balance formats and currency → test_balance_validation_*
- System tracks month-over-month balance changes → test_balance_tracking_*

ASSUMPTIONS FOR VALIDATION:
1. Asset snapshots are taken monthly (end of month)
2. Account names can be in Chinese or English
3. Balance changes are calculated automatically from historical data
4. CSV format: account_name, balance, account_type, as_of_date
5. Multiple accounts can have the same name but different account_type
6. Balance history is preserved for trend analysis
7. Negative balances are allowed (for credit accounts)
8. Asset data is validated before saving
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict, Any
from io import StringIO
import csv
import tempfile
import os


class AssetManager:
    """Asset management service - would be in modules/accounting/data_input/"""
    
    def __init__(self):
        self.assets = []  # In production, this would be a database
        self.balance_history = []
    
    def add_asset_snapshot(self, account_name: str, balance: Decimal, 
                          account_type: str, as_of_date: datetime) -> bool:
        """Add a new asset snapshot"""
        try:
            self._validate_asset_data(account_name, balance, account_type, as_of_date)
            
            asset = {
                "account_name": account_name.strip(),
                "balance": balance,
                "account_type": account_type,
                "as_of_date": as_of_date,
                "currency": "CNY",
                "created_at": datetime.utcnow()
            }
            
            self.assets.append(asset)
            self._update_balance_history(asset)
            return True
            
        except ValueError:
            return False
    
    def _validate_asset_data(self, account_name: str, balance: Decimal, 
                           account_type: str, as_of_date: datetime):
        """Validate asset data"""
        if not account_name or not account_name.strip():
            raise ValueError("Account name cannot be empty")
        
        if account_type not in ["checking", "savings", "investment", "retirement"]:
            raise ValueError("Invalid account type")
        
        if not isinstance(balance, Decimal):
            raise ValueError("Balance must be a Decimal")
        
        if not isinstance(as_of_date, datetime):
            raise ValueError("as_of_date must be a datetime")
    
    def _update_balance_history(self, asset: Dict):
        """Update balance history for tracking changes"""
        self.balance_history.append({
            "account_name": asset["account_name"],
            "account_type": asset["account_type"],
            "balance": asset["balance"],
            "as_of_date": asset["as_of_date"]
        })
    
    def get_assets_by_type(self, account_type: str) -> List[Dict]:
        """Get all assets of a specific type"""
        return [asset for asset in self.assets if asset["account_type"] == account_type]
    
    def get_asset_balance_trend(self, account_name: str, account_type: str) -> List[Dict]:
        """Get balance trend for specific account"""
        return [
            entry for entry in self.balance_history 
            if entry["account_name"] == account_name 
            and entry["account_type"] == account_type
        ]
    
    def calculate_month_over_month_change(self, account_name: str, 
                                        account_type: str) -> Dict[str, Any]:
        """Calculate month-over-month balance change"""
        history = self.get_asset_balance_trend(account_name, account_type)
        
        if len(history) < 2:
            return {"change_amount": Decimal("0"), "change_percentage": Decimal("0")}
        
        # Sort by date
        history.sort(key=lambda x: x["as_of_date"])
        
        current = history[-1]["balance"]
        previous = history[-2]["balance"]
        
        change_amount = current - previous
        
        if previous != 0:
            change_percentage = (change_amount / abs(previous)) * 100
        else:
            change_percentage = Decimal("100") if current > 0 else Decimal("0")
        
        return {
            "change_amount": change_amount,
            "change_percentage": change_percentage,
            "current_balance": current,
            "previous_balance": previous
        }


class AssetImporter:
    """Asset bulk import service - would be in modules/accounting/data_input/"""
    
    def __init__(self, asset_manager: AssetManager):
        self.asset_manager = asset_manager
        self.errors = []
    
    def import_from_csv(self, csv_content: str) -> tuple[int, List[str]]:
        """Import assets from CSV content"""
        self.errors.clear()
        imported_count = 0
        
        try:
            reader = csv.DictReader(StringIO(csv_content))
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    if self._process_asset_row(row):
                        imported_count += 1
                except Exception as e:
                    self.errors.append(f"Row {row_num}: {str(e)}")
                    
        except Exception as e:
            self.errors.append(f"CSV parsing error: {str(e)}")
        
        return imported_count, self.errors
    
    def _process_asset_row(self, row: Dict[str, str]) -> bool:
        """Process a single asset row from CSV"""
        required_fields = ["account_name", "balance", "account_type", "as_of_date"]
        
        # Check required fields
        for field in required_fields:
            if field not in row or not str(row[field]).strip():
                raise ValueError(f"Missing required field: {field}")
        
        # Parse and validate data
        account_name = row["account_name"].strip()
        
        # Parse balance
        try:
            balance_str = row["balance"].replace("¥", "").replace("CNY", "").replace(",", "").strip()
            balance = Decimal(balance_str)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid balance format: {row['balance']}")
        
        account_type = row["account_type"].strip()
        
        # Parse date
        try:
            as_of_date = datetime.strptime(row["as_of_date"], "%Y-%m-%d")
        except ValueError:
            try:
                as_of_date = datetime.strptime(row["as_of_date"], "%Y/%m/%d")
            except ValueError:
                raise ValueError(f"Invalid date format: {row['as_of_date']}")
        
        # Add asset
        return self.asset_manager.add_asset_snapshot(
            account_name, balance, account_type, as_of_date
        )


class TestAssetManualEntry:
    """Test manual asset entry functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.asset_manager = AssetManager()
    
    def test_add_valid_asset(self):
        """Test adding valid asset snapshot"""
        result = self.asset_manager.add_asset_snapshot(
            "中国银行储蓄账户",
            Decimal("50000.00"),
            "savings",
            datetime(2024, 1, 31)
        )
        
        assert result is True
        assert len(self.asset_manager.assets) == 1
        
        asset = self.asset_manager.assets[0]
        assert asset["account_name"] == "中国银行储蓄账户"
        assert asset["balance"] == Decimal("50000.00")
        assert asset["account_type"] == "savings"
        assert asset["currency"] == "CNY"
    
    def test_add_asset_chinese_name(self):
        """Test adding asset with Chinese account name"""
        result = self.asset_manager.add_asset_snapshot(
            "招商银行信用卡",
            Decimal("-2000.00"),  # Credit card debt
            "credit",  # This would be mapped to checking for simplicity
            datetime(2024, 1, 31)
        )
        
        # For this test, we'll use "checking" as the closest valid type
        result = self.asset_manager.add_asset_snapshot(
            "招商银行信用卡",
            Decimal("-2000.00"),
            "checking",
            datetime(2024, 1, 31)
        )
        
        assert result is True
        asset = self.asset_manager.assets[0]
        assert asset["account_name"] == "招商银行信用卡"
        assert asset["balance"] == Decimal("-2000.00")  # Negative balance allowed
    
    def test_add_asset_english_name(self):
        """Test adding asset with English account name"""
        result = self.asset_manager.add_asset_snapshot(
            "Bank of America Checking",
            Decimal("15000.00"),
            "checking",
            datetime(2024, 1, 31)
        )
        
        assert result is True
        asset = self.asset_manager.assets[0]
        assert asset["account_name"] == "Bank of America Checking"
    
    @pytest.mark.parametrize("account_type", ["checking", "savings", "investment", "retirement"])
    def test_valid_account_types(self, account_type):
        """Test all valid account types"""
        result = self.asset_manager.add_asset_snapshot(
            f"Test {account_type} Account",
            Decimal("1000.00"),
            account_type,
            datetime(2024, 1, 31)
        )
        
        assert result is True
        assert self.asset_manager.assets[0]["account_type"] == account_type
    
    @pytest.mark.parametrize("invalid_account_type", ["credit", "loan", "SAVINGS", ""])
    def test_invalid_account_types(self, invalid_account_type):
        """Test invalid account types"""
        result = self.asset_manager.add_asset_snapshot(
            "Test Account",
            Decimal("1000.00"),
            invalid_account_type,
            datetime(2024, 1, 31)
        )
        
        assert result is False
    
    @pytest.mark.parametrize("invalid_account_name", ["", "   ", None])
    def test_invalid_account_names(self, invalid_account_name):
        """Test invalid account names"""
        result = self.asset_manager.add_asset_snapshot(
            invalid_account_name,
            Decimal("1000.00"),
            "checking",
            datetime(2024, 1, 31)
        )
        
        assert result is False
    
    def test_zero_balance_allowed(self):
        """Test that zero balance is allowed"""
        result = self.asset_manager.add_asset_snapshot(
            "Empty Account",
            Decimal("0.00"),
            "checking",
            datetime(2024, 1, 31)
        )
        
        assert result is True
        assert self.asset_manager.assets[0]["balance"] == Decimal("0.00")
    
    def test_negative_balance_allowed(self):
        """Test that negative balance is allowed (for credit scenarios)"""
        result = self.asset_manager.add_asset_snapshot(
            "Credit Account",
            Decimal("-5000.00"),
            "checking",
            datetime(2024, 1, 31)
        )
        
        assert result is True
        assert self.asset_manager.assets[0]["balance"] == Decimal("-5000.00")


class TestAssetTypeFiltering:
    """Test asset filtering by type"""
    
    def setup_method(self):
        """Setup test fixtures with multiple assets"""
        self.asset_manager = AssetManager()
        
        # Add assets of different types
        self.asset_manager.add_asset_snapshot(
            "Checking Account 1", Decimal("5000.00"), "checking", datetime(2024, 1, 31)
        )
        self.asset_manager.add_asset_snapshot(
            "Savings Account 1", Decimal("25000.00"), "savings", datetime(2024, 1, 31)
        )
        self.asset_manager.add_asset_snapshot(
            "Investment Portfolio", Decimal("100000.00"), "investment", datetime(2024, 1, 31)
        )
        self.asset_manager.add_asset_snapshot(
            "Checking Account 2", Decimal("3000.00"), "checking", datetime(2024, 1, 31)
        )
    
    def test_filter_checking_accounts(self):
        """Test filtering checking accounts"""
        checking_accounts = self.asset_manager.get_assets_by_type("checking")
        
        assert len(checking_accounts) == 2
        assert all(asset["account_type"] == "checking" for asset in checking_accounts)
        
        account_names = [asset["account_name"] for asset in checking_accounts]
        assert "Checking Account 1" in account_names
        assert "Checking Account 2" in account_names
    
    def test_filter_savings_accounts(self):
        """Test filtering savings accounts"""
        savings_accounts = self.asset_manager.get_assets_by_type("savings")
        
        assert len(savings_accounts) == 1
        assert savings_accounts[0]["account_name"] == "Savings Account 1"
        assert savings_accounts[0]["balance"] == Decimal("25000.00")
    
    def test_filter_investment_accounts(self):
        """Test filtering investment accounts"""
        investment_accounts = self.asset_manager.get_assets_by_type("investment")
        
        assert len(investment_accounts) == 1
        assert investment_accounts[0]["account_name"] == "Investment Portfolio"
    
    def test_filter_nonexistent_type(self):
        """Test filtering non-existent account type"""
        retirement_accounts = self.asset_manager.get_assets_by_type("retirement")
        assert len(retirement_accounts) == 0


class TestBalanceTracking:
    """Test month-over-month balance tracking"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.asset_manager = AssetManager()
    
    def test_balance_history_tracking(self):
        """Test that balance history is tracked"""
        account_name = "Test Account"
        account_type = "savings"
        
        # Add first snapshot
        self.asset_manager.add_asset_snapshot(
            account_name, Decimal("10000.00"), account_type, datetime(2024, 1, 31)
        )
        
        # Add second snapshot
        self.asset_manager.add_asset_snapshot(
            account_name, Decimal("12000.00"), account_type, datetime(2024, 2, 29)
        )
        
        history = self.asset_manager.get_asset_balance_trend(account_name, account_type)
        
        assert len(history) == 2
        assert history[0]["balance"] == Decimal("10000.00")
        assert history[1]["balance"] == Decimal("12000.00")
    
    def test_month_over_month_positive_change(self):
        """Test positive month-over-month change calculation"""
        account_name = "Growth Account"
        account_type = "investment"
        
        # Add snapshots
        self.asset_manager.add_asset_snapshot(
            account_name, Decimal("10000.00"), account_type, datetime(2024, 1, 31)
        )
        self.asset_manager.add_asset_snapshot(
            account_name, Decimal("11000.00"), account_type, datetime(2024, 2, 29)
        )
        
        change = self.asset_manager.calculate_month_over_month_change(account_name, account_type)
        
        assert change["change_amount"] == Decimal("1000.00")
        assert change["change_percentage"] == Decimal("10.00")  # 10% growth
        assert change["current_balance"] == Decimal("11000.00")
        assert change["previous_balance"] == Decimal("10000.00")
    
    def test_month_over_month_negative_change(self):
        """Test negative month-over-month change calculation"""
        account_name = "Declining Account"
        account_type = "checking"
        
        # Add snapshots
        self.asset_manager.add_asset_snapshot(
            account_name, Decimal("5000.00"), account_type, datetime(2024, 1, 31)
        )
        self.asset_manager.add_asset_snapshot(
            account_name, Decimal("4500.00"), account_type, datetime(2024, 2, 29)
        )
        
        change = self.asset_manager.calculate_month_over_month_change(account_name, account_type)
        
        assert change["change_amount"] == Decimal("-500.00")
        assert change["change_percentage"] == Decimal("-10.00")  # 10% decline
    
    def test_single_snapshot_no_change(self):
        """Test change calculation with only one snapshot"""
        account_name = "New Account"
        account_type = "savings"
        
        self.asset_manager.add_asset_snapshot(
            account_name, Decimal("1000.00"), account_type, datetime(2024, 1, 31)
        )
        
        change = self.asset_manager.calculate_month_over_month_change(account_name, account_type)
        
        assert change["change_amount"] == Decimal("0")
        assert change["change_percentage"] == Decimal("0")
    
    def test_zero_to_positive_change(self):
        """Test change from zero balance to positive"""
        account_name = "Started Empty"
        account_type = "checking"
        
        self.asset_manager.add_asset_snapshot(
            account_name, Decimal("0.00"), account_type, datetime(2024, 1, 31)
        )
        self.asset_manager.add_asset_snapshot(
            account_name, Decimal("1000.00"), account_type, datetime(2024, 2, 29)
        )
        
        change = self.asset_manager.calculate_month_over_month_change(account_name, account_type)
        
        assert change["change_amount"] == Decimal("1000.00")
        assert change["change_percentage"] == Decimal("100")  # Special case for zero base


class TestAssetBulkImport:
    """Test bulk asset import functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.asset_manager = AssetManager()
        self.importer = AssetImporter(self.asset_manager)
    
    def test_csv_import_valid_data(self):
        """Test CSV import with valid asset data"""
        csv_content = """account_name,balance,account_type,as_of_date
中国银行储蓄,50000.00,savings,2024-01-31
工商银行活期,15000.00,checking,2024-01-31
投资组合账户,100000.00,investment,2024-01-31"""
        
        imported_count, errors = self.importer.import_from_csv(csv_content)
        
        assert len(errors) == 0
        assert imported_count == 3
        assert len(self.asset_manager.assets) == 3
        
        # Check first asset
        asset = self.asset_manager.assets[0]
        assert asset["account_name"] == "中国银行储蓄"
        assert asset["balance"] == Decimal("50000.00")
        assert asset["account_type"] == "savings"
    
    def test_csv_import_with_currency_symbols(self):
        """Test CSV import with currency symbols in balance"""
        csv_content = """account_name,balance,account_type,as_of_date
Bank Account 1,¥25000.00,checking,2024-01-31
Bank Account 2,50000.00CNY,savings,2024-01-31
Bank Account 3,"30,000.00",investment,2024-01-31"""
        
        imported_count, errors = self.importer.import_from_csv(csv_content)
        
        assert len(errors) == 0
        assert imported_count == 3
        
        # Check currency symbol removal
        assert self.asset_manager.assets[0]["balance"] == Decimal("25000.00")
        assert self.asset_manager.assets[1]["balance"] == Decimal("50000.00")
        assert self.asset_manager.assets[2]["balance"] == Decimal("30000.00")
    
    def test_csv_import_different_date_formats(self):
        """Test CSV import with different date formats"""
        csv_content = """account_name,balance,account_type,as_of_date
Account 1,1000.00,checking,2024-01-31
Account 2,2000.00,savings,2024/02/29"""
        
        imported_count, errors = self.importer.import_from_csv(csv_content)
        
        assert len(errors) == 0
        assert imported_count == 2
    
    def test_csv_import_with_errors(self):
        """Test CSV import with invalid rows"""
        csv_content = """account_name,balance,account_type,as_of_date
Valid Account,1000.00,checking,2024-01-31
,2000.00,savings,2024-01-31
Invalid Account,invalid_balance,checking,2024-01-31
Another Account,3000.00,invalid_type,2024-01-31
Date Problem,4000.00,savings,invalid-date"""
        
        imported_count, errors = self.importer.import_from_csv(csv_content)
        
        assert imported_count == 1  # Only one valid row
        assert len(errors) == 4  # Four error rows
        
        # Check specific error types
        error_text = " ".join(errors)
        assert "Missing required field: account_name" in error_text
        assert "Invalid balance format: invalid_balance" in error_text
        assert "Invalid account type" in error_text
        assert "Invalid date format: invalid-date" in error_text
    
    def test_csv_import_negative_balances(self):
        """Test CSV import with negative balances"""
        csv_content = """account_name,balance,account_type,as_of_date
Credit Account,-2000.00,checking,2024-01-31
Loan Account,¥-50000.00,checking,2024-01-31"""
        
        imported_count, errors = self.importer.import_from_csv(csv_content)
        
        assert len(errors) == 0
        assert imported_count == 2
        assert self.asset_manager.assets[0]["balance"] == Decimal("-2000.00")
        assert self.asset_manager.assets[1]["balance"] == Decimal("-50000.00")
    
    def test_file_encoding_csv_import(self):
        """Test CSV import with proper Chinese character encoding"""
        csv_data = """account_name,balance,account_type,as_of_date
中国银行储蓄账户,50000.00,savings,2024-01-31
招商银行活期存款,25000.00,checking,2024-01-31
支付宝余额宝,8000.00,savings,2024-01-31"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_data)
            temp_path = f.name
        
        try:
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            imported_count, errors = self.importer.import_from_csv(content)
            
            assert len(errors) == 0
            assert imported_count == 3
            
            # Verify Chinese characters preserved
            assert self.asset_manager.assets[0]["account_name"] == "中国银行储蓄账户"
            assert self.asset_manager.assets[1]["account_name"] == "招商银行活期存款"
            assert self.asset_manager.assets[2]["account_name"] == "支付宝余额宝"
            
        finally:
            os.unlink(temp_path)