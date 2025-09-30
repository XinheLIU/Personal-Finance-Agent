# Cash Flow Statement Generation Test Strategy

## 📋 Feature Overview

**Goal**: Implement cash flow statement generation alongside income statement generation from the same transaction data.

**Current State**:
- Button labeled " 📈 Generate Income Statement& Cash Flow" only generates income statements
- Line 98-99 in `views/pages.py` has TODO placeholder: `cashflow_statements = {}`
- CashFlowGenerator and CashFlowPresenter exist but are not integrated

**Target State**:
- Single button "📈 Generate Income Statement" generates both income and cash flow statements automatically
- Both statements displayed side-by-side
- Single "💾 Save Both Statements" button saves both to separate JSON files
- User selection dropdown applies to both statements
- **Simplified UX**: User only clicks one generate button, system handles both statements

## Testing Strategy 

### Phase 1: Model Layer Tests (CashFlowStatementGenerator)

**File**: `tests/modules/accounting/test_cash_flow_generator.py`

#### Test 1.1: Basic Cash Flow Statement Structure
```python
def test_cash_flow_statement_has_required_sections():
    """Verify cash flow statement contains Operating, Investing, Financing sections"""
```
**Expected Output**:
```python
{
    'Entity': 'User1',
    'Operating Activities': {...},
    'Investing Activities': {...},
    'Financing Activities': {...},
    'Net Change in Cash': <float>
}
```

#### Test 1.2: Operating Activities - Revenue
```python
def test_operating_activities_includes_revenue():
    """Revenue transactions should appear in Operating Activities"""
```
**Sample Input**: Salary transaction (Revenue)
**Expected**: Positive cash in Operating Activities

#### Test 1.3: Operating Activities - Expenses
```python
def test_operating_activities_includes_expenses():
    """Expense transactions should appear in Operating Activities"""
```
**Sample Input**: Rent, food transactions (Expenses)
**Expected**: Negative cash in Operating Activities

#### Test 1.4: Operating Activities - Net Operating Cash Flow
```python
def test_net_operating_cash_flow_calculation():
    """Net Operating Cash Flow = Revenue - Expenses"""
```
**Expected**: Matches Net Income (when no accruals)

#### Test 1.5: Investing Activities - Investment Purchases
```python
def test_investing_activities_investment_purchases():
    """Investment transactions should appear in Investing Activities"""
```
**Sample Input**: Stock purchase, property investment
**Expected**: Negative cash in Investing Activities

#### Test 1.6: Financing Activities - Loans
```python
def test_financing_activities_loan_receipt():
    """Loan transactions should appear in Financing Activities"""
```
**Sample Input**: Loan receipt, debt repayment
**Expected**: Positive/negative cash in Financing Activities

#### Test 1.7: Net Change in Cash Calculation
```python
def test_net_change_in_cash_calculation():
    """Net Change = Operating + Investing + Financing"""
```

#### Test 1.8: Multi-User Cash Flow
```python
def test_multi_user_cash_flow_generation():
    """Generate separate cash flow for multiple users"""
```
**Expected**: Individual statements for User1, User2, Combined

#### Test 1.9: Empty Transaction List
```python
def test_empty_transactions_returns_zero_cash_flow():
    """Handle empty transaction list gracefully"""
```

#### Test 1.10: Consistency with Income Statement
```python
def test_net_operating_cash_flow_matches_net_income():
    """When no accruals, Net Operating Cash Flow ≈ Net Income"""
```

---

### Phase 2: Presenter Layer Tests

**File**: `tests/modules/accounting/test_cash_flow_presenter.py`

#### Test 2.1: CashFlowPresenter DataFrame Input
```python
def test_cash_flow_presenter_accepts_dataframe():
    """CashFlowPresenter should accept DataFrame input like IncomeStatementPresenter"""
```

#### Test 2.2: CashFlowPresenter Error Handling
```python
def test_cash_flow_presenter_handles_validation_errors():
    """Presenter should handle validation errors gracefully"""
```

**File**: `tests/modules/accounting/test_income_statement_presenter.py` (modify existing)

#### Test 2.3: IncomeStatementPresenter Generates Both Statements
```python
def test_presenter_generates_both_income_and_cash_flow():
    """IncomeStatementPresenter should return both income and cash flow statements"""
```
**Expected Return**: `(income_statements, cashflow_statements, users)`

#### Test 2.4: Presenter Integration Test
```python
def test_presenter_integration_both_statements_consistent():
    """Income and cash flow statements should be consistent (same users, same data)"""
```

