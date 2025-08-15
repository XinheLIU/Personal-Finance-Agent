import akshare as ak
import pandas as pd
import os
import argparse
import requests
import glob
from datetime import datetime
from src.app_logger import LOG
from config import ASSETS, PE_ASSETS, YIELD_ASSETS, INDEX_ASSETS

# The entire content is moved from src/data_download.py unchanged
# to centralize data ops in data_center.

def get_data_range_info(df):
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

# Simplified singleton storage functions
def _merge_with_existing_and_save_singleton(dir_path, asset_name, data_type, df, date_col='date'):
    """
    SIMPLIFIED STORAGE: One file per asset-datatype combination.
    Merge newly downloaded data with existing singleton file, preserving older data
    and updating overlapping periods with newest data.
    
    File naming: {asset_name}_{data_type}.csv (e.g., SP500_price.csv, CSI300_pe.csv)
    """
    try:
        os.makedirs(dir_path, exist_ok=True)
        
        # Normalize date column name
        if date_col not in df.columns:
            if 'Date' in df.columns:
                df = df.rename(columns={'Date': 'date'})
            elif '日期' in df.columns:
                df = df.rename(columns={'日期': 'date'})
        
        # Ensure datetime type
        if not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])
        
        # Singleton file path
        singleton_file = os.path.join(dir_path, f"{asset_name}_{data_type}.csv")
        
        # Check if singleton file exists
        if os.path.exists(singleton_file):
            try:
                # Load existing data
                existing_df = pd.read_csv(singleton_file)
                
                # Normalize existing data date column
                if 'date' not in existing_df.columns:
                    if 'Date' in existing_df.columns:
                        existing_df = existing_df.rename(columns={'Date': 'date'})
                    elif '日期' in existing_df.columns:
                        existing_df = existing_df.rename(columns={'日期': 'date'})
                
                if not pd.api.types.is_datetime64_any_dtype(existing_df['date']):
                    existing_df['date'] = pd.to_datetime(existing_df['date'])
                
                # Merge: combine existing and new data
                merged = pd.concat([existing_df, df], ignore_index=True)
                # Remove duplicates by date, keeping the latest (new data wins)
                merged = merged.sort_values('date')
                merged = merged.drop_duplicates(subset=['date'], keep='last')
                merged = merged.sort_values('date').reset_index(drop=True)
                
                # Log merge statistics
                old_count = len(existing_df)
                new_count = len(df)
                final_count = len(merged)
                LOG.info(f"Merged {asset_name}_{data_type}: {old_count} existing + {new_count} new = {final_count} total records")
                
            except Exception as e:
                LOG.warning(f"Failed to read existing {singleton_file}, using new data only: {e}")
                merged = df.copy()
        else:
            # No existing file, use new data as is
            merged = df.copy()
            LOG.info(f"Created new singleton file for {asset_name}_{data_type}: {len(merged)} records")
        
        # Save to singleton file
        merged.to_csv(singleton_file, index=False)
        
        # Get date range for logging
        start_date = merged['date'].min().strftime('%Y-%m-%d')
        end_date = merged['date'].max().strftime('%Y-%m-%d')
        
        LOG.info(f"Saved {asset_name}_{data_type}.csv: {len(merged)} records ({start_date} to {end_date})")
        return singleton_file, start_date, end_date
        
    except Exception as e:
        LOG.error(f"Failed to save singleton {asset_name}_{data_type}: {e}")
        return None, None, None


def download_yfinance_data(ticker, asset_name):
    """Download price data from Yahoo Finance"""
    try:
        import yfinance as yf
        
        LOG.info(f"Downloading {asset_name} data from Yahoo Finance (ticker: {ticker})")
        
        # Download data with maximum history
        ticker_obj = yf.Ticker(ticker)
        data = ticker_obj.history(period="max")
        
        if data.empty:
            LOG.warning(f"No data received for {ticker}")
            return None, None, None
        
        # Ensure date column
        data.reset_index(inplace=True)
        data.rename(columns={'Date': 'date'}, inplace=True)
        
        # Merge with existing and save consolidated
        price_dir = 'data/raw/price'
        filepath, start_date, end_date = _merge_with_existing_and_save_singleton(price_dir, asset_name, 'price', data, 'date')
        return filepath, start_date, end_date
        
    except Exception as e:
        LOG.error(f"Error downloading {asset_name} from Yahoo Finance: {e}")
        return None, None, None

