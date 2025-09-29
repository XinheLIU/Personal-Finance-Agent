"""
Financial statement data structures

Defines the data structures used for financial statements.
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class IncomeStatement:
    """Represents an income statement structure"""
    entity: str
    revenue: Dict[str, float]
    total_revenue: float
    expenses: Dict[str, float] 
    total_expenses: float
    net_income: float


@dataclass 
class CashFlowStatement:
    """Represents a cash flow statement structure"""
    entity: str
    operating_activities: Dict[str, float]
    investing_activities: Dict[str, float]
    financing_activities: Dict[str, float]
    net_cash_flow: float


@dataclass
class BalanceSheet:
    """Represents a balance sheet structure"""
    entity: str
    assets: Dict[str, float]
    liabilities: Dict[str, float]
    equity: Dict[str, float]
    total_assets: float
    total_liabilities: float
    total_equity: float