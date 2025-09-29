"""
Transaction domain entity

Core transaction model representing a single financial transaction.
"""

from dataclasses import dataclass


@dataclass
class Transaction:
    """Represents a single transaction"""
    description: str
    amount: float
    debit_category: str
    credit_account: str
    user: str
    transaction_type: str = "expense"  # revenue, expense, prepaid_asset
    affects_cash_flow: bool = True     # whether this transaction affects cash flow