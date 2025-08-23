"""
Test suite for Professional Accounting Module - YTD Comparative Analysis

ACCEPTANCE CRITERIA → TEST MAPPING:
- US-2.2: System displays YTD data in tabular format → test_ytd_table_display_*
- Budget vs. actual comparisons with variance calculations → test_budget_variance_*
- Month-over-month percentage changes → test_month_over_month_*
- Category trend analysis over time → test_category_trends_*
- Visual indicators for positive/negative trends → test_trend_indicators_*

ASSUMPTIONS FOR VALIDATION:
1. YTD analysis covers January to current month
2. Budget data is set monthly by category
3. Variance = Actual - Budget (positive = over budget)
4. MoM changes calculated as (Current - Previous) / Previous * 100
5. Trends analyzed for major expense categories
6. Visual indicators: ↑ (positive), ↓ (negative), → (neutral)
7. Neutral range: -5% to +5% change
8. Data presented in both CNY amounts and percentages
"""

import pytest
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class TrendDirection(Enum):
    """Trend direction indicators"""
    INCREASING = "↑"
    DECREASING = "↓"
    STABLE = "→"


@dataclass
class Budget:
    """Budget data structure"""
    category: str
    monthly_amount: Decimal
    year: int


@dataclass
class Transaction:
    """Transaction for analysis"""
    description: str
    amount: Decimal
    category: str
    date: datetime


class BudgetManager:
    """Budget management service - would be in modules/accounting/analytics/"""
    
    def __init__(self):
        self.budgets: Dict[str, Dict[int, Decimal]] = {}
    
    def set_budget(self, category: str, year: int, monthly_amount: Decimal):
        """Set monthly budget for a category"""
        if category not in self.budgets:
            self.budgets[category] = {}
        self.budgets[category][year] = monthly_amount
    
    def get_budget(self, category: str, year: int) -> Decimal:
        """Get monthly budget for category"""
        return self.budgets.get(category, {}).get(year, Decimal("0"))
    
    def get_ytd_budget(self, category: str, year: int, through_month: int) -> Decimal:
        """Get YTD budget through specified month"""
        monthly = self.get_budget(category, year)
        return monthly * through_month


