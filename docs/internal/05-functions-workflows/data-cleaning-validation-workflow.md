# Data Cleaning and Validation Workflow

## Overview
The Data Cleaning and Validation Workflow is the crucial initial step in processing raw transaction data. Its primary goal is to transform potentially messy, inconsistent, or incomplete CSV input into a clean, standardized, and validated DataFrame, ready for further financial processing. This step ensures data quality and prevents errors in subsequent financial statement generation.

## 🏗️ Architecture Overview (MVP Pattern)

This workflow is primarily handled within the Model layer of the accounting module, specifically by the `DataCleaner` component, and coordinated by the Presenter layer.

```
src/modules/accounting/
├── models/                 # ALL business logic (Model layer)
│   ├── domain/            # Core entities and business rules
│   │   ├── transaction.py        # Transaction entity
│   │   ├── category.py           # CategoryMapper & category constants
│   │   └── statements.py         # Financial statement data structures
│   ├── business/          # Business logic implementations
│   │   ├── data_cleaner.py              # Data cleaning & validation ⭐
│   │   ├── transaction_processor.py      # CSV processing & transaction logic
│   │   ├── income_statement_generator.py # Income statement generation
│   │   ├── cash_flow_generator.py        # Cash flow statement generation
│   │   ├── balance_sheet_generator.py    # Balance sheet generation
│   │   └── validation_engine.py          # Data validation logic
│   └── repositories/      # Data access layer
│       └── data_storage.py       # I/O utilities and persistence
├── presenters/            # Coordination layer (Presenter layer)
│   ├── income_statement_presenter.py     # Income statement workflow
│   ├── cash_flow_presenter.py            # Cash flow workflow
│   ├── balance_sheet_presenter.py        # Balance sheet workflow
│   └── transaction_presenter.py          # Combined transaction workflows ⭐
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

## 📊 Data Cleaning and Validation Workflow Steps

This workflow begins immediately after a user uploads a CSV file and is critical before any data is presented for user review or further processing.

### 1. **CSV Upload (View Layer)**

```
User → CSV File → views/components.py:handle_csv_upload()
```
- **File**: `views/components.py:handle_csv_upload()`
- **Purpose**: Passive UI component for secure file upload. It provides the raw CSV file path to the Presenter.
- **Expected Format**: Any CSV file with transaction-like data.
- **Output**: Raw CSV file path.

### 2. **Data Cleaning & Validation (Model Layer)**

```
Raw CSV → models/business/data_cleaner.py:DataCleaner → Cleaned & Validated DataFrame + Validation Report
```
- **File**: `models/business/data_cleaner.py:DataCleaner`
- **Purpose**: Automated cleaning and rigorous validation of the raw CSV data.
- **Cleaning Operations**:
    - **Empty Row/Column Removal**: Automatically removes rows and columns that are entirely empty.
    - **Currency Normalization**: Converts various currency formats (e.g., `¥8,000.00`, `$1,500`) into pure numeric values (e.g., `8000.00`, `1500.0`).
    - **Whitespace Stripping**: Removes leading/trailing whitespace from all text fields.
    - **Date Standardization**: Converts various date formats into a consistent `YYYY-MM-DD` format.
- **Validation Rules**:
    - **Required Fields**: Ensures that if an `Amount` is present, both `Debit` and `Credit` accounts are also provided.
    - **Data Types**: Verifies that `Amount` fields are numeric and `Description` fields are text.
    - **Business Rules**: Checks for logical consistency, e.g., revenue categories must have positive amounts.
    - **UTF-8 Encoding**: Ensures proper handling of multi-byte characters, especially for Chinese text.
- **Error Reporting**: Collects all validation errors and warnings, including row numbers and specific field references, into a `ValidationReport`.
- **Output**: 
    - Cleaned DataFrame (ready for preview).
    - `ValidationReport` (containing errors and warnings).

### 3. **Data Preview & Editing (View Layer)**

```
Cleaned DataFrame + Validation Report → views/components.py:show_data_preview_editor() → User-Corrected CSV
```
- **File**: `views/components.py:show_data_preview_editor()`
- **Purpose**: Provides a passive UI for the user to review the pre-cleaned data and manually correct any validation errors identified in the previous step.
- **Features**:
    - **Display Pre-cleaned Data**: Shows the data after automated cleaning, improving user experience by removing obvious formatting issues.
    - **Highlight Validation Errors**: Visually marks rows or cells that have validation errors, often with tooltips explaining the issue.
    - **Inline Editing**: Allows users to directly edit cell values within the UI to fix errors.
    - **Visual Indicators**: May use asterisks or color coding to indicate required fields.
- **Output**: User-corrected DataFrame, where business-level data inconsistencies have been resolved by the user.

### 4. **Orchestration (Presenter Layer)**

```
Raw CSV → presenters/transaction_presenter.py:process_transactions() → Cleaned & Validated Data
```
- **File**: `presenters/transaction_presenter.py` (or similar presenter coordinating initial data flow)
- **Purpose**: Coordinates the CSV upload, data cleaning, and validation steps.
- **Orchestrates**:
    - Receives the raw CSV file path from the View.
    - Instantiates and calls `DataCleaner` to perform cleaning and validation.
    - Passes the cleaned DataFrame and `ValidationReport` to the View for preview and editing.
    - If validation errors exist, it prevents further processing until the user resolves them.
- **Key Output**: A clean, validated DataFrame, ready for transaction processing.

## 📝 Related Documentation

- **Income Statement Generation Workflow**: `docs/04-development/income-statement-generation-workflow.md`
- **Cash Flow Statement Generation Workflow**: `docs/04-development/cash-flow-statement-generation-workflow.md`
- **Balance Sheet Generation Workflow**: `docs/04-development/balance-sheet-generation-workflow.md`
- **Transaction Processing Workflow**: `docs/04-development/transaction-processing-workflow.md`
- **Accounting Module README**: `data/accounting/README.md`

---

**Last Updated**: 2025-09-30
**Version**: 0.4.3 (Data Cleaning and Validation)
