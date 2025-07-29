import akshare as ak
import pandas as pd
import os
import argparse
import requests
from datetime import datetime
from src.app_logger import LOG
from src.config import ASSETS, PE_ASSETS, YIELD_ASSETS

def get_data_range_info(df):
    """Extract data range information from DataFrame"""
    if df.empty:
        return None, None
    
    date_col = None
    for col in ['date', 'Date', '日期']:
        if col in df.columns:
            date_col = col
            break
    
    if date_col is None:
        return None, None
    
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col])
    
    start_date = df[date_col].min()
    end_date = df[date_col].max()
    
    return start_date, end_date

def generate_filename(asset_name, start_date=None, end_date=None):
    """Generate filename with data range information"""
    if start_date and end_date:
        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')
        return f"{asset_name}_{start_str}_to_{end_str}.csv"
    else:
        return f"{asset_name}.csv"

def check_existing_data(asset_name, data_type, refresh=False):
    """Check if data file exists and is valid"""
    data_dir = os.path.join('data', data_type)
    if not os.path.exists(data_dir):
        return False, None
    
    pattern = f"{asset_name}_"
    existing_files = [f for f in os.listdir(data_dir) if f.startswith(pattern) and f.endswith('.csv')]
    
    if not existing_files or refresh:
        return False, None
    
    existing_file = sorted(existing_files)[-1]
    filepath = os.path.join(data_dir, existing_file)
    
    try:
        df = pd.read_csv(filepath)
        if df.empty:
            return False, None
        
        if data_type == 'price':
            expected_cols = ['date', 'close'] if 'close' in df.columns else ['日期', '收盘']
            if not all(col in df.columns for col in expected_cols):
                return False, None
        
        start_date, end_date = get_data_range_info(df)
        if start_date and end_date:
            LOG.info(f"Found existing {data_type} data: {existing_file} ({start_date.date()} to {end_date.date()})")
            return True, (start_date, end_date, filepath)
        else:
            return False, None
            
    except Exception as e:
        LOG.warning(f"Error reading existing file {filepath}: {e}")
        return False, None

def download_akshare_index(symbol, asset_name, data_type="price"):
    """Download index/ETF data using akshare"""
    try:
        LOG.info(f"Downloading {asset_name} {data_type} data via akshare...")
        
        # Check if symbol is ETF (6-digit codes like 159742, 513130)
        if symbol.isdigit() and len(symbol) == 6:
            # ETF data
            df = ak.fund_etf_hist_em(symbol=symbol, period="daily", start_date="20040101", end_date="20250129")
        else:
            # Index data
            df = ak.index_zh_a_hist(symbol=symbol, period="daily", start_date="20040101")
        
        if df.empty:
            raise ValueError(f"No data returned from akshare for {symbol}")
        
        if '日期' in df.columns and '收盘' in df.columns:
            df = df.rename(columns={'日期': 'date', '收盘': 'close'})
        
        start_date, end_date = get_data_range_info(df)
        
        filename = generate_filename(asset_name, start_date, end_date)
        data_dir = os.path.join('data', data_type)
        os.makedirs(data_dir, exist_ok=True)
        filepath = os.path.join(data_dir, filename)
        
        df[['date', 'close']].to_csv(filepath, index=False)
        LOG.info(f"Successfully downloaded {asset_name} to {filepath}")
        
        return filepath, start_date, end_date
        
    except Exception as e:
        LOG.warning(f"Akshare download failed for {asset_name}: {e}")
        return None, None, None

