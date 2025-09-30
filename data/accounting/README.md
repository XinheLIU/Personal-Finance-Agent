# Accounting Data Directory

This directory contains data for the Professional Accounting Module with CSV-based transaction management and financial statement generation.

## 📁 Directory Structure

```
data/accounting/
├── README.md                    # This file
├── transactions.csv             # Transaction data (legacy, optional)
├── csv_uploads/                 # Temporary uploaded CSV files
├── monthly_reports/             # Generated financial statements (NEW)
│   └── {YYYY-MM}/              # Month-specific reports
│       ├── income_statement_*.json    # Income statements by entity
│       ├── cash_flow_*.json           # Cash flow statements by entity
│       └── balance_sheet_*.json       # Balance sheets by entity
├── monthly_data/                # Monthly comparison data
└── parquet/                     # Optimized data storage (optional)
```

## 🆕 New Features (2025-09)

### Dual Statement Generation
The system now generates **both income statements and cash flow statements** simultaneously from the same transaction data:
- Single button: "📈 Generate Income Statement & Cash Flow"
- Both statements displayed side-by-side
- Both saved to `monthly_reports/{YYYY-MM}/` with separate JSON files

### Monthly Reports Structure
```
monthly_reports/2025-09/
├── income_statement_User1.json      # User1's income statement
├── income_statement_Combined.json   # Combined statement
├── cash_flow_User1.json            # User1's cash flow statement
└── cash_flow_Combined.json         # Combined cash flow statement
```

## 📊 File Formats

### Input: Transaction CSV

**Expected Format** (for web upload):
```csv
Description,Amount,Debit,Credit,User
Monthly Salary,¥8000.00,工资收入,Bank Account,User1
Rent Payment,-2000.0,房租,Bank Account,User1
Grocery Shopping,¥580.50,餐饮,Credit Card,User1
Investment Purchase,-5000.0,投资支出,Bank Account,User1
```

**Required Columns**:
- `Description`: Transaction description (Chinese/English supported)
- `Amount`: Transaction amount (positive for income, negative for expenses)
- `Debit`: Debit account/category
- `Credit`: Credit account/category
- `User`: User identifier for multi-user support

**Notes**:
- UTF-8 encoding required for Chinese text
- Currency symbols (¥, $) are automatically cleaned
- Empty rows are automatically removed
- All validation happens before processing

### Output: Financial Statements (JSON)

#### Income Statement
```json
{
  "year_month": "2025-09",
  "statement_type": "income_statement",
  "generated_at": "2025-09-30T14:30:00",
  "statement": {
    "Entity": "User1",
    "Revenue": {
      "工资收入": 8000.0,
      "服务收入": 2000.0
    },
    "Total Revenue": 10000.0,
    "Expenses": {
      "房租": 2000.0,
      "餐饮": 800.0
    },
    "Total Expenses": 2800.0,
    "Net Income": 7200.0
  },
  "metadata": {
    "entity": "User1",
    "generated_at": "2025-09-30T14:30:00",
    "source": "web_upload"
  }
}
```

#### Cash Flow Statement (NEW)
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

#### Balance Sheet
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
    }
  }
}
```

## 💻 Usage

### Web Interface (Recommended)

1. **Launch Streamlit App**:
   ```bash
   streamlit run src/ui/streamlit_app.py
   ```

2. **Navigate to "💰 Accounting Management" tab**

3. **Upload Transaction CSV**:
   - Click "Browse files" under "📊 Income Statement & Cash Flow Generation"
   - Select your CSV file with transaction data
   - Review and edit cleaned data

4. **Generate Statements**:
   - Click "📈 Generate Income Statement & Cash Flow" button
   - Both statements generated automatically
   - Select user from dropdown to view details

5. **Save to Memory**:
   - Specify month in YYYY-MM format
   - Click "💾 Save Both Statements" button
   - Both statements saved to `monthly_reports/{YYYY-MM}/`

### Command Line Interface

```bash
# Check accounting module status
python -m src.cli accounting-status

# Generate income statement (legacy)
python -m src.cli generate-income-statement 2025-01

