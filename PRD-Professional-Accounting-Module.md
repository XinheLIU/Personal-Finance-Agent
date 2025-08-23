# PRD — Personal Finance Agent Accounting MVP

## Executive Summary (MVP)

**Problem:** Users need a simple way to record monthly transactions and view a basic Income Statement. Heavy features (APIs, DB, multi-user consolidation) are unnecessary for first release.

**Solution (MVP):** Add a lightweight accounting module that reads/writes CSV files, validates basic formats, and produces a monthly Income Statement. Integrate as a new page in the existing Streamlit app and a minimal CLI command. No server APIs or databases.

**Value:** Fastest path to usable, auditable personal accounting with minimal engineering footprint and full compatibility with current codebase.

---

## 1) Scope

### In Scope (MVP)
- Single-user workflow using CSV files in `data/accounting/`
- Transaction import from `transactions.csv`
- Optional asset snapshot from `assets.csv` (display + simple MoM delta)
- Monthly Income Statement (Revenue, Expenses, Net Income)
- Streamlit page to upload/select period and view results
- CLI to generate a monthly Income Statement from disk files

### Out of Scope (MVP)
- APIs, databases, authentication, role-based access
- Cash flow statement, balance sheet, advanced analytics
- Budgets, alerts, multi-user consolidation
- PDF export (CSV export only)

---

## 2) Simple Data Model (CSV-based)

All files under `data/accounting/`. UTF-8. Currency: CNY (¥). Amount: negative for expenses, positive for income.

### 2.1 transactions.csv
Headers (exact):

```csv
date,description,amount,category,account_name,account_type,notes
```

Example row:

```csv
2025-01-15,餐饮,-68.50,food_dining,招商银行卡,checking,晚饭
```

Rules:
- `date`: YYYY-MM-DD
- `amount`: number; negative for expenses, positive for income
- `account_type`: one of [checking, savings, credit, investment]; default to `checking` if missing

### 2.2 assets.csv (optional)
Headers:

```csv
as_of_date,account_name,balance,account_type,currency
```

Example:

```csv
2025-01-31,招商银行卡,12000.00,checking,CNY
```

### 2.3 Outputs
- `data/accounting/statements/income_statement_YYYY-MM.csv`

---

## 3) Functional Requirements (MVP)

### 3.1 Import & Validation
- Read CSVs with robust UTF-8 handling
- Validate required headers, dates, numeric amounts
- Fail fast with actionable error messages (console + log)

### 3.2 Income Statement (Monthly)
- Inputs: `transactions.csv` filtered by month
- Revenue = sum of positive `amount`
- Expenses = absolute sum of negative `amount`
- Net Income = Revenue − Expenses
- Category breakdown: sum by `category` with percent of Revenue
- Output table in Streamlit + CSV export

### 3.3 Asset Snapshot (Optional)
- Show balances by `account_name` and `account_type` for end-of-month
- Show simple MoM change if prior month exists

---

## 4) Integration with Current Codebase

### 4.1 Module placement (under `src/`)

```text
src/
├── accounting/
│   ├── __init__.py
│   ├── io.py                # CSV read/write + validation
│   ├── income_statement.py  # monthly statement math
│   └── ui.py                # Streamlit page components
├── streamlit_app.py         # add new page entry
├── cli.py                   # add CLI command
└── app_logger.py            # reuse logging
```

### 4.2 Data directories

```text
data/
└── accounting/
    ├── transactions.csv
    ├── assets.csv                # optional
    └── statements/
        └── income_statement_YYYY-MM.csv
```

### 4.3 Streamlit integration
- New nav: "🧾 Accounting (MVP)"
- Month selector (YYYY-MM), file pickers (or default to files in `data/accounting/`)
- Show statement table with totals and category breakdown
- Export CSV button → `statements/`

### 4.4 CLI (optional but simple)

```bash
python -m src.main --mode accounting --generate-income-statement --period 2025-01
```

---