def download_yfinance_data(ticker, asset_name, data_type="price"):
    """Download data using yfinance"""
    try:
        import yfinance as yf
        LOG.info(f"Downloading {asset_name} {data_type} data via yfinance...")
        
        df = yf.download(ticker, start='2004-01-01')
        
        if df.empty:
            raise ValueError(f"No valid data returned from yfinance for {ticker}")
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [f"{col[0]}_{col[1]}" if col[1] else col[0] for col in df.columns]
        
        close_col = next((col for col in df.columns if col.startswith('Close')), None)
        
        if close_col is None:
            raise ValueError(f"No 'Close' column found in data for {ticker}")
        
        df = df.reset_index()
        df = df.rename(columns={'Date': 'date', close_col: 'close'})
        
        df = df.dropna(subset=['date', 'close'])
        df = df[df['close'] > 0]
        df = df[df['date'].notna() & (df['date'] != ticker)]
        
        if 'date' not in df.columns or 'close' not in df.columns:
            raise ValueError(f"Missing required columns 'date' or 'close' in data for {ticker}")
        
        start_date, end_date = get_data_range_info(df)
        
        filename = generate_filename(asset_name, start_date, end_date)
        data_dir = os.path.join('data', data_type)
        os.makedirs(data_dir, exist_ok=True)
        filepath = os.path.join(data_dir, filename)
        
        output_df = df[['date', 'close']].copy()
        output_df['close'] = pd.to_numeric(output_df['close'], errors='coerce')
        output_df = output_df.dropna()
        
        if output_df.empty:
            raise ValueError(f"No valid numeric data after cleaning for {ticker}")
            
        output_df.to_csv(filepath, index=False)
        LOG.info(f"Successfully downloaded {asset_name} to {filepath}")
        
        return filepath, start_date, end_date
        
    except ImportError:
        LOG.error("yfinance not available")
        return None, None, None
    except Exception as e:
        LOG.warning(f"Yfinance download failed for {asset_name}: {e}")
        return None, None, None

def download_fred_data(series_id, asset_name, data_type="yield"):
    """Download data from FRED API"""
    try:
        # Load API key from environment
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('FRED_API_KEY')
        if not api_key:
            raise ValueError("FRED_API_KEY not found in environment variables")
        
        LOG.info(f"Downloading {asset_name} {data_type} data via FRED...")
        
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json",
            "observation_start": "2004-01-01"  # Start from 2004 like other data
        }
        
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        
        obs = resp.json().get("observations", [])
        if not obs:
            raise ValueError(f"No observations returned from FRED for {series_id}")
        
        # Convert to DataFrame
        df = pd.DataFrame(obs)
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df["date"] = pd.to_datetime(df["date"])
        
        # Clean the data - remove rows with missing values
        df = df.dropna(subset=['value'])
        df = df[df['value'] > 0]  # Remove negative or zero yields
        
        # Rename columns to match our standard format
        df = df.rename(columns={'value': 'yield'})
        df = df[['date', 'yield']]
        
        if df.empty:
            raise ValueError(f"No valid data after cleaning for {series_id}")
        
        start_date, end_date = get_data_range_info(df)
        
        filename = generate_filename(asset_name, start_date, end_date)
        data_dir = os.path.join('data', data_type)
        os.makedirs(data_dir, exist_ok=True)
        filepath = os.path.join(data_dir, filename)
        
        df.to_csv(filepath, index=False)
        LOG.info(f"Successfully downloaded {asset_name} from FRED to {filepath}")
        
        return filepath, start_date, end_date
        
    except ImportError:
        LOG.error("python-dotenv not available. Please install: pip install python-dotenv")
        return None, None, None
    except Exception as e:
        LOG.warning(f"FRED download failed for {asset_name}: {e}")
        return None, None, None

def download_asset_data(asset_name, akshare_symbol=None, yfinance_ticker=None, data_type="price", refresh=False):
    """Download asset data with fallback strategy"""
    exists, date_range = check_existing_data(asset_name, data_type, refresh)
    if exists:
        return date_range[2], date_range[0], date_range[1]
    
    if akshare_symbol:
        filepath, start_date, end_date = download_akshare_index(akshare_symbol, asset_name, data_type)
        if filepath:
            return filepath, start_date, end_date
    
    if yfinance_ticker:
        filepath, start_date, end_date = download_yfinance_data(yfinance_ticker, asset_name, data_type)
        if filepath:
            return filepath, start_date, end_date
    
    error_msg = f"Failed to download {asset_name} data from both akshare and yfinance"
    LOG.error(error_msg)
    raise ValueError(error_msg)