---

### Phase 3: View Layer Tests (Manual/UI)

**File**: Manual UI testing checklist

#### Test 3.1: Display Both Statements Side-by-Side
- [ ] Income statement displayed on left
- [ ] Cash flow statement displayed on right
- [ ] Both statements show same user entities

#### Test 3.2: User Selection Dropdown
- [ ] Dropdown includes all users + "Combined"
- [ ] Selecting user updates both statements
- [ ] Statements stay in sync

#### Test 3.3: Cash Flow Display Format
- [ ] Operating Activities section visible
- [ ] Investing Activities section visible
- [ ] Financing Activities section visible
- [ ] Net Change in Cash highlighted
- [ ] CNY formatting (¥X,XXX.XX)

#### Test 3.4: Consistency Validation
- [ ] Shows message if Net Income ≈ Net Operating Cash Flow
- [ ] Warning if discrepancy exists

#### Test 3.5: Single Generate Button
- [ ] "📈 Generate Income Statement" button generates both statements
- [ ] Both income and cash flow statements appear after single click
- [ ] No separate cash flow generation button needed

#### Test 3.6: Save Both Statements
- [ ] "💾 Save Both Statements" button works
- [ ] Creates `income_statement.json`
- [ ] Creates `cash_flow.json` (new)
- [ ] Both files in same `{YYYY-MM}/` directory

---

### Phase 4: Integration Tests

**File**: `tests/modules/accounting/test_income_cashflow_integration.py`

#### Test 4.1: End-to-End CSV to Both Statements
```python
def test_e2e_csv_to_both_statements():
    """Complete workflow from CSV upload to displaying both statements"""
```

#### Test 4.2: Both Statements Use Same Transaction Objects
```python
def test_both_statements_use_same_transactions():
    """Verify no re-parsing, both use same Transaction list"""
```

#### Test 4.3: Multi-User Integration
```python
def test_multi_user_both_statements():
    """Individual users sum to Combined for both statements"""
```

#### Test 4.4: Storage Integration
```python
def test_storage_saves_both_statements():
    """Verify both JSON files created with correct structure"""
```

---

## 🔨 Implementation Steps

### Step 1: Update CashFlowPresenter for DataFrame Input (if needed)

**File**: `src/modules/accounting/presenters/cash_flow_presenter.py`

**Changes**:
```python
def process_clean_dataframe_and_generate_statements(self, dataframe: pd.DataFrame) -> Tuple[Dict, List]:
    """Process clean DataFrame and generate cash flow statements"""
    # Similar pattern to IncomeStatementPresenter
```

**Tests**: Test 2.1, 2.2

---

### Step 2: Integrate CashFlowGenerator into IncomeStatementPresenter

**File**: `src/modules/accounting/presenters/income_statement_presenter.py`

**Changes**:
```python
def process_clean_dataframe_and_generate_statements(self, dataframe: pd.DataFrame) -> Tuple[Dict, Dict, List]:
    """Generate BOTH income and cash flow statements"""
    # Existing income statement logic
    income_statements = ...

    # NEW: Generate cash flow statements from same transactions
    cash_flow_presenter = CashFlowPresenter()
    cashflow_statements = cash_flow_presenter.generate_from_transactions(transactions)

    return income_statements, cashflow_statements, users
```

**Tests**: Test 2.3, 2.4

---

### Step 3: Update View Layer to Display Both Statements

**File**: `src/modules/accounting/views/pages.py`

**Changes**:
```python
# Line 96: Update to receive both statements
income_statements, cashflow_statements, users = presenter.process_clean_dataframe_and_generate_statements(final_df)

# Display both statements side-by-side
col1, col2 = st.columns(2)
with col1:
    st.subheader("📊 Income Statement")
    display_income_statement(income_statements, selected_entity)

with col2:
    st.subheader("💰 Cash Flow Statement")
    display_cash_flow_statement(cashflow_statements, selected_entity)
```

**Tests**: Test 3.1, 3.2, 3.3, 3.4, 3.5

---

### Step 4: Create Cash Flow Display Component

**File**: `src/modules/accounting/views/components.py` (or new file)

