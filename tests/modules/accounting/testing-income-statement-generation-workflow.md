# 🧪 Testing Strategy for Income Statement Generation Workflow

> **Testing Philosophy**: Follow the 8-step MVP workflow with comprehensive unit, integration, and end-to-end tests ensuring each layer (Model-View-Presenter) maintains proper separation of concerns.

---

## 📋 Table of Contents
1. [Testing Principles](#-testing-principles)
2. [Test Structure (MVP Pattern)](#-test-structure-mvp-pattern)
3. [Workflow-Based Testing Strategy](#-workflow-based-testing-strategy)
4. [Test Coverage Matrix](#-test-coverage-matrix)
5. [Integration & E2E Testing](#-integration--e2e-testing)
6. [Legacy Test Migration Plan](#-legacy-test-migration-plan)

---

## 🎯 Testing Principles

### 1. **Layer Isolation Testing**
- **Model Layer**: Test business logic in complete isolation (no UI, no coordination)
- **Presenter Layer**: Test coordination logic with mocked models and views
- **View Layer**: Test UI components with mocked data (no business logic)

### 2. **Test Data Strategy**
- **Real CSV Files**: Use actual transaction CSVs from `tests/test_cases/`
- **Edge Cases**: Empty rows, currency symbols (¥, $), unicode, malformed data
- **Multi-User Scenarios**: Test individual + consolidated reporting

### 3. **Workflow Integrity**
- **Sequential Testing**: Each workflow step builds on previous step's output
- **Integration Tests**: Validate data flow between steps
- **E2E Tests**: Complete workflow from CSV upload to statement export

### 4. **Error Handling**
- **Validation Failures**: Test all business rule violations
- **Data Quality Issues**: Missing fields, invalid types, empty data
- **User Corrections**: Simulate user editing after validation errors

---

## 🏗️ Test Structure (MVP Pattern)

```
tests/modules/accounting/
├── unit/                          # Isolated component tests
│   ├── models/
│   │   ├── domain/
│   │   │   ├── test_transaction.py              ✅ Transaction entity
│   │   │   ├── test_category_mapper.py          ✅ Category mapping logic
│   │   │   └── test_statements.py               📋 Statement data structures
│   │   ├── business/
│   │   │   ├── test_data_cleaner.py             📋 **STEP 2: Data cleaning & validation** ⭐
│   │   │   ├── test_transaction_processor.py     📋 **STEP 4: Transaction processing**
│   │   │   ├── test_income_statement_generator.py 📋 **STEP 5: Income statement generation**
│   │   │   └── test_cash_flow_generator.py       📋 Cash flow generation
│   │   └── repositories/
│   │       └── test_data_storage.py              📋 **STEP 8: System storage**
│   ├── presenters/
│   │   ├── test_income_statement_presenter.py    📋 **STEP 6: Business orchestration**
│   │   ├── test_cash_flow_presenter.py           📋 Cash flow orchestration
│   │   └── test_transaction_presenter.py         📋 Transaction orchestration
│   └── views/
│       ├── test_components.py                    📋 **STEP 1 & 3: Upload & preview UI**
│       ├── test_pages.py                         📋 Page navigation
│       └── test_displays.py                      📋 **STEP 7: Results display**
│
├── integration/                   # Cross-layer integration tests
│   ├── test_workflow_step_integration.py         📋 Step-by-step data flow
│   ├── test_data_pipeline.py                     📋 CSV → Clean → Process → Generate
│   └── test_multi_user_workflow.py               📋 Multi-user end-to-end
│
├── e2e/                          # Complete workflow tests
│   ├── test_income_statement_workflow.py         📋 Full 8-step workflow
│   ├── test_error_recovery_workflow.py           📋 Validation error handling
│   └── test_real_world_scenarios.py              📋 Production-like test cases
│
└── legacy/                       # Legacy compatibility tests
    ├── test_accounting.py                        ✅ Core functionality
    ├── test_consolidated_reports.py              ✅ Advanced features
    ├── test_comparative_analysis.py              ✅ Analytics
    ├── test_csv_upload_validation.py             ✅ CSV processing (→ migrate to DataCleaner tests)
    ├── test_data_preview_validation.py           ✅ Data validation (→ migrate to DataCleaner tests)
    ├── test_transaction_processing_enhanced.py   ✅ Enhanced processing
    └── test_income_statement_enhanced.py         ✅ Enhanced income statements
```

---

## 🔄 Workflow-Based Testing Strategy

### **STEP 1: CSV Upload (View Layer)** 
📁 `tests/unit/views/test_components.py:TestCSVUpload`

**Component**: `views/components.py:handle_csv_upload()`

#### Test Cases
```python
class TestCSVUpload:
    """Test passive CSV upload UI component (no business logic)"""
    
    def test_file_upload_widget_rendering():
        """Verify upload widget displays correctly"""
        # Assert: File upload UI renders with correct accept types (.csv)
        
    def test_file_path_extraction():
        """Test extraction of uploaded file path"""
        # Given: Mock uploaded file
        # When: handle_csv_upload() called
        # Then: Returns correct file path string
        
    def test_large_file_handling():
        """Test UI behavior with large CSV files (>10MB)"""
        # Assert: UI provides loading indicator or progress bar
        
    def test_invalid_file_type_rejection():
        """Test UI rejects non-CSV files (.xlsx, .txt)"""
        # Assert: Error message displayed, no file path returned
        
    def test_security_file_path_sanitization():
        """Test file path sanitization for security"""
        # Given: File with malicious path (../../etc/passwd)
        # Then: Path sanitized or rejected
```

**Expected Output**: Raw file path string → passed to DataCleaner


---

### **STEP 2: Data Cleaning & Validation (Model Layer)** ⭐ **NEW CRITICAL COMPONENT**
📁 `tests/unit/models/business/test_data_cleaner.py`

**Component**: `models/business/data_cleaner.py:DataCleaner`

#### Test Cases

##### A. **Data Cleaning Operations** 
```python
class TestDataCleaning:
    """Test automated data cleaning (BEFORE user preview)"""
    
    def test_remove_completely_empty_rows():
        """Remove rows with ALL empty cells"""
        # Given: CSV with 3 empty rows interspersed
        # When: DataCleaner.clean()
        # Then: Empty rows removed, valid rows preserved
        
    def test_remove_empty_columns():
        """Remove columns with ALL empty cells"""
        # Given: CSV with 2 empty columns
        # When: DataCleaner.clean()
        # Then: Empty columns removed
        
    def test_normalize_currency_symbols():
        """Convert ¥8,000.00 → 8000.00"""
        # Given: Amounts with ¥, $, commas, decimals
        # When: DataCleaner.clean()
        # Then: Pure numeric values (float)
        # Test cases:
        #   - ¥8,000.00 → 8000.0
        #   - $1,500 → 1500.0
        #   - -2,000.50 → -2000.5
        #   - ¥-800 → -800.0
        
    def test_strip_whitespace_from_text():
        """Remove leading/trailing spaces from all text fields"""
        # Given: "  Monthly Salary  ", "  工资收入  "
        # When: DataCleaner.clean()
        # Then: "Monthly Salary", "工资收入"
        
    def test_standardize_date_formats():
        """Convert various date formats to YYYY-MM-DD"""
        # Given: "2025/07/15", "15-07-2025", "July 15, 2025"
        # When: DataCleaner.clean()
        # Then: "2025-07-15"
        
    def test_preserve_valid_data():
        """Ensure valid data unchanged after cleaning"""
        # Given: Perfect CSV with no issues
        # When: DataCleaner.clean()
        # Then: Data identical (except whitespace normalized)
```

##### B. **Validation Rules**
```python
class TestDataValidation:
    """Test business rule validation (BEFORE user preview)"""
    
    def test_required_fields_validation():
        """If Amount exists, Debit AND Credit accounts required"""
        # Given: Row with Amount=5000, Debit='工资收入', Credit=empty
        # When: DataCleaner.validate()
        # Then: ValidationError with row number and missing field
        
    def test_data_type_validation():
        """Amount must be numeric, Description must be text"""
        # Given: Amount='invalid', Description=123
        # When: DataCleaner.validate()
        # Then: ValidationErrors for both fields with row numbers
        
    def test_business_rule_revenue_positive_amounts():
        """Revenue categories must have positive amounts"""
        # Given: Row with Debit='工资收入' (revenue), Amount=-5000
        # When: DataCleaner.validate()
        # Then: ValidationError "Revenue must be positive (Row 3)"
        
    def test_business_rule_expense_negative_amounts():
        """Expense categories typically negative (warning, not error)"""
        # Given: Row with Debit='餐饮' (expense), Amount=800 (positive)
        # When: DataCleaner.validate()
        # Then: Warning "Expense is positive - is this correct? (Row 5)"
        
    def test_collect_all_validation_errors():
        """Collect ALL errors, not just first one"""
        # Given: CSV with 5 different validation errors
        # When: DataCleaner.validate()
        # Then: ValidationReport with all 5 errors, each with row number
```

##### C. **Validation Report Structure**
```python
class TestValidationReporting:
    """Test validation error reporting for UI display"""
    
    def test_validation_report_structure():
        """Verify ValidationReport data structure"""
        # Expected structure:
        # {
        #     'is_valid': False,
        #     'errors': [
        #         {'row': 3, 'field': 'Credit', 'message': 'Missing required field'},
        #         {'row': 5, 'field': 'Amount', 'message': 'Must be numeric'}
        #     ],
        #     'warnings': [
        #         {'row': 7, 'field': 'Amount', 'message': 'Expense is positive'}
        #     ]
        # }
        
    def test_error_messages_with_row_numbers():
        """All errors include specific row references"""
        # Assert: Each error has 'row' field for user to locate issue
        
    def test_field_level_error_marking():
        """Errors reference specific fields for highlighting"""
        # Assert: Each error has 'field' name for UI highlighting
```

##### D. **Edge Cases & Error Handling**
```python
class TestDataCleanerEdgeCases:
    """Test edge cases and error scenarios"""
    
    def test_empty_csv_file():
        """Handle completely empty CSV"""
        # Given: Empty file or only headers
        # When: DataCleaner.clean()
        # Then: Return empty DataFrame, no errors
        
    def test_malformed_csv_structure():
        """Handle CSV with inconsistent column counts"""
        # Given: Row 1 has 5 columns, Row 2 has 3 columns
        # When: DataCleaner.clean()
        # Then: Normalize to max columns, fill missing with NaN
        
    def test_unicode_character_handling():
        """Preserve Chinese, emoji, special characters"""
        # Given: "午餐 🍜", "Café", "résumé"
        # When: DataCleaner.clean()
        # Then: Unicode preserved correctly
        
    def test_extremely_large_amounts():
        """Handle very large numbers (millions, billions)"""
        # Given: "¥1,234,567,890.00"
        # When: DataCleaner.clean()
        # Then: 1234567890.0 (no precision loss)
        
    def test_mixed_currency_symbols_in_same_file():
        """Handle multiple currency types in one CSV"""
        # Given: Some rows with ¥, others with $
        # When: DataCleaner.clean()
        # Then: Both normalized to pure numbers
        # Note: Currency type tracking (if needed) handled separately
```

**Expected Output**: 
- Cleaned DataFrame (ready for preview)
- ValidationReport (errors + warnings with row numbers)


---

### **STEP 3: Data Preview & Editing (View Layer)**
📁 `tests/unit/views/test_components.py:TestDataPreviewEditor`

**Component**: `views/components.py:show_data_preview_editor()`

#### Test Cases
```python
class TestDataPreviewEditor:
    """Test passive UI for previewing CLEAN data"""
    
    def test_display_cleaned_data():
        """Show pre-cleaned data in editable table"""
        # Given: Cleaned DataFrame (no empty rows, normalized currency)
        # When: show_data_preview_editor(cleaned_df, validation_report)
        # Then: Table displays clean data
        
    def test_highlight_validation_errors():
        """Mark cells with validation errors"""
        # Given: ValidationReport with errors for rows 3, 5
        # When: Render preview
        # Then: Rows 3, 5 highlighted in red with error tooltips
        
    def test_inline_editing_capability():
        """Allow user to edit cells to fix issues"""
        # Given: Editable table UI
        # When: User clicks cell, edits value
        # Then: DataFrame updated with new value
        # Note: NO validation here - just UI update
        
    def test_visual_required_field_indicators():
        """Show which fields are required"""
        # Given: Row with Amount but missing Credit
        # When: Render preview
        # Then: Credit column header marked with asterisk/color
        
    def test_currency_format_display():
        """Display amounts with currency formatting (for readability)"""
        # Given: Amount=8000.0 (numeric)
        # When: Render preview
        # Then: Display "¥8,000.00" (formatted, but still numeric in data)
        # Note: Formatting for DISPLAY only, data stays numeric
```

**Input**: Cleaned DataFrame + ValidationReport  
**Output**: User-corrected DataFrame (business issues fixed)

---

### **STEP 4: Transaction Processing (Model Layer)**
📁 `tests/unit/models/business/test_transaction_processor.py`

**Component**: `models/business/transaction_processor.py:TransactionProcessor`

#### Test Cases
```python
class TestTransactionProcessor:
    """Test conversion of DataFrame to Transaction objects"""
    
    def test_load_transactions_from_cleaned_dataframe():
        """Parse corrected DataFrame into Transaction objects"""
        # Given: User-corrected DataFrame (already clean & valid)
        # When: TransactionProcessor.load_transactions(df)
        # Then: List of Transaction objects created
        # Note: NO data cleaning needed - already done in Step 2!
        
    def test_transaction_type_classification_revenue():
        """Classify revenue transactions"""
        # Given: Debit='工资收入' (in REVENUE_CATEGORIES), Amount=8000
        # When: _determine_transaction_type_and_sign()
        # Then: transaction_type='revenue', amount=8000.0
        
    def test_transaction_type_classification_expense():
        """Classify expense transactions"""
        # Given: Amount=-2000 OR Debit in expense categories
        # When: _determine_transaction_type_and_sign()
        # Then: transaction_type='expense', amount=2000.0 (abs value)
        
    def test_prepaid_asset_classification():
        """Special handling for prepaid expenses"""
        # Given: Debit='预付费用', transaction_type='prepaid_asset'
        # When: Process transaction
        # Then: Transaction marked as prepaid, excluded from current income
        
    def test_multi_user_extraction():
        """Extract unique users from transactions"""
        # Given: DataFrame with User column: ['User1', 'User2', 'User1']
        # When: TransactionProcessor.get_all_users()
        # Then: ['User1', 'User2']
        
    def test_preserve_transaction_metadata():
        """Keep all original transaction data"""
        # Given: Transaction with custom fields (notes, tags, etc.)
        # When: Parse to Transaction object
        # Then: All metadata preserved in Transaction.metadata dict
```

**Input**: User-corrected DataFrame  
**Output**: List of Transaction objects

---

### **STEP 5: Income Statement Generation (Model Layer)**
📁 `tests/unit/models/business/test_income_statement_generator.py`

**Component**: `models/business/income_statement_generator.py:IncomeStatementGenerator`

#### Test Cases
```python
class TestIncomeStatementGenerator:
    """Test income statement generation from transactions"""
    
    def test_revenue_categorization():
        """Group revenue by category"""
        # Given: Transactions with categories ['工资收入', '服务收入', '工资收入']
        # When: IncomeStatementGenerator.generate()
        # Then: Revenue = {'工资收入': 16000, '服务收入': 2000}
        
    def test_expense_categorization_with_category_mapper():
        """Use CategoryMapper for expense classification"""
        # Given: Expenses ['房租', '餐饮', '交通', '所得税']
        # When: Generate income statement
        # Then: Expenses grouped by CategoryMapper logic
        #       {'住房': 2000, '食品': 800, '交通': 200, '税务': 1000}
        
    def test_total_revenue_calculation():
        """Sum all revenue categories"""
        # Given: Revenue = {'工资收入': 8000, '服务收入': 2000}
        # When: Calculate totals
        # Then: Total Revenue = 10000
        
    def test_total_expenses_calculation():
        """Sum all expense categories"""
        # Given: Expenses = {'住房': 2000, '食品': 800}
        # When: Calculate totals
        # Then: Total Expenses = 2800
        
    def test_net_income_calculation():
        """Net Income = Total Revenue - Total Expenses"""
        # Given: Total Revenue=10000, Total Expenses=2800
        # When: Calculate net income
        # Then: Net Income = 7200
        
    def test_multi_user_individual_statements():
        """Generate statement for each user"""
        # Given: Transactions for User1 and User2
        # When: Generate statements
        # Then: Two separate statements + combined household statement
        
    def test_prepaid_asset_exclusion():
        """Exclude prepaid assets from current period income"""
        # Given: Transactions including prepaid_asset type
        # When: Generate income statement
        # Then: Prepaid assets NOT in revenue or expenses
        
    def test_tax_expense_separation():
        """Show tax expenses separately"""
        # Given: Transactions with tax categories (所得税, 增值税)
        # When: Generate statement
        # Then: Tax expenses in separate section (not mixed with operating)
```

**Input**: List of Transaction objects  
**Output**: Income statement dictionaries (per user + household)


---

### **STEP 6: Business Logic Orchestration (Presenter Layer)**
📁 `tests/unit/presenters/test_income_statement_presenter.py`

**Component**: `presenters/income_statement_presenter.py:IncomeStatementPresenter`

#### Test Cases
```python
class TestIncomeStatementPresenter:
    """Test orchestration of workflow steps 2-5"""
    
    def test_workflow_orchestration():
        """Coordinate DataCleaner → Processor → Generator"""
        # Given: Raw CSV file path
        # When: IncomeStatementPresenter.process_transaction_statements()
        # Then: Calls steps in correct order:
        #   1. DataCleaner.clean() + validate()
        #   2. TransactionProcessor.load_transactions()
        #   3. IncomeStatementGenerator.generate()
        
    def test_validation_error_handling():
        """Handle validation failures gracefully"""
        # Given: CSV with validation errors
        # When: Presenter processes
        # Then: Returns ValidationReport to View, does NOT proceed to processing
        
    def test_multi_user_coordination():
        """Coordinate multi-user statement generation"""
        # Given: Transactions for 3 users
        # When: Presenter processes
        # Then: Coordinates generation of 4 statements (3 individual + 1 household)
        
    def test_error_propagation():
        """Propagate Model errors to View layer"""
        # Given: Model raises exception
        # When: Presenter processes
        # Then: Error caught, formatted, returned to View for display
        
    def test_no_business_logic_in_presenter():
        """Presenter only coordinates, no business decisions"""
        # Assert: All calculations, validations done by Model components
        # Assert: Presenter only calls Model methods, passes data between layers
```

**Input**: Raw CSV file path  
**Output**: Complete income statement set OR ValidationReport

---

### **STEP 7: Results Display & Export (View Layer)**
📁 `tests/unit/views/test_displays.py:TestIncomeStatementDisplay`

**Component**: `views/displays.py:display_income_statements_results()`

#### Test Cases
```python
class TestIncomeStatementDisplay:
    """Test passive results presentation (no business logic)"""
    
    def test_summary_table_rendering():
        """Display high-level metrics"""
        # Given: Income statement dict
        # When: display_income_statements_results()
        # Then: Renders table with Total Revenue, Expenses, Net Income
        
    def test_detailed_category_breakdown_display():
        """Show category-wise details"""
        # Given: Revenue = {'工资': 8000, '服务': 2000}
        # When: Render details
        # Then: Table shows each category with amounts
        
    def test_currency_formatting():
        """Format amounts with currency symbols"""
        # Given: Amount=8000.0
        # When: Display
        # Then: Shows "¥8,000.00" (display formatting only)
        
    def test_export_button_rendering():
        """Display download/export UI widgets"""
        # Given: Statement data
        # When: Render export options
        # Then: Buttons for CSV, Excel, PDF export
        # Note: Actual export logic in Model/Repository, View just triggers it
        
    def test_multi_user_statement_navigation():
        """UI for switching between user statements"""
        # Given: Statements for User1, User2, Household
        # When: Render navigation
        # Then: Tabs/dropdown to switch views
        
    def test_empty_statement_display():
        """Handle display when no transactions"""
        # Given: Empty income statement
        # When: Render
        # Then: Shows "No transactions for this period" message
```

**Input**: Income statement dictionaries  
**Output**: Rendered UI (tables, charts, export widgets)

---

### **STEP 8: Optional System Storage (Repository Layer)**
📁 `tests/unit/models/repositories/test_data_storage.py`

**Component**: `models/repositories/data_storage.py:MonthlyDataStorage, MonthlyReportStorage`

#### Test Cases
```python
class TestMonthlyDataStorage:
    """Test source CSV data persistence"""
    
    def test_save_monthly_csv_data():
        """Store uploaded CSV for month"""
        # Given: CSV DataFrame for July 2025
        # When: MonthlyDataStorage.save()
        # Then: File saved to data/accounting/monthly_data/2025-07/
        
    def test_retrieve_monthly_csv_data():
        """Load previously saved CSV"""
        # Given: Saved CSV for July 2025
        # When: MonthlyDataStorage.load('2025-07')
        # Then: Returns original DataFrame
        
    def test_month_directory_organization():
        """Organize files by year-month"""
        # When: Save data for multiple months
        # Then: Directories: 2025-05/, 2025-06/, 2025-07/
        
class TestMonthlyReportStorage:
    """Test financial statement persistence"""
    
    def test_save_income_statement_json():
        """Store generated income statements"""
        # Given: Income statement dict
        # When: MonthlyReportStorage.save()
        # Then: JSON saved to data/accounting/monthly_reports/2025-07/
        
    def test_retrieve_income_statement_for_comparison():
        """Load statement for trend analysis"""
        # Given: Statements for May, June, July
        # When: Load all three
        # Then: Enable month-over-month comparison
        
    def test_storage_path_sanitization():
        """Prevent directory traversal attacks"""
        # Given: Malicious month string "../../etc"
        # When: Attempt to save
        # Then: Path sanitized or rejected
```

**Input**: DataFrames or statement dictionaries  
**Output**: Persisted files + retrieval methods

---

## 📊 Test Coverage Matrix

| Workflow Step | MVP Layer | Component | Test File | Priority | Status |
|--------------|-----------|-----------|-----------|----------|--------|
| **Step 1: CSV Upload** | View | `handle_csv_upload()` | `views/test_components.py:TestCSVUpload` | P1 | 📋 TODO |
| **Step 2: Data Cleaning** ⭐ | Model | `DataCleaner.clean()` | `business/test_data_cleaner.py:TestDataCleaning` | **P0** | 📋 TODO |
| **Step 2: Data Validation** ⭐ | Model | `DataCleaner.validate()` | `business/test_data_cleaner.py:TestDataValidation` | **P0** | 📋 TODO |
| **Step 3: Data Preview** | View | `show_data_preview_editor()` | `views/test_components.py:TestDataPreviewEditor` | P1 | 📋 TODO |
| **Step 4: Transaction Processing** | Model | `TransactionProcessor` | `business/test_transaction_processor.py` | P0 | 📋 TODO |
| **Step 5: Income Generation** | Model | `IncomeStatementGenerator` | `business/test_income_statement_generator.py` | P0 | 📋 TODO |
| **Step 6: Orchestration** | Presenter | `IncomeStatementPresenter` | `presenters/test_income_statement_presenter.py` | P0 | ✅ Partial |
| **Step 7: Display** | View | `display_income_statements_results()` | `views/test_displays.py:TestIncomeStatementDisplay` | P1 | 📋 TODO |
| **Step 8: Storage** | Repository | `MonthlyDataStorage` | `repositories/test_data_storage.py` | P2 | 📋 TODO |

**Priority Levels**:
- **P0**: Critical path (must implement first) - Steps 2, 4, 5, 6
- **P1**: Important (implement second) - Steps 1, 3, 7
- **P2**: Optional (implement if time permits) - Step 8


---

## 🔗 Integration & E2E Testing

### Integration Tests: Step-by-Step Data Flow
📁 `tests/integration/test_workflow_step_integration.py`

```python
class TestWorkflowStepIntegration:
    """Test data flow between adjacent workflow steps"""
    
    def test_step1_to_step2_csv_to_cleaner():
        """CSV upload output → DataCleaner input"""
        # Given: CSV file uploaded via View
        # When: Pass file path to DataCleaner
        # Then: DataCleaner successfully reads and processes
        
    def test_step2_to_step3_cleaner_to_preview():
        """DataCleaner output → Data preview input"""
        # Given: Cleaned DataFrame + ValidationReport from DataCleaner
        # When: Pass to preview UI
        # Then: Preview displays correctly with error highlights
        
    def test_step3_to_step4_preview_to_processor():
        """User-corrected preview → TransactionProcessor"""
        # Given: Edited DataFrame from preview
        # When: Pass to TransactionProcessor
        # Then: Transactions loaded without errors
        
    def test_step4_to_step5_processor_to_generator():
        """Transaction objects → IncomeStatementGenerator"""
        # Given: List of Transaction objects
        # When: Pass to IncomeStatementGenerator
        # Then: Income statements generated correctly
        
    def test_step5_to_step7_generator_to_display():
        """Income statements → Display UI"""
        # Given: Income statement dicts
        # When: Pass to display function
        # Then: UI renders all sections correctly
```

### End-to-End Tests: Complete Workflow
📁 `tests/e2e/test_income_statement_workflow.py`

```python
class TestIncomeStatementE2E:
    """Test complete 8-step workflow from start to finish"""
    
    def test_complete_workflow_happy_path():
        """Perfect CSV → Clean → Process → Generate → Display → Store"""
        # Given: Valid CSV file (tests/test_cases/Transactions1.csv)
        # When: Execute full workflow
        # Then: 
        #   - CSV uploaded successfully
        #   - Data cleaned with no errors
        #   - Preview shows clean data
        #   - Transactions processed correctly
        #   - Income statements generated
        #   - Results displayed
        #   - (Optional) Data stored
        
    def test_workflow_with_validation_errors():
        """CSV with errors → Validation → User fixes → Complete"""
        # Given: CSV with missing Debit accounts
        # When: Execute workflow
        # Then:
        #   - Step 2 detects validation errors
        #   - Step 3 displays errors to user
        #   - User corrects in preview
        #   - Workflow continues to completion
        
    def test_multi_user_complete_workflow():
        """Multi-user CSV → Individual + Household statements"""
        # Given: CSV with User1, User2 transactions
        # When: Execute workflow
        # Then:
        #   - 3 income statements generated (2 individual + 1 household)
        #   - All statements displayed with navigation
        
    def test_workflow_with_special_transactions():
        """Prepaid assets + tax expenses workflow"""
        # Given: CSV with prepaid expenses and tax transactions
        # When: Execute workflow
        # Then:
        #   - Prepaid assets excluded from current income
        #   - Tax expenses shown separately
        #   - Statement structure correct
```

### Error Recovery Tests
📁 `tests/e2e/test_error_recovery_workflow.py`

```python
class TestErrorRecoveryWorkflow:
    """Test error handling and recovery scenarios"""
    
    def test_malformed_csv_recovery():
        """Handle malformed CSV gracefully"""
        # Given: CSV with inconsistent columns
        # When: Upload and clean
        # Then: Error message displayed, user can fix or upload new file
        
    def test_validation_error_correction_flow():
        """User corrects validation errors"""
        # Given: CSV with 5 validation errors
        # When: User fixes all errors in preview
        # Then: Workflow continues successfully
        
    def test_partial_validation_error_correction():
        """Handle incomplete error correction"""
        # Given: CSV with 5 errors, user fixes only 3
        # When: User attempts to proceed
        # Then: Remaining 2 errors highlighted, workflow blocked
        
    def test_processing_error_handling():
        """Handle unexpected processing errors"""
        # Given: Edge case data that causes processing error
        # When: Execute workflow
        # Then: Friendly error message, data preserved for debugging
```

### Real-World Scenarios
📁 `tests/e2e/test_real_world_scenarios.py`

```python
class TestRealWorldScenarios:
    """Test production-like use cases"""
    
    def test_monthly_household_accounting():
        """Realistic monthly household transactions"""
        # Given: CSV with 50+ transactions (salary, rent, utilities, groceries, etc.)
        # When: Execute workflow
        # Then: Comprehensive income statement with all categories
        
    def test_year_end_tax_preparation():
        """Annual tax calculation workflow"""
        # Given: 12 months of CSVs with tax transactions
        # When: Process each month + consolidate
        # Then: Annual tax summary for tax filing
        
    def test_business_expense_tracking():
        """Small business income/expense tracking"""
        # Given: CSV with business revenue and expenses
        # When: Execute workflow
        # Then: Business income statement (revenue - COGS - opex)
        
    def test_multi_currency_household():
        """Mixed currency transactions"""
        # Given: CSV with ¥ (CNY) and $ (USD) amounts
        # When: Clean and process
        # Then: Currencies normalized correctly (or tracked separately)
```

---

## 🔄 Legacy Test Migration Plan

### Current Legacy Tests (Keep for Compatibility)
```
tests/modules/accounting/legacy/
├── ✅ test_accounting.py                    → Core functionality (keep)
├── ✅ test_consolidated_reports.py          → Multi-user features (keep)
├── ✅ test_comparative_analysis.py          → Analytics (keep)
├── ⚠️  test_csv_upload_validation.py        → MIGRATE to test_data_cleaner.py
├── ⚠️  test_data_preview_validation.py      → MIGRATE to test_data_cleaner.py + test_components.py
├── ✅ test_transaction_processing_enhanced.py → Keep (prepaid assets, complex scenarios)
└── ✅ test_income_statement_enhanced.py     → Keep (tax separation, advanced features)
```

### Migration Strategy

#### Phase 1: Extract DataCleaner Tests (High Priority)
- **Source**: `test_csv_upload_validation.py` + `test_data_preview_validation.py`
- **Destination**: `unit/models/business/test_data_cleaner.py`
- **Extract**:
  - Currency normalization tests → `TestDataCleaning.test_normalize_currency_symbols()`
  - Empty row removal → `TestDataCleaning.test_remove_completely_empty_rows()`
  - Whitespace handling → `TestDataCleaning.test_strip_whitespace_from_text()`
  - Required field validation → `TestDataValidation.test_required_fields_validation()`
  - Data type validation → `TestDataValidation.test_data_type_validation()`

#### Phase 2: Extract View Tests (Medium Priority)
- **Source**: `test_data_preview_validation.py`
- **Destination**: `unit/views/test_components.py`
- **Extract**:
  - Preview display logic → `TestDataPreviewEditor.test_display_cleaned_data()`
  - Error highlighting → `TestDataPreviewEditor.test_highlight_validation_errors()`
  - Inline editing → `TestDataPreviewEditor.test_inline_editing_capability()`

#### Phase 3: Keep Legacy Tests for Compatibility (Low Priority)
- **Preserve**: All other legacy tests for backward compatibility
- **Rationale**: 
  - Existing tests cover complex scenarios not yet in MVP tests
  - Provide safety net during migration
  - Can deprecate after MVP test coverage ≥90%

---

## 🎯 Test Execution Strategy

### Development Workflow
1. **Unit Tests First**: Test each component in isolation
2. **Integration Tests**: Test step-by-step data flow
3. **E2E Tests**: Validate complete workflow
4. **Legacy Tests**: Ensure backward compatibility

### Test Commands
```bash
# Run all tests
pytest tests/modules/accounting/

# Run unit tests only
pytest tests/modules/accounting/unit/

# Run integration tests only  
pytest tests/modules/accounting/integration/

# Run E2E tests only
pytest tests/modules/accounting/e2e/

# Run legacy tests for compatibility
pytest tests/modules/accounting/legacy/

# Run specific workflow step tests
pytest tests/modules/accounting/unit/models/business/test_data_cleaner.py

# Run with coverage
pytest tests/modules/accounting/ --cov=src/modules/accounting --cov-report=html
```

### Coverage Goals
- **Unit Tests**: 95%+ code coverage per component
- **Integration Tests**: 100% step transitions covered
- **E2E Tests**: 100% critical user workflows covered
- **Overall**: 90%+ total code coverage

---

## 📝 Next Steps

### Immediate Actions (Priority Order)
1. ✅ **Create test structure directories**
   ```bash
   mkdir -p tests/modules/accounting/{unit/{models/{domain,business,repositories},presenters,views},integration,e2e,legacy}
   ```

2. 📋 **Implement P0 tests (Critical Path)**:
   - `test_data_cleaner.py` (Step 2 - **NEW critical component**)
   - `test_transaction_processor.py` (Step 4)
   - `test_income_statement_generator.py` (Step 5)
   - `test_income_statement_presenter.py` (Step 6 - enhance existing)

3. 📋 **Implement P1 tests (Important)**:
   - `test_components.py` (Steps 1 & 3)
   - `test_displays.py` (Step 7)

4. 📋 **Implement Integration & E2E tests**:
   - `test_workflow_step_integration.py`
   - `test_income_statement_workflow.py`
   - `test_error_recovery_workflow.py`

5. 📋 **Migrate legacy tests**:
   - Extract DataCleaner tests from legacy files
   - Consolidate validation logic tests
   - Preserve complex scenario tests

### Success Criteria
- ✅ All 8 workflow steps have comprehensive unit tests
- ✅ Integration tests validate step-by-step data flow
- ✅ E2E tests cover happy path + error scenarios
- ✅ 90%+ code coverage achieved
- ✅ All legacy tests still passing (backward compatibility)
- ✅ CI/CD pipeline runs all test suites successfully

---

## 📚 Appendix: Test Data Files

### Test CSV Files
```
tests/test_cases/
├── Transactions1.csv          # Basic valid transactions
├── Transactions2.csv          # Multi-user with edge cases
├── transactions_with_errors.csv       # Validation error scenarios
├── transactions_malformed.csv         # Malformed CSV structure
├── transactions_prepaid.csv           # Prepaid asset scenarios
├── transactions_tax.csv               # Tax expense scenarios
└── transactions_unicode.csv           # Chinese + special characters
```

### Expected Test Outputs
```
tests/expected_outputs/
├── income_statement_basic.json        # Expected output for Transactions1.csv
├── income_statement_multi_user.json   # Expected output for Transactions2.csv
├── validation_errors.json             # Expected validation errors
└── cleaned_dataframes/                # Expected cleaned DataFrames
```

---

**Document Version**: 2.0 (Aligned with 8-step MVP workflow)  
**Last Updated**: Based on `income-statement-generation-workflow.md`  
**Next Review**: After DataCleaner implementation complete
