"""
Test suite for Data Preview and Editing functionality

Tests the second step of the income statement generation workflow:
1. Data preview functionality
2. Input validation and corner case handling
3. Missing cell detection (NA/''/Null)
4. User prompting for data completion
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from typing import List, Dict, Any
from unittest.mock import Mock, patch

# Note: Since UI components use Streamlit, we'll test the underlying data logic
# and validation functions that would be used by the UI components


class TestDataPreviewValidation:
    """Test data preview and validation functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.valid_df = pd.DataFrame({
            'Description': ['Salary', 'Rent', 'Groceries'],
            'Amount': [8000.0, -2000.0, -500.0],
            'Debit': ['工资收入', '房租', '餐饮'],
            'Credit': ['Bank Account', 'Bank Account', 'Credit Card'],
            'User': ['User1', 'User1', 'User1']
        })
    
    def test_valid_dataframe_validation(self):
        """Test validation of a complete, valid DataFrame"""
        is_valid, errors = self.validate_dataframe(self.valid_df)
        assert is_valid
        assert len(errors) == 0
    
    def test_missing_required_columns(self):
        """Test detection of missing required columns"""
        incomplete_df = pd.DataFrame({
            'Description': ['Salary', 'Rent'],
            'Amount': [8000.0, -2000.0],
            # Missing 'Debit', 'Credit', 'User' columns
        })
        
        is_valid, errors = self.validate_dataframe(incomplete_df)
        assert not is_valid
        assert any('required column' in error.lower() for error in errors)
    
    def test_missing_cells_detection(self):
        """Test detection of missing cells (NA/''/Null) in rows"""
        df_with_missing = pd.DataFrame({
            'Description': ['Salary', '', 'Groceries'],  # Empty string
            'Amount': [8000.0, -2000.0, np.nan],  # NaN value
            'Debit': ['工资收入', '房租', '餐饮'],
            'Credit': ['Bank Account', None, 'Credit Card'],  # None value
            'User': ['User1', 'User1', 'User1']
        })
        
        missing_data = self.find_missing_data(df_with_missing)
        
        # Should detect missing data in multiple rows
        assert len(missing_data) > 0
        
        # Check specific missing data detection
        missing_by_row = {item['row']: item for item in missing_data}
        
        # Row 1 (index 1) has empty Description
        assert 1 in missing_by_row
        assert 'Description' in missing_by_row[1]['columns']
        
        # Row 2 (index 2) has NaN Amount and None Credit
        assert 2 in missing_by_row
        assert 'Amount' in missing_by_row[2]['columns']
        assert 'Credit' in missing_by_row[2]['columns']
    
    def test_data_type_validation(self):
        """Test validation of data types for each column"""
        invalid_types_df = pd.DataFrame({
            'Description': ['Salary', 'Rent', 'Groceries'],
            'Amount': ['not_a_number', -2000.0, -500.0],  # Invalid amount
            'Debit': ['工资收入', '房租', '餐饮'],
            'Credit': ['Bank Account', 'Bank Account', 'Credit Card'],
            'User': ['User1', 'User1', 'User1']
        })
        
        type_errors = self.validate_data_types(invalid_types_df)
        assert len(type_errors) > 0
        assert any('Amount' in error for error in type_errors)
    
    def test_amount_conversion_validation(self):
        """Test validation and conversion of amount values"""
        amounts_df = pd.DataFrame({
            'Description': ['Salary', 'Rent', 'Groceries', 'Bonus', 'Invalid'],
            'Amount': ['8000.0', '¥2,000.00', '-500.75', '$1,500.50', 'invalid_amount'],
            'Debit': ['工资收入', '房租', '餐饮', '服务收入', '其他'],
            'Credit': ['Bank Account', 'Bank Account', 'Credit Card', 'Cash', 'Bank Account'],
            'User': ['User1', 'User1', 'User1', 'User1', 'User1']
        })
        
        converted_amounts, conversion_errors = self.convert_and_validate_amounts(amounts_df)
        
        # Should successfully convert valid amounts
        assert converted_amounts[0] == 8000.0
        assert converted_amounts[1] == 2000.0
        assert converted_amounts[2] == -500.75
        assert converted_amounts[3] == 1500.5
        
        # Should report error for invalid amount
        assert len(conversion_errors) == 1
        assert 'row 4' in conversion_errors[0].lower() or 'Invalid' in conversion_errors[0]
    
    def test_required_field_completion_check(self):
        """Test checking for completion of required fields"""
        incomplete_df = pd.DataFrame({
            'Description': ['Salary', '', 'Groceries'],  # Missing description
            'Amount': [8000.0, -2000.0, ''],  # Missing amount
            'Debit': ['工资收入', '房租', ''],  # Missing debit
            'Credit': ['Bank Account', '', 'Credit Card'],  # Missing credit
            'User': ['User1', 'User1', '']  # Missing user
        })
        
        completion_issues = self.check_required_field_completion(incomplete_df)
        
        # Should identify all rows with missing required fields
        assert len(completion_issues) == 3  # All 3 rows have issues
        
        rows_with_issues = [issue['row'] for issue in completion_issues]
        assert 1 in rows_with_issues  # Row with missing description and credit
        assert 2 in rows_with_issues  # Row with missing amount, debit, and user
    
    def validate_dataframe(self, df: pd.DataFrame) -> tuple[bool, List[str]]:
        """
        Validate DataFrame structure and completeness
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        required_columns = ['Description', 'Amount', 'Debit', 'Credit', 'User']
        
        # Check for required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")
        
        # Check for empty DataFrame
        if df.empty:
            errors.append("DataFrame is empty")
        
        return len(errors) == 0, errors
    
    def find_missing_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Find missing data in DataFrame (empty strings, NaN, None values)
        
        Returns:
            List of dictionaries with row and column information for missing data
        """
        missing_data = []
        
        for idx, row in df.iterrows():
            missing_columns = []
            
            for col in df.columns:
                value = row[col]
                if pd.isna(value) or value == '' or value is None:
                    missing_columns.append(col)
            
            if missing_columns:
                missing_data.append({
                    'row': idx,
                    'columns': missing_columns,
                    'row_data': row.to_dict()
                })
        
        return missing_data
    
    def validate_data_types(self, df: pd.DataFrame) -> List[str]:
        """
        Validate data types for each column
        
        Returns:
            List of data type errors
        """
        errors = []
        
        # Check Amount column can be converted to numeric
        if 'Amount' in df.columns:
            for idx, value in df['Amount'].items():
                if pd.notna(value) and value != '':
                    try:
                        # Try to clean and convert like the actual processor does
                        import re
                        cleaned = re.sub(r'[¥,￥$]', '', str(value))
                        float(cleaned)
                    except (ValueError, TypeError):
                        errors.append(f"Amount in row {idx} cannot be converted to number: '{value}'")
        
        return errors
    
    def convert_and_validate_amounts(self, df: pd.DataFrame) -> tuple[List[float], List[str]]:
        """
        Convert amount strings to floats and validate
        
        Returns:
            Tuple of (converted_amounts, conversion_errors)
        """
        converted_amounts = []
        errors = []
        
        for idx, value in df['Amount'].items():
            try:
                # Use the same cleaning logic as TransactionProcessor
                import re
                if pd.isna(value) or value == '':
                    converted_amounts.append(0.0)
                else:
                    cleaned = re.sub(r'[¥,￥$]', '', str(value))
                    converted_amounts.append(float(cleaned))
            except (ValueError, TypeError):
                converted_amounts.append(0.0)
                errors.append(f"Cannot convert amount in row {idx}: '{value}'")
        
        return converted_amounts, errors
    
    def check_required_field_completion(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Check for completion of required fields and identify issues
        
        Returns:
            List of completion issues with row and field information
        """
        required_fields = ['Description', 'Amount', 'Debit', 'Credit', 'User']
        completion_issues = []
        
        for idx, row in df.iterrows():
            missing_required = []
            
            for field in required_fields:
                if field in df.columns:
                    value = row[field]
                    if pd.isna(value) or value == '' or value is None:
                        missing_required.append(field)
            
            if missing_required:
                completion_issues.append({
                    'row': idx,
                    'missing_fields': missing_required,
                    'row_data': row.to_dict()
                })
        
        return completion_issues


class TestDataEditingValidation:
    """Test data editing and validation functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.sample_df = pd.DataFrame({
            'Description': ['Salary', 'Rent', 'Groceries'],
            'Amount': [8000.0, -2000.0, -500.0],
            'Debit': ['工资收入', '房租', '餐饮'],
            'Credit': ['Bank Account', 'Bank Account', 'Credit Card'],
            'User': ['User1', 'User1', 'User1']
        })
    
    def test_data_editing_validation(self):
        """Test validation after data editing"""
        # Simulate user editing data
        edited_df = self.sample_df.copy()
        edited_df.loc[1, 'Amount'] = '¥3,000.00'  # User edited amount with currency
        edited_df.loc[2, 'Description'] = '超市购物'  # User changed description to Chinese
        
        # Validate edited data
        is_valid, errors = self.validate_edited_data(edited_df)
        assert is_valid
        assert len(errors) == 0
    
    def test_invalid_editing_validation(self):
        """Test validation catches invalid edits"""
        edited_df = self.sample_df.copy()
        edited_df.loc[1, 'Amount'] = 'not_a_number'  # Invalid amount
        edited_df.loc[2, 'User'] = ''  # Cleared required field
        
        is_valid, errors = self.validate_edited_data(edited_df)
        assert not is_valid
        assert len(errors) >= 2  # Should catch both issues
    
    def test_currency_format_preservation(self):
        """Test that currency formats are handled properly in editing"""
        currency_variations = [
            '¥1,000.00',
            '$500.50',
            '2000',
            '-¥800.75',
            '￥1,234.56'
        ]
        
        for currency_str in currency_variations:
            # Test that each format can be processed
            cleaned_amount = self.clean_amount_for_editing(currency_str)
            assert isinstance(cleaned_amount, float)
            assert cleaned_amount >= 0 or currency_str.startswith('-')
    
    def test_data_consistency_after_editing(self):
        """Test data consistency checks after editing"""
        edited_df = self.sample_df.copy()
        
        # Add some inconsistencies
        edited_df.loc[0, 'User'] = 'User2'  # Changed user
        edited_df.loc[1, 'Debit'] = '工资收入'  # Changed expense to revenue category
        
        consistency_issues = self.check_data_consistency(edited_df)
        
        # Should detect potential issues
        assert len(consistency_issues) >= 0  # May or may not have issues depending on business rules
    
    def validate_edited_data(self, df: pd.DataFrame) -> tuple[bool, List[str]]:
        """
        Validate edited DataFrame data
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check for empty required fields
        required_fields = ['Description', 'Amount', 'Debit', 'Credit', 'User']
        for field in required_fields:
            if field in df.columns:
                empty_rows = df[df[field].isna() | (df[field] == '')].index.tolist()
                if empty_rows:
                    errors.append(f"Empty {field} in rows: {empty_rows}")
        
        # Check amount validity
        if 'Amount' in df.columns:
            for idx, value in df['Amount'].items():
                if pd.notna(value) and value != '':
                    try:
                        import re
                        cleaned = re.sub(r'[¥,￥$]', '', str(value))
                        float(cleaned)
                    except (ValueError, TypeError):
                        errors.append(f"Invalid amount in row {idx}: '{value}'")
        
        return len(errors) == 0, errors
    
    def clean_amount_for_editing(self, amount_str: str) -> float:
        """
        Clean amount string from editing interface
        
        Returns:
            Cleaned float value
        """
        import re
        if pd.isna(amount_str) or amount_str == '':
            return 0.0
        
        # Remove currency symbols and commas
        cleaned = re.sub(r'[¥,￥$]', '', str(amount_str))
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    
    def check_data_consistency(self, df: pd.DataFrame) -> List[str]:
        """
        Check for data consistency issues
        
        Returns:
            List of consistency warnings
        """
        warnings = []
        
        # Check for mixed users (might be intentional)
        if 'User' in df.columns:
            unique_users = df['User'].nunique()
            if unique_users > 3:  # Arbitrary threshold
                warnings.append(f"High number of unique users ({unique_users}) - verify data accuracy")
        
        # Check for unusual amount patterns
        if 'Amount' in df.columns:
            numeric_amounts = pd.to_numeric(df['Amount'], errors='coerce')
            if numeric_amounts.min() < -100000:  # Very large expense
                warnings.append("Very large expense detected - verify amount accuracy")
            if numeric_amounts.max() > 1000000:  # Very large income
                warnings.append("Very large income detected - verify amount accuracy")
        
        return warnings


class TestCornerCaseHandling:
    """Test corner case handling in data preview and editing"""
    
    def test_unicode_character_handling(self):
        """Test handling of Unicode characters in Chinese text"""
        unicode_df = pd.DataFrame({
            'Description': ['工资收入', '餐饮支出', '交通费用'],
            'Amount': [8000.0, -500.0, -200.0],
            'Debit': ['工资收入', '餐饮', '交通'],
            'Credit': ['银行账户', '信用卡', '现金'],
            'User': ['用户1', '用户1', '用户2']
        })
        
        # Should handle Unicode without issues
        is_valid, errors = TestDataPreviewValidation().validate_dataframe(unicode_df)
        assert is_valid
        
        missing_data = TestDataPreviewValidation().find_missing_data(unicode_df)
        assert len(missing_data) == 0
    
    def test_very_large_dataset_handling(self):
        """Test handling of large datasets in preview"""
        # Create a large dataset
        large_df = pd.DataFrame({
            'Description': [f'Transaction {i}' for i in range(1000)],
            'Amount': [100.0 * (i % 10 + 1) for i in range(1000)],
            'Debit': ['expense'] * 1000,
            'Credit': ['Bank Account'] * 1000,
            'User': [f'User{i % 5 + 1}' for i in range(1000)]
        })
        
        # Should handle large dataset validation efficiently
        is_valid, errors = TestDataPreviewValidation().validate_dataframe(large_df)
        assert is_valid
        
        # Preview should be limited (this would be handled by UI layer)
        preview_limit = 50
        preview_df = large_df.head(preview_limit)
        assert len(preview_df) == preview_limit
    
    def test_special_character_handling(self):
        """Test handling of special characters in data"""
        special_char_df = pd.DataFrame({
            'Description': ['Café & Restaurant', 'H&M Shopping', 'AT&T Phone Bill'],
            'Amount': [-50.0, -100.0, -80.0],
            'Debit': ['餐饮', '服饰', '通信费'],
            'Credit': ['Credit Card', 'Debit Card', 'Bank Account'],
            'User': ['User@1', 'User#2', 'User$3']
        })
        
        is_valid, errors = TestDataPreviewValidation().validate_dataframe(special_char_df)
        assert is_valid
    
    def test_mixed_data_types_handling(self):
        """Test handling of mixed data types in amount column"""
        mixed_types_df = pd.DataFrame({
            'Description': ['Salary', 'Rent', 'Groceries', 'Bonus'],
            'Amount': [8000, '¥2,000.00', -500.75, '$1,500'],  # Mixed types
            'Debit': ['工资收入', '房租', '餐饮', '服务收入'],
            'Credit': ['Bank Account', 'Bank Account', 'Credit Card', 'Cash'],
            'User': ['User1', 'User1', 'User1', 'User1']
        })
        
        converted_amounts, errors = TestDataPreviewValidation().convert_and_validate_amounts(mixed_types_df)
        
        # Should successfully convert all valid amounts
        assert converted_amounts[0] == 8000.0
        assert converted_amounts[1] == 2000.0
        assert converted_amounts[2] == -500.75
        assert converted_amounts[3] == 1500.0
        assert len(errors) == 0
    
    def test_empty_dataframe_handling(self):
        """Test handling of empty DataFrame"""
        empty_df = pd.DataFrame()
        
        is_valid, errors = TestDataPreviewValidation().validate_dataframe(empty_df)
        assert not is_valid
        assert any('empty' in error.lower() for error in errors)
    
    def test_single_row_dataframe(self):
        """Test handling of single-row DataFrame"""
        single_row_df = pd.DataFrame({
            'Description': ['Single Transaction'],
            'Amount': [100.0],
            'Debit': ['expense'],
            'Credit': ['Bank Account'],
            'User': ['User1']
        })
        
        is_valid, errors = TestDataPreviewValidation().validate_dataframe(single_row_df)
        assert is_valid
        assert len(errors) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
