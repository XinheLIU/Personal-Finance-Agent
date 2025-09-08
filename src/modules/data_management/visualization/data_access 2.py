"""
Data access utilities for visualization components.

Provides functions to load cleaned singleton data files for charts
without importing Streamlit pages, avoiding circular dependencies.
"""

import os
from typing import Dict

import pandas as pd

from src.ui.app_logger import LOG


def _load_singleton_data_file(file_path: str, data_type: str, asset_name: str) -> pd.DataFrame:
    """Load and clean a singleton data file for visualization."""
    try:
        df = pd.read_csv(file_path)

        if df.empty:
            LOG.warning(f"Empty data file: {file_path}")
            return None

        # Enhanced date parsing
        date_col = None
        if 'date' in df.columns:
            date_col = 'date'
        elif 'Date' in df.columns:
            date_col = 'Date'
        elif len(df.columns) > 0:
            date_col = df.columns[0]

        if date_col:
            try:
                df['Date'] = pd.to_datetime(df[date_col], errors='coerce')
                # Remove invalid dates
                df = df.dropna(subset=['Date'])
            except Exception as e:
                LOG.warning(f"Date parsing error in {file_path}: {e}")
                return None

        # Enhanced value column detection
        value_col = None
        if data_type == "price":
            if 'close' in df.columns:
                value_col = 'close'
            elif 'Close' in df.columns:
                value_col = 'Close'
            elif '收盘' in df.columns:
                value_col = '收盘'
        elif data_type == "pe":
            if 'pe' in df.columns:
                value_col = 'pe'
            elif 'PE' in df.columns:
                value_col = 'PE'
            elif 'pe_ratio' in df.columns:
                value_col = 'pe_ratio'
        elif data_type == "yield":
            if 'yield' in df.columns:
                value_col = 'yield'
            elif 'Yield' in df.columns:
                value_col = 'Yield'
            elif 'Close' in df.columns:  # Yield files sometimes use Close column
                value_col = 'Close'

        # Fallback to last column if no specific column found
        if not value_col and len(df.columns) > 1:
            value_col = df.columns[-1]

        if value_col and value_col in df.columns:
            df['Value'] = pd.to_numeric(df[value_col], errors='coerce')
            # Remove invalid values
            df = df.dropna(subset=['Value'])

            # Filter out unrealistic PE values for PE data
            if data_type == "pe":
                df = df[(df['Value'] > 0) & (df['Value'] < 100)]  # Reasonable PE range

            if not df.empty:
                return df[['Date', 'Value']].copy()
            else:
                LOG.warning(f"No valid data after cleaning: {file_path}")
                return None
        else:
            LOG.warning(f"Could not identify value column in {file_path}")
            return None

    except Exception as e:
        LOG.error(f"Error loading data file {file_path}: {e}")
        return None


def load_data_for_visualization() -> Dict[str, pd.DataFrame]:
    """Load data for visualization using singleton files with fallback to old naming."""
    data_dict: Dict[str, pd.DataFrame] = {}

    # Import here to avoid circular imports
    from config.assets import ASSETS, PE_ASSETS

    # Load price data using singleton files
    price_dir = os.path.join("data", "raw", "price")
    if os.path.exists(price_dir):
        for asset_name in ASSETS.keys():
            # Try singleton file first
            singleton_file = os.path.join(price_dir, f"{asset_name}_price.csv")
            if os.path.exists(singleton_file):
                try:
                    df = _load_singleton_data_file(singleton_file, "price", asset_name)
                    if df is not None:
                        data_dict[f"{asset_name} (PRICE)"] = df
                except Exception as e:
                    LOG.error(f"Error loading singleton price file {singleton_file}: {e}")

    # Load PE data using singleton files (check manual folder too)
    pe_dir = os.path.join("data", "raw", "pe")
    if os.path.exists(pe_dir):
        for asset_name in PE_ASSETS.keys():
            # Try singleton file first, then manual folder
            singleton_file = os.path.join(pe_dir, f"{asset_name}_pe.csv")
            manual_file = os.path.join(pe_dir, "manual", f"{asset_name}_pe.csv")

            pe_file = None
            if os.path.exists(singleton_file):
                pe_file = singleton_file
            elif os.path.exists(manual_file):
                pe_file = manual_file
                LOG.info(f"Using manual PE data for {asset_name}")

            if pe_file:
                try:
                    df = _load_singleton_data_file(pe_file, "pe", asset_name)
                    if df is not None:
                        data_dict[f"{asset_name} (PE)"] = df
                except Exception as e:
                    LOG.error(f"Error loading PE file {pe_file}: {e}")

    # Load yield data using singleton file
    yield_dir = os.path.join("data", "raw", "yield")
    yield_file = os.path.join(yield_dir, "US10Y_yield.csv")
    if os.path.exists(yield_file):
        try:
            df = _load_singleton_data_file(yield_file, "yield", "US10Y")
            if df is not None:
                data_dict["US10Y (YIELD)"] = df
        except Exception as e:
            LOG.error(f"Error loading singleton yield file {yield_file}: {e}")

    return data_dict