## 5) Acceptance Criteria (MVP)
- Load `transactions.csv` and generate Income Statement for selected month
- Clear validation errors explaining what failed and how to fix
- View in Streamlit and export CSV to `statements/`
- If `assets.csv` exists, show snapshot and MoM change
- No APIs or databases required

---

## 6) Success Metrics
- Statement generation < 2s for ≤ 5,000 rows
- Zero silent data errors; fail-fast with actionable messages
- Workflow completable via CSVs + Streamlit UI only

---

## 7) Implementation Plan (fast-track)
- Core: CSV IO + validation, income statement math, Streamlit table, CSV export
- Polish: Category % of revenue, optional assets snapshot, CLI hook, basic tests

---

The following section is the original, detailed (non-MVP) specification preserved for reference only.

## Product Requirements Document (Detailed Spec)
## Personal Finance Agent - Professional Accounting Module

### Executive Summary

**Problem Statement:** The Personal Finance Agent system currently lacks comprehensive accounting functionality to transform user financial data into professional financial statements. Users need a systematic way to input monthly transactions and visualize their financial health through standardized accounting reports including Income Statements, Cash Flow Statements, and Balance Sheets.

**Solution:** Develop a Professional Accounting Module that accepts user transaction inputs in a structured format and generates industry-standard financial statements with comparative analysis, budget tracking, and visual financial health monitoring.

**Business Value:** Enable users to manage personal finances with institutional-grade financial reporting, providing clear insights into spending patterns, asset growth, and financial performance over time.

---

## 1. Functional Requirements

### 1.1 Data Input Management (Must Have)

**FR-1.1: Transaction Journal Entry**
- System shall accept monthly transaction entries with the following mandatory fields:
  - Description (Chinese/English text)
  - Amount (¥ currency format)
  - Category (predefined taxonomy)
  - Account Type (Cash/Credit/Debit)
  - Optional: Notes/Comments
- System shall support both cash and non-cash transactions
- System shall validate data formats and currency amounts
- System shall allow bulk import via CSV/Excel formats

**FR-1.2: Asset Portfolio Input**
- System shall accept monthly asset snapshots including:
  - Account Name (bank/institution identifier)
  - Current Balance (¥ currency format)
  - Account Type (checking, savings, investment, retirement)
- System shall track month-over-month asset changes
- System shall support manual entry and file upload methods

### 1.2 Financial Statement Generation (Must Have)

**FR-2.1: Monthly Income Statement**
- Generate standardized Income Statement with:
  - Revenue section (Service Revenue, Other Income)
  - Tax Expense calculation with percentage analysis
  - Expense categorization (fixed vs. variable costs)
  - Category-wise percentage analysis vs. gross revenue
  - Net Operating Income calculation
- Support individual user and consolidated multi-user statements

**FR-2.2: Year-to-Date Comparative Analysis**
- Generate YTD consolidated view showing:
  - Budget vs. Actual comparisons
  - Month-over-month variance analysis
  - Category trend analysis
  - Percentage change calculations

**FR-2.3: Cash Flow Statement**
- Generate monthly cash flow statements showing:
  - Operating cash flows
  - Investing activities
  - Financing activities
  - Net cash flow analysis
- Support YTD consolidated cash flow reporting

**FR-2.4: Balance Sheet Generation**
- Generate month-end balance sheets including:
  - Asset categorization (current vs. long-term)
  - Account-wise asset breakdown
  - Month-over-month asset change analysis
  - Visual asset growth tracking

### 1.3 Analytics and Visualization (Should Have)

**FR-3.1: Financial Health Dashboard**
- Visual representation of key financial metrics
- Asset growth charts and trend analysis
- Spending pattern visualizations
- Category-wise expense breakdowns

**FR-3.2: Budget Tracking and Alerts**
- Budget setting capabilities by category
- Variance alerts for budget overruns
- Trend-based spending projections

---

## 2. Technical Specifications

### 2.1 Data Models

