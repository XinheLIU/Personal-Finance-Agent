# Accounting Module

A comprehensive, professional accounting system with CSV-based transaction management, financial statement generation, and multi-user support. Features Chinese language support and CNY currency handling.

## 🏗️ Architecture Overview (MVP Pattern)

Following **Model-View-Presenter (MVP)** architecture for clean separation of concerns:

```
src/modules/accounting/
├── models/                 # ALL business logic (Model layer)
│   ├── domain/            # Core entities and business rules
│   │   ├── transaction.py        # Transaction entity
│   │   ├── category.py           # CategoryMapper & category constants
│   │   └── statements.py         # Financial statement data structures
│   ├── business/          # Business logic implementations
│   │   ├── transaction_processor.py      # CSV processing & transaction logic
│   │   ├── income_statement_generator.py # Income statement generation
│   │   ├── cash_flow_generator.py        # Cash flow statement generation
│   │   └── validation_engine.py          # Data validation logic
│   └── repositories/      # Data access layer
│       └── data_storage.py       # I/O utilities and persistence
├── presenters/            # Coordination layer (Presenter layer)
│   ├── income_statement_presenter.py     # Income statement workflow
│   ├── cash_flow_presenter.py            # Cash flow workflow
│   └── transaction_presenter.py          # Combined transaction workflows
├── views/                 # Passive UI layer (View layer)
│   ├── components.py      # Pure UI widgets (no business logic)
│   ├── pages.py          # Page layouts and navigation
│   └── displays.py       # Result presentation and formatting
└── core/                 # Legacy business logic (being phased out)
    ├── models.py         # Moved to models/domain/
    ├── io.py             # Moved to models/business/
    ├── income_statement.py # Moved to models/business/
    └── ...               # Other legacy files
```


## 📊 Income Statement Generation Workflow (MVP Pattern)

### Overview
The income statement generation workflow transforms CSV transaction data into professional financial statements using the **MVP architecture** that cleanly separates business logic, coordination, and presentation.

### MVP Workflow Process

#### 1. **CSV Upload & Validation (View Layer)**
```
User → CSV File → views/components.py:handle_csv_upload()
```
- **File**: `views/components.py:handle_csv_upload()`
- **Purpose**: Passive UI component for secure file upload
- **Expected Format**:
```csv
Description,Amount,Debit,Credit,User
Monthly Salary,8000.0,工资收入,Bank Account,User1
Rent Payment,-2000.0,房租,Bank Account,User1
```
- **Output**: Temporary file path (no business logic)

#### 2. **Data Preview & Editing (View Layer)**
```
Temporary File → views/components.py:show_data_preview_editor() → Enhanced CSV
```
- **File**: `views/components.py:show_data_preview_editor()`
- **Purpose**: Passive UI for data validation and correction
- **Features**: 
  - Live editing capabilities (UI only)
  - Display validation (UI only)
  - Currency formatting display
- **Output**: User-edited DataFrame (no business logic)

#### 3. **Transaction Processing (Model Layer)**
```
Enhanced CSV → models/business/transaction_processor.py:TransactionProcessor → Transaction Objects
```
- **File**: `models/business/transaction_processor.py:TransactionProcessor`
- **Key Methods**:
  - `load_transactions()`: Parse CSV into Transaction objects
  - `_clean_amount()`: Handle currency symbols (¥, $) and formatting
  - `_determine_transaction_type_and_sign()`: Classify transactions
  - `get_all_users()`: Extract unique users for multi-user support

**Transaction Classification Logic**:
```python
# Revenue: Positive amounts in revenue categories
if debit_category in REVENUE_CATEGORIES and amount > 0:
    transaction_type = "revenue"
# Expense: Negative amounts or expense categories  
elif amount < 0:
    transaction_type = "expense"
# Prepaid Asset: Special handling for prepaid expenses
elif transaction_type == "prepaid_asset":
    # Skip from current period income calculation
```

