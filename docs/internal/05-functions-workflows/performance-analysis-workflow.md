# Performance Analysis Workflow

## Overview
Generates comprehensive performance metrics, risk analysis, and visualizations from backtest results. Produces detailed reports with charts and actionable recommendations.

## 🏗️ Architecture

```
src/modules/portfolio/performance/
├── analytics.py              # PerformanceAnalyzer ⭐
└── attribution.py            # PerformanceAttributor (separate workflow)

src/modules/data_management/visualization/
├── charts.py                 # Chart generation functions
└── plotting.py               # Plotly visualizations
```

## 📊 Data Flow

```
Backtest Results → PerformanceAnalyzer → Calculate Metrics →
    Generate Charts → Create Report → Save to JSON/HTML
```

## 🔄 Workflow Steps

### 1. Input Data

**Required**:
```python
backtest_results = {
    'portfolio_evolution': DataFrame,  # Columns: value, returns (indexed by date)
    'initial_value': float,
    'final_value': float,
    'start_date': datetime,
    'end_date': datetime,
    'rebalance_log': str              # Path to CSV (optional)
}
```

### 2. Metrics Calculation

**Entry Function**: `PerformanceAnalyzer.generate_performance_report(backtest_results)`

**Calculated Metrics**:

| Metric | Formula | Description |
|--------|---------|-------------|
| **Total Return** | `(final - initial) / initial` | Overall gain/loss |
| **Annualized Return** | `(1 + total_return)^(365/days) - 1` | Yearly average |
| **Volatility** | `returns.std() * sqrt(252)` | Annualized risk |
| **Sharpe Ratio** | `(ann_return - rf_rate) / volatility` | Risk-adjusted return |
| **Max Drawdown** | `min((current - peak) / peak)` | Worst decline |
| **Sortino Ratio** | `ann_return / downside_deviation` | Downside risk |
| **Calmar Ratio** | `ann_return / abs(max_drawdown)` | Return per drawdown |

### 3. Rolling Window Analysis

**Function**: `PerformanceAnalyzer.rolling_performance_analysis()`

**Windows**:
- 30-day rolling returns
- 90-day rolling Sharpe ratio
- 180-day rolling volatility

**Output**: DataFrame with rolling metrics over time

### 4. Chart Generation

**Function**: `_generate_performance_charts(backtest_results, save_charts=True)`

**Generated Charts**:
1. **Portfolio Value Evolution**: Line chart of portfolio value over time
2. **Returns Distribution**: Histogram of daily returns
3. **Drawdown Chart**: Underwater equity curve
4. **Rolling Metrics**: Line charts for rolling Sharpe, volatility

**Save Location**: `analytics/performance/{strategy_name}_{metric}_{timestamp}.html`

### 5. Rebalancing Analysis

**Function**: `_analyze_rebalancing(rebalance_log_path)`

**Metrics**:
- Rebalancing frequency
- Average turnover per rebalance
- Transaction cost impact estimation

### 6. Recommendations Generation

**Function**: `_generate_recommendations(metrics)`

**Logic**:
```python
if sharpe_ratio < 0.5:
    recommend("Low risk-adjusted returns - consider different strategy")

if max_drawdown < -0.25:
    recommend("High drawdown risk - add defensive assets")

if volatility > 0.20:
    recommend("High volatility - consider more stable allocations")
```

### 7. Report Structure

```python
{
    'summary': {
        'total_return': float,
        'annualized_return': float,
        'sharpe_ratio': float,
        'max_drawdown': float,
        'volatility': float,
        'sortino_ratio': float,
        'calmar_ratio': float
    },
    'rolling_analysis': {
        'rolling_returns': DataFrame,
        'rolling_sharpe': DataFrame,
        'rolling_volatility': DataFrame
    },
    'rebalancing_analysis': {
        'frequency': str,
        'avg_turnover': float,
        'estimated_costs': float
    },
    'charts': {
        'portfolio_evolution': str,  # Path to HTML
        'returns_distribution': str,
        'drawdown_chart': str,
        'rolling_metrics': str
    },
    'recommendations': List[str],
    'generated_at': datetime
}
```

## 💡 Key Functions

### `_calculate_comprehensive_metrics(portfolio_df)`
Calculates all performance and risk metrics from portfolio DataFrame.

**Input**: DataFrame with 'value' and 'returns' columns
**Output**: Dictionary of metrics

### `rolling_performance_analysis(portfolio_df, windows=[30, 90, 180])`
Computes rolling window metrics for trend analysis.

**Input**: Portfolio DataFrame, list of window sizes (days)
**Output**: DataFrame with rolling metrics

### `_generate_performance_charts(results, save_charts=True)`
Creates interactive Plotly charts for visualization.

**Input**: Backtest results dictionary
**Output**: Dictionary of chart paths (if saved)

## ⚠️ Error Handling

**Empty Portfolio**: Returns zeros for all metrics, logs warning
**NaN Returns**: Filters out invalid values before calculations
**Missing Data**: Skips optional analysis (rebalancing, rolling), continues
**Chart Failures**: Logs error, continues with other charts

## 🔗 Integration Points

**Called By**:
- `backtesting/runner.py::run_backtest()` - Auto-generates report after backtest
- Streamlit GUI - Displays metrics and charts in UI

**Uses**:
- `visualization/charts.py` - Chart generation utilities
- `visualization/plotting.py` - Plotly wrapper functions

**Output To**:
- JSON reports for programmatic access
- HTML charts for interactive viewing
- Streamlit components for real-time display

## 📝 Standalone Usage

```python
from src.modules.portfolio.performance.analytics import PerformanceAnalyzer

# Load backtest results
results = {...}  # From run_backtest()

# Generate report
analyzer = PerformanceAnalyzer()
report = analyzer.generate_performance_report(results, save_charts=True)

# Access metrics
print(f"Sharpe Ratio: {report['summary']['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {report['summary']['max_drawdown']:.2%}")
```

## 📊 Example Output

**Performance Metrics**:
```
Total Return:        +45.2%
Annualized Return:   +8.9%
Volatility:          14.3%
Sharpe Ratio:        1.34
Max Drawdown:        -15.6%
Sortino Ratio:       1.89
Calmar Ratio:        0.57
```

**Recommendations**:
```
✓ Strong risk-adjusted returns (Sharpe > 1.0)
✓ Moderate drawdown risk
⚠ Consider adding inflation hedge during high CPI periods
```

**Chart Files**:
```
analytics/performance/
├── 60_40_portfolio_evolution_20250104.html
├── 60_40_portfolio_returns_dist_20250104.html
├── 60_40_portfolio_drawdown_20250104.html
└── 60_40_portfolio_rolling_metrics_20250104.html
```
