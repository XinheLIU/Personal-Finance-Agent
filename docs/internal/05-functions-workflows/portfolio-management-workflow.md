# Portfolio Management & Rebalancing Workflow

## Overview
Manages current portfolio holdings, compares them with strategy targets, identifies gaps, and generates rebalancing recommendations. Provides interactive portfolio editing and gap analysis.

## 🏗️ Architecture

```
src/modules/portfolio/
├── presenters/
│   └── portfolio_presenter.py    # PortfolioPresenter ⭐
├── views/
│   ├── pages.py                  # Main investment page
│   └── components.py             # Portfolio UI components
└── strategies/
    └── registry.py               # Strategy target weights

data/
└── holdings.json                # Current portfolio holdings
```

## 📊 Data Flow

```
Load Holdings JSON → Display Current Allocation → Select Strategy →
    Calculate Gap → Generate Rebalancing Suggestions → User Edits →
    Validate Weights → Save Updated Holdings
```

## 🔄 Workflow Steps

### 1. Holdings Management

**File Format** (`data/holdings.json`):
```json
{
    "SP500": 0.60,
    "TLT": 0.40
}
```

**Operations**:
- **Load**: `PortfolioPresenter.load_holdings()`
- **Save**: `PortfolioPresenter.save_holdings(holdings_dict)`
- **Validation**: Weights sum to 1.0 (100%)

### 2. Interactive Editing

**UI Component**: Streamlit `data_editor` with dynamic rows

**Features**:
- Add/remove assets
- Adjust weights (0-100%)
- Auto-complete asset selection
- Real-time weight validation
- Auto-normalization to 100%

**Validation Rules**:
```python
1. Asset must exist in ASSET_DISPLAY_INFO
2. Weight must be >= 0
3. Total weights normalized to 1.0
4. Minimum 1 asset required
```

### 3. Strategy Comparison

**Function**: `PortfolioPresenter.get_portfolio_gap_analysis(holdings, strategy_name)`

**Process**:
1. Load current holdings
2. Get strategy target weights: `strategy_registry.get(strategy_name).get_target_weights()`
3. Calculate gaps: `target_weight - current_weight`
4. Flag large gaps (>5% deviation)

**Output**:
```python
[
    {
        'Asset': 'SP500',
        'Current': '55.0%',
        'Target': '60.0%',
        'Gap': '+5.0%',
        'Action': 'Buy'
    },
    {
        'Asset': 'TLT',
        'Current': '45.0%',
        'Target': '40.0%',
        'Gap': '-5.0%',
        'Action': 'Sell'
    }
]
```

### 4. Weight Balancing

**Function**: `PortfolioPresenter.balance_portfolio_weights(holdings, updated_asset, new_weight)`

**Auto-Balancing Logic**:
```python
# User updates one asset weight
holdings['SP500'] = 0.65  # Changed from 0.60

# System balances other assets proportionally
total_other = sum(v for k, v in holdings.items() if k != 'SP500')
excess = total_weight - 1.0

for asset in other_assets:
    # Reduce proportionally to reach 100% total
    holdings[asset] -= excess * (holdings[asset] / total_other)
```

### 5. Rebalancing Recommendations

**Function**: `PortfolioPresenter.generate_rebalancing_suggestions()`

**Recommendation Logic**:
```python
if abs(gap) > 0.05:  # 5% threshold
    if gap > 0:
        suggest(f"Buy {asset}: increase by {gap:.1%}")
    else:
        suggest(f"Sell {asset}: decrease by {abs(gap):.1%}")

# Estimate transaction costs
estimated_cost = abs(gap) * portfolio_value * commission_rate
```

**Output**:
```
Rebalancing Suggestions:
─────────────────────────
• Buy SP500: +5.0% ($5,000)
  Estimated cost: $25 (0.5% commission)

• Sell TLT: -5.0% ($5,000)
  Estimated cost: $25 (0.5% commission)

Total turnover: 10.0% ($10,000)
Total costs: $50
```

### 6. Allocation Visualization

