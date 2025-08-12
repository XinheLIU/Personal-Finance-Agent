import pandas as pd
import numpy as np
from src.app_logger import LOG

def calculate_pe_percentile(asset_name, pe_cache, current_date, years=10):
    """
    Calculate PE percentile for a given asset over a specified time period.
    Handles both daily and monthly P/E data properly.
    """
    if asset_name not in pe_cache or pe_cache[asset_name].empty:
        error_msg = f"No PE data available for {asset_name}. Please ensure PE data is downloaded using data_download.py"
        LOG.error(error_msg)
        raise ValueError(error_msg)
        
    try:
        pe_data = pe_cache[asset_name]
        end_date = pd.to_datetime(current_date)
        
        if end_date.tz is not None:
            end_date = end_date.tz_localize(None)
        
        start_date = end_date - pd.DateOffset(years=years)
        
        if hasattr(pe_data.index, 'tz') and pe_data.index.tz is not None:
            pe_data = pe_data.copy()
            pe_data.index = pe_data.index.tz_localize(None)
        
        # For monthly data, find the most recent available P/E data (could be from previous month)
        available_data_up_to_date = pe_data.loc[:end_date]
        if available_data_up_to_date.empty:
            error_msg = f"No PE data available up to {end_date} for {asset_name}. Data range: {pe_data.index.min()} to {pe_data.index.max()}"
            LOG.error(error_msg)
            raise ValueError(error_msg)
        
        period_pe_data = pe_data.loc[start_date:end_date]
        if period_pe_data.empty:
            error_msg = f"No PE data in {years}-year period for {asset_name}. Data range: {pe_data.index.min()} to {pe_data.index.max()}"
            LOG.error(error_msg)
            raise ValueError(error_msg)
        
        # Determine which P/E column to use
        if 'pe_ratio' in period_pe_data.columns:
            pe_col = 'pe_ratio'
            pe_type = 'PE'
        elif 'avg_pe' in period_pe_data.columns:
            pe_col = 'avg_pe'
            pe_type = 'Avg PE'
        elif 'median_pe' in period_pe_data.columns:
            pe_col = 'median_pe'
            pe_type = 'Median PE'
        elif 'equal_weight_pe' in period_pe_data.columns:
            pe_col = 'equal_weight_pe'
            pe_type = 'Equal Weight PE'
        elif 'pe' in period_pe_data.columns:
            pe_col = 'pe'
            pe_type = 'PE'
        elif 'estimated_pe' in period_pe_data.columns:
            pe_col = 'estimated_pe'
            pe_type = 'Est. PE'
        else:
            numeric_cols = period_pe_data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                pe_col = numeric_cols[0]
                pe_type = 'PE'
            else:
                error_msg = f"No numeric PE column found for {asset_name}. Available columns: {list(period_pe_data.columns)}"
                LOG.error(error_msg)
                raise ValueError(error_msg)
        
        # Get valid P/E data for the period
        valid_pe_data = period_pe_data[pe_col].dropna()
        valid_pe_data = valid_pe_data[(valid_pe_data > 0) & (valid_pe_data < 200)]
        
        if valid_pe_data.empty:
            error_msg = f"No valid {pe_type} data for {asset_name} in the specified period"
            LOG.error(error_msg)
            raise ValueError(error_msg)
            
        # Get the most recent P/E value (for monthly data, this is the latest available month)
        most_recent_pe_data = available_data_up_to_date[pe_col].dropna()
        if most_recent_pe_data.empty:
            error_msg = f"No recent {pe_type} data available for {asset_name}"
            LOG.error(error_msg)
            raise ValueError(error_msg)
            
        current_pe = most_recent_pe_data.iloc[-1]
        most_recent_date = most_recent_pe_data.index[-1]
        
        # Calculate percentile based on historical period data
        percentile = (valid_pe_data <= current_pe).mean()
        
        # Clamp percentile to reasonable bounds
        percentile = min(max(percentile, 0.1), 0.9)
        
        LOG.info(f"{asset_name} - Current {pe_type}: {current_pe:.2f} (as of {most_recent_date.date()}), Percentile: {percentile:.2%} (vs {years}Y history)")
        return percentile
        
    except Exception as e:
        LOG.error(f"Error calculating PE percentile for {asset_name}: {e}")
        raise

