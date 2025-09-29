"""
Data storage repository

Handles data persistence and retrieval operations.
"""

import pandas as pd
from typing import Dict, Any


def save_statement_csv(statement_data: dict, filename: str) -> None:
    """Save financial statement data to CSV"""
    df = pd.DataFrame([statement_data])
    df.fillna(0, inplace=True)
    df.to_csv(filename, index=False)
    
    
def save_transposed_data(df: pd.DataFrame, filename: str) -> None:
    """Save transposed data to CSV"""
    df.fillna(0).to_csv(filename)