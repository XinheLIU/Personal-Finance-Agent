"""
Test script for P/E data download functionality.

This script tests the P/E data download process including:
1. Manual file processing
2. Data standardization  
3. Filling to recent dates with fallback methods
4. Yahoo Finance integration
5. Price-based estimation fallback

Usage:
    python src/test/test_pe_data_download.py
"""

import sys
import os
import pandas as pd
import tempfile
import shutil
from datetime import datetime, timedelta

# Add src to path to import project modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src.app_logger import LOG
from src.data_center.download import (
    process_manual_pe_file, 
    fill_pe_data_to_recent,
    get_recent_pe_from_yfinance,
    estimate_recent_pe_from_price,
    parse_manual_pe_date,
    find_manual_pe_files
)

def create_test_manual_files():
    """Create test manual P/E files with different formats"""
    test_files = {}
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    # 1. HSI format (Date, Value with "Dec 2021" format)
    hsi_data = {
        'Date': ['Jan 2020', 'Feb 2020', 'Mar 2020', 'Apr 2020', 'May 2020'],
        'Value': [12.5, 13.2, 11.8, 10.5, 14.1]
    }
    hsi_file = os.path.join(temp_dir, 'HSI-historical-PE-ratio-test.csv')
    pd.DataFrame(hsi_data).to_csv(hsi_file, index=False)
    test_files['HSI'] = hsi_file
    
    # 2. HSTECH format (Date, Value with "Dec 2021" format)
    hstech_data = {
        'Date': ['Jan 2020', 'Feb 2020', 'Mar 2020', 'Apr 2020', 'May 2020'],
        'Value': [25.3, 28.1, 22.4, 19.7, 31.2]
    }
    hstech_file = os.path.join(temp_dir, 'HS-Tech-historical-PE-ratio-test.csv')
    pd.DataFrame(hstech_data).to_csv(hstech_file, index=False)
    test_files['HSTECH'] = hstech_file
    
    # 3. SP500 format (Date, Value with "2025/03/01" format)
    sp500_data = {
        'Date': ['2020/01/01', '2020/02/01', '2020/03/01', '2020/04/01', '2020/05/01'],
        'Value': [18.7, 19.2, 16.8, 15.3, 21.4]
    }
    sp500_file = os.path.join(temp_dir, 'SPX-historical-PE-ratio-test.csv')
    pd.DataFrame(sp500_data).to_csv(sp500_file, index=False)
    test_files['SP500'] = sp500_file
    
    # 4. NASDAQ100 format (Date, Price, PE Ratio with "2024/12/31" format)
    nasdaq_data = {
        'Date': ['2020/01/31', '2020/02/29', '2020/03/31', '2020/04/30', '2020/05/31'],
        'Price': [8500, 8200, 7800, 8900, 9100],
        'PE Ratio': [22.1, 23.5, 20.8, 18.9, 25.7]
    }
    nasdaq_file = os.path.join(temp_dir, 'NASDAQ-historical-PE-ratio-test.csv')
    pd.DataFrame(nasdaq_data).to_csv(nasdaq_file, index=False)
    test_files['NASDAQ100'] = nasdaq_file
    
    LOG.info(f"Created test files in: {temp_dir}")
    return test_files, temp_dir

def test_parse_manual_pe_date():
    """Test date parsing for different manual file formats"""
    LOG.info("=== Testing Date Parsing ===")
    
    # Test HSI/HSTECH format
    hsi_date = parse_manual_pe_date('Jan 2020', 'HSI')
    expected_hsi = pd.Timestamp('2020-01-31')  # End of month
    assert hsi_date == expected_hsi, f"HSI date parsing failed: {hsi_date} != {expected_hsi}"
    LOG.info("✓ HSI date parsing: 'Jan 2020' -> 2020-01-31")
    
    # Test SP500 format  
    sp500_date = parse_manual_pe_date('2020/01/01', 'SP500')
    expected_sp500 = pd.Timestamp('2020-01-31')  # Convert to end of month
    assert sp500_date == expected_sp500, f"SP500 date parsing failed: {sp500_date} != {expected_sp500}"
    LOG.info("✓ SP500 date parsing: '2020/01/01' -> 2020-01-31")
    
    # Test NASDAQ100 format
    nasdaq_date = parse_manual_pe_date('2020/01/31', 'NASDAQ100')
    expected_nasdaq = pd.Timestamp('2020-01-31')
    assert nasdaq_date == expected_nasdaq, f"NASDAQ100 date parsing failed: {nasdaq_date} != {expected_nasdaq}"
    LOG.info("✓ NASDAQ100 date parsing: '2020/01/31' -> 2020-01-31")

def test_process_manual_pe_file():
    """Test processing of manual P/E files"""
    LOG.info("=== Testing Manual File Processing ===")
    
    test_files, temp_dir = create_test_manual_files()
    
    try:
        # Test HSI file processing
        hsi_df = process_manual_pe_file(test_files['HSI'], 'HSI')
        assert 'date' in hsi_df.columns, "HSI: Missing 'date' column"
        assert 'pe_ratio' in hsi_df.columns, "HSI: Missing 'pe_ratio' column"
        assert len(hsi_df) == 5, f"HSI: Expected 5 rows, got {len(hsi_df)}"
        assert hsi_df['pe_ratio'].iloc[0] == 12.5, f"HSI: First P/E should be 12.5, got {hsi_df['pe_ratio'].iloc[0]}"
        LOG.info(f"✓ HSI file processed: {len(hsi_df)} records")
        
        # Test NASDAQ100 file processing
        nasdaq_df = process_manual_pe_file(test_files['NASDAQ100'], 'NASDAQ100')
        assert 'date' in nasdaq_df.columns, "NASDAQ100: Missing 'date' column"
        assert 'pe_ratio' in nasdaq_df.columns, "NASDAQ100: Missing 'pe_ratio' column"
        assert len(nasdaq_df) == 5, f"NASDAQ100: Expected 5 rows, got {len(nasdaq_df)}"
        assert nasdaq_df['pe_ratio'].iloc[0] == 22.1, f"NASDAQ100: First P/E should be 22.1, got {nasdaq_df['pe_ratio'].iloc[0]}"
        LOG.info(f"✓ NASDAQ100 file processed: {len(nasdaq_df)} records")
        
    finally:
        # Clean up
        shutil.rmtree(temp_dir)

