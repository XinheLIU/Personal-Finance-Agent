"""
Portfolio management module for investment strategies and analysis.

This module contains:
- strategies: Investment strategy implementations and registry
- backtesting: Backtesting engine and runners
- performance: Performance analysis and attribution
- trading: Trade execution and management
- presenters: Business logic orchestration (MVP pattern)
- views: UI components and pages (MVP pattern)
"""

# Import key portfolio functionality
from .strategies import *
from .backtesting import *
from .performance import *
from .trading import *
from .presenters import *
from .views import *
