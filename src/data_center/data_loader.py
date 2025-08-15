"""
Enhanced Data Loader for Quant Investment System
Provides clean, date-indexed price DataFrames with robust error handling and validation.
"""

import backtrader as bt
import pandas as pd
import numpy as np
import os
from pathlib import Path
from typing import Dict, Optional, Tuple
import warnings
from src.app_logger import LOG
from config.assets import PE_ASSETS, ASSETS, INDEX_ASSETS

class DataLoader:
    """Enhanced data loader with separation of raw and processed data"""
    
    def __init__(self, data_root: str = "data"):
        self.data_root = Path(data_root)
        self.raw_dir = self.data_root / "raw"
        self.processed_dir = self.data_root / "processed"
        self.accounts_dir = self.data_root / "accounts"
        
        # Ensure directories exist
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.accounts_dir.mkdir(parents=True, exist_ok=True)
    
    def _validate_dataframe(self, df: pd.DataFrame, asset_name: str) -> pd.DataFrame:
        """Validate and clean DataFrame with comprehensive checks"""
        if df.empty:
            LOG.warning(f"Empty DataFrame for {asset_name}")
            return df
        
        # Check for required columns (handle both upper and lowercase)
        close_cols = [col for col in df.columns if col.lower() in ['close', '收盘']]
        if not close_cols:
            raise ValueError(f"Missing 'close' column for {asset_name}. Available columns: {list(df.columns)}")
        
        # Standardize column names (handle various cases)
        column_mapping = {}
        for col in df.columns:
            if col.lower() == 'close' or col == '收盘':
                column_mapping[col] = 'close'
        
        if column_mapping:
            df = df.rename(columns=column_mapping)
        
        # Remove invalid values
        initial_len = len(df)
        df = df.dropna(subset=['close'])
        df = df[df['close'] > 0]  # Remove negative or zero prices
        
        if len(df) < initial_len:
            LOG.info(f"Cleaned {asset_name}: removed {initial_len - len(df)} invalid records")
        
        # Ensure timezone-naive datetime index
        if hasattr(df.index, 'tz') and df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        
        # Sort by date
        df = df.sort_index()
        
        return df
    
    def _normalize_price_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize price data to base 1.0 for return calculations"""
        if df.empty or 'close' not in df.columns:
            return df
        
        normalized_df = df.copy()
        normalized_df['close'] = normalized_df['close'] / normalized_df['close'].iloc[0]
        return normalized_df
    
    def load_data_feed(self, asset_name: str, name: str, start_date: Optional[str] = None) -> Optional[bt.feeds.PandasData]:
        """Load data feed from CSV file with enhanced validation"""
        price_dir = self.raw_dir / 'price'
        
        if not price_dir.exists():
            LOG.error(f"Price data directory not found: {price_dir}")
            return None
        
        # Look for singleton file first, then fall back to complex naming
        singleton_file = price_dir / f"{asset_name}_price.csv"
        
        if singleton_file.exists():
            filepath = singleton_file
        else:
            # Fall back to old complex naming pattern
            pattern = f"{asset_name}_"
            matching_files = [f for f in price_dir.glob(f"{pattern}*.csv")]
            
            if not matching_files:
                raise FileNotFoundError(f"No price data file found for {name} in {price_dir} (tried: {singleton_file} and pattern: {pattern})")
            
            # Use most recent file
            filepath = sorted(matching_files)[-1]
        
        try:
            df = pd.read_csv(filepath)
            
            # Standardize column names - handle various cases
            column_mapping = {}
            
            # Handle date columns
            for col in df.columns:
                if col.lower() == 'date' or col == '日期':
                    column_mapping[col] = 'datetime'
                elif col.lower() == 'close' or col == '收盘':
                    column_mapping[col] = 'close'
            
            if 'datetime' not in column_mapping.values():
                LOG.warning(f"No date column found in {filepath}. Available columns: {list(df.columns)}")
                return None
            
            if 'close' not in column_mapping.values():
                LOG.warning(f"No close column found in {filepath}. Available columns: {list(df.columns)}")
                return None
            
            df = df.rename(columns=column_mapping)
            
            # Handle timezone-aware datetime parsing to avoid mixed timezone warnings
            # Use format='mixed' to handle files with mixed timezone formats gracefully
            df['datetime'] = pd.to_datetime(df['datetime'], format='mixed', utc=True)
            df.set_index('datetime', inplace=True)
            
            # Convert to timezone-naive for consistent comparisons throughout the system
            df.index = df.index.tz_localize(None)
            
            # Validate and clean data
            df = self._validate_dataframe(df, asset_name)
            
            if start_date:
                start_date_parsed = pd.to_datetime(start_date)
                # Ensure start_date is also timezone-naive for comparison
                if hasattr(start_date_parsed, 'tz') and start_date_parsed.tz is not None:
                    start_date_parsed = start_date_parsed.tz_localize(None)
                df = df[df.index >= start_date_parsed]
            
            # Create OHLV data for backtrader
            df['open'] = df['close'].astype(float)
            df['high'] = df['close'].astype(float) * 1.01
            df['low'] = df['close'].astype(float) * 0.99
            df['volume'] = 1000000
            
            # Create custom PandasData feed
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
    
    def load_market_data(self, normalize: bool = False) -> Dict[str, pd.DataFrame]:
        """
        Load historical price data for all assets with enhanced validation
        
        Args:
            normalize: If True, normalize price series to base 1.0
        """
        market_data = {}
        price_dir = self.raw_dir / 'price'
        
        if not price_dir.exists():
            LOG.error(f"Price data directory not found: {price_dir}")
            return market_data
        
        # Load price data for regular assets
        for asset_name in ASSETS.keys():
            try:
                # Look for singleton file first, then fall back to complex naming
                singleton_file = price_dir / f"{asset_name}_price.csv"
                
                if singleton_file.exists():
                    file = singleton_file
                else:
                    # Fall back to old complex naming pattern
                    files = list(price_dir.glob(f'{asset_name}_*.csv'))
                    if files:
                        file = sorted(files)[-1]  # Use most recent file
                    else:
                        raise FileNotFoundError(f"No price data file found for {asset_name}")
                
                df = pd.read_csv(file)
                
                # Standardize date column - handle various cases
                date_column = None
                for col in df.columns:
                    if col.lower() == 'date' or col == '日期':
                        date_column = col
                        break
                
                if date_column:
                    # Handle timezone-aware datetime parsing consistently
                    # Use format='mixed' to handle files with mixed timezone formats gracefully
                    df[date_column] = pd.to_datetime(df[date_column], format='mixed', utc=True)
                    df.set_index(date_column, inplace=True)
                    
                    # Convert to timezone-naive for consistent processing throughout the system
                    df.index = df.index.tz_localize(None)
                else:
                    LOG.warning(f"No date column found for {asset_name}. Available columns: {list(df.columns)}")
                    continue
                
                # Validate and clean
                df = self._validate_dataframe(df, asset_name)
                
                # Normalize if requested
                if normalize:
                    df = self._normalize_price_data(df)
                
                market_data[asset_name] = df
                LOG.info(f"Loaded {asset_name}: {len(df)} records")
                
            except Exception as e:
                LOG.error(f"Error loading market data for {asset_name}: {e}")
                market_data[asset_name] = pd.DataFrame()
        
        # Load yield data
        try:
            yield_data = self.load_yield_data()
            if not yield_data.empty:
                market_data['US10Y'] = yield_data
                LOG.info("US10Y yield data added to market data")
            else:
                LOG.warning("US10Y yield data is empty")
                market_data['US10Y'] = pd.DataFrame()
        except Exception as e:
            LOG.error(f"Error loading US10Y yield data: {e}")
            market_data['US10Y'] = pd.DataFrame()
        
        LOG.info(f"Market data loaded: {len([k for k, v in market_data.items() if not v.empty])} assets")
        return market_data
    
    def load_pe_data(self) -> Dict[str, pd.DataFrame]:
        """Load PE ratio data with enhanced validation"""
        pe_cache = {}
        pe_dir = self.raw_dir / 'pe'
        
        if not pe_dir.exists():
            LOG.error(f"PE data directory not found: {pe_dir}")
            return pe_cache
        
        LOG.info(f"Loading PE ratio data from {pe_dir}...")
        
        for asset in PE_ASSETS.keys():
            try:
                # Look for singleton file first, then fall back to complex naming, then check manual folder
                singleton_file = pe_dir / f"{asset}_pe.csv"
                manual_file = pe_dir / "manual" / f"{asset}_pe.csv"
                
                if singleton_file.exists():
                    pe_file = singleton_file
                elif manual_file.exists():
                    pe_file = manual_file
                    LOG.info(f"Using manual PE data for {asset}: {manual_file}")
                else:
                    # Fall back to old complex naming pattern
                    pe_files = list(pe_dir.glob(f'{asset}_*.csv'))
                    if pe_files:
                        pe_file = sorted(pe_files)[-1]  # Use most recent file
                    else:
                        raise FileNotFoundError(f"PE data file not found for {asset}")
                
                pe_df = pd.read_csv(pe_file)
                
                # Standardize date column handling
                if 'date' in pe_df.columns:
                    pe_df['date'] = pd.to_datetime(pe_df['date'])
                    pe_df.set_index('date', inplace=True)
                elif '日期' in pe_df.columns:
                    pe_df['日期'] = pd.to_datetime(pe_df['日期'])
                    pe_df.set_index('日期', inplace=True)
                
                # Validate and clean PE data
                pe_df = self._validate_pe_data(pe_df, asset)
                
                # Detect data frequency
                frequency = self._detect_data_frequency(pe_df)
                LOG.info(f"Loaded {asset} PE data: {len(pe_df)} {frequency} records")
                
                pe_cache[asset] = pe_df
            except Exception as e:
                LOG.error(f"Error loading PE data for {asset}: {e}")
                pe_cache[asset] = pd.DataFrame()
        
        loaded_assets = [k for k, v in pe_cache.items() if not v.empty]
        LOG.info(f"PE data loading complete. Loaded: {loaded_assets}")
        return pe_cache
    
    def _validate_pe_data(self, df: pd.DataFrame, asset_name: str) -> pd.DataFrame:
        """Validate PE ratio data"""
        if df.empty:
            return df
        
        # Ensure timezone-naive datetime
        if hasattr(df.index, 'tz') and df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        
        # Remove invalid PE values (negative, zero, or extremely high)
        if 'pe_ratio' in df.columns:
            initial_len = len(df)
            df = df[(df['pe_ratio'] > 0) & (df['pe_ratio'] < 1000)]
            if len(df) < initial_len:
                LOG.info(f"Cleaned {asset_name} PE data: removed {initial_len - len(df)} invalid records")
        
        return df.sort_index()
    
    def _detect_data_frequency(self, df: pd.DataFrame) -> str:
        """Detect if data is daily, weekly, or monthly"""
        if len(df) < 2:
            return "unknown"
        
        date_diff = df.index[1] - df.index[0]
        if date_diff.days > 20:
            return "monthly"
        elif date_diff.days > 5:
            return "weekly"
        else:
            return "daily"
    
    def load_yield_data(self) -> pd.DataFrame:
        """Load US 10-year Treasury yield data"""
        yield_dir = self.raw_dir / 'yield'
        
        if not yield_dir.exists():
            LOG.error(f"Yield data directory not found: {yield_dir}")
            return pd.DataFrame()
        
        try:
            # Look for singleton file first, then fall back to complex naming
            singleton_file = yield_dir / "US10Y_yield.csv"
            
            if singleton_file.exists():
                yield_file = singleton_file
            else:
                # Fall back to old complex naming pattern
                yield_files = list(yield_dir.glob('US10Y_*.csv'))
                if yield_files:
                    yield_file = sorted(yield_files)[-1]  # Use most recent file
                else:
                    raise FileNotFoundError("US 10Y yield data file not found")
            
            df = pd.read_csv(yield_file)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # Validate yield data (yield data has 'yield' column, not 'close')
            # Handle both 'yield' and 'Close' columns (some files use Close for yield data)
            if 'yield' not in df.columns:
                if 'Close' in df.columns:
                    df = df.rename(columns={'Close': 'yield'})
                    LOG.info("Renamed 'Close' column to 'yield' for US10Y data")
                elif 'close' in df.columns:
                    df = df.rename(columns={'close': 'yield'})
                    LOG.info("Renamed 'close' column to 'yield' for US10Y data")
                else:
                    raise ValueError(f"Missing 'yield' column for US10Y. Available columns: {list(df.columns)}")
            
            # Remove invalid values
            initial_len = len(df)
            df = df.dropna(subset=['yield'])
            
            # Convert yield to numeric and filter
            df['yield'] = pd.to_numeric(df['yield'], errors='coerce')
            df = df.dropna(subset=['yield'])
            df = df[df['yield'] > 0]  # Remove negative or zero yields
            
            if len(df) < initial_len:
                LOG.info(f"Cleaned US10Y yield data: removed {initial_len - len(df)} invalid records")
            
            # Ensure timezone-naive datetime index
            if hasattr(df.index, 'tz') and df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            
            # Sort by date
            df = df.sort_index()
            
            LOG.info(f"Loaded US 10Y yield data: {len(df)} records")
            return df
                
        except Exception as e:
            LOG.error(f"Error loading yield data: {e}")
            return pd.DataFrame()
    
    def save_processed_data(self, data: pd.DataFrame, asset_name: str, data_type: str = "price") -> None:
        """Save processed data to processed directory"""
        filename = f"{asset_name}_{data_type}_processed.csv"
        filepath = self.processed_dir / filename
        
        try:
            data.to_csv(filepath)
            LOG.info(f"Saved processed data for {asset_name} to {filepath}")
        except Exception as e:
            LOG.error(f"Error saving processed data for {asset_name}: {e}")

# Singleton instances for backward compatibility
_data_loader = DataLoader()

def load_data_feed(asset_name: str, name: str, start_date: Optional[str] = None) -> Optional[bt.feeds.PandasData]:
    """Backward compatibility function"""
    return _data_loader.load_data_feed(asset_name, name, start_date)

def load_market_data() -> Dict[str, pd.DataFrame]:
    """Backward compatibility function"""
    return _data_loader.load_market_data()

def load_pe_data() -> Dict[str, pd.DataFrame]:
    """Backward compatibility function"""
    return _data_loader.load_pe_data()

def load_yield_data() -> pd.DataFrame:
    """Backward compatibility function"""
    return _data_loader.load_yield_data()