"""
Data management module for data processing, visualization, and analytics.

This module contains:
- data_center: Data loading, downloading, and processing
- visualization: Chart generation and data visualization
- analytics: Data analysis and transparency tools
- coordinator: Cross-module coordination functionality
- presenters: Business logic orchestration (MVP pattern)
- views: UI components and pages (MVP pattern)
"""

# Import key data management functionality
from .data_center import *
from .visualization import *
from .analytics import *
from .presenters import *
from .views import *