def download_akshare_index(symbol, asset_name):
    """Download index/ETF data from akshare"""
    try:
        LOG.info(f"Downloading {asset_name} data from akshare (symbol: {symbol})")
        
        # Choose the right function based on symbol pattern
        if symbol.startswith('51') and len(symbol) == 6:  # ETF symbols like 510300, 510500
            # Use ETF function for 6-digit symbols starting with 51
            from datetime import date, timedelta
            end_date = date.today().strftime('%Y%m%d')
            start_date = '20050101'  # Get maximum historical data
            data = ak.fund_etf_hist_em(symbol=symbol, period='daily', start_date=start_date, end_date=end_date)
        else:
            # Use stock function for other symbols
            data = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
        
        if data is None or data.empty:
            LOG.warning(f"No data received for {symbol}")
            return None, None, None
        
        # Standardize column names
        data.reset_index(inplace=True, drop=True)
        if '日期' in data.columns:
            data.rename(columns={'日期': 'date'}, inplace=True)
        
        # Convert date column to datetime
        data['date'] = pd.to_datetime(data['date'])
        
        # Merge with existing and save consolidated
        price_dir = 'data/raw/price'
        filepath, start_date, end_date = _merge_with_existing_and_save_singleton(price_dir, asset_name, 'price', data, 'date')
        return filepath, start_date, end_date
        
    except Exception as e:
        LOG.error(f"Error downloading {asset_name} from akshare: {e}")
        return None, None, None

def download_all_assets(refresh=False):
    """Download data for all configured assets"""
    LOG.info("Starting comprehensive data download...")
    
    successful_downloads = 0
    failed_downloads = 0
    
    # Download price data for all tradable assets
    for asset_name, config in ASSETS.items():
        LOG.info(f"Processing {asset_name}...")
        
        # Try yfinance first if available
        yfinance_ticker = config.get('yfinance')
        if yfinance_ticker:
            filepath, start_date, end_date = download_yfinance_data(yfinance_ticker, asset_name)
            if filepath:
                successful_downloads += 1
                continue
        
        # Try akshare if yfinance failed or not available
        akshare_symbol = config.get('akshare')
        if akshare_symbol:
            filepath, start_date, end_date = download_akshare_index(akshare_symbol, asset_name)
            if filepath:
                successful_downloads += 1
                continue
        
        LOG.warning(f"Failed to download data for {asset_name}")
        failed_downloads += 1
    
    # Download yield data
    try:
        LOG.info("Downloading US 10Y yield data...")
        import yfinance as yf
        yield_data = yf.download("^TNX", period="max")
        
        if not yield_data.empty:
            yield_data.reset_index(inplace=True)
            yield_data.rename(columns={'Date': 'date'}, inplace=True)
            
            # Merge with existing and save consolidated
            yield_dir = 'data/raw/yield'
            filepath, start_date, end_date = _merge_with_existing_and_save_singleton(yield_dir, 'US10Y', 'yield', yield_data, 'date')
            LOG.info(f"Saved US 10Y yield data to {filepath} ({len(yield_data)} records)")
            successful_downloads += 1
        else:
            LOG.warning("Failed to download US 10Y yield data")
            failed_downloads += 1
            
    except Exception as e:
        LOG.error(f"Error downloading yield data: {e}")
        failed_downloads += 1
    
    # Download PE data
    download_pe_data()
    
    LOG.info(f"Data download completed: {successful_downloads} successful, {failed_downloads} failed")
    return successful_downloads, failed_downloads

