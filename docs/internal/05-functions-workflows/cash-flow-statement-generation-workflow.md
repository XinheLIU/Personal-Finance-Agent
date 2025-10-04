# Cash Flow Statement Generation Workflow

## Overview
The cash flow statement generation workflow transforms CSV transaction data into a professional financial statement that details the cash inflows and outflows over a period, categorized into operating, investing, and financing activities. This workflow is integrated with the income statement generation, leveraging the same MVP architecture and transaction processing.

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
│   │   ├── cash_flow_generator.py        # Cash flow statement generation ⭐
│   │   └── validation_engine.py          # Data validation logic
│   └── repositories/      # Data access layer
│       └── data_storage.py       # I/O utilities and persistence
├── presenters/            # Coordination layer (Presenter layer)
│   ├── income_statement_presenter.py     # Income statement workflow
│   ├── cash_flow_presenter.py            # Cash flow workflow ⭐
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

## 📊 Cash Flow Statement Generation Workflow Steps

The cash flow statement generation is part of a unified workflow that starts with CSV upload and data cleaning, similar to the income statement. The key steps specific to cash flow generation are detailed below, assuming prior steps (CSV Upload, Data Cleaning & Validation, Data Preview & Editing, Transaction Processing) have been completed.

### 1. **Transaction Processing (Model Layer)**
(Refer to `data-cleaning-validation-workflow.md` and `income-statement-generation-workflow.md` for initial steps)

```
Corrected CSV → models/business/transaction_processor.py:TransactionProcessor → Transaction Objects
```
- **File**: `models/business/transaction_processor.py:TransactionProcessor`
- **Purpose**: Convert validated DataFrame into domain objects. This step is shared with income statement generation.
- **Key Output**: List of `Transaction` objects, each containing classified transaction details.

### 2. **Cash Flow Statement Generation (Model Layer)**

```
Transaction Objects → models/business/cash_flow_generator.py:CashFlowGenerator → Cash Flow Statement
```
- **File**: `models/business/cash_flow_generator.py:CashFlowGenerator`
- **Purpose**: Analyze transaction objects and categorize cash movements into operating, investing, and financing activities.
- **Core Logic**:
    - **Operating Activities**: Cash inflows and outflows directly related to the primary business operations (e.g., salary income, rent payments, grocery expenses).
    - **Investing Activities**: Cash flows from the purchase or sale of long-term assets or investments (e.g., investment purchases, property sales).
    - **Financing Activities**: Cash flows from debt, equity, and dividends (e.g., loans received, loan repayments, capital contributions).
    - **Net Change in Cash**: Calculates the overall increase or decrease in cash during the period.
    - **Opening/Closing Cash Balance**: Integrates with initial cash balances to determine the final cash position.

**Generated Structure Example**:
```json
{
  "year_month": "2025-09",
  "statement_type": "cash_flow",
  "generated_at": "2025-09-30T14:30:00",
  "statement": {
    "Entity": "User1",
    "Operating Activities": {
      "Details": {
        "Salary Income": 8000.0,
        "Rent": -2000.0,
        "Food & Dining": -800.0
      },
      "Net Cash from Operating": 5200.0
    },
    "Investing Activities": {
      "Details": {
        "Investment Purchase": -5000.0
      },
      "Net Cash from Investing": -5000.0
    },
    "Financing Activities": {
      "Details": {},
      "Net Cash from Financing": 0.0
    },
    "Net Change in Cash": 200.0
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
Core Components → presenters/cash_flow_presenter.py:process_transaction_statements() → Coordinated Results
```
- **File**: `presenters/cash_flow_presenter.py:CashFlowPresenter` (or integrated into `income_statement_presenter.py` for dual generation)
- **Purpose**: Orchestrates the generation of cash flow statements, often in conjunction with income statements.
- **Orchestrates**:
    - Calls `CashFlowGenerator` (Model - step 2).
    - Coordinates multi-user processing for cash flow statements.
    - Handles errors and validation specific to cash flow generation.
- **Key Output**: Complete cash flow statement set (individual users + combined), ready for display.

### 4. **Results Display (View Layer)**

```
Statement Data → views/pages.py:show_income_cashflow_tab() → User Interface
```
- **File**: `views/pages.py:show_income_cashflow_tab()`
- **Purpose**: Presents the generated cash flow statement to the user.
- **Features**:
    - **Dual Statement Display**: Often displayed side-by-side with the income statement for a holistic view.
    - **Summary Tables**: High-level metrics for cash flow.
    - **Detailed Breakdowns**: Operating, Investing, and Financing activities breakdown.
    - **User Selection**: Dropdown to view individual user or combined statements.
    - **Currency Formatting**: Professional formatting for all amounts.

### 5. **Save to Memory (View → Model Layer)**

```
User Action → views/pages.py → core/report_storage.py:MonthlyReportStorage.save_statement()
```
- **File**: `views/pages.py` (UI) + `core/report_storage.py` (Storage)
- **Purpose**: Persist the generated cash flow statements for future analysis and monthly comparison.
- **Storage Format**:
    - `data/accounting/monthly_reports/{YYYY-MM}/cash_flow_*.json`
- **Features**:
    - **Month Selection**: User specifies YYYY-MM format.
    - **Metadata Tracking**: Includes entity, generation timestamp, source.
    - **Multi-User Support**: Saves all entities (individual users + combined).
    - **Dual Statement Storage**: Both income and cash flow statements are saved in a single user action.

## 📝 Related Documentation

- **Income Statement Generation Workflow**: `docs/04-development/income-statement-generation-workflow.md`
- **Data Cleaning and Validation Workflow**: `docs/04-development/data-cleaning-validation-workflow.md`
- **Balance Sheet Generation Workflow**: `docs/04-development/balance-sheet-generation-workflow.md`
- **Accounting Module README**: `data/accounting/README.md`

---

**Last Updated**: 2025-09-30
**Version**: 0.4.3 (Dual Statement Generation)
