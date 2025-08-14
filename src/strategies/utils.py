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



# New helpers that operate on processed, merged strategy data only

def pe_percentile_from_processed(processed_df: pd.DataFrame, asset_name: str, current_date, years: int = 10):
    """
    Calculate P/E percentile using processed strategy DataFrame.
    Expects a column named f"{asset_name}_pe".
    Returns (percentile: float, details: dict)
    """
    pe_col = f"{asset_name}_pe"
    if processed_df is None or processed_df.empty or pe_col not in processed_df.columns:
        error_msg = f"Processed data missing column '{pe_col}'. Ensure data processing includes P/E for {asset_name}."
        LOG.error(error_msg)
        raise ValueError(error_msg)

    end_date = pd.to_datetime(current_date)
    if end_date.tz is not None:
        end_date = end_date.tz_localize(None)
    start_date = end_date - pd.DateOffset(years=years)

    # Clip to available range
    available = processed_df.loc[:end_date]
    if available.empty:
        error_msg = f"No processed data available up to {end_date.date()} for {asset_name}"
        LOG.error(error_msg)
        raise ValueError(error_msg)

    period = processed_df.loc[start_date:end_date]
    if period.empty:
        error_msg = f"No processed P/E data in the {years}Y window for {asset_name}"
        LOG.error(error_msg)
        raise ValueError(error_msg)

    valid_hist = period[pe_col].dropna()
    valid_hist = valid_hist[(valid_hist > 0) & (valid_hist < 200)]
    if valid_hist.empty:
        error_msg = f"No valid processed P/E values for {asset_name} in the specified period"
        LOG.error(error_msg)
        raise ValueError(error_msg)

    recent_series = available[pe_col].dropna()
    if recent_series.empty:
        error_msg = f"No recent processed P/E available for {asset_name}"
        LOG.error(error_msg)
        raise ValueError(error_msg)

    current_pe = float(recent_series.iloc[-1])
    most_recent_date = recent_series.index[-1]
    percentile = float((valid_hist <= current_pe).mean())
    percentile = min(max(percentile, 0.1), 0.9)

    details = {
        'asset': asset_name,
        'pe_col': pe_col,
        'current_pe': current_pe,
        'current_pe_date': most_recent_date.strftime('%Y-%m-%d'),
        'period_start': start_date.strftime('%Y-%m-%d'),
        'period_end': end_date.strftime('%Y-%m-%d'),
        'period_years': years,
        'num_valid_points': int(len(valid_hist)),
        'hist_min': float(valid_hist.min()),
        'hist_median': float(valid_hist.median()),
        'hist_max': float(valid_hist.max()),
    }

    LOG.info(f"[Processed] {asset_name} PE: {current_pe:.2f} @ {most_recent_date.date()} | Percentile: {percentile:.2%}")
    return percentile, details


def yield_percentile_from_processed(processed_df: pd.DataFrame, current_date, years: int = 20) -> float:
    """
    Calculate US10Y yield percentile from processed data (expects 'US10Y_yield').
    """
    col = 'US10Y_yield'
    if processed_df is None or processed_df.empty or col not in processed_df.columns:
        error_msg = "Processed data missing 'US10Y_yield'. Ensure data processing includes yield data."
        LOG.error(error_msg)
        raise ValueError(error_msg)

    end_date = pd.to_datetime(current_date)
    if end_date.tz is not None:
        end_date = end_date.tz_localize(None)
    start_date = end_date - pd.DateOffset(years=years)

    period = processed_df.loc[start_date:end_date]
    if period.empty:
        error_msg = f"No processed yield data in the {years}Y window"
        LOG.error(error_msg)
        raise ValueError(error_msg)

    curr_series = processed_df.loc[:end_date, col].dropna()
    if curr_series.empty:
        error_msg = "No recent processed yield available"
        LOG.error(error_msg)
        raise ValueError(error_msg)

    current_yield = float(curr_series.iloc[-1])
    percentile = float((period[col] <= current_yield).mean())
    return min(max(percentile, 0.1), 0.9)


def current_yield_from_processed(processed_df: pd.DataFrame, current_date) -> float:
    """
    Get latest US10Y yield from processed data; returns 4.0 on failure.
    """
    col = 'US10Y_yield'
    try:
        if processed_df is None or processed_df.empty or col not in processed_df.columns:
            LOG.warning("Processed data missing 'US10Y_yield', using default 4.0%")
            return 4.0
        recent = processed_df.loc[:pd.to_datetime(current_date), col].dropna()
        if recent.empty:
            LOG.warning("No recent processed yield, using default 4.0%")
            return 4.0
        return float(recent.iloc[-1])
    except Exception as e:
        LOG.warning(f"Error reading processed yield, using default 4.0%: {e}")
        return 4.0