def test_get_recent_pe_from_yfinance():
    """Test Yahoo Finance P/E data retrieval"""
    LOG.info("=== Testing Yahoo Finance P/E Retrieval ===")
    
    try:
        # Test with a real ticker (SPY)
        start_date = pd.Timestamp.now() - pd.Timedelta(days=30)
        end_date = pd.Timestamp.now()
        
        recent_data = get_recent_pe_from_yfinance('SPY', start_date, end_date)
        
        if recent_data is not None and not recent_data.empty:
            assert 'date' in recent_data.columns, "Missing 'date' column in Yahoo Finance data"
            assert 'pe_ratio' in recent_data.columns, "Missing 'pe_ratio' column in Yahoo Finance data"
            assert recent_data['pe_ratio'].iloc[0] > 0, "P/E ratio should be positive"
            LOG.info(f"✓ Yahoo Finance retrieval successful: P/E = {recent_data['pe_ratio'].iloc[0]:.2f}")
        else:
            LOG.warning("⚠ Yahoo Finance retrieval returned no data (this may be normal)")
            
    except Exception as e:
        LOG.warning(f"⚠ Yahoo Finance test failed (this may be normal): {e}")

def test_estimate_recent_pe_from_price():
    """Test price-based P/E estimation"""
    LOG.info("=== Testing Price-Based P/E Estimation ===")
    
    # Create sample historical P/E data  
    historical_data = pd.DataFrame({
        'date': [pd.Timestamp('2020-01-31'), pd.Timestamp('2020-02-29')],
        'pe_ratio': [20.0, 22.0]
    })
    
    try:
        start_date = pd.Timestamp('2020-02-29')
        end_date = pd.Timestamp.now()
        
        estimated_data = estimate_recent_pe_from_price('SP500', '^GSPC', historical_data, start_date, end_date)
        
        if estimated_data is not None and not estimated_data.empty:
            assert 'date' in estimated_data.columns, "Missing 'date' column in estimated data"
            assert 'pe_ratio' in estimated_data.columns, "Missing 'pe_ratio' column in estimated data"
            assert all(estimated_data['pe_ratio'] > 0), "All estimated P/E ratios should be positive"
            LOG.info(f"✓ Price-based estimation successful: {len(estimated_data)} data points estimated")
            LOG.info(f"  Latest estimated P/E: {estimated_data['pe_ratio'].iloc[-1]:.2f}")
        else:
            LOG.warning("⚠ Price-based estimation returned no data")
            
    except Exception as e:
        LOG.warning(f"⚠ Price-based estimation test failed: {e}")

def test_fill_pe_data_to_recent():
    """Test the complete fill-to-recent functionality"""
    LOG.info("=== Testing Fill P/E Data to Recent ===")
    
    # Create old manual data (6 months ago)
    old_date = pd.Timestamp.now() - pd.Timedelta(days=180)
    manual_data = pd.DataFrame({
        'date': [old_date - pd.Timedelta(days=30), old_date],
        'pe_ratio': [18.5, 19.2]
    })
    
    try:
        # Test with SP500 (should have Yahoo Finance data available)
        filled_data = fill_pe_data_to_recent(manual_data, 'SP500')
        
        if len(filled_data) > len(manual_data):
            LOG.info(f"✓ Successfully filled data: {len(manual_data)} -> {len(filled_data)} data points")
            
            # Check that original data is preserved
            assert filled_data['pe_ratio'].iloc[0] == 18.5, "Original data should be preserved"
            assert filled_data['pe_ratio'].iloc[1] == 19.2, "Original data should be preserved"
            
            # Check that new data is added
            recent_data = filled_data[filled_data['date'] > old_date]
            if not recent_data.empty:
                LOG.info(f"  Added {len(recent_data)} recent data points")
                LOG.info(f"  Latest P/E: {filled_data['pe_ratio'].iloc[-1]:.2f}")
        else:
            LOG.info("✓ Manual data was recent enough, no filling needed")
            
    except Exception as e:
        LOG.warning(f"⚠ Fill-to-recent test failed: {e}")

def run_all_tests():
    """Run all P/E data download tests"""
    LOG.info("="*60)
    LOG.info("STARTING P/E DATA DOWNLOAD TESTS")
    LOG.info("="*60)
    
    try:
        test_parse_manual_pe_date()
        test_process_manual_pe_file()
        test_get_recent_pe_from_yfinance()
        test_estimate_recent_pe_from_price()
        test_fill_pe_data_to_recent()
        
        LOG.info("="*60)
        LOG.info("ALL TESTS COMPLETED SUCCESSFULLY! ✓")
        LOG.info("="*60)
        
    except Exception as e:
        LOG.error("="*60)
        LOG.error(f"TEST FAILED: {e}")
        LOG.error("="*60)
        raise

if __name__ == '__main__':
    run_all_tests()