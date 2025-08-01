# Test Suite for P/E Data Download

This folder contains tests and demos for the P/E data download functionality.

## Files

### `test_pe_data_download.py`
Comprehensive test suite that validates:
- Date parsing for different manual file formats
- Manual file processing and standardization
- Yahoo Finance P/E data retrieval
- Price-based P/E estimation fallback
- Complete fill-to-recent functionality

**Run tests:**
```bash
python src/test/test_pe_data_download.py
```

### `demo_pe_data_flow.py`
Interactive demonstration of the complete P/E data processing flow:
1. Uses manual downloaded data as input
2. Standardizes different CSV formats
3. Fills gaps to recent dates using fallback methods
4. Shows detailed logging throughout
5. Saves final results to CSV files

**Run demo:**
```bash
python src/test/demo_pe_data_flow.py
```

## Expected P/E Data Flow

The P/E data downloader follows this process:

1. **Input**: User manual downloaded files
   - HSI: `HSI-historical-PE-ratio-*.csv` (Date, Value format)
   - HSTECH: `HS-Tech-historical-PE-ratio-*.csv` (Date, Value format)  
   - SP500: `SPX-historical-PE-ratio-*.csv` (Date, Value format)
   - NASDAQ100: `NASDAQ-historical-PE-ratio-*.csv` (Date, Price, PE Ratio format)

2. **Standardization**: Convert to common format
   - Standardize column names to `date`, `pe_ratio`
   - Parse different date formats consistently
   - Clean and validate data

3. **Fill to Recent Date**: Use fallback methods
   - **Method 1**: Try Yahoo Finance for current P/E
   - **Method 2**: Use price data + earnings assumption
   - Log all attempts and results

4. **Output**: Save complete P/E dataset
   - Combined historical + recent data
   - Consistent format for all assets
   - Ready for strategy calculations

## Manual File Requirements

Place these files in `data/pe/` or project root:

- **HSI**: `HSI-historical-PE-ratio-*.csv`
  - Columns: Date, Value  
  - Date format: "Dec 2021"
  - Source: https://www.hsi.com.hk/index360/schi

- **HSTECH**: `HS-Tech-historical-PE-ratio-*.csv`
  - Columns: Date, Value
  - Date format: "Dec 2021"
  - Source: https://www.hsi.com.hk/index360/schi

- **SP500**: `SPX-historical-PE-ratio-*.csv`
  - Columns: Date, Value
  - Date format: "2025/03/01"
  - Source: https://www.macrotrends.net/2577/sp-500-pe-ratio-price-to-earnings-chart

- **NASDAQ100**: `NASDAQ-historical-PE-ratio-*.csv`
  - Columns: Date, Price, PE Ratio
  - Date format: "2024/12/31"
  - Source: https://www.macrotrends.net/stocks/charts/NDAQ/nasdaq/pe-ratio

## Example Test Output

```
=== Testing Manual File Processing ===
✓ HSI file processed: 5 records
✓ NASDAQ100 file processed: 5 records

=== Testing Yahoo Finance P/E Retrieval ===
✓ Yahoo Finance retrieval successful: P/E = 21.45

=== Testing Fill P/E Data to Recent ===
✓ Successfully filled data: 5 -> 8 data points
  Added 3 recent data points
  Latest P/E: 22.13
```