**Charts Generated**:
1. **Current Allocation Pie Chart**: Shows current holdings distribution
2. **Target vs Current Bar Chart**: Side-by-side comparison
3. **Gap Analysis Chart**: Highlights over/under-weighted assets

## 💡 Key Functions

### `PortfolioPresenter.load_holdings()`
Loads current portfolio from JSON file.

**Returns**: `Dict[str, float]` - Asset weights (summing to 1.0)
**Fallback**: Empty dict if file doesn't exist

### `PortfolioPresenter.save_holdings(holdings_dict)`
Validates and saves portfolio to JSON.

**Validation**:
- Weights are positive
- Weights sum to 1.0
- Assets exist in config

### `PortfolioPresenter.get_portfolio_gap_analysis(holdings, strategy_name)`
Compares current holdings with strategy targets.

**Returns**: List of dicts with gap analysis for each asset

### `PortfolioPresenter.get_strategy_weights(strategy_name)`
Retrieves target weights without running full backtest.

**Static Strategies**: Returns fixed weights
**Dynamic Strategies**: Returns current calculated weights (if available)

## ⚠️ Error Handling

**Missing Holdings File**: Creates empty portfolio, prompts user
**Invalid Weights**: Normalizes to 100%, logs warning
**Unknown Assets**: Filters out, logs error
**Strategy Not Found**: Returns empty weights, shows error message

## 🔗 Integration Points

**Strategy Registry**:
- `strategy_registry.list_strategies()` - Available strategies for dropdown
- `strategy_registry.get(name).get_target_weights()` - Target allocations

**Visualization**:
- `charts.py::display_asset_allocation()` - Pie chart
- `charts.py::display_portfolio_comparison()` - Gap chart

**Backtesting**:
- Portfolio can be tested via backtest workflow
- Holdings saved after backtest completion (optional)

## 📝 GUI Workflow

Navigate to **Investment Management** → **Portfolio Management** tab:

1. **View Current Holdings**:
   - See current allocation pie chart
   - View weight validation status

2. **Edit Holdings**:
   - Use data editor to add/remove assets
   - Adjust weights directly
   - Click "Save Holdings" (auto-normalizes to 100%)

3. **Gap Analysis**:
   - Select strategy from dropdown
   - View target vs current comparison
   - See gap percentages and actions

4. **Rebalancing**:
   - Review suggested trades
   - See estimated transaction costs
   - Execute rebalancing (manual or via backtest)

## 📝 CLI Usage

```python
from src.modules.portfolio.presenters.portfolio_presenter import PortfolioPresenter

# Load current holdings
presenter = PortfolioPresenter()
holdings = presenter.load_holdings()

# Compare with strategy
gap_analysis = presenter.get_portfolio_gap_analysis(holdings, "60_40_portfolio")

# Print recommendations
for item in gap_analysis:
    print(f"{item['Asset']}: {item['Gap']} - {item['Action']}")

# Update holdings
new_holdings = {"SP500": 0.60, "TLT": 0.40}
presenter.save_holdings(new_holdings)
```

## 📊 Example Scenarios

### Scenario 1: Drift from Target
```
Initial: SP500 60%, TLT 40%
After 6 months: SP500 65%, TLT 35% (due to SP500 outperformance)

Gap Analysis:
• SP500: -5% (Overweight - Sell)
• TLT: +5% (Underweight - Buy)

Action: Rebalance back to 60/40
```

### Scenario 2: Strategy Change
```
Current: 60/40 Portfolio (SP500 60%, TLT 40%)
New Target: All-Weather (25% stocks, 55% bonds, 15% gold, 5% commodities)

Gap Analysis:
• SP500: -35% → Reduce significantly
• TLT: +15% → Increase bonds
• GLD: +15% → Add gold
• DBC: +5% → Add commodities

Action: Gradual transition over multiple rebalancing periods
```

### Scenario 3: Adding New Asset
```
Current: SP500 100%
Target: Add international diversification

Steps:
1. Add VXUS to holdings at 0%
2. Adjust SP500 to 70%, VXUS to 30%
3. Save (auto-normalizes)
4. Gap analysis shows buy VXUS +30%, sell SP500 -30%
```
