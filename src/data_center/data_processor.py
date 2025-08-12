"""
Data Processing Pipeline
Handles data normalization, validation, and preparation for strategy consumption.
Processes raw data into strategy-specific merged datasets.
"""

import pandas as pd
import numpy as np
import json
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import warnings
from src.app_logger import LOG
from config.assets import ASSETS, PE_ASSETS, YIELD_ASSETS

class DataProcessor:
    """Data processing pipeline for market data normalization and validation"""
    
    def __init__(self, data_root: str = "data"):
        self.data_root = Path(data_root)
        self.processed_dir = self.data_root / "processed"
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def _get_strategy_data_requirements(self, strategy_name: str) -> Dict[str, List[str]]:
        """Define what data each strategy needs"""
        
        # Default requirements for most strategies
        default_requirements = {
            'price_assets': list(ASSETS.keys()),
            'pe_assets': list(PE_ASSETS.keys()),
            'yield_assets': ['US10Y']
        }
        
        # Strategy-specific requirements
        strategy_requirements = {
            'dynamic_allocation': {
                'price_assets': ['CSI300', 'CSI500', 'HSI', 'HSTECH', 'SP500', 'NASDAQ100', 'TLT', 'GLD'],
                'pe_assets': ['CSI300', 'CSI500', 'HSI', 'HSTECH', 'SP500', 'NASDAQ100'],
                'yield_assets': ['US10Y']
            },
            '60_40': {
                'price_assets': ['SP500', 'TLT'],
                'pe_assets': [],
                'yield_assets': []
            },
            'permanent_portfolio': {
                'price_assets': ['SP500', 'TLT', 'GLD', 'CASH'],
                'pe_assets': [],
                'yield_assets': []
            },
            'all_weather': {
                'price_assets': ['SP500', 'TLT', 'IEF', 'VNQ', 'DBC'],
                'pe_assets': [],
                'yield_assets': []
            },
            'david_swensen': {
                'price_assets': ['SP500', 'VEA', 'VWO', 'VNQ', 'TLT', 'TIP'],
                'pe_assets': [],
                'yield_assets': []
            }
        }
        
        return strategy_requirements.get(strategy_name, default_requirements)
    
    def process_strategy_data(self, strategy_name: str, force_refresh: bool = False) -> bool:
        """Process and merge data for a specific strategy"""
        try:
            LOG.info(f"Processing data for strategy: {strategy_name}")
            
            # Import DataLoader here to avoid circular imports
            from src.data_center.data_loader import DataLoader
            data_loader = DataLoader(str(self.data_root))
            
            # Create strategy-specific directory
            strategy_dir = self.processed_dir / strategy_name
            strategy_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if processing is needed
            processed_file = strategy_dir / "market_data.csv"
            if processed_file.exists() and not force_refresh:
                if self._is_processed_data_fresh(processed_file):
                    LOG.info(f"Processed data for {strategy_name} is up to date")
                    return True
            
            # Get data requirements for this strategy
            requirements = self._get_strategy_data_requirements(strategy_name)
            
            # Load raw data
            market_data = data_loader.load_market_data(normalize=False)
            pe_data = data_loader.load_pe_data()
            
            # Filter data based on strategy requirements
            filtered_market_data = {
                asset: data for asset, data in market_data.items() 
                if asset in requirements['price_assets'] and not data.empty
            }
            
            filtered_pe_data = {
                asset: data for asset, data in pe_data.items()
                if asset in requirements['pe_assets'] and not data.empty
            }
            
            # Create merged dataset
            merged_data = self._merge_strategy_data(
                filtered_market_data, 
                filtered_pe_data, 
                requirements,
                data_loader
            )
            
            if merged_data.empty:
                LOG.error(f"No data available for strategy {strategy_name}")
                return False
            
            # Save processed data
            merged_data.to_csv(processed_file)
            LOG.info(f"Saved processed data for {strategy_name}: {len(merged_data)} records")
            
            # Save metadata
            self._save_strategy_metadata(strategy_dir, strategy_name, requirements, merged_data)
            
            return True
            
        except Exception as e:
            LOG.error(f"Error processing data for strategy {strategy_name}: {e}")
            return False
    
    def _merge_strategy_data(self, market_data: Dict[str, pd.DataFrame], 
                           pe_data: Dict[str, pd.DataFrame], 
                           requirements: Dict[str, List[str]],
                           data_loader) -> pd.DataFrame:
        """Merge market data, PE data, and yield data for a strategy"""
        
        if not market_data:
            LOG.warning("No market data available for merging")
            return pd.DataFrame()
        
        # Start with the first asset's price data as base
        base_asset = list(market_data.keys())[0]
        merged_df = market_data[base_asset][['close']].copy()
        merged_df.columns = [f'{base_asset}_price']
        
        # Add price data for other assets
        for asset_name, asset_data in market_data.items():
            if asset_name == base_asset or asset_data.empty:
                continue
                
            price_col = f'{asset_name}_price'
            merged_df = merged_df.join(
                asset_data[['close']].rename(columns={'close': price_col}), 
                how='outer'
            )
        
        # Add PE data
        for asset_name, pe_df in pe_data.items():
            if pe_df.empty:
                continue
                
            pe_col = f'{asset_name}_pe'
            if 'pe_ratio' in pe_df.columns:
                pe_series = pe_df[['pe_ratio']].rename(columns={'pe_ratio': pe_col})
                # Forward fill PE data for daily frequency matching
                merged_df = merged_df.join(pe_series, how='outer')
                merged_df[pe_col] = merged_df[pe_col].fillna(method='ffill')
        
        # Add yield data if required
        if 'US10Y' in requirements.get('yield_assets', []):
            try:
                yield_data = data_loader.load_yield_data()
                if not yield_data.empty and 'yield' in yield_data.columns:
                    yield_series = yield_data[['yield']].rename(columns={'yield': 'US10Y_yield'})
                    merged_df = merged_df.join(yield_series, how='outer')
                    merged_df['US10Y_yield'] = merged_df['US10Y_yield'].fillna(method='ffill')
            except Exception as e:
                LOG.warning(f"Could not add yield data: {e}")
        
        # Remove rows with all NaN values and sort by date
        merged_df = merged_df.dropna(how='all').sort_index()
        
        LOG.info(f"Merged data shape: {merged_df.shape}, columns: {list(merged_df.columns)}")
        return merged_df
    
    def _is_processed_data_fresh(self, processed_file: Path) -> bool:
        """Check if processed data is newer than raw data"""
        try:
            processed_mtime = processed_file.stat().st_mtime
            
            # Check if any raw data file is newer
            raw_dir = self.data_root / "raw"
            for data_type in ['price', 'pe', 'yield']:
                type_dir = raw_dir / data_type
                if type_dir.exists():
                    for raw_file in type_dir.glob('*.csv'):
                        if raw_file.stat().st_mtime > processed_mtime:
                            return False
            
            return True
        except Exception as e:
            LOG.warning(f"Error checking data freshness: {e}")
            return False
    
    def _save_strategy_metadata(self, strategy_dir: Path, strategy_name: str, 
                              requirements: Dict[str, List[str]], merged_data: pd.DataFrame):
        """Save metadata about the processed data"""
        metadata = {
            'strategy_name': strategy_name,
            'processed_at': datetime.now().isoformat(),
            'data_requirements': requirements,
            'data_shape': merged_data.shape,
            'date_range': {
                'start': str(merged_data.index.min()),
                'end': str(merged_data.index.max())
            },
            'columns': list(merged_data.columns)
        }
        
        metadata_file = strategy_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def process_all_strategies(self, force_refresh: bool = False) -> Dict[str, bool]:
        """Process data for all known strategies"""
        strategies = [
            'dynamic_allocation',
            '60_40', 
            'permanent_portfolio',
            'all_weather',
            'david_swensen'
        ]
        
        results = {}
        for strategy in strategies:
            results[strategy] = self.process_strategy_data(strategy, force_refresh)
        
        return results
    
    def get_processed_data(self, strategy_name: str) -> Optional[pd.DataFrame]:
        """Load processed data for a strategy"""
        try:
            processed_file = self.processed_dir / strategy_name / "market_data.csv"
            if not processed_file.exists():
                LOG.warning(f"No processed data found for {strategy_name}")
                return None
            
            df = pd.read_csv(processed_file, index_col=0, parse_dates=True)
            LOG.info(f"Loaded processed data for {strategy_name}: {df.shape}")
            return df
            
        except Exception as e:
            LOG.error(f"Error loading processed data for {strategy_name}: {e}")
            return None
    
    def cleanup_processed_data(self, strategy_name: Optional[str] = None):
        """Remove processed data to force regeneration"""
        try:
            if strategy_name:
                strategy_dir = self.processed_dir / strategy_name
                if strategy_dir.exists():
                    shutil.rmtree(strategy_dir)
                    LOG.info(f"Cleaned up processed data for {strategy_name}")
            else:
                # Clean all processed data
                if self.processed_dir.exists():
                    shutil.rmtree(self.processed_dir)
                    self.processed_dir.mkdir(parents=True, exist_ok=True)
                    LOG.info("Cleaned up all processed data")
        except Exception as e:
            LOG.error(f"Error cleaning up processed data: {e}")
    
    def get_processing_status(self) -> Dict[str, Any]:
        """Get status of data processing for all strategies"""
        if not self.processed_dir.exists():
            return {'processed_strategies': [], 'total_strategies': 0}
        
        processed_strategies = []
        for strategy_dir in self.processed_dir.iterdir():
            if strategy_dir.is_dir():
                metadata_file = strategy_dir / "metadata.json"
                data_file = strategy_dir / "market_data.csv"
                
                if metadata_file.exists() and data_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        
                        processed_strategies.append({
                            'name': strategy_dir.name,
                            'processed_at': metadata.get('processed_at'),
                            'data_shape': metadata.get('data_shape'),
                            'date_range': metadata.get('date_range'),
                            'file_size_mb': round(data_file.stat().st_size / 1024 / 1024, 2)
                        })
                    except Exception as e:
                        LOG.warning(f"Could not read metadata for {strategy_dir.name}: {e}")
        
        return {
            'processed_strategies': processed_strategies,
            'total_strategies': len(processed_strategies),
            'processed_dir': str(self.processed_dir)
        }
    
    def normalize_price_series(self, data: Dict[str, pd.DataFrame], base_date: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """
        Normalize price series to start at 1.0 for return calculations
        
        Args:
            data: Dictionary of asset DataFrames
            base_date: Optional base date for normalization, uses earliest common date if None
        """
        normalized_data = {}
        
        if base_date:
            base_date = pd.to_datetime(base_date)
        else:
            # Find earliest common date across all assets
            valid_assets = {k: v for k, v in data.items() if not v.empty and 'close' in v.columns}
            if not valid_assets:
                LOG.warning("No valid price data found for normalization")
                return data
            
            base_date = max([df.index.min() for df in valid_assets.values()])
        
        LOG.info(f"Normalizing price series from base date: {base_date}")
        
        for asset_name, df in data.items():
            if df.empty or 'close' not in df.columns:
                normalized_data[asset_name] = df
                continue
            
            try:
                # Filter data from base date
                filtered_df = df[df.index >= base_date].copy()
                
                if filtered_df.empty:
                    LOG.warning(f"No data for {asset_name} from base date {base_date}")
                    normalized_data[asset_name] = df
                    continue
                
                # Normalize to base 1.0
                base_price = filtered_df['close'].iloc[0]
                filtered_df['close_normalized'] = filtered_df['close'] / base_price
                
                # Calculate returns
                filtered_df['returns'] = filtered_df['close'].pct_change()
                filtered_df['log_returns'] = np.log(filtered_df['close'] / filtered_df['close'].shift(1))
                
                normalized_data[asset_name] = filtered_df
                LOG.debug(f"Normalized {asset_name}: base price {base_price:.4f}")
                
            except Exception as e:
                LOG.error(f"Error normalizing {asset_name}: {e}")
                normalized_data[asset_name] = df
        
        return normalized_data
    
    def align_data_dates(self, data: Dict[str, pd.DataFrame], method: str = 'inner') -> Dict[str, pd.DataFrame]:
        """
        Align all data to common date range
        
        Args:
            data: Dictionary of asset DataFrames
            method: 'inner' (intersection) or 'outer' (union) for date alignment
        """
        valid_assets = {k: v for k, v in data.items() if not v.empty}
        
        if not valid_assets:
            LOG.warning("No valid data to align")
            return data
        
        if method == 'inner':
            # Find common date range (intersection)
            start_date = max([df.index.min() for df in valid_assets.values()])
            end_date = min([df.index.max() for df in valid_assets.values()])
        else:
            # Use full date range (union)
            start_date = min([df.index.min() for df in valid_assets.values()])
            end_date = max([df.index.max() for df in valid_assets.values()])
        
        LOG.info(f"Aligning data to date range: {start_date} to {end_date} (method: {method})")
        
        aligned_data = {}
        for asset_name, df in data.items():
            if df.empty:
                aligned_data[asset_name] = df
                continue
            
            try:
                # Filter to common date range
                aligned_df = df[(df.index >= start_date) & (df.index <= end_date)].copy()
                aligned_data[asset_name] = aligned_df
                
                if not aligned_df.empty:
                    LOG.debug(f"Aligned {asset_name}: {len(aligned_df)} records")
                else:
                    LOG.warning(f"No data for {asset_name} in aligned date range")
                
            except Exception as e:
                LOG.error(f"Error aligning {asset_name}: {e}")
                aligned_data[asset_name] = df
        
        return aligned_data
    
    def calculate_rolling_statistics(self, data: Dict[str, pd.DataFrame], windows: List[int] = [20, 50, 200]) -> Dict[str, pd.DataFrame]:
        """
        Calculate rolling statistics for each asset
        
        Args:
            data: Dictionary of asset DataFrames
            windows: List of window sizes for rolling statistics
        """
        enhanced_data = {}
        
        for asset_name, df in data.items():
            if df.empty or 'close' not in df.columns:
                enhanced_data[asset_name] = df
                continue
            
            try:
                enhanced_df = df.copy()
                
                for window in windows:
                    # Rolling mean and std
                    enhanced_df[f'sma_{window}'] = enhanced_df['close'].rolling(window=window).mean()
                    enhanced_df[f'std_{window}'] = enhanced_df['close'].rolling(window=window).std()
                    
                    # Bollinger Band components
                    enhanced_df[f'bb_upper_{window}'] = enhanced_df[f'sma_{window}'] + 2 * enhanced_df[f'std_{window}']
                    enhanced_df[f'bb_lower_{window}'] = enhanced_df[f'sma_{window}'] - 2 * enhanced_df[f'std_{window}']
                
                # RSI (14-period)
                enhanced_df['rsi_14'] = self._calculate_rsi(enhanced_df['close'], 14)
                
                enhanced_data[asset_name] = enhanced_df
                LOG.debug(f"Calculated rolling statistics for {asset_name}")
                
            except Exception as e:
                LOG.error(f"Error calculating statistics for {asset_name}: {e}")
                enhanced_data[asset_name] = df
        
        return enhanced_data
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except Exception as e:
            LOG.error(f"Error calculating RSI: {e}")
            return pd.Series(index=prices.index, dtype=float)
    
    def detect_outliers(self, data: Dict[str, pd.DataFrame], method: str = 'zscore', threshold: float = 3.0) -> Dict[str, pd.DataFrame]:
        """
        Detect and flag outliers in price data
        
        Args:
            data: Dictionary of asset DataFrames
            method: 'zscore' or 'iqr' for outlier detection
            threshold: Threshold for outlier detection
        """
        cleaned_data = {}
        outlier_counts = {}
        
        for asset_name, df in data.items():
            if df.empty or 'close' not in df.columns:
                cleaned_data[asset_name] = df
                continue
            
            try:
                cleaned_df = df.copy()
                returns = cleaned_df['close'].pct_change().dropna()
                
                if method == 'zscore':
                    # Z-score method
                    z_scores = np.abs((returns - returns.mean()) / returns.std())
                    outliers = z_scores > threshold
                elif method == 'iqr':
                    # IQR method
                    Q1 = returns.quantile(0.25)
                    Q3 = returns.quantile(0.75)
                    IQR = Q3 - Q1
                    outliers = (returns < (Q1 - threshold * IQR)) | (returns > (Q3 + threshold * IQR))
                else:
                    LOG.warning(f"Unknown outlier detection method: {method}")
                    cleaned_data[asset_name] = df
                    continue
                
                # Flag outliers
                cleaned_df['is_outlier'] = False
                cleaned_df.loc[outliers[outliers].index, 'is_outlier'] = True
                
                outlier_count = outliers.sum()
                outlier_counts[asset_name] = outlier_count
                
                if outlier_count > 0:
                    LOG.info(f"Detected {outlier_count} outliers in {asset_name} ({outlier_count/len(returns)*100:.1f}%)")
                
                cleaned_data[asset_name] = cleaned_df
                
            except Exception as e:
                LOG.error(f"Error detecting outliers for {asset_name}: {e}")
                cleaned_data[asset_name] = df
        
        total_outliers = sum(outlier_counts.values())
        if total_outliers > 0:
            LOG.info(f"Total outliers detected across all assets: {total_outliers}")
        
        return cleaned_data
    
    def validate_data_quality(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
        """
        Comprehensive data quality validation
        
        Returns:
            Dictionary with quality metrics for each asset
        """
        quality_report = {}
        
        for asset_name, df in data.items():
            metrics = {
                'total_records': len(df),
                'date_range': (df.index.min(), df.index.max()) if not df.empty else (None, None),
                'missing_values': df.isnull().sum().to_dict() if not df.empty else {},
                'duplicate_dates': df.index.duplicated().sum() if not df.empty else 0,
                'data_gaps': 0,
                'price_anomalies': 0
            }
            
            if not df.empty and 'close' in df.columns:
                # Check for data gaps (weekends excluded)
                date_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq='D')
                business_days = pd.bdate_range(start=df.index.min(), end=df.index.max())
                expected_days = len(business_days)
                actual_days = len(df)
                metrics['data_gaps'] = max(0, expected_days - actual_days)
                
                # Check for price anomalies (zero or negative prices)
                metrics['price_anomalies'] = (df['close'] <= 0).sum()
                
                # Calculate data completeness ratio
                metrics['completeness_ratio'] = actual_days / expected_days if expected_days > 0 else 0
            
            quality_report[asset_name] = metrics
        
        # Log summary
        valid_assets = [k for k, v in quality_report.items() if v['total_records'] > 0]
        LOG.info(f"Data quality validation complete: {len(valid_assets)}/{len(data)} assets have data")
        
        return quality_report
    
    def save_processed_data(self, data: Dict[str, pd.DataFrame], suffix: str = "processed") -> None:
        """Save processed data to files"""
        for asset_name, df in data.items():
            if df.empty:
                continue
                
            filename = f"{asset_name}_{suffix}.csv"
            filepath = self.processed_dir / filename
            
            try:
                df.to_csv(filepath)
                LOG.debug(f"Saved {asset_name} processed data to {filepath}")
            except Exception as e:
                LOG.error(f"Error saving processed data for {asset_name}: {e}")
        
        LOG.info(f"Processed data saved to {self.processed_dir}")

# Global data processor instance
_data_processor = DataProcessor()

# Convenience functions for strategy-specific data processing
def process_strategy_data(strategy_name: str, force_refresh: bool = False) -> bool:
    """Process data for a specific strategy"""
    return _data_processor.process_strategy_data(strategy_name, force_refresh)

def process_all_strategies(force_refresh: bool = False) -> Dict[str, bool]:
    """Process data for all strategies"""
    return _data_processor.process_all_strategies(force_refresh)

def get_processed_data(strategy_name: str) -> Optional[pd.DataFrame]:
    """Get processed data for a strategy"""
    return _data_processor.get_processed_data(strategy_name)

def get_processing_status() -> Dict[str, Any]:
    """Get processing status for all strategies"""
    return _data_processor.get_processing_status()

def cleanup_processed_data(strategy_name: Optional[str] = None):
    """Clean up processed data"""
    return _data_processor.cleanup_processed_data(strategy_name)