**Transaction Model:**
```python
class Transaction:
    id: str
    user_id: str
    date: datetime
    description: str
    amount: Decimal
    category: str
    account_type: str  # Cash, Credit, Debit
    transaction_type: str  # Cash, Non-Cash
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
```

**Asset Model:**
```python
class Asset:
    id: str
    user_id: str
    account_name: str
    balance: Decimal
    account_type: str  # checking, savings, investment, retirement
    as_of_date: datetime
    currency: str = "CNY"
    created_at: datetime
```

**Category Taxonomy:**
```python
EXPENSE_CATEGORIES = {
    "fixed_costs": ["房租", "水电费", "保险"],
    "food_dining": ["餐饮", "买菜/杭州日常餐饮"],
    "transportation": ["交通", "通勤"],
    "daily_shopping": ["日用购物", "服饰"],
    "personal": ["个人消费", "教育/买书"],
    "health_fitness": ["运动和健康", "买药/医疗"],
    "social_entertainment": ["人情/旅行支出", "社交吃饭"],
    "pets": ["宠物"],
    "work_related": ["办公支出"]
}
```

### 2.2 Architecture Integration

**Module Structure:**
```
modules/
├── accounting/
│   ├── __init__.py
│   ├── data_input/
│   │   ├── transaction_parser.py
│   │   ├── asset_importer.py
│   │   └── data_validator.py
│   ├── statements/
│   │   ├── income_statement.py
│   │   ├── cash_flow.py
│   │   ├── balance_sheet.py
│   │   └── report_generator.py
│   ├── analytics/
│   │   ├── trend_analysis.py
│   │   ├── budget_tracker.py
│   │   └── visualization.py
│   └── streamlit_interface/
│       ├── accounting_dashboard.py
│       ├── data_entry_forms.py
│       └── report_viewer.py
```

### 2.3 Database Schema

**Tables Required:**
- `users` (existing)
- `transactions` (new)
- `assets` (new)
- `budgets` (new)
- `categories` (new)

### 2.4 API Endpoints

**Data Input APIs:**
- `POST /api/accounting/transactions` - Create transaction entry
- `POST /api/accounting/transactions/bulk` - Bulk transaction import
- `POST /api/accounting/assets` - Update asset positions
- `GET /api/accounting/categories` - Retrieve category taxonomy

**Report Generation APIs:**
- `GET /api/accounting/income-statement/{user_id}/{period}` - Generate income statement
- `GET /api/accounting/cash-flow/{user_id}/{period}` - Generate cash flow statement
- `GET /api/accounting/balance-sheet/{user_id}/{date}` - Generate balance sheet
- `GET /api/accounting/consolidated/{period}` - Multi-user consolidated reports

---

## 3. User Stories and Acceptance Criteria

### Epic 1: Data Entry and Management

**US-1.1: As a user, I want to input my monthly transactions so that I can track my spending**

*Acceptance Criteria:*
- [ ] User can input transactions with description, amount, category, and account type
- [ ] System validates currency format (¥) and positive/negative amounts
- [ ] User can categorize transactions using predefined categories
- [ ] System supports both Chinese and English descriptions
- [ ] User can add optional notes to transactions
- [ ] System saves transactions with timestamp

**US-1.2: As a user, I want to upload my asset balances so that I can track my wealth**

*Acceptance Criteria:*
- [ ] User can manually enter account balances by institution
- [ ] System supports various account types (checking, savings, investment)
- [ ] User can upload asset data via CSV/Excel
- [ ] System validates balance formats and currency
- [ ] System tracks month-over-month balance changes

### Epic 2: Financial Statement Generation

**US-2.1: As a user, I want to view my monthly income statement so that I can understand my financial performance**

*Acceptance Criteria:*
- [ ] System generates professional income statement format
- [ ] Revenue section shows service revenue and other income
- [ ] Tax expenses calculated with percentage of gross revenue
- [ ] Expenses categorized into fixed and variable costs
- [ ] Each category shows percentage of gross revenue
- [ ] Net operating income calculated correctly

**US-2.2: As a user, I want to see year-to-date comparisons so that I can track my financial trends**