def download_pe_data():
    """Download P/E ratio data from various sources"""
    LOG.info("Downloading P/E ratio data...")
    
    for asset_name, config in PE_ASSETS.items():
        try:
            akshare_source = config.get('akshare')
            
            if akshare_source == 'INDEX_PE':
                # Download CSI300 P/E data using akshare
                pe_data = ak.stock_index_pe_lg()
                if not pe_data.empty:
                    # Filter for CSI300 (沪深300)
                    csi300_data = pe_data[pe_data['指数代码'] == '000300']
                    if not csi300_data.empty:
                        # Process and save
                        processed_data = csi300_data[['日期', '市盈率']].copy()
                        processed_data.columns = ['date', 'pe_ratio']
                        processed_data['date'] = pd.to_datetime(processed_data['date'])
                        
                        # Merge with existing and save consolidated
                        pe_dir = 'data/raw/pe'
                        filepath, start_date, end_date = _merge_with_existing_and_save_singleton(pe_dir, asset_name, 'pe', processed_data, 'date')
                        LOG.info(f"Saved {asset_name} P/E data to {filepath} ({len(processed_data)} records)")
                    
            elif akshare_source == 'MARKET_PE':
                # Download CSI500 P/E data using akshare
                pe_data = ak.stock_market_pe_lg()
                if not pe_data.empty:
                    # Filter for CSI500 (中证500)
                    csi500_data = pe_data[pe_data['指数代码'] == '000905']
                    if not csi500_data.empty:
                        # Process and save
                        processed_data = csi500_data[['日期', '市盈率']].copy()
                        processed_data.columns = ['date', 'pe_ratio']
                        processed_data['date'] = pd.to_datetime(processed_data['date'])
                        
                        # Merge with existing and save consolidated
                        pe_dir = 'data/raw/pe'
                        filepath, start_date, end_date = _merge_with_existing_and_save_singleton(pe_dir, asset_name, 'pe', processed_data, 'date')
                        LOG.info(f"Saved {asset_name} P/E data to {filepath} ({len(processed_data)} records)")
            
            # For manual files, just log that they should be downloaded manually
            manual_file = config.get('manual_file')
            if manual_file:
                LOG.info(f"{asset_name}: Manual P/E file required - {manual_file}")
                
        except Exception as e:
            LOG.error(f"Error downloading P/E data for {asset_name}: {e}")

def main(refresh=False, auto_process=True):
    """Main function for data download script"""
    LOG.info("=" * 60)
    LOG.info("MARKET DATA DOWNLOAD SCRIPT")
    LOG.info("=" * 60)
    
    try:
        successful, failed = download_all_assets(refresh=refresh)
        
        LOG.info("=" * 60)
        LOG.info(f"DOWNLOAD COMPLETED: {successful} successful, {failed} failed")
        
        # Auto-process data after successful downloads
        if auto_process and successful > 0:
            LOG.info("Auto-processing data for all strategies...")
            try:
                from src.data_center.data_processor import process_all_strategies
                results = process_all_strategies(force_refresh=refresh)
                
                processed_count = sum(1 for success in results.values() if success)
                LOG.info(f"DATA PROCESSING COMPLETED: {processed_count}/{len(results)} strategies processed")
                
                if processed_count < len(results):
                    failed_strategies = [k for k, v in results.items() if not v]
                    LOG.warning(f"Failed to process data for: {failed_strategies}")
                
            except Exception as e:
                LOG.error(f"Auto-processing failed: {e}")
        
        LOG.info("=" * 60)
        
        return successful, failed
        
    except Exception as e:
        LOG.error(f"Download script failed: {e}")
        return 0, 1

def parse_manual_pe_date(date_str, asset_name):
    try:
        if asset_name in ['HSI', 'HSTECH']:
            date_obj = pd.to_datetime(date_str, format='%b %Y')
            return date_obj + pd.offsets.MonthEnd(0)
        elif asset_name == 'SP500':
            date_obj = pd.to_datetime(date_str, format='%Y/%m/%d')
            return date_obj + pd.offsets.MonthEnd(0)
        elif asset_name == 'NASDAQ100':
            return pd.to_datetime(date_str, format='%Y/%m/%d')
        else:
            return pd.to_datetime(date_str)
    except Exception as e:
        LOG.warning(f"Failed to parse date '{date_str}' for {asset_name}: {e}")
        return None