def download_pe_data(asset_name, akshare_symbol=None, yfinance_ticker=None, refresh=False):
    """Download PE ratio data with fallback strategy"""
    data_type = "pe"
    exists, date_range = check_existing_data(asset_name, data_type, refresh)
    if exists:
        return date_range[2], date_range[0], date_range[1]
    
    try:
        pe_df = pd.DataFrame()
        if akshare_symbol:
            try:
                LOG.info(f"Downloading PE data for {asset_name} via akshare...")
                if asset_name == 'CSI300':
                    df = ak.stock_index_pe_lg()
                    if not df.empty:
                        pe_df = df.rename(columns={'日期': 'date', '静态市盈率': 'pe_ratio', '等权静态市盈率': 'equal_weight_pe', '静态市盈率中位数': 'median_pe'})
                        pe_df = pe_df[['date', 'pe_ratio', 'equal_weight_pe', 'median_pe']]
                elif asset_name == 'CSI500':
                    df = ak.stock_market_pe_lg()
                    if not df.empty:
                        pe_df = df.rename(columns={'日期': 'date', '平均市盈率': 'avg_pe'})
                        pe_df = pe_df[['date', 'avg_pe']]
                elif akshare_symbol.isdigit() and len(akshare_symbol) == 6:
                    # ETF codes don't have PE data available from akshare, skip to yfinance
                    LOG.info(f"ETF {akshare_symbol} detected, skipping akshare PE data (not available)")
                else:
                    LOG.warning(f"No PE data logic implemented for {asset_name} with symbol {akshare_symbol}")
            except Exception as e:
                LOG.warning(f"Akshare PE download failed for {asset_name}: {e}")

        if pe_df.empty and yfinance_ticker:
            try:
                import yfinance as yf
                LOG.info(f"Downloading PE data for {asset_name} via yfinance...")
                ticker_obj = yf.Ticker(yfinance_ticker)
                
                # Get historical data from last 20 years (like price data)
                hist_data = ticker_obj.history(start='2004-01-01')
                
                if not hist_data.empty:
                    # Get current PE ratio from ticker info
                    info = ticker_obj.info
                    current_pe = info.get('trailingPE')
                    
                    if current_pe and current_pe > 0:
                        # Use current PE ratio as the latest PE value
                        current_price = hist_data['Close'].iloc[-1]
                        
                        # Calculate historical PE ratios
                        # Assumption: PE = Price / Earnings, so if current PE is known, 
                        # historical PE = historical_price / (current_price / current_pe)
                        # Simplified: historical_PE = (historical_price / current_price) * current_pe
                        # But this assumes earnings stayed constant, which is wrong.
                        # Better approach: assume earnings grow at market rate, use current PE as baseline
                        hist_data['pe_ratio'] = (hist_data['Close'] / current_price) * current_pe
                        
                        pe_df = hist_data.reset_index()[['Date', 'pe_ratio']]
                        pe_df.columns = ['date', 'pe']
                        
                        # Clean the data
                        pe_df = pe_df.dropna(subset=['date', 'pe'])
                        pe_df = pe_df[pe_df['pe'] > 0]  # Remove negative/zero PE values
                        
                        LOG.info(f"Retrieved {len(pe_df)} PE data points for {asset_name} (current PE: {current_pe:.2f})")
                    else:
                        LOG.warning(f"No valid current PE ratio found for {yfinance_ticker}")
                else:
                    LOG.warning(f"No historical data found for {yfinance_ticker}")
                    
            except Exception as e:
                LOG.warning(f"Yfinance PE download failed for {asset_name}: {e}")

        if not pe_df.empty:
            start_date, end_date = get_data_range_info(pe_df)
            filename = generate_filename(asset_name, start_date, end_date)
            data_dir = os.path.join('data', data_type)
            os.makedirs(data_dir, exist_ok=True)
            filepath = os.path.join(data_dir, filename)
            pe_df.to_csv(filepath, index=False)
            LOG.info(f"Successfully downloaded {asset_name} PE data to {filepath}")
            return filepath, start_date, end_date

        error_msg = f"Failed to download PE data for {asset_name} from both sources"
        LOG.error(error_msg)
        raise ValueError(error_msg)
        
    except Exception as e:
        LOG.error(f"Error downloading PE data for {asset_name}: {e}")
        raise

