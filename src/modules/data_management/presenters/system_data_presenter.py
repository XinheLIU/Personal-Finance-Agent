"""
System Data Presenter

Orchestrates data management, system health monitoring, and accounting data operations.
Separates business logic from UI concerns for better testability and reusability.
"""

import os
import pandas as pd
from datetime import date
from typing import Dict, Any, List, Tuple, Optional

from src.modules.data_management.data_center.download import main as download_data_main, get_data_range_info
from src.modules.data_management.data_center.data_processor import (
    get_processing_status,
    process_all_strategies,
    cleanup_processed_data
)
from src.modules.portfolio.strategies.registry import strategy_registry
from src.ui.app_logger import LOG
from src.modules.data_management.visualization.data_access import load_data_for_visualization

# Import accounting data management components
from src.modules.accounting.core.data_storage import MonthlyDataStorage
from src.modules.accounting.core.data_storage_utils import (
    get_current_year_month, 
    get_recent_months, 
    validate_month_format,
    csv_to_dataframe
)
from src.modules.accounting.core.report_storage import MonthlyReportStorage


class SystemDataPresenter:
    """Presenter for system data management operations."""
    
    def __init__(self):
        self.data_storage = MonthlyDataStorage()
        self.report_storage = MonthlyReportStorage()
    
    def get_available_data(self) -> pd.DataFrame:
        """Get information about available data files using singleton storage system."""
        data_files = []
        
        # Import here to avoid circular imports
        from config.assets import ASSETS, PE_ASSETS
        
        # Check price data (singleton files)
        price_dir = os.path.join("data", "raw", "price")
        if os.path.exists(price_dir):
            for asset_name in ASSETS.keys():
                singleton_file = os.path.join(price_dir, f"{asset_name}_price.csv")
                if os.path.exists(singleton_file):
                    try:
                        df = pd.read_csv(singleton_file)
                        start_date, end_date = get_data_range_info(df)
                        # Compute freshness
                        days_since_update = None
                        stale_flag = "Unknown"
                        if end_date is not None:
                            try:
                                days_since_update = (date.today() - end_date.date()).days
                                stale_flag = "Yes" if days_since_update is not None and days_since_update > 30 else "No"
                            except Exception:
                                pass
                        data_files.append({
                            "Type": "PRICE",
                            "Asset": asset_name,
                            "Start Date": start_date.strftime('%Y-%m-%d') if start_date else "N/A",
                            "End Date": end_date.strftime('%Y-%m-%d') if end_date else "N/A",
                            "Records": len(df),
                            "Last Updated (days)": days_since_update if days_since_update is not None else "N/A",
                            "Stale (>30d)": stale_flag
                        })
                    except Exception as e:
                        LOG.error(f"Error reading price data file {singleton_file}: {e}")
        
        # Check PE data (singleton files + manual folder)
        pe_dir = os.path.join("data", "raw", "pe")
        if os.path.exists(pe_dir):
            for asset_name in PE_ASSETS.keys():
                # Check singleton file first, then manual folder
                singleton_file = os.path.join(pe_dir, f"{asset_name}_pe.csv")
                manual_file = os.path.join(pe_dir, "manual", f"{asset_name}_pe.csv")
                
                pe_file = None
                data_source = "Auto"
                if os.path.exists(singleton_file):
                    pe_file = singleton_file
                    data_source = "Auto"
                elif os.path.exists(manual_file):
                    pe_file = manual_file
                    data_source = "Manual"
                
                if pe_file:
                    try:
                        df = pd.read_csv(pe_file)
                        start_date, end_date = get_data_range_info(df)
                        # Compute freshness
                        days_since_update = None
                        stale_flag = "Unknown"
                        if end_date is not None:
                            try:
                                days_since_update = (date.today() - end_date.date()).days
                                stale_flag = "Yes" if days_since_update is not None and days_since_update > 30 else "No"
                            except Exception:
                                pass
                        data_files.append({
                            "Type": "PE",
                            "Asset": f"{asset_name} ({data_source})",
                            "Start Date": start_date.strftime('%Y-%m-%d') if start_date else "N/A",
                            "End Date": end_date.strftime('%Y-%m-%d') if end_date else "N/A",
                            "Records": len(df),
                            "Last Updated (days)": days_since_update if days_since_update is not None else "N/A",
                            "Stale (>30d)": stale_flag
                        })
                    except Exception as e:
                        LOG.error(f"Error reading PE data file {pe_file}: {e}")
        
        # Check yield data (singleton file)
        yield_dir = os.path.join("data", "raw", "yield")
        yield_file = os.path.join(yield_dir, "US10Y_yield.csv")
        if os.path.exists(yield_file):
            try:
                df = pd.read_csv(yield_file)
                start_date, end_date = get_data_range_info(df)
                # Compute freshness
                days_since_update = None
                stale_flag = "Unknown"
                if end_date is not None:
                    try:
                        days_since_update = (date.today() - end_date.date()).days
                        stale_flag = "Yes" if days_since_update is not None and days_since_update > 30 else "No"
                    except Exception:
                        pass
                data_files.append({
                    "Type": "YIELD",
                    "Asset": "US10Y",
                    "Start Date": start_date.strftime('%Y-%m-%d') if start_date else "N/A",
                    "End Date": end_date.strftime('%Y-%m-%d') if end_date else "N/A",
                    "Records": len(df),
                    "Last Updated (days)": days_since_update if days_since_update is not None else "N/A",
                    "Stale (>30d)": stale_flag
                })
            except Exception as e:
                LOG.error(f"Error reading yield data file {yield_file}: {e}")
        
        return pd.DataFrame(data_files) if data_files else pd.DataFrame()
    
    def refresh_all_data(self) -> str:
        """Refresh all data by downloading latest information."""
        try:
            download_data_main(refresh=True)
            return "Data download completed successfully!"
        except Exception as e:
            LOG.error(f"Data download failed: {e}")
            return f"Data download failed: {e}"
    
    def download_new_ticker(self, ticker: str) -> str:
        """Download data for a new ticker symbol."""
        try:
            from src.modules.data_management.data_center.download import download_yfinance_data, download_akshare_index
            
            # Try yfinance first
            filepath, _, _ = download_yfinance_data(ticker, ticker)
            if filepath:
                return f"Successfully downloaded {ticker} from yfinance."
            else:
                # Try akshare
                filepath, _, _ = download_akshare_index(ticker, ticker)
                if filepath:
                    return f"Successfully downloaded {ticker} from akshare."
                else:
                    return f"Failed to download {ticker} from both sources."
        except Exception as e:
            LOG.error(f"Error downloading {ticker}: {e}")
            return f"Error downloading {ticker}: {e}"
    
    def get_system_health_status(self) -> Dict[str, Any]:
        """Get system health status and metrics."""
        data_df = self.get_available_data()
        
        if not data_df.empty:
            total_files = len(data_df)
            price_files = len(data_df[data_df['Type'] == 'PRICE'])
            pe_files = len(data_df[data_df['Type'] == 'PE'])
            yield_files = len(data_df[data_df['Type'] == 'YIELD'])

            # Freshness
            def _is_stale(v):
                try:
                    return (v == "N/A") or (float(v) > 30)
                except Exception:
                    return True
            stale_count = data_df["Last Updated (days)"].apply(_is_stale).sum() if "Last Updated (days)" in data_df.columns else 0
        else:
            total_files = price_files = pe_files = yield_files = stale_count = 0
        
        # Strategy registry status
        strategies = strategy_registry.list_strategies()
        
        return {
            'total_files': total_files,
            'price_files': price_files,
            'pe_files': pe_files,
            'yield_files': yield_files,
            'stale_files': int(stale_count),
            'available_strategies': len(strategies)
        }
    
    def get_processing_status(self) -> Dict[str, Any]:
        """Get processed data status."""
        try:
            status = get_processing_status()
            processed = status.get('processed_strategies', [])
            return {
                'processed_strategies': processed,
                'has_processed_data': len(processed) > 0
            }
        except Exception as e:
            LOG.error(f"Failed to load processing status: {e}")
            return {'processed_strategies': [], 'has_processed_data': False, 'error': str(e)}
    
    def process_all_strategies(self) -> Dict[str, Any]:
        """Process all strategies and return results."""
        try:
            results = process_all_strategies(force_refresh=True)
            success_count = sum(1 for v in results.values() if v)
            return {
                'success': True,
                'processed_count': success_count,
                'total_count': len(results),
                'message': f"Processed {success_count}/{len(results)} strategies."
            }
        except Exception as e:
            LOG.error(f"Processing failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def cleanup_processed_data(self) -> Dict[str, Any]:
        """Clean up processed data cache."""
        try:
            cleanup_processed_data()
            return {'success': True, 'message': 'Processed data cache cleaned.'}
        except Exception as e:
            LOG.error(f"Cleanup failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_accounting_data_info(self, time_range: str = "Last 12 months") -> Dict[str, Any]:
        """Get accounting data information for the specified time range."""
        try:
            available_months = self.data_storage.list_available_months()
            
            if not available_months:
                return {
                    'has_data': False,
                    'months': [],
                    'transactions_count': 0,
                    'message': "No accounting data found. Upload some data to get started!"
                }
            
            # Filter months based on selection
            if time_range == "All data":
                display_months = available_months
            else:
                month_count = int(time_range.split()[1])
                display_months = sorted(available_months, reverse=True)[:month_count]
            
            # Load and combine data from all selected months
            all_transactions = []
            for month in display_months:
                transactions_df, _ = self.data_storage.load_monthly_data(month)
                if transactions_df is not None:
                    all_transactions.append(transactions_df)
            
            if all_transactions:
                combined = pd.concat(all_transactions, ignore_index=True)
                return {
                    'has_data': True,
                    'months': display_months,
                    'transactions_count': len(combined),
                    'message': f"Loaded {len(combined)} transactions from {len(display_months)} months"
                }
            else:
                return {
                    'has_data': False,
                    'months': display_months,
                    'transactions_count': 0,
                    'message': "No transaction data found in selected months"
                }
                
        except Exception as e:
            LOG.error(f"Error getting accounting data info: {e}")
            return {
                'has_data': False,
                'months': [],
                'transactions_count': 0,
                'error': str(e)
            }
    
    def load_combined_transactions(self, months: List[str]) -> pd.DataFrame:
        """Load and combine transactions from multiple months."""
        all_transactions = []
        
        for month in months:
            transactions_df, _ = self.data_storage.load_monthly_data(month)
            if transactions_df is not None:
                transactions_df['month'] = month  # Add month column for tracking
                all_transactions.append(transactions_df)
        
        if all_transactions:
            combined = pd.concat(all_transactions, ignore_index=True)
            # Sort by month (newest first) - transactions don't have date column
            combined = combined.sort_values('month', ascending=False)
            return combined
        
        return pd.DataFrame()
    
    def get_visualization_data(self) -> Dict[str, pd.DataFrame]:
        """Get data for visualization."""
        return load_data_for_visualization()
