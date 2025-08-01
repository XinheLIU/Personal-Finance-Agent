"""
Demo script showing the expected P/E data download flow.

This demonstrates:
1. Processing manual P/E files
2. Standardizing different formats 
3. Filling to recent dates using fallback methods
4. Detailed logging throughout the process

Usage:
    python src/test/demo_pe_data_flow.py
"""

import sys
import os
import pandas as pd
import tempfile

# Add src to path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app_logger import LOG
from data_download import download_pe_data
from config import PE_ASSETS

def create_demo_manual_file():
    """Create a demo manual P/E file (HSI format)"""
    # Create a temporary HSI file with old data (to trigger fill-to-recent)
    temp_dir = tempfile.mkdtemp()
    
    # Data from 6 months ago to trigger recent filling
    demo_data = {
        'Date': ['Jul 2024', 'Aug 2024', 'Sep 2024', 'Oct 2024', 'Nov 2024'],
        'Value': [12.5, 13.2, 11.8, 10.5, 14.1]
    }
    
    demo_file = os.path.join(temp_dir, 'HSI-historical-PE-ratio-demo.csv')
    pd.DataFrame(demo_data).to_csv(demo_file, index=False)
    
    LOG.info(f"Created demo manual file: {demo_file}")
    return demo_file, temp_dir

def demo_pe_data_flow():
    """Demonstrate the complete P/E data processing flow"""
    LOG.info("="*80)
    LOG.info("DEMO: P/E Data Download Flow")
    LOG.info("="*80)
    
    LOG.info("Expected behavior:")
    LOG.info("1. ✓ Use manual downloaded data as input")
    LOG.info("2. ✓ Standardize it to common format")
    LOG.info("3. ✓ Fill to recent date using:")
    LOG.info("   - First try Yahoo Finance")
    LOG.info("   - If Yahoo fails, use price + earnings assumption")
    LOG.info("4. ✓ Print detailed logs for everything")
    LOG.info("5. ✓ Save to separate CSV files")
    LOG.info("")
    
    try:
        # Create demo file
        demo_file, temp_dir = create_demo_manual_file()
        
        # Temporarily modify the search path to include our demo file
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        LOG.info("--- STEP 1: Processing Manual File ---")
        LOG.info("Input: HSI-historical-PE-ratio-demo.csv")
        LOG.info("Format: Date (Jul 2024), Value (12.5)")
        LOG.info("")
        
        # The download_pe_data function will:
        # 1. Find the manual file
        # 2. Process and standardize it  
        # 3. Fill to recent date using fallbacks
        # 4. Save the result
        
        try:
            filepath, start_date, end_date = download_pe_data(
                asset_name='HSI',
                manual_file_pattern='HSI-historical-PE-ratio', 
                refresh=True
            )
            
            LOG.info("--- STEP 5: Final Result ---")
            LOG.info(f"Saved complete P/E data to: {filepath}")
            LOG.info(f"Date range: {start_date.date()} to {end_date.date()}")
            
            # Show the final result
            result_df = pd.read_csv(filepath)
            LOG.info(f"Total data points: {len(result_df)}")
            LOG.info("Sample data:")
            LOG.info(result_df.head().to_string(index=False))
            LOG.info("...")
            LOG.info(result_df.tail().to_string(index=False))
            
        except Exception as e:
            LOG.error(f"Demo failed: {e}")
            
        finally:
            # Restore original directory
            os.chdir(original_cwd)
            
            # Clean up
            import shutil
            shutil.rmtree(temp_dir)
            
    except Exception as e:
        LOG.error(f"Demo setup failed: {e}")

def show_pe_assets_config():
    """Show the current P/E assets configuration"""
    LOG.info("="*60)
    LOG.info("CURRENT P/E ASSETS CONFIGURATION")
    LOG.info("="*60)
    
    for asset_name, config in PE_ASSETS.items():
        LOG.info(f"{asset_name}:")
        if config.get('manual_file'):
            LOG.info(f"  Type: Manual download")
            LOG.info(f"  File pattern: {config['manual_file']}*.csv")
            LOG.info(f"  Expected location: data/pe/ or project root")
        elif config.get('akshare'):
            LOG.info(f"  Type: Akshare API")
            LOG.info(f"  Symbol: {config['akshare']}")
        LOG.info("")

if __name__ == '__main__':
    show_pe_assets_config()
    demo_pe_data_flow()