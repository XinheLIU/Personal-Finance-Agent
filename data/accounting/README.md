# Accounting Data Directory

This directory contains CSV files for the Professional Accounting Module.

## File Structure

```
data/accounting/
├── transactions.csv    # Monthly transaction data
├── assets.csv         # Asset balance snapshots (optional)
└── statements/        # Generated financial statements
    └── income_statement_YYYY-MM.csv
```

## File Formats

### transactions.csv
```csv
date,description,amount,category,account_name,account_type,notes
2025-01-15,餐饮,-68.50,food_dining,招商银行卡,checking,晚饭
```

Required columns:
- `date`: YYYY-MM-DD format
- `description`: Transaction description (Chinese/English)
- `amount`: Decimal amount (negative for expenses, positive for income)  
- `category`: Must match predefined category taxonomy
- `account_name`: Account identifier
- `account_type`: checking, savings, credit, investment
- `notes`: Optional notes

### assets.csv (Optional)
```csv
as_of_date,account_name,balance,account_type,currency
2025-01-31,招商银行卡,12000.00,checking,CNY
```

Required columns:
- `as_of_date`: YYYY-MM-DD format
- `account_name`: Account identifier
- `balance`: Current balance (can be negative)
- `account_type`: checking, savings, investment, retirement
- `currency`: Always CNY

## Usage

1. **Manual Data Entry**: Create/edit the CSV files directly
2. **Import via Streamlit**: Use the web interface to upload CSV files
3. **Generate Statements**: Use CLI or web interface to generate income statements

## CLI Commands

```bash
# Generate monthly income statement
python -m src.main --mode accounting --generate-income-statement --period 2025-01

# List available periods
python -m src.main --mode accounting --status
```

## Data Validation

- All amounts in Chinese Yuan (¥)
- UTF-8 encoding required for Chinese text
- Date format must be YYYY-MM-DD
- Categories must match predefined taxonomy
- File sizes limited to reasonable amounts for CSV processing

## Generated Statements

Income statements are automatically saved to `statements/` directory with filename format:
- `income_statement_YYYY-MM.csv` for monthly statements
- `income_statement_YTD_YYYY.csv` for year-to-date statements