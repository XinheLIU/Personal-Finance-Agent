  1. tests/test_data_models.py - Data Models and Validation
    - Transaction model validation
    - Asset model validation
    - Category taxonomy testing
    - Currency format validation
    - Data type and constraint testing
  2. tests/test_transaction_input.py - Transaction Input Management
    - Transaction input validation (multilingual support)
    - Currency format validation (¥ symbol handling)
    - Category validation against taxonomy
    - Bulk CSV/Excel import functionality
    - File upload simulation and encoding tests
  3. tests/test_asset_management.py - Asset Portfolio Management
    - Manual asset entry validation
    - Account type validation (checking, savings, investment, retirement)
    - Balance tracking and month-over-month calculations
    - CSV bulk import for assets
    - Asset filtering by type
  4. tests/test_income_statement.py - Income Statement Generation
    - Monthly and YTD income statement generation
    - Revenue/expense categorization (fixed vs variable costs)
    - Tax calculation with different brackets
    - Percentage analysis relative to gross revenue
    - Professional format validation
  5. tests/test_comparative_analysis.py - YTD Comparative Analysis
    - Budget vs actual variance calculations
    - Month-over-month change analysis with trend indicators
    - Category trend analysis over time
    - Budget adherence scoring
    - Visual trend indicators (↑↓→)
  6. tests/test_consolidated_reports.py - Multi-User Consolidated Reports
    - Household transaction consolidation
    - Individual vs household reporting comparison
    - Shared expense analysis and distribution
    - Multi-user asset portfolio consolidation
    - Revenue/expense reconciliation between individual and household totals
  7. tests/test_analytics_visualization.py - Analytics and Visualization
    - Asset trend chart generation with growth calculations
    - Account breakdown pie charts and allocation analysis
    - Financial metrics dashboard (expense ratios, savings rates)
    - Budget alert system with severity levels
    - Diversification score calculations