#### 4. **Income Statement Generation (Model Layer)**
```
Transaction Objects → models/business/income_statement_generator.py:IncomeStatementGenerator → Income Statement
```
- **File**: `models/business/income_statement_generator.py:IncomeStatementGenerator`
- **Core Logic**:
  - **Revenue Categorization**: Groups positive amounts by category
  - **Expense Categorization**: Uses CategoryMapper for proper classification
  - **Multi-User Support**: Generates individual + combined statements
  - **Calculations**: Total Revenue, Total Expenses, Net Income

**Generated Structure**:
```python
{
    'Entity': 'User1',
    'Revenue': {'工资收入': 8000.0, '服务收入': 2000.0},
    'Total Revenue': 10000.0,
    'Expenses': {'房租': 2000.0, '餐饮': 800.0},
    'Total Expenses': 2800.0,
    'Net Income': 7200.0
}
```

#### 5. **Business Logic Orchestration (Presenter Layer)**
```
Core Components → presenters/income_statement_presenter.py:process_transaction_statements() → Coordinated Results
```
- **File**: `presenters/income_statement_presenter.py:IncomeStatementPresenter`
- **Orchestrates**:
  - Calls TransactionProcessor (Model)
  - Calls IncomeStatementGenerator (Model)
  - Coordinates multi-user processing
  - Handles errors and validation
- **Output**: Complete financial statement set (no business logic, just coordination)

#### 6. **Results Display & Export (View Layer)**
```
Statement Data → views/displays.py:display_income_statements_results() → User Interface
```
- **File**: `views/displays.py:display_income_statements_results()`
- **Features**:
  - **Summary Tables**: High-level metrics display (passive)
  - **Detailed Breakdowns**: Category-wise revenue and expense presentation
  - **Export Options**: Download UI widgets (no business logic)
  - **Currency Formatting**: Display formatting only

#### 7. **Optional System Storage (Model/Repository Layer)**
```
Generated Statements → models/repositories/data_storage.py → Persistent Storage
```
- **File**: `models/repositories/data_storage.py` + Legacy compatibility
- **Storage Components**:
  - `MonthlyDataStorage`: Source CSV data persistence
  - `MonthlyReportStorage`: Financial statement persistence
- **Benefits**: Enables monthly comparison and trend analysis

## 🧪 Testing Strategy (MVP Architecture)

### MVP Test Structure

```
tests/modules/accounting/
├── models/                    # Model layer tests
│   ├── domain/
│   │   └── test_domain_models.py         ✅ Domain entities tests
│   └── business/
│       ├── test_transaction_processor.py  📋 Business logic tests
│       ├── test_income_statement_generator.py
│       └── test_cash_flow_generator.py
├── presenters/               # Presenter layer tests
│   ├── test_income_statement_presenter.py ✅ Presenter coordination tests
│   ├── test_cash_flow_presenter.py        📋 Coming soon
│   └── test_transaction_presenter.py      📋 Coming soon
├── views/                    # View layer tests (UI components)
│   ├── test_components.py                 📋 Passive UI tests
│   ├── test_pages.py                     📋 Page layout tests
│   └── test_displays.py                  📋 Display formatting tests
└── legacy/                   # Legacy test compatibility
    ├── test_accounting.py                ✅ Legacy core tests
    ├── test_consolidated_reports.py      ✅ Legacy advanced tests
    ├── test_comparative_analysis.py      ✅ Legacy analytics tests
    ├── test_csv_upload_validation.py     ✅ Legacy CSV tests
    ├── test_data_preview_validation.py   ✅ Legacy validation tests
    ├── test_transaction_processing_enhanced.py ✅ Legacy enhanced tests
    └── test_income_statement_enhanced.py ✅ Legacy income tests
```

### Test Coverage Matrix (MVP)

