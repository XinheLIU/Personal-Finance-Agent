# Manual PE Data Updates

This folder is for **manual PE data updates** that cannot be automatically downloaded by the system.

## 📁 File Naming Convention

Use the **singleton naming convention** for consistency:
- `{ASSET_NAME}_pe.csv` (e.g., `SP500_pe.csv`, `CSI300_pe.csv`)

## 📊 Required CSV Format

Your CSV files should have the following columns:

```csv
date,pe_ratio
2024-01-01,25.5
2024-02-01,26.3
2024-03-01,24.8
```

### Column Requirements:
- **`date`**: Date in YYYY-MM-DD format
- **`pe_ratio`**: PE ratio as a decimal number (e.g., 25.5, not 2550%)

## 🔄 How to Update PE Data

1. **Drop your CSV files here** with the correct naming format
2. **Run the data processing**: `python src/data_center/download.py --process-manual-pe`
3. **System will automatically**:
   - Merge your manual data with existing automated data
   - Remove duplicates (manual data takes precedence)
   - Update the main PE singleton files
   - Clean and validate the data

## 📈 Supported Assets

You can provide manual PE data for any of these assets:
- `SP500_pe.csv` - S&P 500 Index
- `NASDAQ100_pe.csv` - NASDAQ-100 Index  
- `CSI300_pe.csv` - CSI 300 Index (China)
- `CSI500_pe.csv` - CSI 500 Index (China)
- `HSI_pe.csv` - Hang Seng Index (Hong Kong)
- `HSTECH_pe.csv` - Hang Seng Tech Index

## ⚠️ Important Notes

- **Manual data overwrites automated data** for the same dates
- **Keep your source files** - the system will copy and merge, not move
- **Date format is critical** - use YYYY-MM-DD format only
- **Validate your data** - unrealistic PE values (>1000 or <0) will be filtered out

## 🧹 After Processing

Once processed, you can:
- Keep files here for future reference
- Move them to a backup folder
- Delete them (data is already merged into main system)

The system will continue to use your manual data until you provide updates or remove the files.
