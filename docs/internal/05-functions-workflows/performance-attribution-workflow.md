# Performance Attribution Analysis Workflow

## Overview
Decomposes portfolio returns into allocation, selection, and interaction effects using Brinson attribution methodology. Analyzes how asset/sector choices and weights contribute to performance vs benchmark.

## 🏗️ Architecture

```
src/modules/portfolio/performance/
├── attribution.py           # PerformanceAttributor ⭐
└── sector_attribution.py    # SectorAttributor (Brinson)

config/
└── sectors.py              # Sector classification mapping
```

## 📊 Data Flow

```
Portfolio Returns + Asset Returns + Weights → Align Data by Date →
    Calculate Attribution Effects → Aggregate by Period/Sector →
    Generate Waterfall Charts → Export Report
```

## 🔄 Workflow Steps

### 1. Input Data Requirements

```python
{
    'portfolio_data': DataFrame,      # Columns: returns (indexed by date)
    'asset_returns': DataFrame,       # Columns: {asset1}, {asset2}, ... (indexed by date)
    'weights_data': DataFrame,        # Columns: {asset1}, {asset2}, ... (indexed by date)
    'benchmark_weights': Dict         # Optional: {asset: weight} for comparison
}
```

**Critical**: All DataFrames must have timezone-naive, date-only indices for alignment.

### 2. Data Alignment

**Process**:
1. Normalize all indices to date-only (remove time component)
2. Inner join on dates (only use overlapping periods)
3. Forward-fill weights to match daily returns
4. Validate no NaN values in aligned data

### 3. Attribution Calculation (Brinson Methodology)

**Three Effects Calculated**:

| Effect | Formula | Meaning |
|--------|---------|---------|
| **Allocation** | `(w_p - w_b) * (r_b - r_p)` | Impact of over/under-weighting |
| **Selection** | `w_b * (r_p - r_b)` | Impact of asset picking skill |
| **Interaction** | `(w_p - w_b) * (r_p - r_b)` | Combined allocation+selection |

Where:
- `w_p` = Portfolio weight
- `w_b` = Benchmark weight
- `r_p` = Portfolio asset return
- `r_b` = Benchmark asset return

### 4. Period Aggregation

**Frequencies**:
- **Daily**: Individual day attribution
- **Weekly**: Aggregated by week
- **Monthly**: Aggregated by month

**Aggregation Method**: Sum of daily effects within period

### 5. Sector Attribution

**Sector Classification**: Defined in `config/sectors.py`

**9 Institutional Sectors**:
1. US Equity
2. International Equity
3. Emerging Markets
4. Fixed Income
5. Real Estate
6. Commodities
7. Cash
8. Alternatives
9. China Equity

**Process**:
1. Map each asset to sector
2. Aggregate attribution effects by sector
3. Calculate sector contribution to total return

### 6. Report Generation

**Entry Function**: `PerformanceAttributor.generate_attribution_report()`

**Report Structure**:
```python
{
    'daily_attribution': DataFrame,      # Daily effects by asset
    'weekly_attribution': DataFrame,     # Weekly aggregated
    'monthly_attribution': DataFrame,    # Monthly aggregated
    'sector_attribution': {
        'allocation_effect': Dict[sector, float],
        'selection_effect': Dict[sector, float],
        'interaction_effect': Dict[sector, float],
        'total_effect': Dict[sector, float]
    },
    'summary': {
        'total_allocation': float,
        'total_selection': float,
        'total_interaction': float,
        'total_attribution': float,
        'portfolio_return': float,
        'benchmark_return': float
    },
    'period': {
        'start_date': datetime,
        'end_date': datetime,
        'days': int
    }
}
```

### 7. Visualization

**Waterfall Charts**:
- Allocation effect breakdown by asset/sector
- Selection effect breakdown
- Cumulative attribution

**Time Series Charts**:
- Rolling attribution effects over time
- Sector contribution evolution

