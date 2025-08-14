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

# Data download functions
def _merge_with_existing_and_save(dir_path, asset_name, data_type, df, date_col='date'):
    """
    Merge newly downloaded df with any existing files for this asset and data_type,
    preserving older time periods (override duplicates by newest), then save a single
    consolidated file named with the merged date range.
    """
    try:
        os.makedirs(dir_path, exist_ok=True)
        # Normalize date column
        if date_col not in df.columns:
            # Try common variants
            if 'Date' in df.columns:
                df = df.rename(columns={'Date': 'date'})
            elif '日期' in df.columns:
                df = df.rename(columns={'日期': 'date'})
        # Ensure datetime
        if not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])

        # Gather existing files and merge
        pattern = os.path.join(dir_path, f"{asset_name}_{data_type}_*.csv")
        existing_files = sorted(glob.glob(pattern))
        frames = [df]
        for fpath in existing_files:
            try:
                old = pd.read_csv(fpath)
                if 'date' not in old.columns:
                    if 'Date' in old.columns:
                        old = old.rename(columns={'Date': 'date'})
                    elif '日期' in old.columns:
                        old = old.rename(columns={'日期': 'date'})
                if pd.api.types.is_datetime64_any_dtype(old['date']) is False:
                    old['date'] = pd.to_datetime(old['date'])
                frames.append(old)
            except Exception as read_err:
                LOG.warning(f"Skipping unreadable file during merge: {fpath} ({read_err})")
                continue

        merged = pd.concat(frames, ignore_index=True, sort=False)
        # Deduplicate by date, keep the last occurrence (newest download wins)
        merged = merged.sort_values('date')
        merged = merged.drop_duplicates(subset=['date'], keep='last')
        merged = merged.sort_values('date').reset_index(drop=True)

        # Save consolidated file
        start_date = merged['date'].min().strftime('%Y%m%d')
        end_date = merged['date'].max().strftime('%Y%m%d')
        out_name = f"{asset_name}_{data_type}_{start_date}_to_{end_date}.csv"
        out_path = os.path.join(dir_path, out_name)
        merged.to_csv(out_path, index=False)
        LOG.info(f"Saved consolidated {asset_name} {data_type} to {out_path} ({len(merged)} records)")
        return out_path, start_date, end_date
    except Exception as e:
        LOG.error(f"Failed to merge and save {asset_name} {data_type}: {e}")
        # Fallback to saving only the new df
        start_date = df['date'].min().strftime('%Y%m%d')
        end_date = df['date'].max().strftime('%Y%m%d')
        out_name = f"{asset_name}_{data_type}_{start_date}_to_{end_date}.csv"
        out_path = os.path.join(dir_path, out_name)
        df.to_csv(out_path, index=False)
        LOG.info(f"Saved (no-merge fallback) {asset_name} {data_type} to {out_path} ({len(df)} records)")
        return out_path, start_date, end_date


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
        filepath, start_date, end_date = _merge_with_existing_and_save(price_dir, asset_name, 'price', data, 'date')
        return filepath, start_date, end_date
        
    except Exception as e:
        LOG.error(f"Error downloading {asset_name} from Yahoo Finance: {e}")
        return None, None, None

def download_akshare_index(symbol, asset_name):
    """Download index data from akshare"""
    try:
        LOG.info(f"Downloading {asset_name} data from akshare (symbol: {symbol})")
        
        # Get stock data from akshare
        data = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
        
        if data.empty:
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
        filepath, start_date, end_date = _merge_with_existing_and_save(price_dir, asset_name, 'price', data, 'date')
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
            filepath, start_date, end_date = _merge_with_existing_and_save(yield_dir, 'US10Y', 'yield', yield_data, 'date')
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
                        filepath, start_date, end_date = _merge_with_existing_and_save(pe_dir, asset_name, 'pe', processed_data, 'date')
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
                        filepath, start_date, end_date = _merge_with_existing_and_save(pe_dir, asset_name, 'pe', processed_data, 'date')
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


