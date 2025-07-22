from src.strategy import DynamicAllocationStrategy
from src.app_logger import LOG
from src.backtest_runner import run_backtest

if __name__ == '__main__':
    LOG.info("Personal Finance Agent - Multi-Asset Dynamic Allocation Backtest")
    LOG.info("=" * 60)
    
    # Run Dynamic Allocation Strategy
    run_backtest(DynamicAllocationStrategy, "Dynamic Allocation Strategy")
