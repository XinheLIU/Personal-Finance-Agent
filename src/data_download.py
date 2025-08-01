import akshare as ak
import pandas as pd
import os
import argparse
import requests
import glob
from datetime import datetime
from src.app_logger import LOG
from src.config import ASSETS, PE_ASSETS, YIELD_ASSETS, INDEX_ASSETS

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

def parse_manual_pe_date(date_str, asset_name):
    """Parse date strings from different manual P/E file formats"""
    try:
        if asset_name in ['HSI', 'HSTECH']:
            # Format: "Dec 2021" -> convert to end of month
            date_obj = pd.to_datetime(date_str, format='%b %Y')
            # Convert to end of month for consistency
            return date_obj + pd.offsets.MonthEnd(0)
        elif asset_name == 'SP500':
            # Format: "2025/03/01" -> first day of month, convert to end of month
            date_obj = pd.to_datetime(date_str, format='%Y/%m/%d')
            return date_obj + pd.offsets.MonthEnd(0)
        elif asset_name == 'NASDAQ100':
            # Format: "2024/12/31" -> already end of month
            return pd.to_datetime(date_str, format='%Y/%m/%d')
        else:
            # Try general parsing
            return pd.to_datetime(date_str)
    except Exception as e:
        LOG.warning(f"Failed to parse date '{date_str}' for {asset_name}: {e}")
        return None

def find_manual_pe_files(manual_file_pattern):
    """Find manual P/E files matching the pattern (.xlsx or .csv)"""
    # Look in data/pe directory and project root
    search_paths = ['data/pe/', './']
    found_files = []
    
    for search_path in search_paths:
        # Look for both Excel and CSV files
        for extension in ['.xlsx', '.csv']:
            pattern = os.path.join(search_path, f"{manual_file_pattern}*{extension}")
            files = glob.glob(pattern)
            found_files.extend(files)
    
    if found_files:
        # Return the most recent file (assuming date suffix in filename)
        return sorted(found_files)[-1]
    return None

