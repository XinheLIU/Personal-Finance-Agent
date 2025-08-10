#!/usr/bin/env python3
"""
Debug script to check Excel files in data/pe/ directory
"""

import pandas as pd
import os
import glob

def check_excel_file(filepath):
    """Check if an Excel file can be read and what it contains"""
    print(f"\n=== Checking {filepath} ===")
    
    if not os.path.exists(filepath):
        print(f"❌ File does not exist: {filepath}")
        return False
    
    try:
        # Check file size
        file_size = os.path.getsize(filepath)
        print(f"File size: {file_size} bytes")
        
        if file_size == 0:
            print("❌ File is empty")
            return False
        
        # Try to read with openpyxl
        try:
            df = pd.read_excel(filepath, engine='openpyxl')
            print(f"✅ Successfully read with openpyxl")
            print(f"Shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            if not df.empty:
                print("First few rows:")
                print(df.head().to_string())
            return True
        except Exception as e:
            print(f"❌ openpyxl failed: {e}")
        
        # Try to read with default engine
        try:
            df = pd.read_excel(filepath)
            print(f"✅ Successfully read with default engine")
            print(f"Shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            if not df.empty:
                print("First few rows:")
                print(df.head().to_string())
            return True
        except Exception as e:
            print(f"❌ Default engine failed: {e}")
        
        return False
        
    except Exception as e:
        print(f"❌ General error: {e}")
        return False

def main():
    print("=== Excel File Debug Tool ===")
    
    # Check for required libraries
    try:
        import openpyxl
        print("✅ openpyxl is available")
    except ImportError:
        print("❌ openpyxl is NOT available - install with: pip install openpyxl")
    
    # Find all Excel files in data/pe/
    excel_files = glob.glob("data/pe/*.xlsx")
    
    if not excel_files:
        print("No Excel files found in data/pe/")
        return
    
    print(f"Found {len(excel_files)} Excel files:")
    for filepath in sorted(excel_files):
        print(f"  - {filepath}")
    
    # Check each file
    success_count = 0
    for filepath in sorted(excel_files):
        if check_excel_file(filepath):
            success_count += 1
    
    print(f"\n=== Summary ===")
    print(f"Successfully read {success_count}/{len(excel_files)} files")

if __name__ == '__main__':
    main()