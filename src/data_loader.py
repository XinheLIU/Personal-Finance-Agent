import backtrader as bt
import pandas as pd
import os
from src.app_logger import LOG
from src.config import PE_ASSETS, ASSETS, INDEX_ASSETS

def load_data_feed(asset_name, name, start_date=None):
    """Load data feed from CSV file with new naming convention"""
    data_dir = os.path.join('data', 'price')
    if not os.path.exists(data_dir):
        LOG.warning(f"Data directory not found: {data_dir}")
        return None
    
    pattern = f"{asset_name}_"
    matching_files = [f for f in os.listdir(data_dir) if f.startswith(pattern) and f.endswith('.csv')]
    
    if not matching_files:
        raise FileNotFoundError(f"No price data file found for {name} in {data_dir} (pattern: {pattern})")
    
    filename = sorted(matching_files)[-1]
    filepath = os.path.join(data_dir, filename)
    
    try:
        df = pd.read_csv(filepath)
        
        if '日期' in df.columns and '收盘' in df.columns:
            df = df.rename(columns={'日期': 'datetime', '收盘': 'close'})
        elif 'date' in df.columns and 'close' in df.columns:
            df = df.rename(columns={'date': 'datetime'})
        else:
            LOG.warning(f"Unknown column format in {filepath}")
            return None
            
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)

        if start_date:
            df = df[df.index >= pd.to_datetime(start_date)]
        
        df['open'] = df['close'].astype(float)
        df['high'] = df['close'].astype(float) * 1.01
        df['low'] = df['close'].astype(float) * 0.99
        df['volume'] = 1000000
        
        class PandasData(bt.feeds.PandasData):
            params = (
                ('datetime', None),
                ('open', 'open'),
                ('high', 'high'), 
                ('low', 'low'),
                ('close', 'close'),
                ('volume', 'volume'),
                ('openinterest', -1),
            )
        
        data_feed = PandasData(dataname=df)
        LOG.info(f"Loaded {name}: {len(df)} records from {df.index.min()} to {df.index.max()}")
        return data_feed
        
    except Exception as e:
        LOG.error(f"Error loading {filepath}: {e}")
        return None

def load_market_data():
    """
    Load historical price data for all assets from CSV files and yield data.
    """
    market_data = {}
    
    # Load price data for regular assets
    data_dir = os.path.join('data', 'price')
    for asset_name in ASSETS.keys():
        try:
            files = [f for f in os.listdir(data_dir) if f.startswith(f'{asset_name}_') and f.endswith('.csv')]
            if files:
                file = sorted(files)[-1]
                filepath = os.path.join(data_dir, file)
                df = pd.read_csv(filepath)
                if '日期' in df.columns:
                    df['日期'] = pd.to_datetime(df['日期'])
                    df.set_index('日期', inplace=True)
                else:
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)
                market_data[asset_name] = df
            else:
                raise FileNotFoundError(f"No price data file found for {asset_name} in {data_dir}")
        except Exception as e:
            LOG.error(f"Error loading market data for {asset_name}: {e}")
            market_data[asset_name] = pd.DataFrame()
    
    # Load yield data (US10Y)
    try:
        yield_data = load_yield_data()
        if not yield_data.empty:
            market_data['US10Y'] = yield_data
            LOG.info("US10Y yield data added to market data")
        else:
            LOG.warning("US10Y yield data is empty, using empty DataFrame")
            market_data['US10Y'] = pd.DataFrame()
    except Exception as e:
        LOG.error(f"Error loading US10Y yield data: {e}")
        market_data['US10Y'] = pd.DataFrame()
    
    LOG.info("Market data loaded successfully")
    return market_data

def load_pe_data():
    """
    Load PE (Price-to-Earnings) ratio data from CSV files.
    Note: P/E data is monthly for manual downloads, daily for akshare downloads.
    """
    pe_cache = {}
    data_dir = os.path.join('data', 'pe')
    LOG.info(f"Loading PE ratio data from {data_dir}...")
    
    for asset in PE_ASSETS.keys():
        try:
            pe_files = [f for f in os.listdir(data_dir) if f.startswith(f'{asset}_') and f.endswith('.csv')]
            
            if pe_files:
                pe_file = sorted(pe_files)[-1]
                filepath = os.path.join(data_dir, pe_file)
                pe_df = pd.read_csv(filepath)
                
                # Standardize date column handling
                if 'date' in pe_df.columns:
                    pe_df['date'] = pd.to_datetime(pe_df['date'])
                    pe_df.set_index('date', inplace=True)
                elif '日期' in pe_df.columns:
                    pe_df['日期'] = pd.to_datetime(pe_df['日期'])
                    pe_df.set_index('日期', inplace=True)
                
                # Ensure timezone-naive datetime for consistency
                if pe_df.index.tz is not None:
                    pe_df.index = pe_df.index.tz_localize(None)
                
                # Sort by date
                pe_df = pe_df.sort_index()
                
                # Log data frequency info
                if len(pe_df) > 1:
                    date_diff = pe_df.index[1] - pe_df.index[0]
                    if date_diff.days > 20:  # Assume monthly if > 20 days between points
                        LOG.info(f"Loaded {asset} PE data: {len(pe_df)} monthly records from {filepath}")
                    else:
                        LOG.info(f"Loaded {asset} PE data: {len(pe_df)} daily records from {filepath}")
                else:
                    LOG.info(f"Loaded {asset} PE data: {len(pe_df)} records from {filepath}")
                
                pe_cache[asset] = pe_df
            else:
                raise FileNotFoundError(f"PE data file not found for {asset} in {data_dir}")
                
        except Exception as e:
            LOG.error(f"Error loading PE data for {asset}: {e}")
            pe_cache[asset] = pd.DataFrame()
    
    loaded_assets = [k for k, v in pe_cache.items() if not v.empty]
    LOG.info(f"PE data loading complete. Loaded data for: {loaded_assets}")
    return pe_cache

def load_yield_data():
    """
    Load US 10-year Treasury yield data from CSV file.
    """
    data_dir = os.path.join('data', 'yield')
    try:
        yield_files = [f for f in os.listdir(data_dir) if f.startswith('US10Y_') and f.endswith('.csv')]
        if yield_files:
            yield_file = sorted(yield_files)[-1]
            filepath = os.path.join(data_dir, yield_file)
            df = pd.read_csv(filepath)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            LOG.info(f"Loaded US 10Y yield data: {len(df)} records from {filepath}")
            return df
        else:
            raise FileNotFoundError(f"US 10Y yield data file not found in {data_dir}")
    except Exception as e:
        LOG.error(f"Error loading yield data: {e}")
        return pd.DataFrame()
