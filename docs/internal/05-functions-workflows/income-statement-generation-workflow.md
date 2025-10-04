# Accounting Module

A comprehensive, professional accounting system with CSV-based transaction management, financial statement generation, and multi-user support. Features Chinese language support and CNY currency handling.

# 🏗️ Architecture Overview (MVP Pattern)

Following **Model-View-Presenter (MVP)** architecture for clean separation of concerns:

```
src/modules/accounting/
├── models/                 # ALL business logic (Model layer)
│   ├── domain/            # Core entities and business rules
│   │   ├── transaction.py        # Transaction entity
│   │   ├── category.py           # CategoryMapper & category constants
│   │   └── statements.py         # Financial statement data structures
│   ├── business/          # Business logic implementations
│   │   ├── data_cleaner.py              # Data cleaning & validation ⭐ NEW
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


## 📊 Income Statement & Cash Flow Generation Workflow (MVP Pattern)

### Overview
The income statement and cash flow generation workflow transforms CSV transaction data into **two professional financial statements simultaneously** using the **MVP architecture** that cleanly separates business logic, coordination, and presentation. Both statements are generated from the same transaction data in a single unified workflow.

### MVP Workflow Process

#### 1. **CSV Upload (View Layer)**
```
User → CSV File → views/components.py:handle_csv_upload()
```
- **File**: `views/components.py:handle_csv_upload()`
- **Purpose**: Passive UI component for secure file upload
- **Expected Format**:
```csv
Description,Amount,Debit,Credit,User
Monthly Salary,¥8,000.00,工资收入,Bank Account,User1
Rent Payment,-2000.0,房租,Bank Account,User1
```
- **Output**: Raw CSV file path (no business logic, no validation)

#### 2. **Data Cleaning & Validation (Model Layer)** ⭐ **NEW**
```
Raw CSV → models/business/data_cleaner.py:DataCleaner → Cleaned & Validated DataFrame
```
- **File**: `models/business/data_cleaner.py:DataCleaner` (to be implemented)
- **Purpose**: Automated data cleaning and validation BEFORE user preview
- **Cleaning Operations**:
  - Remove completely empty rows and columns
  - Normalize currency symbols (¥8,000.00 → 8000.00, $1,500 → 1500)
  - Strip whitespace from text fields
  - Standardize date formats
- **Validation Rules**:
  - ✅ **Required Fields**: If row has Amount, must have both Debit AND Credit accounts
  - ✅ **Data Types**: Amount must be numeric, Description must be text
  - ✅ **Business Rules**: Revenue categories must have positive amounts
  - ❌ **Errors**: Collect all validation errors with row numbers for user review
- **Output**: 
  - Cleaned DataFrame (ready for preview)
  - Validation report (errors with specific row references)

#### 3. **Data Preview & Editing (View Layer)**
```
Cleaned DataFrame + Validation Errors → views/components.py:show_data_preview_editor() → User-Corrected CSV
```
- **File**: `views/components.py:show_data_preview_editor()`
- **Purpose**: Passive UI for reviewing CLEAN data and fixing validation errors
- **Features**: 
  - Display **pre-cleaned** data (no empty rows, normalized currency)
  - Highlight validation errors with clear messages
  - Live editing capabilities for fixing issues (UI only)
  - Visual indicators for required field completion
- **User Experience**: 
  - User sees clean, professional data immediately
  - Validation errors clearly marked (e.g., "Row 5: Missing Debit account")
  - User fixes only real issues, not formatting problems
- **Output**: User-corrected DataFrame (business issues fixed)

#### 4. **Transaction Processing (Model Layer)**

```
Corrected CSV → models/business/transaction_processor.py:TransactionProcessor → Transaction Objects
```

- **File**: `models/business/transaction_processor.py:TransactionProcessor`
- **Purpose**: Convert validated DataFrame into domain objects
- **Key Methods**:
  - `load_transactions()`: Parse DataFrame into Transaction objects
  - `_determine_transaction_type_and_sign()`: Classify transactions
  - `get_all_users()`: Extract unique users for multi-user support
- **Note**: No data cleaning needed here - data is already clean from step 2!

**Transaction Classification Logic**:

```python
# Revenue: Credit is a revenue account
if credit in REVENUE_CATEGORIES:
    transaction_type = "revenue"
    amount = abs(amount)