*Acceptance Criteria:*
- [ ] System displays YTD data in tabular format
- [ ] Budget vs. actual comparisons with variance calculations
- [ ] Month-over-month percentage changes
- [ ] Category trend analysis over time
- [ ] Visual indicators for positive/negative trends

### Epic 3: Multi-User and Analytics

**US-3.1: As a household, we want to see consolidated financial statements so that we can manage our joint finances**

*Acceptance Criteria:*
- [ ] System combines multiple user transactions
- [ ] Consolidated income statement for all users
- [ ] Consolidated asset portfolio view
- [ ] Individual vs. household reporting options

**US-3.2: As a user, I want to visualize my asset growth so that I can track my wealth building progress**

*Acceptance Criteria:*
- [ ] Charts showing asset balance trends over time
- [ ] Account-wise asset breakdown visualizations
- [ ] Month-over-month growth percentages
- [ ] Asset allocation pie charts by account type

---

## 4. UI/UX Requirements

### 4.1 Streamlit Interface Design

**Navigation Structure:**
```
Personal Finance Agent
├── 📊 Investment Analysis (existing)
├── 📈 Backtesting (existing)
├── 💼 Portfolio Management (existing)
├── 📋 System Status (existing)
└── 🧾 Professional Accounting (NEW)
    ├── 📝 Transaction Entry
    ├── 💰 Asset Management
    ├── 📊 Financial Statements
    │   ├── Income Statement
    │   ├── Cash Flow Statement
    │   └── Balance Sheet
    ├── 📈 Financial Analytics
    └── ⚙️ Accounting Settings
```

### 4.2 Key Interface Components

**Transaction Entry Form:**
- Multi-row data entry table with inline validation
- Category dropdown with search functionality
- Amount input with currency formatting
- Bulk upload interface with template download
- Real-time total calculations

**Financial Statement Viewer:**
- Professional statement formatting with Chinese/English labels
- Expandable/collapsible sections
- Export to PDF/Excel functionality
- Print-friendly layouts
- Interactive period selection (monthly/quarterly/YTD)

**Asset Dashboard:**
- Asset balance cards with growth indicators
- Interactive charts for balance trends
- Account-wise filtering and sorting
- Historical balance comparison tables

### 4.3 Responsive Design Requirements

- Mobile-friendly transaction entry
- Tablet-optimized statement viewing
- Desktop-focused analytics dashboards
- Touch-friendly controls for mobile users

---

## 5. Integration Requirements

### 5.1 Existing System Integration

**Data Center Module Integration:**
- Extend existing data loader to handle accounting data
- Implement accounting data validation alongside market data validation
- Add accounting data to system health checks

**Management Module Integration:**
- Add accounting module to SystemCoordinator
- Implement accounting system status monitoring
- Add accounting data backup and recovery processes

**Configuration Integration:**
- Extend `config/system.py` with accounting parameters
- Add accounting categories to `config/assets.py`
- Implement accounting-specific logging configuration

### 5.2 Database Integration

**Data Storage:**
- Extend existing data structure: `data/accounts/` → `data/accounting/`
- Create subdirectories: `transactions/`, `assets/`, `statements/`
- Implement data archival and retention policies

**Backup and Recovery:**
- Integrate with existing backup systems
- Implement transaction log recovery mechanisms
- Add accounting data to system validation checks

### 5.3 CLI Integration

**New CLI Commands:**
```bash
# Accounting data management
python -m src.main --mode accounting --import-transactions file.csv
python -m src.main --mode accounting --generate-statements --period 2024-01
python -m src.main --mode accounting --export-reports --format excel

# System integration
python -m src.main --validate  # Include accounting data validation
python -m src.main --mode system --status  # Include accounting module status
```

---

## 6. Success Metrics and Validation Criteria

### 6.1 Functional Success Metrics

**Data Accuracy Metrics:**
- 100% transaction data integrity (no data loss during import/export)
- <1% calculation errors in financial statements
- 99.9% uptime for accounting module functionality