| MVP Layer | Component | Test File | Coverage Status |
|-----------|-----------|-----------|----------------|
| **Model - Domain** | Transaction Entity | `models/test_domain_models.py:TestTransaction` | ✅ Complete (6/6) |
| **Model - Domain** | CategoryMapper | `models/test_domain_models.py:TestCategoryMapper` | ✅ Complete (6/6) |
| **Model - Domain** | Category Constants | `models/test_domain_models.py:TestCategoryConstants` | ✅ Complete (6/6) |
| **Model - Business** | TransactionProcessor | `models/business/test_transaction_processor.py` | 📋 **MVP TODO** |
| **Model - Business** | IncomeStatementGenerator | `models/business/test_income_statement_generator.py` | 📋 **MVP TODO** |
| **Model - Business** | CashFlowGenerator | `models/business/test_cash_flow_generator.py` | 📋 **MVP TODO** |
| **Presenter** | IncomeStatementPresenter | `presenters/test_income_statement_presenter.py` | ✅ Complete (4/4) |
| **Presenter** | CashFlowPresenter | `presenters/test_cash_flow_presenter.py` | 📋 **MVP TODO** |
| **Presenter** | TransactionPresenter | `presenters/test_transaction_presenter.py` | 📋 **MVP TODO** |
| **View** | Pure UI Components | `views/test_components.py` | 📋 **MVP TODO** |
| **View** | Page Layouts | `views/test_pages.py` | 📋 **MVP TODO** |
| **View** | Display Formatting | `views/test_displays.py` | 📋 **MVP TODO** |
| **Legacy** | Core Functionality | `legacy/test_accounting.py` | ✅ Complete |
| **Legacy** | Advanced Features | `legacy/test_consolidated_reports.py` | ✅ Complete |
| **Legacy** | Analytics | `legacy/test_comparative_analysis.py` | ✅ Complete |
| **Legacy** | CSV Processing | `legacy/test_csv_upload_validation.py` | ✅ Complete |
| **Legacy** | Data Validation | `legacy/test_data_preview_validation.py` | ✅ Complete |
| **Legacy** | Enhanced Processing | `legacy/test_transaction_processing_enhanced.py` | ✅ Complete |
| **Legacy** | Enhanced Income | `legacy/test_income_statement_enhanced.py` | ✅ Complete |

### Current Test Files

#### 1. `test_accounting.py` - Core Functionality ✅
```python
# Transaction processing
TestTransactionProcessor.test_transaction_loading()
TestTransactionProcessor.test_amount_cleaning() 
TestTransactionProcessor.test_get_users()

# Income statement generation  
TestIncomeStatementGeneration.test_income_statement_generation()
TestIncomeStatementGeneration.test_revenue_categorization()
TestIncomeStatementGeneration.test_expense_categorization()

# Multi-user coordination
TestFinancialReportGenerator.test_report_generation()
```

#### 2. `test_consolidated_reports.py` - Advanced Features ✅
```python
# Multi-user consolidation
TestMultiUserTransactionConsolidation.test_*()

# Consolidated income statements
TestConsolidatedIncomeStatement.test_*()

# Individual vs household reporting
TestIndividualVsHouseholdReporting.test_*()
```

#### 3. `test_comparative_analysis.py` - Analytics ✅
```python
# YTD analysis
TestYTDTableDisplay.test_*()

# Budget variance tracking
TestBudgetVarianceCalculation.test_*()

# Trend analysis
TestCategoryTrendAnalysis.test_*()
```

#### 4. `test_csv_upload_validation.py` - CSV Processing ✅ **NEW**
```python
# File upload and validation
TestCSVUploadValidation.test_valid_csv_upload()
TestCSVUploadValidation.test_malformed_csv_handling()

# Data cleaning
TestDataCleaning.test_remove_empty_rows_from_dataframe()
TestDataCleaning.test_currency_sign_handling()
TestDataCleaning.test_whole_empty_row_removal()

# Currency handling
TestCurrencyHandling.test_chinese_currency_symbols()
TestCurrencyHandling.test_comma_separated_thousands()
TestCurrencyHandling.test_edge_cases()

# Integration
TestCSVValidationIntegration.test_comprehensive_data_cleaning_workflow()
```

