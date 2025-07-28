import pandas as pd
import os
from src.app_logger import LOG

def log_rebalance_details(strategy_name, rebalance_data):
    """
    Logs detailed rebalancing data to a CSV file.

    Args:
        strategy_name (str): The name of the strategy.
        rebalance_data (list): A list of dictionaries, where each dictionary
                               contains the data for a single rebalancing event.
    """
    if not rebalance_data:
        LOG.info("No rebalancing data to log.")
        return

    df = pd.DataFrame(rebalance_data)
    
    # Define the output path
    output_dir = "analytics"
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{strategy_name.replace(' ', '_').lower()}_rebalance_log.csv")

    # Save to CSV
    df.to_csv(file_path, index=False)
    LOG.info(f"Rebalancing details logged to {file_path}")