**Export Formats**: CSV, JSON, Excel

## 💡 Key Functions

### `PerformanceAttributor.generate_attribution_report()`
Main entry point for attribution analysis.

**Parameters**:
- `strategy_name`: str
- `portfolio_data`: DataFrame
- `asset_returns`: DataFrame
- `weights_data`: DataFrame
- `include_weekly`: bool (default: True)
- `include_monthly`: bool (default: True)

### `SectorAttributor.calculate_sector_attribution()`
Aggregates asset-level attribution to sector level using Brinson methodology.

**Input**: Asset-level returns, weights, sector mappings
**Output**: Sector-level allocation/selection/interaction effects

### `_align_data_by_date()`
Critical preprocessing step ensuring all data aligns by date.

**Handles**:
- Timezone conversion (to naive)
- Date normalization (remove time)
- Missing data (forward-fill, drop NaN)
- Index alignment (inner join)

## ⚠️ Error Handling

**Missing Weights**: Uses equal-weight fallback, logs warning
**Timezone Mismatch**: Auto-converts to timezone-naive
**Data Gaps**: Skips periods with missing data, continues
**NaN Values**: Drops rows with NaN after alignment

## 🔗 Integration Points

**Called By**:
- `backtesting/runner.py::run_backtest()` - When `enable_attribution=True`
- Streamlit Attribution tab - Standalone analysis

**Requires**:
- Strategy must track `weights_evolution` or `rebalance_log`
- Backtest must save `portfolio_evolution` DataFrame
- Asset returns captured during backtest

**Uses**:
- `config/sectors.py` - Sector classification
- `visualization/charts.py::display_attribution_analysis()` - Chart rendering

## 📝 Standalone Usage

```python
from src.modules.portfolio.performance.attribution import PerformanceAttributor

# Prepare data (from backtest results)
portfolio_data = backtest_results['portfolio_evolution']
asset_returns = backtest_results['asset_returns']
weights_data = backtest_results['weights_evolution']

# Run attribution
attributor = PerformanceAttributor()
report = attributor.generate_attribution_report(
    strategy_name="60/40 Portfolio",
    portfolio_data=portfolio_data,
    asset_returns=asset_returns,
    weights_data=weights_data,
    include_weekly=True,
    include_monthly=True
)

# Access results
print(f"Allocation Effect: {report['summary']['total_allocation']:.2%}")
print(f"Selection Effect: {report['summary']['total_selection']:.2%}")
```

## 📝 GUI Usage

Navigate to **Investment Management** → **Attribution Analysis** tab:
1. Select completed backtest
2. Choose period (Last Week, Month, Quarter, YTD, All)
3. Select frequency (Daily, Weekly, Monthly)
4. Click "Generate Attribution Analysis"
5. View waterfall charts and sector breakdown
6. Export to CSV/JSON/Excel

## 📊 Example Output

**Summary Metrics**:
```
Portfolio Return:      +12.5%
Benchmark Return:      +10.2%
Active Return:         +2.3%

Attribution Breakdown:
Allocation Effect:     +1.2%
Selection Effect:      +0.8%
Interaction Effect:    +0.3%
Total Attribution:     +2.3% ✓
```

**Sector Attribution**:
```
Sector              Allocation  Selection  Interaction  Total
─────────────────────────────────────────────────────────────
US Equity           +0.5%       +0.3%      +0.1%        +0.9%
Fixed Income        +0.4%       +0.2%      +0.1%        +0.7%
International Eq    +0.2%       +0.2%      +0.0%        +0.4%
Emerging Markets    +0.1%       +0.1%      +0.1%        +0.3%
```

**Interpretation**:
- **Allocation (+1.2%)**: Overweighting outperforming sectors added value
- **Selection (+0.8%)**: Asset choices within sectors beat benchmark
- **Interaction (+0.3%)**: Combined effects amplified returns
