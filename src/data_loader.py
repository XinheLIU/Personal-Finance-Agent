import backtrader as bt
import pandas as pd
import os
from src.app_logger import LOG
from src.config import PE_ASSETS, ASSETS

def load_data_feed(asset_name, name):
    """Load data feed from CSV file with new naming convention"""
    # Look for files with the new naming convention
    data_dir = 'data'
    if not os.path.exists(data_dir):
        LOG.warning(f"Data directory not found: {data_dir}")
        return None
    
    # Search for files matching the asset name pattern
    pattern = f"{asset_name}_price_"
    matching_files = [f for f in os.listdir(data_dir) if f.startswith(pattern) and f.endswith('.csv')]
    
    if not matching_files:
        raise FileNotFoundError(f"No price data file found for {name} (pattern: {pattern})")
    
    # Use the most recent file (assuming it has the latest date range)
    filename = sorted(matching_files)[-1]
    filepath = os.path.join(data_dir, filename)
    
    try:
        df = pd.read_csv(filepath)
        
        # Handle different column naming conventions
        if '日期' in df.columns and '收盘' in df.columns:
            # Chinese data format
            df = df.rename(columns={'日期': 'datetime', '收盘': 'close'})
        elif 'date' in df.columns and 'close' in df.columns:
            # English data format  
            df = df.rename(columns={'date': 'datetime'})
        else:
            LOG.warning(f"Unknown column format in {filepath}")
            return None
            
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
        
        # Add required OHLV columns for backtrader (use close price for all)
        df['open'] = df['close'].astype(float)
        df['high'] = df['close'].astype(float) * 1.01  # Simulate small spread
        df['low'] = df['close'].astype(float) * 0.99
        df['volume'] = 1000000  # Dummy volume
        
        # Create backtrader data feed
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
    Load historical price data for all assets from CSV files.
    """
    market_data = {}
    for asset_name in ASSETS.keys():
        try:
            files = [f for f in os.listdir('data') if f.startswith(f'{asset_name}_price_') and f.endswith('.csv')]
            if files:
                file = sorted(files)[-1]
                df = pd.read_csv(f'data/{file}')
                if '日期' in df.columns:
                    df['日期'] = pd.to_datetime(df['日期'])
                    df.set_index('日期', inplace=True)
                else:
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)
                market_data[asset_name] = df
            else:
                raise FileNotFoundError(f"No price data file found for {asset_name}")
        except Exception as e:
            LOG.error(f"Error loading market data for {asset_name}: {e}")
            market_data[asset_name] = pd.DataFrame()
    LOG.info("Market data loaded successfully")
    return market_data

def load_pe_data():
    """
    Load PE (Price-to-Earnings) ratio data from CSV files.
    """
    pe_cache = {}
    LOG.info("Loading PE ratio data from files...")
    
    for asset in PE_ASSETS.keys():
        try:
            pe_files = [f for f in os.listdir('data') if f.startswith(f'{asset}_pe_') and f.endswith('.csv')]
            
            if pe_files:
                pe_file = sorted(pe_files)[-1]
                pe_df = pd.read_csv(f'data/{pe_file}')
                
                if 'date' in pe_df.columns:
                    pe_df['date'] = pd.to_datetime(pe_df['date'], utc=True).dt.tz_localize(None)
                    pe_df.set_index('date', inplace=True)
                elif '日期' in pe_df.columns:
                    pe_df['日期'] = pd.to_datetime(pe_df['日期'])
                    pe_df.set_index('日期', inplace=True)
                
                pe_cache[asset] = pe_df
                LOG.info(f"Loaded {asset} PE data: {len(pe_df)} records")
            else:
                raise FileNotFoundError(f"PE data file not found for {asset}")
                
        except Exception as e:
            LOG.error(f"Error loading PE data for {asset}: {e}")
            pe_cache[asset] = pd.DataFrame()
    
    loaded_assets = [k for k, v in pe_cache.items() if not v.empty]
    LOG.info(f"PE data loading complete. Loaded data for: {loaded_assets}")
    return pe_cache