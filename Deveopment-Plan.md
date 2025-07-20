# Personal Minimal Backtesting System – MVP Development Plan

(Designed for "average programmers", deliverable in 6 weeks)

## 0. Goal

- Backtest a single strategy (the asset allocation formula you provide).
- No need for speed, UI, or live trading; as long as it runs, plots, and allows parameter changes, it's enough.
- Total code ≤ 600 lines, dependencies ≤ 5 common libraries.

## 1. Tech Stack

| Module         | Choice                | Reason                                  |
|----------------|----------------------|-----------------------------------------|
| Language       | Python 3.10+          | Most familiar                           |
| Backtest Engine| backtrader            | Single pip install, well-documented     |
| Data           | akshare + local CSV   | akshare is free, download once to CSV   |
| Visualization  | matplotlib            | backtrader has built-in plotting        |
| Env Mgmt       | venv                  | Prevents polluting system environment   |

## 2. File Structure (all in one folder)

~/my_backtest/
```
├── data/                 # Manually downloaded CSVs
│   ├── CSI300.csv
│   ├── CSI500.csv
│   ├── HSTECH.csv
│   ├── SP500.csv
│   ├── NASDAQ100.csv
│   ├── TLT.csv
│   ├── GLD.csv
│   ├── CGB.csv           # China bond fund
│   ├── US10Y.csv         # US 10Y rate
│   └── CASH.csv          # USD cash, rate=0
├── strategy.py           # Core strategy
├── main.py               # One-click run
├── requirements.txt
└── README.md             # How to run
```

## 3. Data Preparation (Week 0, 1 day)

- Use akshare to download daily data from 2004-2024, save as CSV.
- Example script (data_download.py):
  ```python
  import akshare as ak, pandas as pd
  def save(symbol, fn):
      df = ak.index_zh_a_hist(symbol=symbol, period="daily", start_date="20040101")
      df.to_csv(fn, index=False)
  save("000300", "data/CSI300.csv")
  ```
- For US stocks, TLT, gold, rates: use akshare or yfinance if not available.
- Manually check CSVs have at least: date, close columns.

## 4. Development Roadmap (6 weeks, 2-3 hours/week)

| Week | Milestone         | Tasks Breakdown                                                                 | Deliverable                        |
|------|-------------------|--------------------------------------------------------------------------------|------------------------------------|
| 0    | Env + Data        | 1. Create venv 2. Install backtrader/akshare 3. Run data_download.py            | All data/*.csv ready               |
| 1    | "Hello backtrader"| 1. Read one asset (CSI300) in main.py 2. Buy & hold backtest 3. Plot equity    | Simplest script runs               |
| 2    | Indicator Funcs   | 1. Write `percentile(series, n)` 2. Write `get_pe_percentile(ticker, date)` 3. Unit test: PE percentile on 2020-01-01? | Reusable functions in utils.py     |
| 3    | Strategy Skeleton | 1. Create `AssetAllocationStrategy(bt.Strategy)` in strategy.py 2. Print date & target weights in next() | See target weights in terminal     |
| 4    | Real Rebalance    | 1. Use `self.order_target_percent` to trade by weight 2. Implement 1% rebalance trigger (custom observer) | Rebalance logs in backtest         |
| 5    | All Assets        | 1. Add all 10 assets 2. Allocate leftover to CGB 3. Run 2014-2024, plot         | equity_curve.png                   |
| 6    | Params + README   | 1. Make PE window, fixed weights as strategy params 2. Write README: how to rebalance/change params 3. Publish on GitHub | Reproducible repo                  |

## 5. Key Pseudocode (strategy.py)

```python
class AssetAllocationStrategy(bt.Strategy):
    params = dict(
        pe_window = {'CSI300': 2520, 'SP500': 5040, ...},
        fixed_gold = 0.10,
        ...
    )
    def __init__(self):
        self.pe_cache = {}
    def next(self):
        date = self.datas[0].datetime.date(0)
        target = {}
        # 1. Calculate target weights
        target['CSI300'] = 0.20 * (1 - pe_percentile('CSI300', date))
        target['GLD']    = self.p.fixed_gold
        ...
        # 2. Allocate leftover to CGB
        total = sum(target.values())
        target['CGB'] = max(0, 1 - total)
        # 3. Rebalance
        for d in self.datas:
            ticker = d._name
            current_weight = self.broker.getvalue([d]) / self.broker.getvalue()
            if abs(current_weight - target[ticker]) > 0.01:
                self.order_target_percent(d, target[ticker])
```

## 6. Common Pitfalls & Tips

- Percentile: use pandas.Series.rolling(n).rank(pct=True), fill NaN with 0.5.
- Backtest start date: use the first date where all assets have data, or backtrader will error.
- FX: All assets in RMB, akshare handles conversion.
- Weekends/holidays: backtrader skips automatically.
- Performance: 10 years, 10 assets, daily, <1s per run; don't worry about speed.

## 7. Acceptance Criteria

- One command: `python main.py` runs 2014-2024, terminal prints:
  ```
  Initial capital: 1000000
  Final capital: xxxxx
  Annualized return: x%
  Max drawdown: x%
  ```
- Generates result.png, curve should look like exponential growth.

---

By completing these 6 weeks of tasks, you'll have a minimal, modifiable, and shareable backtesting system.
