# Balance Sheet Generation Workflow (MVP Pattern)

## 📊 Overview

The balance sheet generation workflow transforms CSV account data into professional financial statements using the **MVP architecture** that cleanly separates business logic, coordination, and presentation. This workflow is **simpler** than the income statement workflow since it focuses on account balances (snapshots) rather than transaction flows.

---

## 🏗️ MVP Workflow Process

### 1. **CSV Upload (View Layer)**
```
User → CSV File → views/components.py:handle_csv_upload()
```
- **File**: `views/components.py:handle_csv_upload()`
- **Purpose**: Passive UI component for secure file upload
- **Expected Format**:
```csv
Account Name,Account Type,CNY,USD
现金账户,Cash CNY,¥25,000.00,-
美元账户,Cash USD,-,$3,500.00
股票投资,Investment,¥150,000.00,-
长期基金,Long-Term Investment,-,$50,000.00
```
- **Output**: Raw CSV file path (no business logic, no validation)

---

### 2. **Data Cleaning & Validation (Model Layer)**
```
Raw CSV → models/business/data_cleaner.py:DataCleaner → Cleaned & Validated DataFrame
```
- **File**: `models/business/data_cleaner.py:DataCleaner`
- **Purpose**: Automated data cleaning and validation BEFORE user preview
- **Cleaning Operations**:
  - Remove completely empty rows and columns
  - Normalize currency symbols (¥25,000.00 → 25000.00, $3,500 → 3500)
  - Strip whitespace from text fields
  - Handle dash/empty values consistently
- **Validation Rules**:
  - ✅ **Required Fields**: Account Name and Account Type must be present
  - ✅ **Data Types**: CNY and USD must be numeric (after cleaning)
  - ✅ **Business Rules**: At least one currency value must be present
  - ✅ **Account Types**: Must be valid (Cash CNY, Cash USD, Investment, Long-Term Investment)
  - ❌ **Errors**: Collect all validation errors with row numbers for user review
- **Output**:
  - Cleaned DataFrame (ready for preview)
  - Validation report (errors with specific row references)

---

### 3. **Data Preview & Editing (View Layer)**
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
  - Validation errors clearly marked (e.g., "Row 3: Missing Account Type")
  - User fixes only real issues, not formatting problems
- **Output**: User-corrected DataFrame (business issues fixed)

---

### 4. **Balance Sheet Generation (Model Layer)**
```
Corrected CSV → core/balance_sheet.py:BalanceSheetGenerator → Balance Sheet
```

- **File**: `core/balance_sheet.py:BalanceSheetGenerator`
- **Core Logic**:
  - **Account Categorization**: Maps accounts to balance sheet categories
  - **Currency Conversion**: Calculates missing currency using exchange rate
  - **Asset Classification**: Separates current assets from fixed assets
  - **Dual-Currency Support**: All amounts displayed in both CNY and USD

**Account Categorization Logic**:

```python
account_categories = {
    'Cash CNY': 'Current Assets - Cash',
    'Cash USD': 'Current Assets - Cash',
    'Investment': 'Current Assets - Investments',
    'Long-Term Investment': 'Fixed Assets - Long-term investments'
}

# Mapping logic
if account_type in ['Cash CNY', 'Cash USD']:
    category = 'Current Assets - Cash'
elif account_type == 'Investment':
    category = 'Current Assets - Investments'
elif account_type == 'Long-Term Investment':
    category = 'Fixed Assets - Long-term investments'
else:
    category = 'Current Assets - Other'
```

**Currency Conversion Logic**:

```python
# Fill missing currency values automatically
if CNY is empty and USD has value:
    CNY = USD × exchange_rate
elif USD is empty and CNY has value:
    USD = CNY ÷ exchange_rate
```

**Generated Structure**:
```python
{
    'Current Assets': {
        'Cash': {'CNY': 25000.0, 'USD': 3571.43},
        'Investments': {'CNY': 150000.0, 'USD': 21428.57},
        'Other': {'CNY': 0.0, 'USD': 0.0},
        'Total Current Assets': {'CNY': 175000.0, 'USD': 25000.0}
    },
    'Fixed Assets': {
        'Long-term Investments': {'CNY': 350000.0, 'USD': 50000.0},
        'Total Fixed Assets': {'CNY': 350000.0, 'USD': 50000.0}
    },
    'Total Assets': {
        'CNY': 525000.0,
        'USD': 75000.0
    }
}
```

---

### 5. **Business Logic Orchestration (Presenter Layer)**
```
Core Components → presenters/balance_sheet_presenter.py:process_balance_sheet() → Coordinated Results
```
- **File**: `presenters/balance_sheet_presenter.py:BalanceSheetPresenter` *(to be implemented)*
- **Orchestrates**:
  - Calls DataCleaner (Model - step 2)
  - Calls BalanceSheetGenerator (Model)
  - Handles errors and validation
  - Coordinates multi-currency processing