#### 5. `test_data_preview_validation.py` - Data Validation ✅ **NEW**
```python
# Data preview validation
TestDataPreviewValidation.test_missing_cells_detection()
TestDataPreviewValidation.test_data_type_validation()
TestDataPreviewValidation.test_required_field_completion_check()

# Data editing validation
TestDataEditingValidation.test_data_editing_validation()
TestDataEditingValidation.test_currency_format_preservation()

# Corner case handling
TestCornerCaseHandling.test_unicode_character_handling()
TestCornerCaseHandling.test_mixed_data_types_handling()
TestCornerCaseHandling.test_empty_dataframe_handling()
```

#### 6. `test_transaction_processing_enhanced.py` - Transaction Processing ✅ **NEW**
```python
# Enhanced transaction processing
TestTransactionProcessingEnhanced.test_basic_transaction_classification()
TestTransactionProcessingEnhanced.test_cash_flow_impact_detection()

# Prepaid asset handling
TestPrepaidAssetHandling.test_prepaid_asset_creation()
TestPrepaidAssetHandling.test_prepaid_asset_conversion_to_expense()
TestPrepaidAssetHandling.test_prepaid_asset_complete_workflow()

# Complex scenarios
TestComplexTransactionScenarios.test_mixed_transaction_types_processing()
TestComplexTransactionScenarios.test_multi_user_prepaid_scenarios()

# Integration
TestTransactionProcessorIntegration.test_full_processor_workflow_with_prepaid()
```

#### 7. `test_income_statement_enhanced.py` - Income Statement Enhancement ✅ **NEW**
```python
# Tax expense separation
TestTaxExpenseSeparation.test_tax_expense_categorization()
TestTaxExpenseSeparation.test_tax_expense_separation_display()
TestTaxExpenseSeparation.test_complex_tax_scenario()

# Prepaid asset handling
TestPrepaidAssetHandling.test_prepaid_asset_exclusion()
TestPrepaidAssetHandling.test_prepaid_asset_conversion_included()
TestPrepaidAssetHandling.test_complex_prepaid_scenario()

# Integration and formatting
TestIncomeStatementIntegration.test_complete_workflow_with_csv()
TestIncomeStatementDisplayAndFormatting.test_currency_formatting()
```

## 🎯 Test Results and Known Issues

### Test Execution Summary

**Total Tests Created**: 41 new tests across 4 new test files  
**Tests Passing**: 35 tests (85.4% pass rate)  
**Tests Failing**: 6 tests (14.6% failure rate)  

### Identified Issues Through Testing ⚠️

The tests have successfully identified several critical issues that need attention:

#### 1. CSV Processing Issues
- **Malformed CSV Handling**: Pandas parser fails on inconsistent column counts
- **Currency Symbol Processing**: Some Chinese currency formats cause parsing errors
- **Empty Row Filtering**: Logic doesn't properly handle mixed empty/partial rows

#### 2. Transaction Classification Issues  
- **Cash Flow Detection**: "Bank Account" not recognized as cash-equivalent
- **Revenue Classification**: Debit/Credit logic needs refinement for revenue transactions
- **Prepaid Asset Logic**: Cash flow impact detection incorrect for prepaid transactions

#### 3. Income Statement Issues
- **Tax Category Mapping**: Tax expenses not properly mapped to "Tax" categories
- **Prepaid Exclusion**: Some prepaid conversions not properly included as expenses

### Remaining Test Coverage Gaps

#### UI Layer Components (Not Yet Tested)
```python
# Future enhancement: test_ui_components.py
class TestStreamlitComponents:
    def test_file_uploader_integration()
    def test_data_editor_functionality()
    def test_error_message_display()
```

#### True Integration Testing (Partially Covered)
```python
# Future enhancement: test_full_integration.py  
class TestEndToEndUserWorkflow:
    def test_streamlit_ui_to_statement_generation()
    def test_error_propagation_through_ui()
    def test_multi_user_session_handling()
```

## 🚀 Next Steps and Improvements

Based on test failures, address these critical issues:

1. **Enhance CSV Error Handling**: Improve pandas error handling for malformed CSV files
2. **Fix Transaction Classification**: Correct revenue/expense classification logic  
4. **Fix Tax Category Mapping**: Ensure tax expenses are properly categorized
5. **Correct Prepaid Logic**: Fix cash flow impact detection for prepaid assets

