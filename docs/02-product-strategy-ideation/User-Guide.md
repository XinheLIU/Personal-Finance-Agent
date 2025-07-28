# Personal Finance Agent - User Guide

## Overview

The Personal Finance Agent is a Python-based backtesting engine for multi-asset dynamic allocation strategies. It allows users to test and analyze complex investment strategies using historical data.

## Getting Started

### Prerequisites

- Python 3.x
- Conda

### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/Personal-Finance-Agent.git
    cd Personal-Finance-Agent
    ```

2.  **Create and activate the conda environment:**

    ```bash
    conda create -n py-fin python=3.10
    conda activate py-fin
    ```

3.  **Install the required packages:**

    ```bash
    pip install -r requirements.txt
    ```

### Running the Backtest

1.  **Download the data:**

    Before running a backtest, you need to download the required historical data. Run the following command from the project's root directory:

    ```bash
    python -m src.data_download
    ```

    This will download the necessary price, PE, and yield data and store it in the `data` directory.

2.  **Run the backtest:**

    To run the default dynamic allocation strategy, run the following command from the project's root directory:

    ```bash
    python -m src.main
    ```

## Analytics

After each backtest, the following analytics files are generated in the `analytics` directory:

-   **`dynamic_allocation_strategy_performance_summary.csv`**: A summary of the strategy's performance metrics.
-   **`dynamic_allocation_strategy_portfolio_performance.png`**: A chart showing the portfolio's performance over time.
-   **`dynamic_allocation_strategy_rebalance_log.csv`**: A detailed log of each rebalancing event, including:
    -   Total portfolio value
    -   Transactions
    -   Target weights for each asset
    -   Asset prices
    -   PE and yield data
    -   PE and yield percentiles

This detailed log allows for in-depth analysis and debugging of the strategy's behavior.