- **Output**: Complete balance sheet statement (no business logic, just coordination)

---

### 6. **Results Display (View Layer)**
```
Statement Data → views/pages.py:show_balance_sheet_tab() → User Interface
```
- **File**: `views/pages.py:show_balance_sheet_tab()`
- **Features**:
  - **Dual-Currency Display**: Professional CNY and USD formatting side-by-side
  - **Category Breakdown**: Current assets vs fixed assets with subtotals
  - **Professional Formatting**: Aligned columns with currency symbols (¥X,XXX.XX / $X,XXX.XX)
  - **Export Options**: Download balance sheet as CSV or JSON

**Example Display Format**:
```
BALANCE SHEET

ASSETS:

Current Assets:
                        CNY        USD
  Cash:                ¥25,000.00   $3,571.43
  Investments:         ¥150,000.00  $21,428.57
  ────────────────────────────────────────
  Total Current:       ¥175,000.00  $25,000.00

Fixed Assets:
  Long-term Invest:    ¥350,000.00  $50,000.00
  ────────────────────────────────────────
  Total Fixed:         ¥350,000.00  $50,000.00

TOTAL ASSETS:          ¥525,000.00  $75,000.00
══════════════════════════════════════════
```

---

### 7. **Save to Memory (View → Model Layer)**
```
User Action → views/pages.py → models/repositories/data_storage.py:MonthlyReportStorage.save_statement()
```
- **File**: `views/pages.py` (UI) + `models/repositories/data_storage.py` (Storage)
- **Purpose**: Persist generated balance sheets for future analysis and monthly comparison
- **Storage Format**: JSON files in `data/accounting/reports/{YYYY-MM}/balance_sheet.json`
- **Features**:
  - **Month Selection**: User specifies YYYY-MM format (defaults to current month)
  - **Metadata Tracking**: Includes generation timestamp, exchange rate, source
  - **Dual-Currency Storage**: Saves both CNY and USD values
  - **Validation**: Month format validation with error handling
- **Storage Structure**:
```json
{
  "year_month": "2025-09",
  "statement_type": "balance_sheet",
  "generated_at": "2025-09-30T14:30:00",
  "exchange_rate": 7.0,
  "data": {
    "Current Assets": {
      "Cash": {"CNY": 25000.0, "USD": 3571.43},
      "Investments": {"CNY": 150000.0, "USD": 21428.57}
    },
    "Fixed Assets": {
      "Long-term Investments": {"CNY": 350000.0, "USD": 50000.0}
    },
    "Total Assets": {
      "CNY": 525000.0,
      "USD": 75000.0
    }
  },
  "metadata": {
    "source": "web_upload",
    "exchange_rate": 7.0
  }
}
```
- **Benefits**:
  - Enables monthly comparison and trend analysis
  - Historical record of asset balances over time
  - Reusable for reporting and net worth tracking

---

## 🔧 Key Differences from Income Statement Workflow

### **Simpler Processing**
| Aspect | Income Statement | Balance Sheet |
|--------|------------------|---------------|
| **Data Type** | Transactions (flows) | Account balances (snapshots) |
| **Complexity** | Multi-step classification (revenue, expense, reimbursement) | Simple categorization (cash, investment, fixed) |
| **Calculations** | Aggregation, netting, tax calculations | Simple summation and currency conversion |
| **Multi-User** | Splits by user, generates combined statements | Single entity per balance sheet |
| **Transaction Logic** | Requires double-entry accounting logic | No transaction logic needed |

### **No Transaction Processing**
- Balance sheet does NOT process transactions or transaction flow
- No need for TransactionProcessor or transaction classification
- No reimbursement handling, sign preservation, or category mapping complexity
- Simply reads current account balances and categorizes them

### **Automatic Currency Conversion**
- If CNY is empty but USD has value → Calculate CNY = USD × rate
- If USD is empty but CNY has value → Calculate USD = CNY ÷ rate
- Both currencies always displayed for complete view

### **No Multi-User Logic**
- One balance sheet per upload (represents single entity's assets)
- No user splitting or combined statements needed
- Simpler than income statement's multi-user support

---

## 🎯 Data Flow Summary

```
1. User uploads accounts CSV with dual currency columns
   ↓
2. DataCleaner removes empty rows, normalizes currency symbols
   ↓
3. User reviews CLEAN data, makes corrections if needed
   ↓
4. BalanceSheetGenerator categorizes accounts and converts currencies
   ↓
5. BalanceSheetPresenter orchestrates the workflow
   ↓
6. View displays professional dual-currency balance sheet
   ↓
7. Save to data/accounting/reports/{YYYY-MM}/balance_sheet.json
```

**Processing Time**: < 1 second for typical account lists (10-50 accounts)
**Data Integrity**: Full validation pipeline ensures accuracy
**User Control**: Review and edit data before final statement generation