def process_manual_pe_file(filepath, asset_name):
    """Process and reformat manual P/E file to standard format (CSV or Excel)"""
    try:
        LOG.info(f"Processing manual P/E file for {asset_name}: {filepath}")
        
        # Read the file (Excel or CSV)
        if filepath.endswith('.xlsx'):
            try:
                # Try reading Excel file with openpyxl engine (required for .xlsx)
                df = pd.read_excel(filepath, sheet_name=0, engine='openpyxl')
                LOG.info(f"Reading Excel file: {filepath}")
            except Exception as excel_error:
                LOG.warning(f"Failed to read Excel file {filepath} with openpyxl: {excel_error}")
                # Try reading with different approaches
                try:
                    # First try without specifying sheet
                    df = pd.read_excel(filepath, engine='openpyxl')
                    LOG.info(f"Successfully read Excel file using default sheet: {filepath}")
                except Exception as fallback_error:
                    try:
                        # Try with xlsxwriter engine as last resort
                        df = pd.read_excel(filepath)
                        LOG.info(f"Successfully read Excel file with default engine: {filepath}")
                    except Exception as final_error:
                        raise ValueError(f"Cannot read Excel file {filepath}. Tried openpyxl and default engines. "
                                       f"Original error: {excel_error}. Final error: {final_error}. "
                                       f"Please ensure the file is a valid Excel file and openpyxl is installed.")
        elif filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
            LOG.info(f"Reading CSV file: {filepath}")
        else:
            raise ValueError(f"Unsupported file format: {filepath}. Only .xlsx and .csv are supported.")
        
        # Handle different column formats based on asset
        if asset_name in ['HSI', 'HSTECH']:
            # Format: Date, Value (where Value is P/E ratio)
            if 'Date' in df.columns and 'Value' in df.columns:
                df = df.rename(columns={'Date': 'date', 'Value': 'pe_ratio'})
            else:
                raise ValueError(f"Expected columns 'Date' and 'Value' not found in {filepath}")
                
        elif asset_name == 'SP500':
            # Format: Date, Value (where Value is P/E ratio) - handle both capitalized and lowercase
            date_col = None
            value_col = None
            
            # Find date column (case insensitive)
            for col in df.columns:
                if col.strip().lower() == 'date':
                    date_col = col
                    break
            
            # Find value column (case insensitive)  
            for col in df.columns:
                if col.strip().lower() == 'value':
                    value_col = col
                    break
            
            if date_col and value_col:
                df = df.rename(columns={date_col: 'date', value_col: 'pe_ratio'})
            else:
                raise ValueError(f"Expected columns 'Date/date' and 'Value/value' not found in {filepath}. Found: {list(df.columns)}")
                
        elif asset_name == 'NASDAQ100':
            # Format: Date, Price, PE Ratio
            if 'Date' in df.columns and 'PE Ratio' in df.columns:
                df = df.rename(columns={'Date': 'date', 'PE Ratio': 'pe_ratio'})
                df = df[['date', 'pe_ratio']]  # Keep only date and PE ratio
            else:
                raise ValueError(f"Expected columns 'Date' and 'PE Ratio' not found in {filepath}")
        
        # Parse dates using asset-specific format
        df['date'] = df['date'].apply(lambda x: parse_manual_pe_date(x, asset_name))
        
        # Remove rows with invalid dates
        df = df.dropna(subset=['date'])
        
        # Convert PE ratio to numeric first (this handles "--" and other non-numeric values)
        df['pe_ratio'] = pd.to_numeric(df['pe_ratio'], errors='coerce')
        
        # Remove rows with invalid PE ratios (NaN, negative, or zero)
        df = df.dropna(subset=['pe_ratio'])
        df = df[df['pe_ratio'] > 0]
        
        # Sort by date
        df = df.sort_values('date')
        
        if df.empty:
            raise ValueError(f"No valid data after processing {filepath}")
        
        LOG.info(f"Processed {len(df)} P/E data points for {asset_name}")
        return df
        
    except Exception as e:
        LOG.error(f"Error processing manual P/E file {filepath}: {e}")
        raise

def fill_pe_data_to_recent(pe_df, asset_name, target_date=None):
    """
    Fill P/E data from manual file to recent date using fallback methods:
    1. Try Yahoo Finance for recent P/E data
    2. If Yahoo fails, use price data with earnings assumption
    """
    if target_date is None:
        target_date = pd.Timestamp.now()
    else:
        target_date = pd.to_datetime(target_date)
    
    if pe_df.empty:
        LOG.error(f"Cannot fill empty P/E data for {asset_name}")
        return pe_df
    
    # Get the latest date in manual data
    latest_manual_date = pe_df['date'].max()
    LOG.info(f"Manual P/E data for {asset_name} ends on: {latest_manual_date.date()}")
    
    # Check if we need to fill to recent date (if manual data is older than 2 months)
    months_gap = (target_date - latest_manual_date).days / 30
    if months_gap < 2:
        LOG.info(f"Manual P/E data for {asset_name} is recent enough ({months_gap:.1f} months old)")
        return pe_df
    
    LOG.info(f"Need to fill P/E data for {asset_name} from {latest_manual_date.date()} to recent date")
    
    # Get the asset configuration for fallback data sources
    # Use INDEX_ASSETS for PE data since PE ratios come from indices, not ETFs
    from src.config import INDEX_ASSETS
    asset_config = INDEX_ASSETS.get(asset_name, {})
    yfinance_ticker = asset_config.get('yfinance')
    
    # Attempt 1: Try Yahoo Finance for recent P/E data
    recent_pe_data = None
    if yfinance_ticker:
        LOG.info(f"Attempting to fill {asset_name} P/E data using Yahoo Finance ticker: {yfinance_ticker}")
        recent_pe_data = get_recent_pe_from_yfinance(yfinance_ticker, latest_manual_date, target_date)
    
    # Attempt 2: If Yahoo fails, use price-based estimation
    if recent_pe_data is None or recent_pe_data.empty:
        LOG.warning(f"Yahoo Finance P/E data failed for {asset_name}, trying price-based estimation")
        recent_pe_data = estimate_recent_pe_from_price(asset_name, yfinance_ticker, pe_df, latest_manual_date, target_date)
    
    # Combine manual data with recent data
    if recent_pe_data is not None and not recent_pe_data.empty:
        # Filter out overlapping dates to avoid duplicates
        recent_pe_data = recent_pe_data[recent_pe_data['date'] > latest_manual_date]
        if not recent_pe_data.empty:
            combined_df = pd.concat([pe_df, recent_pe_data], ignore_index=True)
            combined_df = combined_df.sort_values('date')
            LOG.info(f"Successfully filled {asset_name} P/E data with {len(recent_pe_data)} additional data points")
            return combined_df
        else:
            LOG.info(f"No additional recent P/E data found for {asset_name}")
    else:
        LOG.warning(f"Failed to obtain recent P/E data for {asset_name} using all fallback methods")
    
    return pe_df