# Generate year-to-date statement
python -m src.cli generate-income-statement YTD --export-csv
```

## 🔍 Data Validation

The system performs comprehensive validation:

### Automatic Cleaning
- ✅ Removes empty rows and columns
- ✅ Normalizes currency symbols (¥8,000.00 → 8000.00)
- ✅ Strips whitespace from text fields
- ✅ Standardizes date formats

### Validation Rules
- ✅ **Required Fields**: Amount, Debit, and Credit must be present
- ✅ **Data Types**: Amount must be numeric
- ✅ **Business Rules**: Revenue categories must have positive amounts
- ✅ **Category Matching**: Categories must match predefined taxonomy

### Error Reporting
- Clear error messages with row numbers
- Validation errors shown before processing
- User can edit data to fix issues

## 📈 Financial Statement Categories

### Revenue Categories
- 工资收入 (Salary Income)
- 服务收入 (Service Income)
- 其他收入 (Other Income)

### Expense Categories
Operating expenses include:
- 房租 (Rent)
- 餐饮 (Food & Dining)
- 交通/通勤 (Transportation)
- 购物 (Shopping)
- 教育 (Education)
- 医疗/健康 (Healthcare)
- 保险费 (Insurance)
- 旅行 (Travel)

### Activity Classification (Cash Flow)
- **Operating Activities**: Revenue and regular expenses
- **Investing Activities**: 投资支出, 房产投资, 股票购买
- **Financing Activities**: 借款, 贷款, 还款

## 🏗️ Architecture (MVP Pattern)

The accounting module follows **Model-View-Presenter (MVP)** architecture:

```
src/modules/accounting/
├── models/                      # Business logic
│   ├── domain/                 # Core entities
│   └── business/               # Generators & processors
│       ├── income_statement_generator.py
│       ├── cash_flow_generator.py
│       └── transaction_processor.py
├── presenters/                 # Coordination layer
│   ├── income_statement_presenter.py
│   └── cash_flow_presenter.py
└── views/                      # UI layer
    ├── pages.py                # Page layouts
    └── components.py           # Display components
```

## 🔄 Data Flow

```
1. Upload CSV → 2. Clean & Validate → 3. User Review/Edit
                                              ↓
4. Transaction Processing → 5. Generate Both Statements
                                              ↓
6. Display Side-by-Side → 7. Save Both to JSON
```

**Key Features**:
- ✅ Single transaction processing for both statements
- ✅ No duplicate data parsing
- ✅ Efficient DataFrame operations
- ✅ Multi-user support (individual + combined statements)

## 📝 Migration Notes

### From Legacy Format
If you have old CSV files in the legacy format:
```csv
date,description,amount,category,account_name,account_type,notes
```

Convert to new format:
```csv
Description,Amount,Debit,Credit,User
```

**Mapping**:
- `description` → `Description`
- `amount` → `Amount`
- `category` → `Debit` (for expenses) or `Credit` (for revenue)
- Add `User` column for multi-user support

### Old Directory Structure
Legacy directories are being phased out:
- `income_statements/` → Replaced by `monthly_reports/{YYYY-MM}/`
- `cash_flow_statements/` → Replaced by `monthly_reports/{YYYY-MM}/`
- `balance_sheets/` → Replaced by `monthly_reports/{YYYY-MM}/`

**New structure** consolidates all statements for a given month in one directory.

## 🐛 Troubleshooting

### "Missing required columns"
- Ensure CSV has: Description, Amount, Debit, Credit, User
- Check column names match exactly (case-sensitive)

### "Data validation errors"
- Review error messages with row numbers
- Edit data in preview editor before generating statements

### "Cannot save statements"
- Check month format is YYYY-MM
- Ensure `monthly_reports/` directory exists

### "Mixed data types error"
- Ensure text fields contain only text (not numbers)
- Check Amount column contains only numeric values

## 📚 Related Documentation

- Architecture: `src/modules/accounting/income-statement-generation-workflow.md`
- Balance Sheet: `src/modules/accounting/balance-sheet-generation-workflow.md`
- Category Config: `src/modules/accounting/config/category_mappings.json`
- Main README: `README.md` (project root)

---

**Last Updated**: 2025-09-30
**Version**: 0.4.3 (Dual Statement Generation)