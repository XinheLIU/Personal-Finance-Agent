"""
Data Processing Pipeline
Handles data normalization, validation, and preparation for strategy consumption.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import warnings
from src.app_logger import LOG

class DataProcessor:
    """Data processing pipeline for market data normalization and validation"""
    
    def __init__(self, data_root: str = "data"):
        self.data_root = Path(data_root)
        self.processed_dir = self.data_root / "processed"
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
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