import akshare as ak
import pandas as pd
import os
import argparse
from datetime import datetime
from src.app_logger import LOG
from src.config import ASSETS, PE_ASSETS

def get_data_range_info(df):
    """Extract data range information from DataFrame"""
    if df.empty:
        return None, None
    
    # Handle different date column names
    date_col = None
    for col in ['date', 'Date', '日期']:
        if col in df.columns:
            date_col = col
            break
    
    if date_col is None:
        return None, None
    
    # Convert to datetime if needed
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col])
    
    start_date = df[date_col].min()
    end_date = df[date_col].max()
    
    return start_date, end_date

def generate_filename(asset_name, data_type, start_date=None, end_date=None):
    """Generate filename with data range information"""
    if start_date and end_date:
        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')
        return f"{asset_name}_{data_type}_{start_str}_to_{end_str}.csv"
    else:
        return f"{asset_name}_{data_type}.csv"

def check_existing_data(asset_name, data_type, refresh=False):
    """Check if data file exists and is valid"""
    # Look for any existing file for this asset and data type
    data_dir = 'data'
    if not os.path.exists(data_dir):
        return False, None
    
    # Search for existing files with this asset name and data type
    pattern = f"{asset_name}_{data_type}_"
    existing_files = [f for f in os.listdir(data_dir) if f.startswith(pattern) and f.endswith('.csv')]
    
    if not existing_files:
        return False, None
    
    if refresh:
        return False, None
    
    # Use the most recent file (assuming it has the latest date range)
    existing_file = sorted(existing_files)[-1]
    filepath = os.path.join(data_dir, existing_file)
    
    try:
        df = pd.read_csv(filepath)
        if df.empty:
            return False, None
        
        # Check if file has expected columns
        expected_cols = ['date', 'close'] if 'close' in df.columns else ['日期', '收盘']
        if not all(col in df.columns for col in expected_cols):
            return False, None
        
        start_date, end_date = get_data_range_info(df)
        if start_date and end_date:
            LOG.info(f"Found existing data: {existing_file} ({start_date.date()} to {end_date.date()})")
            return True, (start_date, end_date, filepath)
        else:
            return False, None
            
    except Exception as e:
        LOG.warning(f"Error reading existing file {filepath}: {e}")
        return False, None

def download_akshare_index(symbol, asset_name, data_type="price"):
    """Download index data using akshare"""
    try:
        LOG.info(f"Downloading {asset_name} data via akshare...")
        df = ak.index_zh_a_hist(symbol=symbol, period="daily", start_date="20040101")
        
        if df.empty:
            raise ValueError(f"No data returned from akshare for {symbol}")
        
        # Standardize column names
        if '日期' in df.columns and '收盘' in df.columns:
            df = df.rename(columns={'日期': 'date', '收盘': 'close'})
        
        # Get data range
        start_date, end_date = get_data_range_info(df)
        
        # Generate filename
        filename = generate_filename(asset_name, data_type, start_date, end_date)
        filepath = os.path.join('data', filename)
        
        # Save data
        df[['date', 'close']].to_csv(filepath, index=False)
        LOG.info(f"Successfully downloaded {asset_name} via akshare: {filename}")
        
        return filepath, start_date, end_date
        
    except Exception as e:
        LOG.warning(f"Akshare download failed for {asset_name}: {e}")
        return None, None, None