def calculate_pe_percentile_with_details(asset_name, pe_cache, current_date, years=10):
    """
    Calculate PE percentile and return detailed inputs used for the calculation.
    Returns a tuple: (percentile: float, details: dict)
    details includes:
      - pe_type, pe_col
      - current_pe, current_pe_date
      - period_start, period_end, period_years
      - num_valid_points, hist_min, hist_median, hist_max
    """
    if asset_name not in pe_cache or pe_cache[asset_name].empty:
        error_msg = f"No PE data available for {asset_name}. Please ensure PE data is downloaded using data_download.py"
        LOG.error(error_msg)
        raise ValueError(error_msg)
    
    pe_data = pe_cache[asset_name]
    end_date = pd.to_datetime(current_date)
    if end_date.tz is not None:
        end_date = end_date.tz_localize(None)
    start_date = end_date - pd.DateOffset(years=years)
    
    if hasattr(pe_data.index, 'tz') and pe_data.index.tz is not None:
        pe_data = pe_data.copy()
        pe_data.index = pe_data.index.tz_localize(None)
    
    available_data_up_to_date = pe_data.loc[:end_date]
    if available_data_up_to_date.empty:
        error_msg = f"No PE data available up to {end_date} for {asset_name}. Data range: {pe_data.index.min()} to {pe_data.index.max()}"
        LOG.error(error_msg)
        raise ValueError(error_msg)
    
    period_pe_data = pe_data.loc[start_date:end_date]
    if period_pe_data.empty:
        error_msg = f"No PE data in {years}-year period for {asset_name}. Data range: {pe_data.index.min()} to {pe_data.index.max()}"
        LOG.error(error_msg)
        raise ValueError(error_msg)
    
    # Determine PE column
    if 'pe_ratio' in period_pe_data.columns:
        pe_col = 'pe_ratio'; pe_type = 'PE'
    elif 'avg_pe' in period_pe_data.columns:
        pe_col = 'avg_pe'; pe_type = 'Avg PE'
    elif 'median_pe' in period_pe_data.columns:
        pe_col = 'median_pe'; pe_type = 'Median PE'
    elif 'equal_weight_pe' in period_pe_data.columns:
        pe_col = 'equal_weight_pe'; pe_type = 'Equal Weight PE'
    elif 'pe' in period_pe_data.columns:
        pe_col = 'pe'; pe_type = 'PE'
    elif 'estimated_pe' in period_pe_data.columns:
        pe_col = 'estimated_pe'; pe_type = 'Est. PE'
    else:
        numeric_cols = period_pe_data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            pe_col = numeric_cols[0]; pe_type = 'PE'
        else:
            error_msg = f"No numeric PE column found for {asset_name}. Available columns: {list(period_pe_data.columns)}"
            LOG.error(error_msg)
            raise ValueError(error_msg)
    
    valid_pe_data = period_pe_data[pe_col].dropna()
    valid_pe_data = valid_pe_data[(valid_pe_data > 0) & (valid_pe_data < 200)]
    if valid_pe_data.empty:
        error_msg = f"No valid {pe_type} data for {asset_name} in the specified period"
        LOG.error(error_msg)
        raise ValueError(error_msg)
    
    most_recent_pe_data = available_data_up_to_date[pe_col].dropna()
    if most_recent_pe_data.empty:
        error_msg = f"No recent {pe_type} data available for {asset_name}"
        LOG.error(error_msg)
        raise ValueError(error_msg)
    
    current_pe = float(most_recent_pe_data.iloc[-1])
    most_recent_date = most_recent_pe_data.index[-1]
    percentile = float((valid_pe_data <= current_pe).mean())
    percentile = min(max(percentile, 0.1), 0.9)
    
    details = {
        'asset': asset_name,
        'pe_type': pe_type,
        'pe_col': pe_col,
        'current_pe': current_pe,
        'current_pe_date': most_recent_date.strftime('%Y-%m-%d'),
        'period_start': start_date.strftime('%Y-%m-%d'),
        'period_end': end_date.strftime('%Y-%m-%d'),
        'period_years': years,
        'num_valid_points': int(len(valid_pe_data)),
        'hist_min': float(valid_pe_data.min()),
        'hist_median': float(valid_pe_data.median()),
        'hist_max': float(valid_pe_data.max()),
    }
    
    return percentile, details

def calculate_yield_percentile(market_data, current_date, years=20):
    """
    Calculate US 10Y Treasury yield percentile over a specified time period.
    """
    if market_data['US10Y'].empty:
        error_msg = "No US 10Y yield data available. Please ensure US10Y.csv is downloaded."
        LOG.error(error_msg)
        raise ValueError(error_msg)
        
    try:
        end_date = pd.to_datetime(current_date)
        start_date = end_date - pd.DateOffset(years=years)
        
        period_data = market_data['US10Y'].loc[start_date:end_date]
        if period_data.empty:
            error_msg = f"No yield data in {years}-year period. Data range: {market_data['US10Y'].index.min()} to {market_data['US10Y'].index.max()}"
            LOG.error(error_msg)
            raise ValueError(error_msg)
            
        current_yield = period_data['yield'].iloc[-1]
        percentile = (period_data['yield'] <= current_yield).mean()
        
        return min(max(percentile, 0.1), 0.9)
        
    except Exception as e:
        LOG.error(f"Error calculating yield percentile: {e}")
        raise

def get_current_yield(market_data, current_date):
    """
    Get current US 10Y Treasury yield for cash allocation decisions.
    """
    if market_data['US10Y'].empty:
        LOG.warning("No US 10Y yield data available, using default 4.0%")
        return 4.0
        
    try:
        recent_data = market_data['US10Y'].loc[:pd.to_datetime(current_date)]
        if recent_data.empty:
            LOG.warning("No recent yield data available, using default 4.0%")
            return 4.0
        return recent_data['yield'].iloc[-1]
    except Exception as e:
        LOG.warning(f"Error getting current yield, using default 4.0%: {e}")
        return 4.0