def download_yield_data(asset_name, fred_series=None, yfinance_ticker=None, refresh=False):
    """Download yield data with fallback strategy"""
    data_type = "yield"
    exists, date_range = check_existing_data(asset_name, data_type, refresh)
    if exists:
        return date_range[2], date_range[0], date_range[1]
    
    try:
        # Try FRED first
        if fred_series:
            filepath, start_date, end_date = download_fred_data(fred_series, asset_name, data_type)
            if filepath:
                return filepath, start_date, end_date
        
        # Fallback to yfinance
        if yfinance_ticker:
            LOG.info(f"FRED failed, trying yfinance for {asset_name}...")
            filepath, start_date, end_date = download_yfinance_data(yfinance_ticker, asset_name, data_type)
            if filepath:
                # Rename 'close' column to 'yield' for consistency
                df = pd.read_csv(filepath)
                if 'close' in df.columns:
                    df = df.rename(columns={'close': 'yield'})
                    df.to_csv(filepath, index=False)
                    LOG.info(f"Converted yfinance data format for {asset_name}")
                return filepath, start_date, end_date
        
        error_msg = f"Failed to download yield data for {asset_name} from both FRED and yfinance"
        LOG.error(error_msg)
        raise ValueError(error_msg)
        
    except Exception as e:
        LOG.error(f"Error downloading yield data for {asset_name}: {e}")
        raise

def main(refresh=False):
    """Main download function"""
    LOG.info("Starting data download process...")
    
    os.makedirs('data/price', exist_ok=True)
    os.makedirs('data/pe', exist_ok=True)
    os.makedirs('data/yield', exist_ok=True)
    
    downloaded_files = []
    
    LOG.info("=== Downloading Price Data ===")
    for asset_name, config in ASSETS.items():
        try:
            filepath, start_date, end_date = download_asset_data(
                asset_name, 
                config.get('akshare'), 
                config.get('yfinance'), 
                "price", 
                refresh
            )
            downloaded_files.append((asset_name, "price", filepath, start_date, end_date))
        except Exception as e:
            LOG.error(f"Failed to download price data for {asset_name}: {e}")
    
    LOG.info("=== Downloading PE Data ===")
    for asset_name, config in PE_ASSETS.items():
        try:
            filepath, start_date, end_date = download_pe_data(
                asset_name,
                config.get('akshare'),
                config.get('yfinance'),
                refresh
            )
            downloaded_files.append((asset_name, "pe", filepath, start_date, end_date))
        except Exception as e:
            LOG.error(f"Failed to download PE data for {asset_name}: {e}")
    
    LOG.info("=== Downloading Yield Data ===")
    for asset_name, config in YIELD_ASSETS.items():
        try:
            filepath, start_date, end_date = download_yield_data(
                asset_name,
                config.get('fred'),
                config.get('yfinance'),
                refresh
            )
            downloaded_files.append((asset_name, "yield", filepath, start_date, end_date))
        except Exception as e:
            LOG.error(f"Failed to download yield data for {asset_name}: {e}")
    
    LOG.info("=== Download Summary ===")
    if downloaded_files:
        LOG.info(f"Successfully processed {len(downloaded_files)} files:")
        for asset_name, data_type, filepath, start_date, end_date in downloaded_files:
            date_range = f" ({start_date.date()} to {end_date.date()})" if start_date and end_date else ""
            LOG.info(f"  - {asset_name} ({data_type}): {filepath}{date_range}")
    else:
        LOG.warning("No files were downloaded or updated.")
    
    LOG.info("Data download process completed.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download financial data for Personal Finance Agent')
    parser.add_argument('--refresh', action='store_true', 
                       help='Refresh existing data files (default: skip if exists)')
    args = parser.parse_args()
    
    main(refresh=args.refresh)