def find_manual_pe_files(manual_file_pattern):
    search_paths = ['data/raw/pe/', './']
    found_files = []
    for search_path in search_paths:
        for extension in ['.xlsx', '.csv']:
            pattern = os.path.join(search_path, f"{manual_file_pattern}*{extension}")
            files = glob.glob(pattern)
            found_files.extend(files)
    if found_files:
        return sorted(found_files)[-1]
    return None

def process_manual_pe_file(filepath, asset_name):
    try:
        LOG.info(f"Processing manual P/E file for {asset_name}: {filepath}")
        if filepath.endswith('.xlsx'):
            try:
                df = pd.read_excel(filepath, sheet_name=0, engine='openpyxl')
                LOG.info(f"Reading Excel file: {filepath}")
            except Exception as excel_error:
                LOG.warning(f"Failed to read Excel file {filepath} with openpyxl: {excel_error}")
                try:
                    df = pd.read_excel(filepath, engine='openpyxl')
                    LOG.info(f"Successfully read Excel file using default sheet: {filepath}")
                except Exception as fallback_error:
                    try:
                        df = pd.read_excel(filepath)
                        LOG.info(f"Successfully read Excel file with default engine: {filepath}")
                    except Exception as final_error:
                        raise ValueError(
                            f"Cannot read Excel file {filepath}. Tried openpyxl and default engines. "
                            f"Original error: {excel_error}. Final error: {final_error}. "
                            f"Please ensure the file is a valid Excel file and openpyxl is installed.")
        elif filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
            LOG.info(f"Reading CSV file: {filepath}")
        else:
            raise ValueError(f"Unsupported file format: {filepath}. Only .xlsx and .csv are supported.")
        if asset_name in ['HSI', 'HSTECH']:
            if 'Date' in df.columns and 'Value' in df.columns:
                df = df.rename(columns={'Date': 'date', 'Value': 'pe_ratio'})
            else:
                raise ValueError(f"Expected columns 'Date' and 'Value' not found in {filepath}")
        elif asset_name == 'SP500':
            date_col = None
            value_col = None
            for col in df.columns:
                if col.strip().lower() == 'date':
                    date_col = col
                    break
            for col in df.columns:
                if col.strip().lower() == 'value':
                    value_col = col
                    break
            if date_col and value_col:
                df = df.rename(columns={date_col: 'date', value_col: 'pe_ratio'})
            else:
                raise ValueError(f"Expected columns 'Date/date' and 'Value/value' not found in {filepath}. Found: {list(df.columns)}")
        elif asset_name == 'NASDAQ100':
            if 'Date' in df.columns and 'PE Ratio' in df.columns:
                df = df.rename(columns={'Date': 'date', 'PE Ratio': 'pe_ratio'})
                df = df[['date', 'pe_ratio']]
            else:
                raise ValueError(f"Expected columns 'Date' and 'PE Ratio' not found in {filepath}")
        df['date'] = df['date'].apply(lambda x: parse_manual_pe_date(x, asset_name))
        df = df.dropna(subset=['date'])
        df['pe_ratio'] = pd.to_numeric(df['pe_ratio'], errors='coerce')
        df = df.dropna(subset=['pe_ratio'])
        df = df[df['pe_ratio'] > 0]
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