def download_yfinance_data(ticker, asset_name, data_type="price"):
    """Download data using yfinance"""
    try:
        import yfinance as yf
        LOG.info(f"Downloading {asset_name} data via yfinance...")
        
        df = yf.download(ticker, start='2004-01-01')
        
        if df.empty:
            raise ValueError(f"No valid data returned from yfinance for {ticker}")
        
        # Handle MultiIndex columns (yfinance sometimes returns this structure)
        if isinstance(df.columns, pd.MultiIndex):
            # Flatten the MultiIndex columns
            new_columns = []
            for col in df.columns:
                if col[1] == '':
                    new_columns.append(col[0])
                else:
                    new_columns.append(f"{col[0]}_{col[1]}")
            df.columns = new_columns
        
        # Find the Close column (it might be named Close or Close_ticker)
        close_col = None
        for col in df.columns:
            if col.startswith('Close'):
                close_col = col
                break
        
        if close_col is None:
            raise ValueError(f"No 'Close' column found in data for {ticker}")
        
        # Standardize format
        df = df.reset_index()
        df = df.rename(columns={'Date': 'date', close_col: 'close'})
        
        # Clean up any empty rows or invalid data
        df = df.dropna(subset=['date', 'close'])
        df = df[df['close'] > 0]  # Remove zero or negative prices
        
        # Remove any rows where date is empty or contains ticker symbols
        df = df[df['date'].notna() & (df['date'] != ticker)]
        
        # Ensure we have the required columns
        if 'date' not in df.columns or 'close' not in df.columns:
            raise ValueError(f"Missing required columns 'date' or 'close' in data for {ticker}")
        
        # Get data range
        start_date, end_date = get_data_range_info(df)
        
        # Generate filename
        filename = generate_filename(asset_name, data_type, start_date, end_date)
        filepath = os.path.join('data', filename)
        
        # Save data - ensure we only save the required columns and clean data
        output_df = df[['date', 'close']].copy()
        # Convert close to numeric to ensure no string values
        output_df['close'] = pd.to_numeric(output_df['close'], errors='coerce')
        output_df = output_df.dropna()  # Remove any rows with NaN values
        
        if output_df.empty:
            raise ValueError(f"No valid numeric data after cleaning for {ticker}")
            
        output_df.to_csv(filepath, index=False)
        LOG.info(f"Successfully downloaded {asset_name} via yfinance: {filename}")
        
        return filepath, start_date, end_date
        
    except ImportError:
        LOG.error("yfinance not available")
        return None, None, None
    except Exception as e:
        LOG.warning(f"Yfinance download failed for {asset_name}: {e}")
        return None, None, None

def download_asset_data(asset_name, akshare_symbol=None, yfinance_ticker=None, data_type="price", refresh=False):
    """Download asset data with fallback strategy"""
    # Check if data already exists
    exists, date_range = check_existing_data(asset_name, data_type, refresh)
    if exists:
        return date_range[2], date_range[0], date_range[1]  # Return filepath, start_date, end_date
    
    # Try akshare first if symbol provided
    if akshare_symbol:
        filepath, start_date, end_date = download_akshare_index(akshare_symbol, asset_name, data_type)
        if filepath:
            return filepath, start_date, end_date
    
    # Fallback to yfinance if ticker provided
    if yfinance_ticker:
        filepath, start_date, end_date = download_yfinance_data(yfinance_ticker, asset_name, data_type)
        if filepath:
            return filepath, start_date, end_date
    
    # Both failed
    error_msg = f"Failed to download {asset_name} data from both akshare and yfinance"
    LOG.error(error_msg)
    raise ValueError(error_msg)

