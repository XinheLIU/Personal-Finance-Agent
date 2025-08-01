# Data Sources

## Complete Data Acquisition System Overview

Our system uses a multi-source data acquisition strategy optimized for accuracy and reliability:

```
Manual Downloads (PE) + API Downloads (Price/Yield) → Standardization → Fill-to-Recent → Strategy
```

### Data Flow Architecture

1. **Manual P/E Downloads** → Authoritative historical data (monthly)
2. **API P/E Downloads** → Real-time data (daily) via AkShare  
3. **API Price Downloads** → Real-time price data via AkShare + Yahoo Finance
4. **API Yield Downloads** → Treasury yield data via FRED + Yahoo Finance fallback
5. **Fill-to-Recent** → Bridge historical to current using Yahoo Finance + price estimation
6. **Standardization** → Uniform format for strategy calculations

---

## P/E Ratio Data (Enhanced System)

### Architecture: Manual + API + Fill-to-Recent

Our P/E data system combines **manual downloads** for historical accuracy with **API downloads** for real-time data, plus **automatic gap filling** to recent dates.

#### **Step 1: Manual Downloads (Historical Foundation)**

| Asset | Source | File Pattern | Format | Frequency |
|-------|--------|-------------|---------|-----------|
| **HSI** | [HSI.com.hk](https://www.hsi.com.hk/index360/schi) | `HSI-hist-PE-ratio-*.(xlsx\|csv)` | Date, Value | Monthly |
| **HSTECH** | [HSI.com.hk](https://www.hsi.com.hk/index360/schi) | `HS-Tech-hist-PE-ratio-*.(xlsx\|csv)` | Date, Value | Monthly |
| **S&P 500** | [Macrotrends](https://www.macrotrends.net/2577/sp-500-pe-ratio-price-to-earnings-chart) | `SPX-historical-PE-ratio-*.(xlsx\|csv)` | Date, Value | Monthly |
| **NASDAQ100** | [Macrotrends](https://www.macrotrends.net/stocks/charts/NDAQ/nasdaq/pe-ratio) | `NASDAQ-historical-PE-ratio-*.(xlsx\|csv)` | Date, Price, PE Ratio | Monthly |

**Manual File Details:**
- **Location**: Place in `data/pe/` or project root
- **File Formats**: Supports both Excel (.xlsx) and CSV (.csv) files
- **Date Formats**: 
  - HSI/HSTECH: "Dec 2021" (converted to 2021-12-31)
  - S&P 500: "2025/03/01" (converted to 2025-03-31)  
  - NASDAQ100: "2024/12/31" (already end of month)
- **Processing**: `process_manual_pe_file()` standardizes all formats and file types

#### **Step 2: API Downloads (Real-time Data)**

**Chinese Indices** (via AkShare):
```python
# CSI300 P/E Data
    import akshare as ak
df = ak.stock_index_pe_lg()  # 沪深300静态市盈率
pe_column = df['静态市盈率']

# CSI500 P/E Data  
df = ak.stock_market_pe_lg()  # 中证500平均市盈率
pe_column = df['平均市盈率']
```

**International Indices**: Use manual downloads (more accurate than API estimates)

#### **Step 3: Fill-to-Recent (Gap Bridging)**

Automatically fills gaps from manual data to current date using 2-step fallback:

```python
def fill_pe_data_to_recent(pe_df, asset_name):
    # Step 1: Try Yahoo Finance for current P/E
    recent_data = get_recent_pe_from_yfinance(ticker)
    
    # Step 2: If Yahoo fails, use price + earnings assumption
    if recent_data is None:
        recent_data = estimate_recent_pe_from_price(asset_name, ticker, pe_df)
    
    # Combine historical + recent
    return pd.concat([pe_df, recent_data])
```

**Fallback Method 1 - Yahoo Finance:**
- Gets `trailingPE` from ticker info
- Creates current data point with today's date
- Works well for major indices (^GSPC, ^NDX, ^HSI)

**Fallback Method 2 - Price-based Estimation:**
- Uses recent price data + latest manual P/E as baseline
- Formula: `PE_new = PE_baseline × (Price_new / Price_baseline)`
- Assumes earnings unchanged (documented limitation)
- Provides detailed logging of estimation process

---

## Stock Price Data

### Primary: AkShare (Chinese Assets)

```python
# Index Data
df = ak.index_zh_a_hist(symbol="000300", period="daily", start_date="20040101")

# ETF Data  
df = ak.fund_etf_hist_em(symbol="159742", period="daily", start_date="20040101")
```

**Assets via AkShare:**
- CSI300 (000300), CSI500 (000905) - Index data
- HSTECH (159742) - ETF data from AkShare

### Fallback: Yahoo Finance

```python
import yfinance as yf
df = yf.download("^GSPC", start='2004-01-01')  # S&P 500
df = yf.download("^NDX", start='2004-01-01')   # NASDAQ 100
df = yf.download("^HSI", start='2004-01-01')   # Hang Seng Index
df = yf.download("TLT", start='2004-01-01')    # Bond ETF
df = yf.download("GLD", start='2004-01-01')    # Gold ETF
```

**Assets via Yahoo Finance:**
- HSI (^HSI), SP500 (^GSPC), NASDAQ100 (^NDX) - Index data
- TLT, GLD, CASH (CASHX) - ETF/Fund data

### Data Processing Pipeline

1. **Primary Source Attempt**: Try AkShare first
2. **Fallback**: Use Yahoo Finance if AkShare fails
3. **Standardization**: Convert to common format (`date`, `close`)
4. **Cleaning**: Remove invalid values, handle timezone issues
5. **Storage**: Save as `ASSET_YYYYMMDD_to_YYYYMMDD.csv`

---

## US Treasury Yield Data

### Primary: FRED API

```python
import requests
from dotenv import load_dotenv

# Get US 10-Year Treasury Rate
url = "https://api.stlouisfed.org/fred/series/observations"
params = {
    "series_id": "DGS10",  # 10-Year Treasury Constant Maturity Rate
    "api_key": os.getenv('FRED_API_KEY'),
    "file_type": "json",
    "observation_start": "2004-01-01"
}
```

**FRED API Features:**
- Clean percentage format (4.38% vs 4.373000144958496%)
- Official Federal Reserve data
- Daily updates, long historical coverage
- Requires free API key from FRED

### Fallback: Yahoo Finance

```python
import yfinance as yf
df = yf.download("^TNX", start='2004-01-01')  # 10-Year Treasury Note Yield
```

**Fallback Process:**
- Automatically tries Yahoo Finance if FRED fails
- Converts 'close' column to 'yield' for consistency
- Ensures data availability even if FRED API is down

---

## Technical Implementation Details

### File Organization

```
data/
├── pe/                    # P/E ratio data
│   ├── HSI_YYYYMMDD_to_YYYYMMDD.csv
│   ├── SP500_YYYYMMDD_to_YYYYMMDD.csv
│   └── ...
├── price/                 # Stock price data  
│   ├── CSI300_YYYYMMDD_to_YYYYMMDD.csv
│   ├── SP500_YYYYMMDD_to_YYYYMMDD.csv
│   └── ...
└── yield/                 # Treasury yield data
    └── US10Y_YYYYMMDD_to_YYYYMMDD.csv
```

### Key Functions

**Data Download Orchestration:**
```python
# Main entry point
def main(refresh=False):
    download_price_data()    # AkShare + Yahoo Finance
    download_pe_data()       # Manual + AkShare + Fill-to-recent  
    download_yield_data()    # FRED + Yahoo Finance fallback
```

**P/E Data Processing:**
```python
def download_pe_data(asset_name, akshare_symbol, manual_file_pattern):
    # 1. Process manual file
    pe_df = process_manual_pe_file(manual_file)
    
    # 2. Fill to recent date
    pe_df = fill_pe_data_to_recent(pe_df, asset_name)
    
    # 3. Save standardized result
    pe_df.to_csv(output_path)
```

**Multi-source Fallback:**
```python
def download_asset_data(asset_name, akshare_symbol, yfinance_ticker):
    # Try AkShare first
    if akshare_symbol:
        data = download_akshare_index(akshare_symbol)
        if data: return data
    
    # Fallback to Yahoo Finance
    if yfinance_ticker:
        data = download_yfinance_data(yfinance_ticker)
        if data: return data
    
    # Raise error if all sources fail
    raise ValueError(f"Failed to download {asset_name} from all sources")
```

### Error Handling & Logging

**Comprehensive Logging:**
- Source attempt logs (AkShare → Yahoo Finance)
- Data processing logs (standardization, cleaning)
- Fill-to-recent process logs (Yahoo PE → Price estimation)
- File save confirmations with date ranges

**Graceful Degradation:**
- If manual P/E file missing → Clear error message with download instructions
- If Yahoo Finance fails → Automatic fallback to price-based estimation
- If FRED fails → Automatic fallback to Yahoo Finance yield data
- If data too old → Automatic gap filling with detailed logging

### Data Quality Assurance

**Validation Checks:**
- Date format consistency across sources
- P/E ratio bounds (0 < PE < 200)
- Yield data bounds (0 < yield < 20%)
- Price data positivity and continuity

**Multi-source Verification:**
- Cross-reference manual P/E with Yahoo Finance estimates
- Compare FRED vs Yahoo Finance yield data
- Log discrepancies for manual review

---

## Usage Examples

### Download All Data
```bash
# Download/refresh all data sources
python src/data_download.py --refresh

# Download only missing data
python src/data_download.py
```

### Run Tests
```bash
# Test P/E data processing
python src/test/test_pe_data_download.py

# Interactive demo of complete flow
python src/test/demo_pe_data_flow.py
```

### Manual File Setup
1. Download required P/E files from sources listed above
2. Place in `data/pe/` directory or project root with correct naming:
   - HSI: `HSI-hist-PE-ratio-*.xlsx` (note: "hist" not "historical")
   - HSTECH: `HS-Tech-hist-PE-ratio-*.xlsx` (note: "hist" not "historical")
   - S&P 500: `SPX-historical-PE-ratio-*.xlsx`
   - NASDAQ100: `NASDAQ-historical-PE-ratio-*.xlsx`
3. Files can be either Excel (.xlsx) or CSV (.csv) format
4. Run data download to process and fill to recent date
5. Check logs for successful processing confirmation

---






# Data Source References


## 一、数据源选择策略

### 按用户级别推荐

| 用户类型 | 推荐方案 | 核心数据源 | 预估成本 |
|----------|----------|------------|----------|
| **初学者** | 免费方案 | AkShare + Yahoo Finance + FRED | 免费 |
| **进阶用户** | 混合方案 | Tushare Pro + Alpha Vantage + 部分付费API | $50-100/月 |
| **专业用户** | 付费方案 | Wind + Bloomberg + 专业数据商 | $500+/月 |

### 按资产类别推荐

| 资产类别 | 国内推荐 | 国际推荐 | 备注 |
|----------|----------|----------|------|
| **股票** | AkShare + Tushare Pro | Yahoo Finance + Alpha Vantage | 免费+付费组合 |
| **债券** | 中债平台 + AkShare | FRED + Investing.com | 专业数据重要 |
| **宏观** | 国家统计局 + Wind | FRED + World Bank | 政府数据优先 |

## 二、国内数据源详览

### 国内股票数据

| 数据源 | 免费/付费 | 覆盖范围 | 主要优势 | 主要限制 |
|--------|-----------|----------|----------|----------|
| **AkShare** | 免费 | A股、ETF、可转债 | 开源、无需注册、实时更新 | 数据质量不稳定 |
| **Tushare Pro** | 积分制/付费 | A股、港股、美股 | 数据质量高、API稳定 | 免费额度有限 |
| **Wind Client API** | 付费 | 全市场 | 专业级数据、权威来源 | 成本高、主要面向机构 |
| **同花顺iFinD** | 付费 | A股为主 | 财务数据丰富 | 个人用户门槛高 |

### 国内债券数据

| 数据源 | 类型 | 覆盖范围 | 特色功能 |
|--------|------|----------|----------|
| **中债数据平台** | 付费/会员免费 | 银行间债券 | 权威估值、收益率曲线 |
| **AkShare债券模块** | 免费 | 交易所债券、可转债 | 实时行情、转股数据 |
| **上交所/深交所** | 免费 | 交易所债券 | 官方数据、发行信息 |

## 三、国际数据源详览

### 国际股票数据

| 数据源 | 免费层级 | 付费层级 | 覆盖市场 | 特色功能 |
|--------|----------|----------|----------|----------|
| **Yahoo Finance** | 完全免费 | - | 全球主要市场 | 历史数据丰富、社区工具多 |
| **Alpha Vantage** | 25次/天 | $49.99-249.99/月 | 全球股票+基本面 | 数据质量高、支持技术指标 |
| **Polygon.io** | 基础免费 | $29-199/月 | 美股为主 | 机构级质量、低延迟 |
| **Finnhub** | 免费额度 | $29-399/月 | 全球股票 | 财报数据、新闻情绪 |
| **IEX Cloud** | 免费额度 | $9-999/月 | 美股 | 实时数据、高质量 |

### 国际债券数据

| 数据源 | 访问方式 | 覆盖范围 | 主要用途 |
|--------|----------|----------|----------|
| **FRED API** | 免费 | 美国宏观、国债收益率 | 宏观分析、基准利率 |
| **FINRA TRACE** | 免费查询/付费API | 美国公司债 | 成交价格、市场透明度 |
| **Investing.com** | 免费 | 全球政府债、公司债 | 行情监控、收益率比较 |
| **Bloomberg** | 付费终端 | 全球债券 | 专业分析、机构标准 |

## 四、免费数据源入门组合

### 基础配置（完全免费）

```text
国内股票：AkShare
国际股票：Yahoo Finance (yfinance)
债券数据：FRED API + AkShare债券模块
宏观数据：FRED + 国家统计局
```

### 代码示例

```python
# 国内股票数据
import akshare as ak
stock_data = ak.stock_zh_a_hist(symbol="000001", start_date="20240101")

# 国际股票数据
import yfinance as yf
spy_data = yf.download("SPY", start="2024-01-01")

# 美国国债收益率
import fredapi
fred = fredapi.Fred(api_key='your_api_key')
us_10y = fred.get_series('DGS10', start='2024-01-01')
```

## 五、付费升级路径

### 第一阶段：轻度付费（$50/月以内）

- **Tushare Pro**：积分购买或月度订阅
- **Alpha Vantage**：基础付费计划
- **Polygon.io**：入门级实时数据

### 第二阶段：专业级（$100-500/月）

- **Wind Client API**：国内专业标准
- **Bloomberg API**：国际专业标准  
- **Refinitiv Eikon**：综合金融数据

### 第三阶段：机构级（$500+/月）

- **Bloomberg Terminal**：行业标杆
- **FactSet**：机构研究平台
- **专业数据供应商**：定制化服务

## 六、数据质量与合规注意事项

### 数据验证

1. **多源交叉验证**：关键指标用2-3个数据源对比
2. **复权处理**：确保价格数据已正确复权
3. **时区统一**：国际数据注意时区转换
4. **缺失值处理**：建立数据清洗流程

### 合规要求

1. **API使用条款**：严格遵守各数据源的使用协议
2. **数据再分发**：避免未经授权的数据转售
3. **访问频率**：遵守API调用频率限制
4. **数据存储**：注意数据本地存储的合规性

### 成本优化建议

1. **免费优先**：充分利用免费数据源
2. **按需付费**：根据策略需求选择付费服务
3. **批量处理**：优化API调用减少成本
4. **缓存策略**：避免重复获取相同数据

## 七、参考资源

### 主要文档链接

- [Tushare Pro官方文档](https://tushare.pro/document/1)
- [AkShare使用手册](https://akshare.akfamily.xyz/)
- [Yahoo Finance API (yfinance)](https://pypi.org/project/yfinance/)
- [Alpha Vantage API文档](https://www.alphavantage.co/documentation/)
- [FRED API指南](https://fred.stlouisfed.org/docs/api/fred/)

### 开源工具推荐

- **量化框架**：[Qlib](https://github.com/microsoft/qlib), [vnpy](https://github.com/vnpy/vnpy)
- **数据处理**：pandas, numpy, scipy
- **可视化**：matplotlib, plotly, seaborn
- **回测引擎**：backtrader, zipline

---

*最后更新：2025年1月* | *适用范围：个人量化投资者* | *建议定期更新API信息*