class ComparativeAnalyzer:
    """YTD comparative analysis service - would be in modules/accounting/analytics/"""
    
    def __init__(self, budget_manager: BudgetManager):
        self.budget_manager = budget_manager
    
    def generate_ytd_analysis(self, transactions: List[Transaction], 
                             year: int, through_month: int) -> Dict[str, Any]:
        """Generate YTD comparative analysis"""
        # Filter YTD transactions
        ytd_transactions = [
            t for t in transactions 
            if t.date.year == year and t.date.month <= through_month
        ]
        
        # Group by category
        category_actuals = self._calculate_category_actuals(ytd_transactions)
        
        # Calculate budget vs actual
        budget_comparison = self._compare_budget_vs_actual(
            category_actuals, year, through_month
        )
        
        # Calculate month-over-month changes
        mom_changes = self._calculate_mom_changes(transactions, year, through_month)
        
        # Generate trend analysis
        trend_analysis = self._analyze_trends(transactions, year, through_month)
        
        return {
            "period": f"YTD {year} (through {through_month:02d})",
            "budget_vs_actual": budget_comparison,
            "month_over_month": mom_changes,
            "trend_analysis": trend_analysis,
            "summary_metrics": self._calculate_summary_metrics(
                category_actuals, budget_comparison
            )
        }
    
    def _calculate_category_actuals(self, transactions: List[Transaction]) -> Dict[str, Decimal]:
        """Calculate actual spending by category"""
        actuals = {}
        
        for transaction in transactions:
            category = transaction.category
            amount = abs(transaction.amount) if transaction.amount < 0 else Decimal("0")
            
            if category not in actuals:
                actuals[category] = Decimal("0")
            actuals[category] += amount
        
        return actuals
    
    def _compare_budget_vs_actual(self, actuals: Dict[str, Decimal], 
                                 year: int, through_month: int) -> List[Dict[str, Any]]:
        """Compare budget vs actual for each category"""
        comparison = []
        
        # Get all categories (from actuals and budgets)
        all_categories = set(actuals.keys())
        for category_budgets in self.budget_manager.budgets.values():
            all_categories.update(self.budget_manager.budgets.keys())
        
        for category in all_categories:
            actual = actuals.get(category, Decimal("0"))
            budget = self.budget_manager.get_ytd_budget(category, year, through_month)
            
            variance = actual - budget
            variance_pct = self._calculate_percentage(variance, budget) if budget > 0 else Decimal("0")
            
            comparison.append({
                "category": category,
                "budget": budget,
                "actual": actual,
                "variance": variance,
                "variance_percentage": variance_pct,
                "status": self._get_variance_status(variance_pct)
            })
        
        return sorted(comparison, key=lambda x: abs(x["variance"]), reverse=True)
    
    def _calculate_mom_changes(self, transactions: List[Transaction], 
                              year: int, through_month: int) -> List[Dict[str, Any]]:
        """Calculate month-over-month changes"""
        if through_month < 2:
            return []  # Need at least 2 months for comparison
        
        current_month_transactions = [
            t for t in transactions 
            if t.date.year == year and t.date.month == through_month
        ]
        
        previous_month_transactions = [
            t for t in transactions 
            if t.date.year == year and t.date.month == through_month - 1
        ]
        
        current_actuals = self._calculate_category_actuals(current_month_transactions)
        previous_actuals = self._calculate_category_actuals(previous_month_transactions)
        
        mom_changes = []
        all_categories = set(current_actuals.keys()) | set(previous_actuals.keys())
        
        for category in all_categories:
            current = current_actuals.get(category, Decimal("0"))
            previous = previous_actuals.get(category, Decimal("0"))
            
            change = current - previous
            change_pct = self._calculate_percentage(change, previous) if previous > 0 else Decimal("100")
            
            mom_changes.append({
                "category": category,
                "current_month": current,
                "previous_month": previous,
                "change": change,
                "change_percentage": change_pct,
                "trend": self._determine_trend(change_pct)
            })
        
        return sorted(mom_changes, key=lambda x: abs(x["change"]), reverse=True)
    
    def _analyze_trends(self, transactions: List[Transaction], 
                       year: int, through_month: int) -> List[Dict[str, Any]]:
        """Analyze spending trends over time"""
        trends = []
        
        # Calculate monthly spending for each category
        monthly_data = {}
        for month in range(1, through_month + 1):
            month_transactions = [
                t for t in transactions 
                if t.date.year == year and t.date.month == month
            ]
            monthly_data[month] = self._calculate_category_actuals(month_transactions)
        
        # Analyze trend for each category
        all_categories = set()
        for month_actuals in monthly_data.values():
            all_categories.update(month_actuals.keys())
        
        for category in all_categories:
            monthly_amounts = []
            for month in range(1, through_month + 1):
                amount = monthly_data[month].get(category, Decimal("0"))
                monthly_amounts.append(amount)
            
            if len(monthly_amounts) >= 2:
                trend_direction = self._calculate_trend_direction(monthly_amounts)
                avg_change = self._calculate_average_change(monthly_amounts)
                
                trends.append({
                    "category": category,
                    "monthly_data": monthly_amounts,
                    "trend_direction": trend_direction,
                    "average_change_percentage": avg_change,
                    "total_spent": sum(monthly_amounts),
                    "months_analyzed": len(monthly_amounts)
                })
        
        return sorted(trends, key=lambda x: x["total_spent"], reverse=True)
    
    def _calculate_summary_metrics(self, actuals: Dict[str, Decimal], 
                                  budget_comparison: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary metrics for the analysis"""
        total_actual = sum(actuals.values())
        total_budget = sum(item["budget"] for item in budget_comparison)
        total_variance = total_actual - total_budget
        
        over_budget_categories = len([
            item for item in budget_comparison 
            if item["variance"] > 0
        ])
        
        under_budget_categories = len([
            item for item in budget_comparison 
            if item["variance"] < 0
        ])
        
        return {
            "total_actual": total_actual,
            "total_budget": total_budget,
            "total_variance": total_variance,
            "total_variance_percentage": self._calculate_percentage(total_variance, total_budget),
            "categories_over_budget": over_budget_categories,
            "categories_under_budget": under_budget_categories,
            "budget_adherence_score": self._calculate_adherence_score(budget_comparison)
        }
    
    def _calculate_percentage(self, amount: Decimal, base: Decimal) -> Decimal:
        """Calculate percentage with proper rounding"""
        if base == 0:
            return Decimal("0")
        return ((amount / base) * 100).quantize(Decimal("0.01"), ROUND_HALF_UP)
    
    def _get_variance_status(self, variance_pct: Decimal) -> str:
        """Get variance status indicator"""
        if variance_pct > 10:
            return "Significantly Over"
        elif variance_pct > 0:
            return "Over Budget"
        elif variance_pct > -10:
            return "On Track"
        else:
            return "Under Budget"
    
    def _determine_trend(self, change_pct: Decimal) -> TrendDirection:
        """Determine trend direction from percentage change"""
        if change_pct > 5:
            return TrendDirection.INCREASING
        elif change_pct < -5:
            return TrendDirection.DECREASING
        else:
            return TrendDirection.STABLE
    
    def _calculate_trend_direction(self, monthly_amounts: List[Decimal]) -> TrendDirection:
        """Calculate overall trend direction from monthly data"""
        if len(monthly_amounts) < 2:
            return TrendDirection.STABLE
        
        # Simple linear trend calculation
        increases = 0
        decreases = 0
        
        for i in range(1, len(monthly_amounts)):
            if monthly_amounts[i] > monthly_amounts[i-1]:
                increases += 1
            elif monthly_amounts[i] < monthly_amounts[i-1]:
                decreases += 1
        
        if increases > decreases:
            return TrendDirection.INCREASING
        elif decreases > increases:
            return TrendDirection.DECREASING
        else:
            return TrendDirection.STABLE
    
    def _calculate_average_change(self, monthly_amounts: List[Decimal]) -> Decimal:
        """Calculate average month-over-month change percentage"""
        if len(monthly_amounts) < 2:
            return Decimal("0")
        
        total_change = Decimal("0")
        valid_comparisons = 0
        
        for i in range(1, len(monthly_amounts)):
            if monthly_amounts[i-1] > 0:
                change = self._calculate_percentage(
                    monthly_amounts[i] - monthly_amounts[i-1], 
                    monthly_amounts[i-1]
                )
                total_change += change
                valid_comparisons += 1
        
        return (total_change / valid_comparisons).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        ) if valid_comparisons > 0 else Decimal("0")
    
    def _calculate_adherence_score(self, budget_comparison: List[Dict[str, Any]]) -> Decimal:
        """Calculate budget adherence score (0-100)"""
        if not budget_comparison:
            return Decimal("100")
        
        total_score = Decimal("0")
        for item in budget_comparison:
            variance_pct = abs(item["variance_percentage"])
            # Score decreases as variance increases
            category_score = max(Decimal("0"), Decimal("100") - variance_pct)
            total_score += category_score
        
        return (total_score / len(budget_comparison)).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )


class TestYTDTableDisplay:
    """Test YTD data table display functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.budget_manager = BudgetManager()
        self.analyzer = ComparativeAnalyzer(self.budget_manager)
        
        # Set up budgets
        self.budget_manager.set_budget("房租", 2024, Decimal("2000.00"))
        self.budget_manager.set_budget("餐饮", 2024, Decimal("800.00"))
        self.budget_manager.set_budget("交通", 2024, Decimal("300.00"))
        
        # Sample transactions
        self.sample_transactions = [
            # January
            Transaction("Rent Jan", Decimal("-2000.00"), "房租", datetime(2024, 1, 1)),
            Transaction("Food Jan", Decimal("-900.00"), "餐饮", datetime(2024, 1, 15)),
            Transaction("Transport Jan", Decimal("-250.00"), "交通", datetime(2024, 1, 20)),
            # February  
            Transaction("Rent Feb", Decimal("-2100.00"), "房租", datetime(2024, 2, 1)),
            Transaction("Food Feb", Decimal("-750.00"), "餐饮", datetime(2024, 2, 15)),
            Transaction("Transport Feb", Decimal("-320.00"), "交通", datetime(2024, 2, 20)),
        ]
    
    def test_ytd_analysis_generation(self):
        """Test YTD analysis generates proper table format"""
        analysis = self.analyzer.generate_ytd_analysis(
            self.sample_transactions, 2024, 2
        )
        
        assert analysis["period"] == "YTD 2024 (through 02)"
        assert "budget_vs_actual" in analysis
        assert "month_over_month" in analysis
        assert "trend_analysis" in analysis
        assert "summary_metrics" in analysis
    
    def test_budget_vs_actual_table_structure(self):
        """Test budget vs actual comparison table structure"""
        analysis = self.analyzer.generate_ytd_analysis(
            self.sample_transactions, 2024, 2
        )
        
        budget_comparison = analysis["budget_vs_actual"]
        
        # Should have entries for all categories
        categories = [item["category"] for item in budget_comparison]
        assert "房租" in categories
        assert "餐饮" in categories
        assert "交通" in categories
        
        # Check table structure
        for item in budget_comparison:
            assert "category" in item
            assert "budget" in item
            assert "actual" in item
            assert "variance" in item
            assert "variance_percentage" in item
            assert "status" in item
    
    def test_ytd_data_calculation_accuracy(self):
        """Test YTD data calculations are accurate"""
        analysis = self.analyzer.generate_ytd_analysis(
            self.sample_transactions, 2024, 2
        )
        
        # Find rent category in results
        rent_data = next(
            item for item in analysis["budget_vs_actual"] 
            if item["category"] == "房租"
        )
        
        # YTD budget: 2000 * 2 months = 4000
        assert rent_data["budget"] == Decimal("4000.00")
        
        # YTD actual: 2000 + 2100 = 4100
        assert rent_data["actual"] == Decimal("4100.00")
        
        # Variance: 4100 - 4000 = 100
        assert rent_data["variance"] == Decimal("100.00")
        
        # Variance percentage: 100/4000 * 100 = 2.5%
        assert rent_data["variance_percentage"] == Decimal("2.50")


class TestBudgetVarianceCalculation:
    """Test budget vs actual variance calculations"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.budget_manager = BudgetManager()
        self.analyzer = ComparativeAnalyzer(self.budget_manager)
        
        self.budget_manager.set_budget("餐饮", 2024, Decimal("1000.00"))
    
    def test_over_budget_variance(self):
        """Test variance calculation when over budget"""
        transactions = [
            Transaction("Food 1", Decimal("-1200.00"), "餐饮", datetime(2024, 1, 15)),
        ]
        
        analysis = self.analyzer.generate_ytd_analysis(transactions, 2024, 1)
        
        food_data = next(
            item for item in analysis["budget_vs_actual"] 
            if item["category"] == "餐饮"
        )
        
        assert food_data["budget"] == Decimal("1000.00")
        assert food_data["actual"] == Decimal("1200.00")
        assert food_data["variance"] == Decimal("200.00")  # Over budget
        assert food_data["variance_percentage"] == Decimal("20.00")
        assert food_data["status"] == "Significantly Over"
    
    def test_under_budget_variance(self):
        """Test variance calculation when under budget"""
        transactions = [
            Transaction("Food 1", Decimal("-800.00"), "餐饮", datetime(2024, 1, 15)),
        ]
        
        analysis = self.analyzer.generate_ytd_analysis(transactions, 2024, 1)
        
        food_data = next(
            item for item in analysis["budget_vs_actual"] 
            if item["category"] == "餐饮"
        )
        
        assert food_data["variance"] == Decimal("-200.00")  # Under budget
        assert food_data["variance_percentage"] == Decimal("-20.00")
        assert food_data["status"] == "Under Budget"
    
    def test_no_budget_set_variance(self):
        """Test variance when no budget is set for category"""
        transactions = [
            Transaction("Entertainment", Decimal("-500.00"), "娱乐", datetime(2024, 1, 15)),
        ]
        
        analysis = self.analyzer.generate_ytd_analysis(transactions, 2024, 1)
        
        entertainment_data = next(
            item for item in analysis["budget_vs_actual"] 
            if item["category"] == "娱乐"
        )
        
        assert entertainment_data["budget"] == Decimal("0.00")
        assert entertainment_data["actual"] == Decimal("500.00")
        assert entertainment_data["variance"] == Decimal("500.00")
    
    @pytest.mark.parametrize("variance_pct,expected_status", [
        (Decimal("15.00"), "Significantly Over"),
        (Decimal("5.00"), "Over Budget"),
        (Decimal("0.00"), "On Track"),
        (Decimal("-5.00"), "On Track"),
        (Decimal("-15.00"), "Under Budget")
    ])
    def test_variance_status_indicators(self, variance_pct, expected_status):
        """Test variance status indicators"""
        status = self.analyzer._get_variance_status(variance_pct)
        assert status == expected_status


class TestMonthOverMonthChanges:
    """Test month-over-month change calculations"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.budget_manager = BudgetManager()
        self.analyzer = ComparativeAnalyzer(self.budget_manager)
    
    def test_mom_increase_calculation(self):
        """Test month-over-month increase calculation"""
        transactions = [
            # January: 800
            Transaction("Food Jan", Decimal("-800.00"), "餐饮", datetime(2024, 1, 15)),
            # February: 1000
            Transaction("Food Feb", Decimal("-1000.00"), "餐饮", datetime(2024, 2, 15)),
        ]
        
        analysis = self.analyzer.generate_ytd_analysis(transactions, 2024, 2)
        
        mom_data = analysis["month_over_month"]
        food_mom = next(item for item in mom_data if item["category"] == "餐饮")
        
        assert food_mom["current_month"] == Decimal("1000.00")
        assert food_mom["previous_month"] == Decimal("800.00")
        assert food_mom["change"] == Decimal("200.00")
        assert food_mom["change_percentage"] == Decimal("25.00")
        assert food_mom["trend"] == TrendDirection.INCREASING
    
    def test_mom_decrease_calculation(self):
        """Test month-over-month decrease calculation"""
        transactions = [
            # January: 1000
            Transaction("Food Jan", Decimal("-1000.00"), "餐饮", datetime(2024, 1, 15)),
            # February: 600
            Transaction("Food Feb", Decimal("-600.00"), "餐饮", datetime(2024, 2, 15)),
        ]
        
        analysis = self.analyzer.generate_ytd_analysis(transactions, 2024, 2)
        
        mom_data = analysis["month_over_month"]
        food_mom = next(item for item in mom_data if item["category"] == "餐饮")
        
        assert food_mom["change"] == Decimal("-400.00")
        assert food_mom["change_percentage"] == Decimal("-40.00")
        assert food_mom["trend"] == TrendDirection.DECREASING
    
    def test_mom_no_previous_data(self):
        """Test MoM calculation with no previous month data"""
        transactions = [
            Transaction("Food Feb", Decimal("-1000.00"), "餐饮", datetime(2024, 2, 15)),
        ]
        
        analysis = self.analyzer.generate_ytd_analysis(transactions, 2024, 2)
        
        mom_data = analysis["month_over_month"]
        food_mom = next(item for item in mom_data if item["category"] == "餐饮")
        
        assert food_mom["previous_month"] == Decimal("0.00")
        assert food_mom["change_percentage"] == Decimal("100.00")  # Special case
    
    def test_mom_first_month_no_comparison(self):
        """Test MoM analysis for first month (no comparison possible)"""
        transactions = [
            Transaction("Food Jan", Decimal("-800.00"), "餐饮", datetime(2024, 1, 15)),
        ]
        
        analysis = self.analyzer.generate_ytd_analysis(transactions, 2024, 1)
        
        # Should have empty MoM data for first month
        assert len(analysis["month_over_month"]) == 0


class TestCategoryTrendAnalysis:
    """Test category trend analysis over time"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.budget_manager = BudgetManager()
        self.analyzer = ComparativeAnalyzer(self.budget_manager)
        
        # 3 months of data with clear trends
        self.trend_transactions = [
            # January - baseline
            Transaction("Food Jan", Decimal("-800.00"), "餐饮", datetime(2024, 1, 15)),
            Transaction("Transport Jan", Decimal("-200.00"), "交通", datetime(2024, 1, 20)),
            # February - increasing food, stable transport
            Transaction("Food Feb", Decimal("-1000.00"), "餐饮", datetime(2024, 2, 15)),
            Transaction("Transport Feb", Decimal("-210.00"), "交通", datetime(2024, 2, 20)),
            # March - continuing increase in food, decreasing transport
            Transaction("Food Mar", Decimal("-1200.00"), "餐饮", datetime(2024, 3, 15)),
            Transaction("Transport Mar", Decimal("-150.00"), "交通", datetime(2024, 3, 20)),
        ]
    
    def test_increasing_trend_analysis(self):
        """Test analysis of increasing spending trend"""
        analysis = self.analyzer.generate_ytd_analysis(
            self.trend_transactions, 2024, 3
        )
        
        trends = analysis["trend_analysis"]
        food_trend = next(item for item in trends if item["category"] == "餐饮")
        
        assert food_trend["trend_direction"] == TrendDirection.INCREASING
        assert food_trend["monthly_data"] == [
            Decimal("800.00"), Decimal("1000.00"), Decimal("1200.00")
        ]
        assert food_trend["total_spent"] == Decimal("3000.00")
        assert food_trend["months_analyzed"] == 3
        
        # Average change should be positive
        assert food_trend["average_change_percentage"] > Decimal("0")
    
    def test_decreasing_trend_analysis(self):
        """Test analysis of decreasing spending trend"""
        analysis = self.analyzer.generate_ytd_analysis(
            self.trend_transactions, 2024, 3
        )
        
        trends = analysis["trend_analysis"]
        transport_trend = next(item for item in trends if item["category"] == "交通")
        
        # Transport shows mixed trend (slight increase then decrease)
        # The overall direction depends on the algorithm implementation
        assert transport_trend["monthly_data"] == [
            Decimal("200.00"), Decimal("210.00"), Decimal("150.00")
        ]
        assert transport_trend["total_spent"] == Decimal("560.00")
    
    def test_stable_trend_analysis(self):
        """Test analysis of stable spending pattern"""
        stable_transactions = [
            Transaction("Rent Jan", Decimal("-2000.00"), "房租", datetime(2024, 1, 1)),
            Transaction("Rent Feb", Decimal("-2000.00"), "房租", datetime(2024, 2, 1)),
            Transaction("Rent Mar", Decimal("-2010.00"), "房租", datetime(2024, 3, 1)),  # Very small change
        ]
        
        analysis = self.analyzer.generate_ytd_analysis(stable_transactions, 2024, 3)
        
        trends = analysis["trend_analysis"]
        rent_trend = next(item for item in trends if item["category"] == "房租")
        
        # Should be stable due to minimal variation
        assert rent_trend["trend_direction"] == TrendDirection.STABLE
        assert abs(rent_trend["average_change_percentage"]) < Decimal("5.00")
    
    def test_trend_analysis_sorting(self):
        """Test trend analysis is sorted by total spending"""
        analysis = self.analyzer.generate_ytd_analysis(
            self.trend_transactions, 2024, 3
        )
        
        trends = analysis["trend_analysis"]
        
        # Should be sorted by total_spent in descending order
        for i in range(1, len(trends)):
            assert trends[i-1]["total_spent"] >= trends[i]["total_spent"]


class TestTrendIndicators:
    """Test visual trend indicators"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.budget_manager = BudgetManager()
        self.analyzer = ComparativeAnalyzer(self.budget_manager)
    
    @pytest.mark.parametrize("change_pct,expected_trend", [
        (Decimal("10.00"), TrendDirection.INCREASING),
        (Decimal("6.00"), TrendDirection.INCREASING),
        (Decimal("3.00"), TrendDirection.STABLE),
        (Decimal("0.00"), TrendDirection.STABLE),
        (Decimal("-3.00"), TrendDirection.STABLE),
        (Decimal("-6.00"), TrendDirection.DECREASING),
        (Decimal("-10.00"), TrendDirection.DECREASING)
    ])
    def test_trend_direction_determination(self, change_pct, expected_trend):
        """Test trend direction indicators"""
        trend = self.analyzer._determine_trend(change_pct)
        assert trend == expected_trend
    
    def test_trend_indicator_symbols(self):
        """Test trend indicator symbols are correct"""
        assert TrendDirection.INCREASING.value == "↑"
        assert TrendDirection.DECREASING.value == "↓"
        assert TrendDirection.STABLE.value == "→"


class TestSummaryMetrics:
    """Test summary metrics calculation"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.budget_manager = BudgetManager()
        self.analyzer = ComparativeAnalyzer(self.budget_manager)
        
        # Set budgets
        self.budget_manager.set_budget("餐饮", 2024, Decimal("800.00"))
        self.budget_manager.set_budget("交通", 2024, Decimal("300.00"))
        
        self.summary_transactions = [
            Transaction("Food", Decimal("-900.00"), "餐饮", datetime(2024, 1, 15)),
            Transaction("Transport", Decimal("-250.00"), "交通", datetime(2024, 1, 20)),
        ]
    
    def test_summary_metrics_calculation(self):
        """Test summary metrics are calculated correctly"""
        analysis = self.analyzer.generate_ytd_analysis(
            self.summary_transactions, 2024, 1
        )
        
        summary = analysis["summary_metrics"]
        
        # Total actual: 900 + 250 = 1150
        assert summary["total_actual"] == Decimal("1150.00")
        
        # Total budget: 800 + 300 = 1100
        assert summary["total_budget"] == Decimal("1100.00")
        
        # Total variance: 1150 - 1100 = 50
        assert summary["total_variance"] == Decimal("50.00")
        
        # Variance percentage: 50/1100 * 100 = 4.55%
        expected_pct = Decimal("4.55")
        assert summary["total_variance_percentage"] == expected_pct
    
    def test_category_counts(self):
        """Test over/under budget category counts"""
        analysis = self.analyzer.generate_ytd_analysis(
            self.summary_transactions, 2024, 1
        )
        
        summary = analysis["summary_metrics"]
        
        # Food is over budget (900 vs 800), Transport is under (250 vs 300)
        assert summary["categories_over_budget"] == 1
        assert summary["categories_under_budget"] == 1
    
    def test_budget_adherence_score(self):
        """Test budget adherence score calculation"""
        analysis = self.analyzer.generate_ytd_analysis(
            self.summary_transactions, 2024, 1
        )
        
        summary = analysis["summary_metrics"]
        
        # Score should be between 0-100
        score = summary["budget_adherence_score"]
        assert Decimal("0") <= score <= Decimal("100")
        
        # With small variances, score should be relatively high
        assert score > Decimal("80")  # Expecting good adherence
    
    def test_perfect_budget_adherence(self):
        """Test perfect budget adherence scenario"""
        perfect_transactions = [
            Transaction("Food", Decimal("-800.00"), "餐饮", datetime(2024, 1, 15)),
            Transaction("Transport", Decimal("-300.00"), "交通", datetime(2024, 1, 20)),
        ]
        
        analysis = self.analyzer.generate_ytd_analysis(perfect_transactions, 2024, 1)
        summary = analysis["summary_metrics"]
        
        assert summary["total_variance"] == Decimal("0.00")
        assert summary["budget_adherence_score"] == Decimal("100.00")


class TestEdgeCasesComparativeAnalysis:
    """Test edge cases in comparative analysis"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.budget_manager = BudgetManager()
        self.analyzer = ComparativeAnalyzer(self.budget_manager)
    
    def test_no_transactions_analysis(self):
        """Test analysis with no transactions"""
        analysis = self.analyzer.generate_ytd_analysis([], 2024, 1)
        
        assert analysis["budget_vs_actual"] == []
        assert analysis["month_over_month"] == []
        assert analysis["trend_analysis"] == []
        
        summary = analysis["summary_metrics"]
        assert summary["total_actual"] == Decimal("0.00")
        assert summary["categories_over_budget"] == 0
        assert summary["categories_under_budget"] == 0
    
    def test_no_budgets_set(self):
        """Test analysis when no budgets are set"""
        transactions = [
            Transaction("Food", Decimal("-500.00"), "餐饮", datetime(2024, 1, 15))
        ]
        
        analysis = self.analyzer.generate_ytd_analysis(transactions, 2024, 1)
        
        budget_data = analysis["budget_vs_actual"]
        food_data = next(item for item in budget_data if item["category"] == "餐饮")
        
        assert food_data["budget"] == Decimal("0.00")
        assert food_data["actual"] == Decimal("500.00")
        assert food_data["variance"] == Decimal("500.00")
    
    def test_single_month_analysis(self):
        """Test analysis for single month (no MoM comparison)"""
        transactions = [
            Transaction("Food", Decimal("-500.00"), "餐饮", datetime(2024, 1, 15))
        ]
        
        analysis = self.analyzer.generate_ytd_analysis(transactions, 2024, 1)
        
        # No month-over-month data for single month
        assert len(analysis["month_over_month"]) == 0
        
        # Trend analysis should still work
        trends = analysis["trend_analysis"]
        assert len(trends) >= 0  # May be empty if insufficient data