def get_recent_pe_from_yfinance(ticker, start_date, end_date):
    """Get recent P/E data from Yahoo Finance"""
    try:
        import yfinance as yf
        LOG.info(f"Downloading recent P/E data from Yahoo Finance for {ticker}")
        
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        current_pe = info.get('trailingPE')
        
        if current_pe and current_pe > 0:
            # Create a single data point with current P/E
            recent_data = pd.DataFrame({
                'date': [pd.Timestamp.now().normalize()],
                'pe_ratio': [current_pe]
            })
            LOG.info(f"Retrieved current P/E from Yahoo Finance for {ticker}: {current_pe:.2f}")
            return recent_data
        else:
            LOG.warning(f"No valid trailing P/E found in Yahoo Finance for {ticker}")
            return None
            
    except Exception as e:
        LOG.warning(f"Yahoo Finance P/E retrieval failed for {ticker}: {e}")
        return None

def estimate_recent_pe_from_price(asset_name, ticker, historical_pe_df, start_date, end_date):
    """Estimate recent P/E using price data and earnings assumption"""
    try:
        if not ticker:
            LOG.warning(f"No ticker available for price-based P/E estimation for {asset_name}")
            return None
            
        import yfinance as yf
        LOG.info(f"Attempting price-based P/E estimation for {asset_name} using ticker {ticker}")
        
        # Get recent price data
        ticker_obj = yf.Ticker(ticker)
        price_data = ticker_obj.history(start=start_date, end=end_date)
        
        if price_data.empty:
            LOG.warning(f"No recent price data available for {ticker}")
            return None
        
        # Get the latest P/E ratio from manual data to use as baseline
        if historical_pe_df.empty:
            LOG.warning(f"No historical P/E data available for baseline estimation")
            return None
            
        latest_manual_pe = historical_pe_df['pe_ratio'].iloc[-1]
        latest_manual_date = historical_pe_df['date'].iloc[-1]
        
        # Find price around the latest manual P/E date (within 30 days)
        price_data.index = price_data.index.tz_localize(None)  # Remove timezone for comparison
        baseline_date = pd.to_datetime(latest_manual_date)
        
        # Get price near the baseline date
        date_range_start = baseline_date - pd.Timedelta(days=15)
        date_range_end = baseline_date + pd.Timedelta(days=15)
        baseline_prices = price_data.loc[date_range_start:date_range_end]
        
        if baseline_prices.empty:
            LOG.warning(f"No price data available around baseline date {baseline_date.date()} for {ticker}")
            return None
            
        baseline_price = baseline_prices['Close'].mean()  # Use average price around baseline date
        
        # Estimate P/E for recent dates assuming earnings unchanged
        # PE_new = PE_old * (Price_new / Price_old)
        recent_pe_data = []
        
        for date, row in price_data.iterrows():
            if date > baseline_date:
                current_price = row['Close']
                estimated_pe = latest_manual_pe * (current_price / baseline_price)
                recent_pe_data.append({
                    'date': date,
                    'pe_ratio': estimated_pe
                })
        
        if recent_pe_data:
            estimated_df = pd.DataFrame(recent_pe_data)
            LOG.info(f"Estimated {len(estimated_df)} P/E data points for {asset_name} using price-based method")
            LOG.info(f"Baseline: P/E={latest_manual_pe:.2f} at price=${baseline_price:.2f} on {baseline_date.date()}")
            LOG.info(f"Latest estimate: P/E={estimated_df['pe_ratio'].iloc[-1]:.2f} (assumes earnings unchanged)")
            return estimated_df
        else:
            LOG.warning(f"No recent price data found after baseline date for {asset_name}")
            return None
            
    except Exception as e:
        LOG.warning(f"Price-based P/E estimation failed for {asset_name}: {e}")
        return None

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