def download_pe_data(asset_name, akshare_symbol=None, yfinance_ticker=None, refresh=False):
    """Download PE ratio data with fallback strategy"""
    # Check if PE data already exists
    exists, date_range = check_existing_data(asset_name, "pe", refresh)
    if exists:
        return date_range[2], date_range[0], date_range[1]  # Return filepath, start_date, end_date
    
    try:
        # Try akshare PE data first
        if akshare_symbol:
            try:
                LOG.info(f"Downloading PE data for {asset_name} via akshare...")
                
                if asset_name in ['CSI300', 'CSI500']:
                    # Use A-share market PE data
                    if asset_name == 'CSI300':
                        pe_df = ak.stock_index_pe_lg()
                        if not pe_df.empty:
                            pe_df = pe_df.rename(columns={
                                '日期': 'date',
                                '静态市盈率': 'pe_ratio',
                                '等权静态市盈率': 'equal_weight_pe',
                                '静态市盈率中位数': 'median_pe'
                            })
                            pe_df = pe_df[['date', 'pe_ratio', 'equal_weight_pe', 'median_pe']]
                    else:  # CSI500
                        pe_df = ak.stock_market_pe_lg()
                        if not pe_df.empty:
                            pe_df = pe_df.rename(columns={
                                '日期': 'date',
                                '平均市盈率': 'avg_pe'
                            })
                            pe_df = pe_df[['date', 'avg_pe']]
                    
                    if not pe_df.empty:
                        start_date, end_date = get_data_range_info(pe_df)
                        filename = generate_filename(asset_name, "pe", start_date, end_date)
                        filepath = os.path.join('data', filename)
                        pe_df.to_csv(filepath, index=False)
                        LOG.info(f"Successfully downloaded {asset_name} PE data via akshare: {filename}")
                        return filepath, start_date, end_date
                
            except Exception as e:
                LOG.warning(f"Akshare PE download failed for {asset_name}: {e}")
        
        # Fallback to yfinance PE estimation
        if yfinance_ticker:
            try:
                import yfinance as yf
                LOG.info(f"Downloading PE data for {asset_name} via yfinance...")
                
                ticker_obj = yf.Ticker(yfinance_ticker)
                info = ticker_obj.info
                current_pe = info.get('trailingPE', 20.0)  # Default if not available
                
                hist_data = ticker_obj.history(period="max")
                if not hist_data.empty:
                    current_price = hist_data['Close'].iloc[-1]
                    hist_data['estimated_pe'] = (hist_data['Close'] / current_price) * current_pe
                    
                    pe_df = hist_data.reset_index()[['Date', 'estimated_pe']]
                    pe_df.columns = ['date', 'pe']
                    
                    start_date, end_date = get_data_range_info(pe_df)
                    filename = generate_filename(asset_name, "pe", start_date, end_date)
                    filepath = os.path.join('data', filename)
                    pe_df.to_csv(filepath, index=False)
                    LOG.info(f"Successfully downloaded {asset_name} PE data via yfinance: {filename}")
                    return filepath, start_date, end_date
                    
            except Exception as e:
                LOG.warning(f"Yfinance PE download failed for {asset_name}: {e}")
        
        # Both failed
        error_msg = f"Failed to download PE data for {asset_name} from both sources"
        LOG.error(error_msg)
        raise ValueError(error_msg)
        
    except Exception as e:
        LOG.error(f"Error downloading PE data for {asset_name}: {e}")
        raise

def main(refresh=False):
    """Main download function"""
    LOG.info("Starting data download process...")
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    downloaded_files = []
    
    # Download price data
    LOG.info("=== Downloading Price Data ===")
    for asset_name, config in ASSETS.items():
        try:
            filepath, start_date, end_date = download_asset_data(
                asset_name, 
                config['akshare'], 
                config['yfinance'], 
                "price", 
                refresh
            )
            downloaded_files.append((asset_name, filepath, start_date, end_date))
        except Exception as e:
            LOG.error(f"Failed to download {asset_name}: {e}")
    
    # Download PE data for assets that support it
    LOG.info("=== Downloading PE Data ===")
    for asset_name, config in PE_ASSETS.items():
        try:
            filepath, start_date, end_date = download_pe_data(
                asset_name,
                config['akshare'],
                config['yfinance'],
                refresh
            )
            downloaded_files.append((f"{asset_name}_PE", filepath, start_date, end_date))
        except Exception as e:
            LOG.error(f"Failed to download PE data for {asset_name}: {e}")
    
    # Summary
    LOG.info("=== Download Summary ===")
    if downloaded_files:
        LOG.info(f"Successfully downloaded {len(downloaded_files)} files:")
        for asset_name, filepath, start_date, end_date in downloaded_files:
            date_range = f" ({start_date.date()} to {end_date.date()})" if start_date and end_date else ""
            LOG.info(f"  {asset_name}: {os.path.basename(filepath)}{date_range}")
    else:
        LOG.warning("No files were downloaded successfully")
    
    LOG.info("Data download process completed")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download financial data for Personal Finance Agent')
    parser.add_argument('--refresh', action='store_true', 
                       help='Refresh existing data files (default: skip if exists)')
    args = parser.parse_args()
    
    main(refresh=args.refresh) 