**New Function**:
```python
def display_cash_flow_statement(cashflow_statements: Dict, entity: str):
    """Display formatted cash flow statement"""
    if entity not in cashflow_statements:
        st.warning(f"No cash flow data for {entity}")
        return

    statement = cashflow_statements[entity]

    # Operating Activities
    st.write("**Operating Activities**")
    for item, amount in statement['Operating Activities']['Details'].items():
        st.write(f"  {item}: ¥{amount:,.2f}")
    st.write(f"**Net Operating Cash Flow**: ¥{statement['Operating Activities']['Net Cash from Operating']:,.2f}")

    # Investing Activities
    st.write("**Investing Activities**")
    # ... similar pattern

    # Financing Activities
    st.write("**Financing Activities**")
    # ... similar pattern

    # Net Change
    st.write(f"**Net Change in Cash**: ¥{statement['Net Change in Cash']:,.2f}")
```

**Tests**: Test 3.3

---

### Step 5: Update Save Button Logic

**File**: `src/modules/accounting/views/pages.py`

**Changes**:
```python
# Replace existing "💾 Save Income Statement" button with:
if st.button("💾 Save Both Statements", type="primary", use_container_width=True):
    storage = MonthlyReportStorage()

    # Save income statements
    for entity, statement in income_statements.items():
        metadata = {
            "entity": entity,
            "generated_at": datetime.now().isoformat(),
            "source": "web_upload"
        }
        storage.save_statement(year_month, "income_statement", statement, metadata)

    # Save cash flow statements
    for entity, statement in cashflow_statements.items():
        metadata = {
            "entity": entity,
            "generated_at": datetime.now().isoformat(),
            "source": "web_upload"
        }
        storage.save_statement(year_month, "cash_flow", statement, metadata)

    st.success("✅ Both income and cash flow statements saved!")
```

**Tests**: Test 3.6, 4.4

---

### Step 6: Add Consistency Validation

**File**: `src/modules/accounting/views/pages.py`

**New Feature**:
```python
# Validate consistency
net_income = income_statements[selected_entity]['Net Income']
net_operating_cf = cashflow_statements[selected_entity]['Operating Activities']['Net Cash from Operating']

if abs(net_income - net_operating_cf) < 0.01:
    st.success(f"✅ Consistent: Net Income (¥{net_income:,.2f}) ≈ Net Operating Cash Flow (¥{net_operating_cf:,.2f})")
else:
    st.warning(f"⚠️ Discrepancy: Net Income (¥{net_income:,.2f}) vs Net Operating Cash Flow (¥{net_operating_cf:,.2f})")
```

**Tests**: Test 3.4

---

## 📊 Test Execution Order

### Phase 1: Red Phase (Write Failing Tests)
1. Write all Model Layer tests (1.1-1.10) → All FAIL
2. Write all Presenter Layer tests (2.1-2.4) → All FAIL
3. Create manual UI testing checklist (3.1-3.6)
4. Write Integration tests (4.1-4.4) → All FAIL

### Phase 2: Green Phase (Implement Code)
1. Implement Step 1 (CashFlowPresenter DataFrame input) → Tests 2.1, 2.2 PASS
2. Implement Step 2 (Presenter integration) → Tests 2.3, 2.4 PASS
3. Implement Step 3 (View updates) → Manual tests 3.1, 3.2, 3.5 PASS
4. Implement Step 4 (Display component) → Manual test 3.3 PASS
5. Implement Step 5 (Save button update) → Tests 3.6, 4.4 PASS
6. Implement Step 6 (Validation) → Manual test 3.4 PASS
7. Run integration tests → Tests 4.1-4.4 PASS

### Phase 3: Refactor Phase
1. Extract duplicate code into helper methods
2. Add type hints to all new methods
3. Add docstrings following Google style
4. Update workflow documentation
5. Final test run → All tests GREEN

---

## ✅ Definition of Done

**Functionality**:
- [ ] Single "📈 Generate Income Statement" button generates both statements automatically
- [ ] Both statements displayed side-by-side
- [ ] User selection dropdown updates both statements
- [ ] Consistency validation message shown
- [ ] Single "💾 Save Both Statements" button saves both to separate JSON files

**Testing**:
- [ ] All unit tests pass (30+ tests)
- [ ] All integration tests pass (4 tests)
- [ ] Manual UI checklist completed
- [ ] Test coverage > 95% for new code

**Code Quality**:
- [ ] All methods have type hints
- [ ] All public methods have docstrings
- [ ] No code duplication (DRY principle)
- [ ] Follows MVP architecture pattern
- [ ] Matches existing code style

**Documentation**:
- [ ] Workflow documentation updated
- [ ] Architecture documentation updated
- [ ] Inline comments for complex logic
- [ ] CHANGELOG.md updated