def download_pe_data(asset_name, akshare_symbol=None, manual_file_pattern=None, refresh=False):
    """Download PE ratio data using manual files or akshare"""
    data_type = "pe"
    exists, date_range = check_existing_data(asset_name, data_type, refresh)
    if exists:
        return date_range[2], date_range[0], date_range[1]
    
    try:
        pe_df = pd.DataFrame()
        
        # Try manual file first (for HSI, HSTECH, SP500, NASDAQ100)
        if manual_file_pattern:
            manual_file = find_manual_pe_files(manual_file_pattern)
            if manual_file:
                # Process manual file and standardize format
                pe_df = process_manual_pe_file(manual_file, asset_name)
                # Fill to recent date using fallback methods
                pe_df = fill_pe_data_to_recent(pe_df, asset_name)
            else:
                raise FileNotFoundError(f"Manual P/E file not found for {asset_name}. "
                                      f"Please download '{manual_file_pattern}*.csv' file "
                                      f"and place it in data/pe/ or project root directory.")
        
        # Try akshare (for CSI300, CSI500)
        elif akshare_symbol:
            try:
                LOG.info(f"Downloading PE data for {asset_name} via akshare...")
                if asset_name == 'CSI300':
                    df = ak.stock_index_pe_lg()
                    if not df.empty:
                        pe_df = df.rename(columns={'日期': 'date', '静态市盈率': 'pe_ratio', '等权静态市盈率': 'equal_weight_pe', '静态市盈率中位数': 'median_pe'})
                        pe_df = pe_df[['date', 'pe_ratio', 'equal_weight_pe', 'median_pe']]
                        pe_df['date'] = pd.to_datetime(pe_df['date'])
                elif asset_name == 'CSI500':
                    df = ak.stock_market_pe_lg()
                    if not df.empty:
                        pe_df = df.rename(columns={'日期': 'date', '平均市盈率': 'pe_ratio'})
                        pe_df = pe_df[['date', 'pe_ratio']]
                        pe_df['date'] = pd.to_datetime(pe_df['date'])
                else:
                    LOG.warning(f"No akshare PE data logic implemented for {asset_name}")
                
                # Clean akshare data
                if not pe_df.empty:
                    pe_df = pe_df.dropna(subset=['date', 'pe_ratio'])
                    pe_df = pe_df[pe_df['pe_ratio'] > 0]
                    pe_df = pe_df.sort_values('date')
                    
            except Exception as e:
                LOG.warning(f"Akshare PE download failed for {asset_name}: {e}")

        if not pe_df.empty:
            start_date, end_date = get_data_range_info(pe_df)
            filename = generate_filename(asset_name, start_date, end_date)
            data_dir = os.path.join('data', data_type)
            os.makedirs(data_dir, exist_ok=True)
            filepath = os.path.join(data_dir, filename)
            pe_df.to_csv(filepath, index=False)
            LOG.info(f"Successfully processed {asset_name} PE data to {filepath}")
            return filepath, start_date, end_date

        error_msg = f"Failed to download PE data for {asset_name}. "
        if manual_file_pattern:
            error_msg += f"Manual file '{manual_file_pattern}*.csv' not found."
        else:
            error_msg += "Akshare download failed."
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
                config.get('manual_file'),
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