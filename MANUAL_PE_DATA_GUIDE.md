# 📊 Manual PE Data Update Workflow

Your Personal Finance Agent now supports **manual PE data updates** through a dedicated workflow that integrates seamlessly with the simplified singleton storage system.

## 🎯 Quick Start

1. **Drop your PE data files** in: `data/raw/pe/manual/`
2. **Run processing command**: `python src/data_center/download.py --process-manual-pe`
3. **Data automatically merges** with the main system

## 📁 Directory Structure

```
data/raw/pe/
├── manual/              ← **DROP YOUR FILES HERE**
│   ├── README.md        ← Detailed instructions
│   ├── SP500_pe.csv     ← Your manual files
│   └── CSI300_pe.csv    ← Follow naming convention
├── SP500_pe.csv         ← Auto-generated singletons
├── CSI300_pe.csv        ← System uses these
└── [other PE files]
```

## 📋 File Format Requirements

### ✅ Correct Format
```csv
date,pe_ratio
2024-01-01,25.5
2024-02-01,26.3
2024-03-01,24.8
```

### 📝 Column Names Accepted
- **Date**: `date` (required)
- **PE Ratio**: `pe_ratio`, `pe`, `PE`, or `PE_ratio`

### 🎯 Naming Convention
- **Format**: `{ASSET_NAME}_pe.csv`
- **Examples**: `SP500_pe.csv`, `CSI300_pe.csv`, `NASDAQ100_pe.csv`

## 🔄 Processing Commands

### Process Manual PE Data
```bash
python src/data_center/download.py --process-manual-pe
```

### View All Options
```bash
python src/data_center/download.py --help
```

## 🏗️ System Architecture

### Data Flow
1. **Manual Files** → `data/raw/pe/manual/`
2. **Processing** → Validates, cleans, merges data
3. **Singleton Files** → `data/raw/pe/{ASSET}_pe.csv`
4. **Frontend** → Automatically loads updated data

### Priority Order
1. **Processed Singleton Files** (highest priority)
2. **Manual Files** (if singleton doesn't exist)
3. **Legacy Complex Files** (fallback)

## ✨ Features

### 🔀 Smart Merging
- **Preserves History**: Old data is kept
- **Updates Duplicates**: Manual data overwrites existing dates
- **Validates Data**: Removes invalid PE values (>1000 or <0)

### 🛡️ Error Handling
- **Column Validation**: Checks for required columns
- **Data Cleaning**: Removes NaN and unrealistic values
- **Graceful Failures**: Continues processing other files if one fails

### 📊 Comprehensive Logging
- **Processing Status**: Shows success/failure counts
- **Data Statistics**: Record counts and date ranges
- **File Locations**: Shows where data was saved

## 🎮 Usage Examples

### Example 1: Update S&P 500 PE Data
```bash
# 1. Create file: data/raw/pe/manual/SP500_pe.csv
# 2. Run processing
python src/data_center/download.py --process-manual-pe
```

### Example 2: Batch Update Multiple Assets
```bash
# 1. Create files: 
#    data/raw/pe/manual/SP500_pe.csv
#    data/raw/pe/manual/NASDAQ100_pe.csv
#    data/raw/pe/manual/CSI300_pe.csv
# 2. Run processing
python src/data_center/download.py --process-manual-pe
```

## 📈 Supported Assets

- `SP500` - S&P 500 Index
- `NASDAQ100` - NASDAQ-100 Index  
- `CSI300` - CSI 300 Index (China)
- `CSI500` - CSI 500 Index (China)
- `HSI` - Hang Seng Index (Hong Kong)
- `HSTECH` - Hang Seng Tech Index

## 🧹 File Management

### After Processing
Your manual files remain in the `manual/` folder. You can:

1. **Keep for Reference**: Leave them for future updates
2. **Archive**: Move to a backup folder
3. **Delete**: Remove them (data is already merged)

### File Status
- ✅ **Processed**: Data merged into singleton files
- ✅ **Active**: System uses updated data immediately
- ✅ **Persistent**: Data survives system restarts

## 🚀 Integration

### Frontend Integration
- **Streamlit App**: Automatically detects and loads manual data
- **Data Visualization**: Updated charts reflect manual PE data
- **Strategy Analysis**: Strategies use latest manual PE values

### API Integration
- **Data Loader**: Seamlessly integrates manual and automated data
- **Backtrader**: PE data available for strategy backtesting
- **Analytics**: Performance attribution includes manual PE data

## ⚠️ Important Notes

- **Date Format**: Use YYYY-MM-DD format only
- **Data Quality**: System validates and cleans your data automatically
- **Overwrite Behavior**: Manual data overwrites existing dates
- **No Backup**: System doesn't backup original files - keep your copies

## 🆘 Troubleshooting

### Common Issues

**❌ "Missing 'date' column"**
- Fix: Ensure your CSV has a 'date' column

**❌ "No PE ratio column found"**
- Fix: Use one of: pe_ratio, pe, PE, PE_ratio

**❌ "No valid data after cleaning"**
- Fix: Check PE values are between 0 and 1000

### Getting Help

Check the detailed README in the manual folder:
```
data/raw/pe/manual/README.md
```

---

**🎉 Your PE data workflow is now fully automated and integrated with the simplified singleton storage system!**
