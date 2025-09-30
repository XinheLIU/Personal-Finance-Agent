# Cash Flow Statement Generation Integration

## 📋 Feature Overview

**Goal**: Implement cash flow statement generation alongside income statement generation from the same transaction data.

**Current State**:
- Button labeled "📈 Generate Income Statement & Cash Flow" only generates income statements
- Line 98-99 in `views/pages.py` has TODO placeholder: `cashflow_statements = {}`
- CashFlowGenerator and CashFlowPresenter exist but are not integrated

**Target State**:
- Single button generates both income and cash flow statements simultaneously
- Both statements displayed side-by-side
- Both statements saved to separate JSON files
- User selection dropdown applies to both statements

---

## 🏗️ Architecture Analysis

### Existing Components

**Model Layer** (`models/business/`):
- ✅ `cash_flow_generator.py:CashFlowStatementGenerator` - Exists, generates cash flow from transactions
- ✅ `income_statement_generator.py:IncomeStatementGenerator` - Working, generates income statements
- ✅ `transaction_processor.py:TransactionProcessor` - Working, parses CSV into Transaction objects
- ✅ `data_cleaner.py:DataCleaner` - Working, cleans and validates CSV data

**Presenter Layer** (`presenters/`):
- ✅ `cash_flow_presenter.py:CashFlowPresenter` - Exists but may need DataFrame input support
- ⚠️ `income_statement_presenter.py:IncomeStatementPresenter` - Needs cash flow integration
- ✅ `transaction_presenter.py:TransactionPresenter` - May be used for combined workflows

**View Layer** (`views/`):
- ⚠️ `pages.py:show_income_cashflow_tab()` - Needs cash flow display logic
- ✅ `components.py` - Has reusable display components
- ❌ Cash flow specific display components - Need to create

**Storage Layer** (`core/`):
- ✅ `report_storage.py:MonthlyReportStorage` - Supports saving statements

### Data Flow

```
CSV Upload → DataCleaner → User Preview/Edit
    ↓
TransactionProcessor → Transaction Objects
    ↓
┌─────────────────────────┴───────────────────────┐
│                                                  │
IncomeStatementGenerator              CashFlowStatementGenerator
    ↓                                              ↓
Income Statement Dict                  Cash Flow Statement Dict
    ↓                                              ↓
└─────────────────────────┬───────────────────────┘
                          ↓
               IncomeStatementPresenter (orchestrates both)
                          ↓
                Display Both Statements
                          ↓
                Save Both to JSON
```

## 🎯 Success Metrics

**Performance**:
- Both statements generated in < 2 seconds for 200 transactions
- No duplicate transaction processing

**Accuracy**:
- Net Income ≈ Net Operating Cash Flow (when no accruals)
- Individual statements sum to Combined statement
- All transactions accounted for in cash flow

**Usability**:
- User can see both statements without scrolling
- Clear CNY formatting (¥X,XXX.XX)
- Consistency validation message visible

**Maintainability**:
- Test coverage > 95%
- Clear separation of concerns (MVP pattern)
- Easy to add new cash flow categories

---

## 📝 Notes for Implementer

1. **Reuse Existing Patterns**: Follow `IncomeStatementPresenter` pattern exactly
2. **Share Transaction Objects**: Don't re-parse CSV for cash flow
3. **Match Existing Display Style**: Use same formatting as income statement
4. **Leverage CategoryMapper**: Use existing category classification
5. **Test First**: Write tests before implementation (TDD!)

**Key Files to Review**:
- `src/modules/accounting/income-statement-generation-workflow.md` - Workflow design
- `src/modules/accounting/presenters/income_statement_presenter.py` - Pattern to follow
- `src/modules/accounting/models/business/income_statement_generator.py` - Generator pattern
- `tests/modules/accounting/test_income_statement_enhanced.py` - Test pattern
