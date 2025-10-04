# Transaction Processing Workflow

## Overview
The Transaction Processing Workflow is a core component of the accounting module, responsible for transforming cleaned and validated raw transaction data into structured `Transaction` objects. This workflow classifies each transaction, extracts relevant details, and prepares the data for subsequent financial statement generation (Income Statement, Cash Flow Statement, and Balance Sheet).

## 🏗️ Architecture Overview (MVP Pattern)

This workflow primarily resides within the Model layer, specifically handled by the `TransactionProcessor` component. It receives input from the data cleaning and validation steps and provides output to the various financial statement generators.

```
src/modules/accounting/
├── models/                 # ALL business logic (Model layer)
│   ├── domain/            # Core entities and business rules
│   │   ├── transaction.py        # Transaction entity ⭐
│   │   ├── category.py           # CategoryMapper & category constants
│   │   └── statements.py         # Financial statement data structures
│   ├── business/          # Business logic implementations
│   │   ├── data_cleaner.py              # Data cleaning & validation
│   │   ├── transaction_processor.py      # CSV processing & transaction logic ⭐
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

## 📊 Transaction Processing Workflow Steps

This workflow takes the user-corrected DataFrame (from the Data Cleaning and Validation Workflow) and converts it into a list of rich `Transaction` objects.

### 1. **Input: User-Corrected DataFrame**

```
User-Corrected CSV → models/business/transaction_processor.py:TransactionProcessor
```
- **Source**: Output from the Data Cleaning and Validation Workflow (specifically, after user review and editing in the UI).
- **Purpose**: Provides a clean, validated, and semantically correct DataFrame as input for transaction processing.

### 2. **Load Transactions (Model Layer)**

```
DataFrame → models/business/transaction_processor.py:load_transactions() → List[Transaction]
```
- **File**: `models/business/transaction_processor.py`
- **Method**: `load_transactions(dataframe: pd.DataFrame)`
- **Purpose**: Iterates through each row of the input DataFrame and converts it into a `Transaction` domain object.
- **Key Operations**:
    - **Initialization**: Creates a `TransactionProcessor` instance, potentially with a DataFrame or CSV path.
    - **Iteration**: Loops through each record in the DataFrame.
    - **Object Creation**: For each record, it instantiates a `Transaction` object, populating its attributes (description, amount, debit, credit, user, date, etc.).

### 3. **Transaction Classification Logic (Model Layer)**

```
Transaction Data → models/business/transaction_processor.py:_determine_transaction_type_and_sign() → Classified Transaction
```
- **File**: `models/business/transaction_processor.py`
- **Method**: `_determine_transaction_type_and_sign(debit, credit, amount)`
- **Purpose**: This is the core business logic for classifying transactions into types (revenue, expense, prepaid asset, etc.) and ensuring the correct sign (`+` for income, `-` for expense/outflow) is applied to the amount.
- **Classification Rules**:
    - **Revenue**: Identified when the `Credit` account is a recognized revenue category (e.g., `工资收入`, `服务收入`). The amount is treated as positive.
    - **Reimbursement**: A special type of expense reduction. Detected when `Debit` is a cash account (e.g., `Cash`, `现金`) and `Credit` is an expense category. The amount is treated as negative to reduce total expenses.
    - **Prepaid Expense Creation**: When `Debit` is a prepaid asset account (e.g., `预付费用`) and `Credit` is a cash account. This transaction creates an asset and is typically excluded from current period income/expenses.
    - **Prepaid Expense Usage**: When `Debit` is an expense account and `Credit` is a prepaid asset account. This recognizes the expense as the prepaid asset is consumed.
    - **Regular Expense**: All other transactions where `Debit` is an expense category and `Credit` is a cash or liability account. The amount is treated as positive (for internal calculation, later converted to negative for cash flow).
- **Sign Preservation**: Crucially, this step ensures that the `amount` attribute within the `Transaction` object accurately reflects the nature of the cash flow (inflow vs. outflow) or impact on income/expense.

### 4. **Output: List of Transaction Objects**

```
List[Transaction] → Financial Statement Generators
```
- **Purpose**: The processed list of `Transaction` objects serves as the primary input for all subsequent financial statement generation processes.
- **Key Features of `Transaction` Objects**:
    - **Structured Data**: Each object encapsulates all details of a single transaction.
    - **Classified**: Includes `transaction_type` (e.g., 'revenue', 'expense', 'prepaid_asset').
    - **Correctly Signed Amounts**: Amounts are adjusted based on classification for accurate financial calculations.
    - **Multi-User Support**: Contains the `user` identifier for individual and combined reporting.

## 📝 Related Documentation

- **Data Cleaning and Validation Workflow**: `docs/04-development/data-cleaning-validation-workflow.md`
- **Income Statement Generation Workflow**: `docs/04-development/income-statement-generation-workflow.md`
- **Cash Flow Statement Generation Workflow**: `docs/04-development/cash-flow-statement-generation-workflow.md`
- **Balance Sheet Generation Workflow**: `docs/04-development/balance-sheet-generation-workflow.md`
- **Accounting Module README**: `data/accounting/README.md`

---

**Last Updated**: 2025-09-30
**Version**: 0.4.3 (Transaction Processing)
