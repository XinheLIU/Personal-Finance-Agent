import yfinance as yf
import pandas as pd

# Test yfinance download
ticker = '^GSPC'
print(f"Downloading {ticker}...")

df = yf.download(ticker, start='2004-01-01')
print(f"Raw data shape: {df.shape}")
print(f"Columns type: {type(df.columns)}")
print(f"Columns: {df.columns.tolist()}")
print(f"First few rows:")
print(df.head())

# Handle MultiIndex columns
if isinstance(df.columns, pd.MultiIndex):
    print(f"\nMultiIndex columns detected:")
    print(f"Column levels: {df.columns.levels}")
    print(f"Column names: {df.columns.names}")
    
    # Flatten the MultiIndex columns
    new_columns = []
    for col in df.columns:
        if col[1] == '':
            new_columns.append(col[0])
        else:
            new_columns.append(f"{col[0]}_{col[1]}")
    
    df.columns = new_columns
    print(f"\nAfter flattening MultiIndex:")
    print(f"New columns: {df.columns.tolist()}")

# Reset index
df = df.reset_index()
print(f"\nAfter reset_index:")
print(f"Columns: {df.columns.tolist()}")
print(df.head())

# Rename columns
df = df.rename(columns={'Date': 'date', 'Close': 'close'})
print(f"\nAfter rename:")
print(f"Columns: {df.columns.tolist()}")
print(df.head())

# Check for any string values in close column
print(f"\nClose column dtype: {df['close'].dtype}")
print(f"Sample close values: {df['close'].head().tolist()}")

# Check for any non-numeric values
non_numeric = df[~pd.to_numeric(df['close'], errors='coerce').notna()]
print(f"\nNon-numeric rows: {len(non_numeric)}")
if len(non_numeric) > 0:
    print(non_numeric) 