# Reimbursement: Debit = Cash, Credit = Expense category (cash inflow reduces expense)
# Example: 报销 ¥1,509.00 Cash 通勤 (got cash back for transportation)
elif debit.lower() in ["cash", "现金"] and credit not in REVENUE_CATEGORIES:
    transaction_type = "expense"
    amount = -abs(amount)  # Negative amount = expense reduction

# Prepaid expense being used: Debit = expense, Credit = prepaid
elif "prepaid" in credit.lower():
    transaction_type = "expense"
    amount = abs(amount)

# Prepaid asset creation: Debit = prepaid, Credit = cash
elif "prepaid" in debit.lower():
    transaction_type = "prepaid_asset"  # Skip from current period income

# Regular expense: Debit = expense, Credit = cash (or other account)
else:
    transaction_type = "expense"
    amount = abs(amount)
```

**Key Features**:
- ✅ **Reimbursements Handled**: Cash receipts for expenses correctly reduce total expenses
- ✅ **Sign Preservation**: Negative amounts preserved through processing pipeline
- ✅ **No Double-Counting**: Reimbursements subtract from expenses, not miscategorized

#### 5. **Financial Statement Generation (Model Layer)**

**Both statements are generated from the same transaction objects in parallel:**

##### 5a. Income Statement Generation
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

##### 5b. Cash Flow Statement Generation
```
Transaction Objects → models/business/cash_flow_generator.py:CashFlowGenerator → Cash Flow Statement
```

- **File**: `models/business/cash_flow_generator.py:CashFlowGenerator`
- **Core Logic**:
  - **Operating Activities**: Cash from revenue and expenses (salary in, rent out, etc.)
  - **Investing Activities**: Cash used for investments and asset purchases
  - **Financing Activities**: Cash from loans, equity, and debt repayment
  - **Cash Flow Calculations**: Opening balance + Net change = Closing balance

**Generated Structure**:
```python
{
    'Entity': 'User1',
    'Operating Activities': {
        'Cash from Revenue': 10000.0,
        'Cash for Expenses': -2800.0,
        'Net Operating Cash Flow': 7200.0
    },
    'Investing Activities': {
        'Investment Purchases': -5000.0,
        'Net Investing Cash Flow': -5000.0
    },
    'Financing Activities': {
        'Net Financing Cash Flow': 0.0
    },
    'Net Change in Cash': 2200.0,
    'Opening Cash Balance': 15000.0,
    'Closing Cash Balance': 17200.0
}
```

**Key Features**:
- ✅ **Unified Data Source**: Both statements use the same Transaction objects
- ✅ **Parallel Generation**: Both statements generated simultaneously for efficiency
- ✅ **Consistency Guaranteed**: Net Income (Income Statement) = Net Operating Cash Flow (Cash Flow) when no accruals

#### 6. **Business Logic Orchestration (Presenter Layer)**
```
Core Components → presenters/income_statement_presenter.py:process_transaction_statements() → Coordinated Results
```
- **File**: `presenters/income_statement_presenter.py:IncomeStatementPresenter`
- **Orchestrates**:
  - Calls DataCleaner (Model - step 2)
  - Calls TransactionProcessor (Model - step 4)
  - Calls IncomeStatementGenerator (Model - step 5a)
  - Calls CashFlowGenerator (Model - step 5b) **← Generates cash flow simultaneously**
  - Coordinates multi-user processing for both statements
  - Handles errors and validation
- **Output**: Complete financial statement set containing:
  - ✅ Income statements (individual users + combined)
  - ✅ Cash flow statements (individual users + combined)
  - ✅ Coordinated results ready for display (no business logic, just coordination)

#### 7. **Results Display (View Layer)**
```
Statement Data → views/pages.py:show_income_cashflow_tab() → User Interface
```
- **File**: `views/pages.py:show_income_cashflow_tab()`
- **Features**:
  - **Dual Statement Display**: Shows both income statement AND cash flow statement side-by-side
  - **Summary Tables**: High-level metrics for both statements (passive)
  - **Detailed Breakdowns**:
    - Income Statement: Category-wise revenue and expense presentation
    - Cash Flow: Operating/Investing/Financing activities breakdown
  - **User Selection**: Dropdown to view individual user or combined statements (applies to both)
  - **Currency Formatting**: Professional CNY formatting (¥X,XXX.XX) for all amounts
  - **Consistency Validation**: Displays relationship between Net Income and Net Operating Cash Flow

#### 8. **Save to Memory (View → Model Layer)**
```
User Action → views/pages.py → core/report_storage.py:MonthlyReportStorage.save_statement()
```
- **File**: `views/pages.py` (UI) + `core/report_storage.py` (Storage)
- **Purpose**: Persist **both generated statements** for future analysis and monthly comparison
- **Storage Format**:
  - Income Statement: `data/accounting/reports/{YYYY-MM}/income_statement.json`
  - Cash Flow Statement: `data/accounting/reports/{YYYY-MM}/cash_flow.json`
- **Features**:
  - **Month Selection**: User specifies YYYY-MM format (defaults to current month)
  - **Metadata Tracking**: Includes entity, generation timestamp, source
  - **Multi-User Support**: Saves all entities (individual users + combined) for both statements
  - **Dual Statement Storage**: Both statements saved in single user action
  - **Validation**: Month format validation with error handling
- **Storage Structure (Income Statement)**:
```json
{
  "year_month": "2025-09",
  "statement_type": "income_statement",
  "generated_at": "2025-09-30T14:30:00",
  "data": {
    "Entity": "User1",
    "Revenue": {...},
    "Expenses": {...},
    "Net Income": 7200.0
  },
  "metadata": {
    "entity": "User1",
    "source": "web_upload"
  }
}
```
- **Storage Structure (Cash Flow Statement)**:
```json
{
  "year_month": "2025-09",
  "statement_type": "cash_flow",
  "generated_at": "2025-09-30T14:30:00",
  "data": {
    "Entity": "User1",
    "Operating Activities": {...},
    "Investing Activities": {...},
    "Financing Activities": {...},
    "Net Change in Cash": 2200.0
  },
  "metadata": {
    "entity": "User1",
    "source": "web_upload"
  }
}
```
- **Benefits**:
  - Enables monthly comparison and trend analysis for both statements
  - Historical record of both financial statements with perfect alignment
  - Reusable for comprehensive reporting and analytics
  - Cash flow trends visible alongside income trends

---

## 🔧 Recent Fixes & Enhancements

### Reimbursement Handling Fix (2025-09-30)

**Problem**: Reimbursement transactions (e.g., `报销 ¥1,509.00 Cash 通勤`) were being double-counted as expenses instead of reducing expenses.

**Root Cause**:
1. `TransactionProcessor` didn't detect reimbursements (Debit=Cash, Credit=Expense)
2. `IncomeStatementGenerator` used `abs()` converting negative amounts to positive

**Solution**:
1. **Added Reimbursement Detection** (`transaction_processor.py:56-59`):
   ```python
   elif debit.lower() in ["cash", "现金"] and credit not in REVENUE_CATEGORIES:
       return "expense", credit, cash_involved, -abs(amount)  # Negative!
   ```

2. **Preserved Sign in Generator** (`income_statement_generator.py:57-61`):
   ```python
   # Keep sign! Negative amounts = expense reductions (reimbursements)
   amount = transaction.amount  # DO NOT use abs() - preserve sign!
   expense_summary[category] = expense_summary.get(category, 0) + amount
   ```

3. **Enhanced Category Mappings** (`config/category_mappings.json`):
   - Added common Chinese category variations (交通, 旅行, 购物, 教育, 医疗, 健康, 保险费)

**Example**:
```csv
交通,¥1,219.55,通勤,Cash      → +1,219.55 Transportation
火车票,¥1,725.00,通勤,Cash     → +1,725.00 Transportation
报销,¥1,509.00,Cash,通勤       → -1,509.00 Transportation (reduction!)
```
**Result**: Net Transportation = ¥1,435.55 ✅ (correctly netted, not double-counted)

### TransactionProcessor Signature Update (2025-09-30)

**Problem**: `TransactionProcessor.__init__()` got unexpected keyword argument 'dataframe'

**Root Cause**: Presenter called `TransactionProcessor(dataframe=cleaned_df)` but `__init__()` only accepted `csv_file_path`.

**Solution**: Updated `__init__()` to accept BOTH parameters:
```python
def __init__(self, csv_file_path: str = None, dataframe: pd.DataFrame = None):
    """Initialize with either a CSV file path or a clean DataFrame."""
```

**Benefits**:
- ✅ Supports new workflow (DataFrame from DataCleaner)
- ✅ Backward compatible (CSV file path still works)
- ✅ Cleaner separation of concerns (cleaning happens before processing)