**User Adoption Metrics:**
- Users actively inputting transactions monthly: >80% retention
- Average transaction entries per user per month: >20
- Financial statement generation usage: >60% monthly active users

**Performance Metrics:**
- Statement generation time: <5 seconds for monthly statements
- Data import processing: <30 seconds for 1000 transactions
- Dashboard load time: <3 seconds

### 6.2 Business Success Metrics

**User Engagement:**
- Monthly active users in accounting module: Target 70% of total users
- Average session duration in accounting features: >10 minutes
- User-reported financial awareness improvement: >80% positive feedback

**Feature Utilization:**
- YTD comparative analysis usage: >50% of users
- Asset tracking feature adoption: >60% of users
- Multi-user household management: >30% of applicable users

### 6.3 Technical Success Criteria

**System Integration:**
- Zero conflicts with existing investment modules
- Successful integration with current authentication system
- Consistent UI/UX experience across all modules

**Data Quality:**
- Comprehensive data validation with <0.1% invalid entries
- Successful backup and recovery testing
- Complete audit trail for all financial transactions

**Scalability:**
- Support for 1000+ users simultaneously
- Handle 100,000+ transactions without performance degradation
- Successful stress testing under peak load conditions

---

## 7. Risk Assessment and Mitigation

### 7.1 Technical Risks

**Risk: Data Privacy and Security**
- *Impact:* High - Financial data exposure
- *Mitigation:* Implement encryption at rest and in transit, role-based access controls, audit logging

**Risk: Calculation Accuracy**
- *Impact:* High - Incorrect financial statements
- *Mitigation:* Comprehensive unit testing, financial calculation validation, third-party auditing tools

**Risk: System Integration Complexity**
- *Impact:* Medium - Development delays
- *Mitigation:* Phased rollout, extensive integration testing, fallback mechanisms

### 7.2 Business Risks

**Risk: User Adoption**
- *Impact:* Medium - Low feature utilization
- *Mitigation:* User training materials, intuitive UI design, gradual feature introduction

**Risk: Regulatory Compliance**
- *Impact:* High - Legal/regulatory issues
- *Mitigation:* Legal review of financial reporting features, compliance documentation

---

## 8. Implementation Timeline

### Phase 1: Foundation (Weeks 1-4)
- [ ] Data models and database schema design
- [ ] Core transaction parsing and validation logic
- [ ] Basic Streamlit interface for data entry
- [ ] Integration with existing system architecture

### Phase 2: Core Features (Weeks 5-8)
- [ ] Income statement generation
- [ ] Asset tracking functionality
- [ ] Basic financial statement viewer
- [ ] CSV/Excel import capabilities

### Phase 3: Advanced Features (Weeks 9-12)
- [ ] Cash flow and balance sheet generation
- [ ] YTD comparative analysis
- [ ] Multi-user consolidation
- [ ] Advanced visualizations and analytics

### Phase 4: Polish and Launch (Weeks 13-16)
- [ ] UI/UX refinements
- [ ] Performance optimization
- [ ] Comprehensive testing and bug fixes
- [ ] User documentation and training materials
- [ ] Production deployment and monitoring

---

## 9. Assumptions and Dependencies

### 9.1 Assumptions
- Users will consistently input monthly transaction data
- Chinese Yuan (¥) is the primary currency for all calculations
- Users understand basic accounting terminology
- Existing Personal Finance Agent users will adopt accounting features

### 9.2 Dependencies
- Continued maintenance of existing system modules
- Streamlit framework compatibility and updates
- Database performance under increased data load
- User availability for testing and feedback during development

### 9.3 Out of Scope
- Integration with external banking APIs
- Real-time transaction monitoring
- Tax calculation and filing features
- Multi-currency support (Phase 2 consideration)
- Automated transaction categorization via AI/ML

---

**Document Version:** 1.0  
**Last Updated:** 2025-08-23  
**Prepared By:** Claude Code - Senior Product Manager  
**Review Status:** Ready for Stakeholder Review