def process_manual_pe_data():
    """Process manual PE data files from data/raw/pe/manual/ folder"""
    manual_pe_dir = os.path.join('data', 'raw', 'pe', 'manual')
    pe_dir = os.path.join('data', 'raw', 'pe')
    
    if not os.path.exists(manual_pe_dir):
        LOG.info(f"Manual PE directory not found: {manual_pe_dir}")
        return
    
    manual_files = [f for f in os.listdir(manual_pe_dir) if f.endswith('.csv') and not f.startswith('.')]
    
    if not manual_files:
        LOG.info("No manual PE data files found to process")
        return
    
    LOG.info("=" * 60)
    LOG.info("PROCESSING MANUAL PE DATA")
    LOG.info("=" * 60)
    LOG.info(f"Found {len(manual_files)} manual PE data files")
    
    processed_count = 0
    failed_count = 0
    
    for file_name in manual_files:
        try:
            file_path = os.path.join(manual_pe_dir, file_name)
            asset_name = file_name.replace('_pe.csv', '').replace('.csv', '')
            
            LOG.info(f"Processing manual PE data for {asset_name}: {file_name}")
            
            # Read manual data
            manual_df = pd.read_csv(file_path)
            
            # Validate and clean manual data
            if 'date' not in manual_df.columns:
                LOG.error(f"Missing 'date' column in {file_name}")
                failed_count += 1
                continue
            
            # Find PE column
            pe_column = None
            for col in ['pe_ratio', 'pe', 'PE', 'PE_ratio']:
                if col in manual_df.columns:
                    pe_column = col
                    break
            
            if not pe_column:
                LOG.error(f"No PE ratio column found in {file_name}. Expected: pe_ratio, pe, PE, or PE_ratio")
                failed_count += 1
                continue
            
            # Standardize column names
            manual_df = manual_df.rename(columns={pe_column: 'pe_ratio'})
            manual_df['date'] = pd.to_datetime(manual_df['date'])
            
            # Clean data
            initial_len = len(manual_df)
            manual_df = manual_df.dropna(subset=['date', 'pe_ratio'])
            manual_df = manual_df[(manual_df['pe_ratio'] > 0) & (manual_df['pe_ratio'] < 1000)]
            manual_df = manual_df.sort_values('date').reset_index(drop=True)
            
            if len(manual_df) < initial_len:
                LOG.info(f"Cleaned manual data: removed {initial_len - len(manual_df)} invalid records")
            
            if manual_df.empty:
                LOG.warning(f"No valid data in {file_name} after cleaning")
                failed_count += 1
                continue
            
            # Merge with existing PE data using singleton storage
            filepath, start_date, end_date = _merge_with_existing_and_save_singleton(
                pe_dir, asset_name, 'pe', manual_df, 'date'
            )
            
            if filepath:
                LOG.info(f"Successfully processed manual PE data for {asset_name}")
                LOG.info(f"  Records: {len(manual_df)} manual entries")
                LOG.info(f"  Date range: {manual_df['date'].min().strftime('%Y-%m-%d')} to {manual_df['date'].max().strftime('%Y-%m-%d')}")
                LOG.info(f"  Updated: {filepath}")
                processed_count += 1
            else:
                LOG.error(f"Failed to save processed data for {asset_name}")
                failed_count += 1
                
        except Exception as e:
            LOG.error(f"Error processing {file_name}: {e}")
            failed_count += 1
    
    LOG.info("=" * 60)
    LOG.info("MANUAL PE DATA PROCESSING COMPLETED")
    LOG.info(f"Processed: {processed_count} files")
    LOG.info(f"Failed: {failed_count} files")
    LOG.info("=" * 60)
    
    if processed_count > 0:
        LOG.info("Manual PE data has been merged into the main system.")
        LOG.info("You can now:")
        LOG.info("1. Keep manual files for future reference")
        LOG.info("2. Move them to a backup folder") 
        LOG.info("3. Delete them (data is already merged)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Financial Data Download and Processing Tool')
    parser.add_argument('--refresh', action='store_true', 
                       help='Force refresh of all data regardless of existing files')
    parser.add_argument('--no-auto-process', action='store_true',
                       help='Skip automatic data processing after download')
    parser.add_argument('--asset', type=str,
                       help='Download data for specific asset only (e.g., SP500, CSI300)')
    parser.add_argument('--process-manual-pe', action='store_true',
                       help='Process manual PE data files from data/raw/pe/manual/ folder')
    
    args = parser.parse_args()
    
    if args.process_manual_pe:
        process_manual_pe_data()
    else:
        auto_process = not args.no_auto_process
        main(refresh=args.refresh, auto_process=auto_process)
