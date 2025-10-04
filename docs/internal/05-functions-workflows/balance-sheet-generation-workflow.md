# Balance Sheet Generation Workflow

## Overview
The balance sheet generation workflow creates a snapshot of an entity's financial position at a specific point in time, detailing assets, liabilities, and equity. This workflow integrates with the transaction processing system to derive account balances.

## 🏗️ Architecture Overview (MVP Pattern)

The accounting module follows a Model-View-Presenter (MVP) architecture for clear separation of concerns:

```
src/modules/accounting/
├── models/                 # ALL business logic (Model layer)
│   ├── domain/            # Core entities and business rules
│   │   ├── transaction.py        # Transaction entity
│   │   ├── category.py           # CategoryMapper & category constants
│   │   └── statements.py         # Financial statement data structures
│   ├── business/          # Business logic implementations
│   │   ├── data_cleaner.py              # Data cleaning & validation
│   │   ├── transaction_processor.py      # CSV processing & transaction logic
│   │   ├── income_statement_generator.py # Income statement generation
│   │   ├── cash_flow_generator.py        # Cash flow statement generation
│   │   ├── balance_sheet_generator.py    # Balance sheet generation ⭐
│   │   └── validation_engine.py          # Data validation logic
│   └── repositories/      # Data access layer
│       └── data_storage.py       # I/O utilities and persistence
├── presenters/            # Coordination layer (Presenter layer)
│   ├── income_statement_presenter.py     # Income statement workflow
│   ├── cash_flow_presenter.py            # Cash flow workflow
│   ├── balance_sheet_presenter.py        # Balance sheet workflow ⭐
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

## 📊 Balance Sheet Generation Workflow Steps

The balance sheet generation process relies on processed transaction data and potentially an initial set of account balances. It typically follows these steps:

### 1. **Transaction Processing (Model Layer)**
(Refer to `transaction-processing-workflow.md` for details)

```
Corrected CSV → models/business/transaction_processor.py:TransactionProcessor → Transaction Objects
```
- **File**: `models/business/transaction_processor.py:TransactionProcessor`
- **Purpose**: Convert validated DataFrame into domain objects. These transactions are the basis for updating account balances.
- **Key Output**: List of `Transaction` objects.

### 2. **Account Balance Aggregation (Model Layer)**

```
Transaction Objects + Initial Balances → models/business/balance_sheet_generator.py:BalanceSheetGenerator → Account Balances
```
- **File**: `models/business/balance_sheet_generator.py:BalanceSheetGenerator`
- **Purpose**: Aggregate all relevant transactions up to the balance sheet date to determine the ending balances for all asset, liability, and equity accounts.
- **Core Logic**:
    - **Initial Balances**: Starts with opening balances for all accounts (e.g., from `data/accounts/holdings.json`).
    - **Transaction Application**: Applies all debit and credit transactions to their respective accounts.
    - **Categorization**: Groups accounts into standard balance sheet classifications (Current Assets, Non-Current Assets, Current Liabilities, Non-Current Liabilities, Equity).
    - **Multi-User Support**: Generates balance sheets for individual users and a combined household view.

**Generated Structure Example**:
```json
{
  "year_month": "2025-09",
  "statement_type": "balance_sheet",
  "generated_at": "2025-09-30T14:30:00",
  "statement": {
    "Current Assets": {
      "Cash": {"CNY": 25000.0, "USD": 3571.43},
      "Investments": {"CNY": 150000.0, "USD": 21428.57}
    },
    "Total Assets": {
      "CNY": 525000.0,
      "USD": 75000.0
    },
    "Current Liabilities": {
      "Credit Card Debt": {"CNY": 5000.0}
    },
    "Total Liabilities": {
      "CNY": 5000.0
    },
    "Equity": {
      "Retained Earnings": {"CNY": 520000.0}
    },
    "Total Liabilities & Equity": {
      "CNY": 525000.0,
      "USD": 75000.0
    }
  },
  "metadata": {
    "entity": "User1",
    "generated_at": "2025-09-30T14:30:00",
    "source": "web_upload"
  }
}
```

### 3. **Business Logic Orchestration (Presenter Layer)**

```
Core Components → presenters/balance_sheet_presenter.py:generate_balance_sheet() → Coordinated Results
```
- **File**: `presenters/balance_sheet_presenter.py:BalanceSheetPresenter`
- **Purpose**: Orchestrates the balance sheet generation process.
- **Orchestrates**:
    - Calls `TransactionProcessor` to get transaction objects.
    - Calls `BalanceSheetGenerator` to compute account balances.
    - Coordinates multi-user processing.
    - Handles errors and ensures data consistency.
- **Key Output**: Complete balance sheet set (individual users + combined), ready for display.

### 4. **Results Display (View Layer)**

```
Statement Data → views/pages.py:show_balance_sheet_tab() → User Interface
```
- **File**: `views/pages.py` (specific balance sheet display function)
- **Purpose**: Presents the generated balance sheet to the user.
- **Features**:
    - **Categorized Display**: Shows assets, liabilities, and equity in a clear, hierarchical structure.
    - **Summary Totals**: Displays total assets, total liabilities, and total equity.
    - **Balance Check**: Visually confirms that Assets = Liabilities + Equity.
    - **User Selection**: Dropdown to view individual user or combined balance sheets.
    - **Currency Formatting**: Professional formatting for all amounts.

### 5. **Save to Memory (View → Model Layer)**

```
User Action → views/pages.py → core/report_storage.py:MonthlyReportStorage.save_statement()
```
- **File**: `views/pages.py` (UI) + `core/report_storage.py` (Storage)
- **Purpose**: Persist the generated balance sheets for historical record and future analysis.
- **Storage Format**:
    - `data/accounting/monthly_reports/{YYYY-MM}/balance_sheet_*.json`
- **Features**:
    - **Month Selection**: User specifies YYYY-MM format.
    - **Metadata Tracking**: Includes entity, generation timestamp, source.
    - **Multi-User Support**: Saves all entities (individual users + combined).

## 📝 Related Documentation

- **Income Statement Generation Workflow**: `docs/04-development/income-statement-generation-workflow.md`
- **Cash Flow Statement Generation Workflow**: `docs/04-development/cash-flow-statement-generation-workflow.md`
- **Data Cleaning and Validation Workflow**: `docs/04-development/data-cleaning-validation-workflow.md`
- **Transaction Processing Workflow**: `docs/04-development/transaction-processing-workflow.md`
- **Accounting Module README**: `data/accounting/README.md`

---

**Last Updated**: 2025-09-30
**Version**: 0.4.3 (Balance Sheet Generation)
