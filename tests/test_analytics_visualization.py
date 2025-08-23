"""
Test suite for Professional Accounting Module - Analytics and Visualization

ACCEPTANCE CRITERIA → TEST MAPPING:
- US-3.2: Charts showing asset balance trends over time → test_asset_trend_charts_*
- Account-wise asset breakdown visualizations → test_asset_breakdown_*
- Month-over-month growth percentages → test_growth_calculations_*
- Asset allocation pie charts by account type → test_asset_allocation_charts_*
- FR-3.1: Visual representation of key financial metrics → test_financial_metrics_visualization_*
- FR-3.2: Budget tracking and alerts → test_budget_alerts_*

ASSUMPTIONS FOR VALIDATION:
1. Charts generated as data structures ready for visualization libraries
2. Asset trends calculated from historical snapshot data
3. Growth percentages calculated as (Current - Previous) / Previous * 100
4. Pie charts include percentages and CNY amounts
5. Financial metrics dashboard includes key ratios and indicators
6. Budget alerts triggered when variance > threshold (default 10%)
7. Visualization data includes metadata for chart rendering
8. Color schemes and styling handled by frontend components
"""

import pytest
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class AlertType(Enum):
    """Budget alert types"""
    OVER_BUDGET = "over_budget"
    APPROACHING_LIMIT = "approaching_limit"
    SIGNIFICANT_INCREASE = "significant_increase"
    TREND_WARNING = "trend_warning"


@dataclass
class AssetSnapshot:
    """Asset snapshot for trend analysis"""
    account_name: str
    account_type: str
    balance: Decimal
    as_of_date: datetime
    user_id: str


@dataclass
class BudgetAlert:
    """Budget alert structure"""
    alert_type: AlertType
    category: str
    message: str
    severity: str  # "low", "medium", "high"
    actual_amount: Decimal
    budget_amount: Decimal
    variance_percentage: Decimal


class VisualizationDataGenerator:
    """Visualization data generation service - would be in modules/accounting/analytics/"""
    
    def __init__(self):
        self.color_palette = {
            "checking": "#4CAF50",
            "savings": "#2196F3", 
            "investment": "#FF9800",
            "retirement": "#9C27B0"
        }
    
    def generate_asset_trend_chart(self, snapshots: List[AssetSnapshot], 
                                 account_name: str, account_type: str) -> Dict[str, Any]:
        """Generate asset trend chart data"""
        # Filter snapshots for specific account
        account_snapshots = [
            s for s in snapshots 
            if s.account_name == account_name and s.account_type == account_type
        ]
        
        # Sort by date
        account_snapshots.sort(key=lambda x: x.as_of_date)
        
        if not account_snapshots:
            return {"error": "No data available for specified account"}
        
        # Extract data points
        dates = [s.as_of_date.strftime("%Y-%m-%d") for s in account_snapshots]
        balances = [float(s.balance) for s in account_snapshots]
        
        # Calculate growth rates
        growth_rates = []
        for i in range(1, len(balances)):
            if balances[i-1] != 0:
                growth = (balances[i] - balances[i-1]) / abs(balances[i-1]) * 100
                growth_rates.append(round(growth, 2))
            else:
                growth_rates.append(0.0)
        
        return {
            "chart_type": "line",
            "title": f"{account_name} Balance Trend",
            "data": {
                "labels": dates,
                "datasets": [{
                    "label": f"{account_name} Balance",
                    "data": balances,
                    "borderColor": self.color_palette.get(account_type, "#666666"),
                    "backgroundColor": self.color_palette.get(account_type, "#666666") + "20",
                    "fill": True,
                    "tension": 0.4
                }]
            },
            "options": {
                "responsive": True,
                "scales": {
                    "y": {
                        "beginAtZero": False,
                        "title": {"display": True, "text": "Balance (¥)"}
                    },
                    "x": {
                        "title": {"display": True, "text": "Date"}
                    }
                },
                "plugins": {
                    "tooltip": {
                        "callbacks": {
                            "label": "Balance: ¥{value}"
                        }
                    }
                }
            },
            "metadata": {
                "account_name": account_name,
                "account_type": account_type,
                "data_points": len(dates),
                "date_range": {
                    "start": dates[0] if dates else None,
                    "end": dates[-1] if dates else None
                },
                "growth_rates": growth_rates,
                "total_growth": growth_rates[-1] if growth_rates else 0,
                "current_balance": balances[-1] if balances else 0
            }
        }
    
    def generate_account_breakdown_chart(self, snapshots: List[AssetSnapshot], 
                                       as_of_date: datetime) -> Dict[str, Any]:
        """Generate account-wise asset breakdown visualization"""
        # Filter snapshots for specific date
        date_snapshots = [
            s for s in snapshots 
            if s.as_of_date.date() == as_of_date.date()
        ]
        
        # Group by account type
        breakdown = {}
        total_assets = Decimal("0")
        
        for snapshot in date_snapshots:
            account_type = snapshot.account_type
            if account_type not in breakdown:
                breakdown[account_type] = {
                    "total_balance": Decimal("0"),
                    "accounts": []
                }
            
            breakdown[account_type]["total_balance"] += snapshot.balance
            breakdown[account_type]["accounts"].append({
                "name": snapshot.account_name,
                "balance": float(snapshot.balance),
                "user_id": snapshot.user_id
            })
            total_assets += snapshot.balance
        
        # Calculate percentages
        for account_type in breakdown:
            if total_assets > 0:
                breakdown[account_type]["percentage"] = float(
                    (breakdown[account_type]["total_balance"] / total_assets * 100).quantize(
                        Decimal("0.01"), ROUND_HALF_UP
                    )
                )
            else:
                breakdown[account_type]["percentage"] = 0.0
        
        # Prepare chart data
        labels = list(breakdown.keys())
        data = [float(breakdown[account_type]["total_balance"]) for account_type in labels]
        colors = [self.color_palette.get(account_type, "#666666") for account_type in labels]
        
        return {
            "chart_type": "doughnut",
            "title": f"Asset Breakdown - {as_of_date.strftime('%Y-%m-%d')}",
            "data": {
                "labels": labels,
                "datasets": [{
                    "data": data,
                    "backgroundColor": colors,
                    "borderColor": ["#FFFFFF"] * len(colors),
                    "borderWidth": 2
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "legend": {
                        "position": "right"
                    },
                    "tooltip": {
                        "callbacks": {
                            "label": "¥{value} ({percentage}%)"
                        }
                    }
                },
                "cutout": "60%"
            },
            "metadata": {
                "total_assets": float(total_assets),
                "as_of_date": as_of_date.strftime("%Y-%m-%d"),
                "breakdown": breakdown,
                "account_count": sum(len(data["accounts"]) for data in breakdown.values())
            }
        }
    
    def calculate_growth_metrics(self, snapshots: List[AssetSnapshot], 
                               account_name: str, account_type: str) -> Dict[str, Any]:
        """Calculate month-over-month growth percentages and metrics"""
        account_snapshots = [
            s for s in snapshots 
            if s.account_name == account_name and s.account_type == account_type
        ]
        
        account_snapshots.sort(key=lambda x: x.as_of_date)
        
        if len(account_snapshots) < 2:
            return {"error": "Insufficient data for growth calculation"}
        
        current = account_snapshots[-1]
        previous = account_snapshots[-2]
        
        balance_change = current.balance - previous.balance
        
        if previous.balance != 0:
            growth_percentage = (balance_change / abs(previous.balance) * 100).quantize(
                Decimal("0.01"), ROUND_HALF_UP
            )
        else:
            growth_percentage = Decimal("100") if current.balance > 0 else Decimal("0")
        
        # Calculate additional metrics
        days_diff = (current.as_of_date - previous.as_of_date).days
        daily_growth = balance_change / days_diff if days_diff > 0 else Decimal("0")
        
        # Annualized growth rate (simple approximation)
        if days_diff > 0 and previous.balance > 0:
            daily_rate = balance_change / abs(previous.balance) / days_diff
            annualized_growth = (daily_rate * 365 * 100).quantize(Decimal("0.01"), ROUND_HALF_UP)
        else:
            annualized_growth = Decimal("0")
        
        return {
            "account_name": account_name,
            "account_type": account_type,
            "current_balance": current.balance,
            "previous_balance": previous.balance,
            "balance_change": balance_change,
            "growth_percentage": growth_percentage,
            "period_days": days_diff,
            "daily_growth": daily_growth,
            "annualized_growth": annualized_growth,
            "current_date": current.as_of_date.strftime("%Y-%m-%d"),
            "previous_date": previous.as_of_date.strftime("%Y-%m-%d"),
            "trend": "increasing" if balance_change > 0 else "decreasing" if balance_change < 0 else "stable"
        }
    
    def generate_asset_allocation_pie_chart(self, snapshots: List[AssetSnapshot], 
                                          as_of_date: datetime) -> Dict[str, Any]:
        """Generate asset allocation pie chart by account type"""
        date_snapshots = [
            s for s in snapshots 
            if s.as_of_date.date() == as_of_date.date()
        ]
        
        # Calculate totals by account type
        allocation = {}
        total_assets = Decimal("0")
        
        for snapshot in date_snapshots:
            account_type = snapshot.account_type
            if account_type not in allocation:
                allocation[account_type] = Decimal("0")
            allocation[account_type] += snapshot.balance
            total_assets += snapshot.balance
        
        # Calculate percentages
        allocation_data = []
        for account_type, amount in allocation.items():
            percentage = (amount / total_assets * 100).quantize(
                Decimal("0.01"), ROUND_HALF_UP
            ) if total_assets > 0 else Decimal("0")
            
            allocation_data.append({
                "account_type": account_type,
                "amount": amount,
                "percentage": percentage,
                "color": self.color_palette.get(account_type, "#666666")
            })
        
        # Sort by amount descending
        allocation_data.sort(key=lambda x: x["amount"], reverse=True)
        
        return {
            "chart_type": "pie",
            "title": f"Asset Allocation - {as_of_date.strftime('%Y-%m-%d')}",
            "data": {
                "labels": [item["account_type"].title() for item in allocation_data],
                "datasets": [{
                    "data": [float(item["amount"]) for item in allocation_data],
                    "backgroundColor": [item["color"] for item in allocation_data],
                    "borderColor": "#FFFFFF",
                    "borderWidth": 2
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "legend": {
                        "position": "bottom",
                        "labels": {
                            "generateLabels": "function(chart) { return custom labels with amounts }"
                        }
                    },
                    "tooltip": {
                        "callbacks": {
                            "label": "¥{value} ({percentage}%)"
                        }
                    }
                }
            },
            "metadata": {
                "total_assets": float(total_assets),
                "allocation_data": allocation_data,
                "largest_allocation": allocation_data[0]["account_type"] if allocation_data else None,
                "diversification_score": self._calculate_diversification_score(allocation_data)
            }
        }
    
    def _calculate_diversification_score(self, allocation_data: List[Dict[str, Any]]) -> float:
        """Calculate portfolio diversification score (0-100)"""
        if not allocation_data:
            return 0.0
        
        # Simple diversification score based on distribution
        percentages = [float(item["percentage"]) for item in allocation_data]
        
        # Perfect diversification would be equal distribution
        ideal_percentage = 100.0 / len(percentages)
        
        # Calculate deviation from ideal
        total_deviation = sum(abs(pct - ideal_percentage) for pct in percentages)
        max_possible_deviation = (len(percentages) - 1) * ideal_percentage
        
        if max_possible_deviation > 0:
            diversification_score = (1 - total_deviation / max_possible_deviation) * 100
            return round(max(0.0, diversification_score), 2)
        
        return 100.0


class BudgetAlertSystem:
    """Budget alert and tracking system - would be in modules/accounting/analytics/"""
    
    def __init__(self):
        self.alert_thresholds = {
            "over_budget": 0.0,  # Any amount over budget
            "approaching_limit": -10.0,  # Within 10% of budget
            "significant_increase": 25.0,  # 25% increase from previous period
            "trend_warning": 50.0  # 50% increase trend over 3 periods
        }
    
    def generate_budget_alerts(self, budget_vs_actual: List[Dict[str, Any]], 
                             historical_data: Optional[List[Dict[str, Any]]] = None) -> List[BudgetAlert]:
        """Generate budget alerts based on variance and trends"""
        alerts = []
        
        for category_data in budget_vs_actual:
            category = category_data["category"]
            actual = category_data["actual"]
            budget = category_data["budget"]
            variance_pct = category_data["variance_percentage"]
            
            # Over budget alert
            if variance_pct > self.alert_thresholds["over_budget"]:
                severity = self._determine_severity(variance_pct)
                alerts.append(BudgetAlert(
                    alert_type=AlertType.OVER_BUDGET,
                    category=category,
                    message=f"{category} is over budget by ¥{actual - budget:.2f} ({variance_pct:.1f}%)",
                    severity=severity,
                    actual_amount=actual,
                    budget_amount=budget,
                    variance_percentage=variance_pct
                ))
            
            # Approaching limit alert
            elif variance_pct > self.alert_thresholds["approaching_limit"]:
                alerts.append(BudgetAlert(
                    alert_type=AlertType.APPROACHING_LIMIT,
                    category=category,
                    message=f"{category} is approaching budget limit ({variance_pct:.1f}% of budget used)",
                    severity="medium",
                    actual_amount=actual,
                    budget_amount=budget,
                    variance_percentage=variance_pct
                ))
        
        # Historical trend alerts
        if historical_data:
            trend_alerts = self._generate_trend_alerts(historical_data)
            alerts.extend(trend_alerts)
        
        return sorted(alerts, key=lambda x: self._get_severity_priority(x.severity))
    
    def _determine_severity(self, variance_pct: Decimal) -> str:
        """Determine alert severity based on variance percentage"""
        if variance_pct > 50:
            return "high"
        elif variance_pct > 20:
            return "medium"
        else:
            return "low"
    
    def _get_severity_priority(self, severity: str) -> int:
        """Get priority order for severity (lower number = higher priority)"""
        return {"high": 1, "medium": 2, "low": 3}.get(severity, 4)
    
    def _generate_trend_alerts(self, historical_data: List[Dict[str, Any]]) -> List[BudgetAlert]:
        """Generate alerts based on spending trends"""
        alerts = []
        
        # Group historical data by category
        category_trends = {}
        for period_data in historical_data:
            for category_data in period_data.get("budget_vs_actual", []):
                category = category_data["category"]
                if category not in category_trends:
                    category_trends[category] = []
                category_trends[category].append(category_data["actual"])
        
        # Analyze trends
        for category, amounts in category_trends.items():
            if len(amounts) >= 3:  # Need at least 3 data points
                recent_avg = sum(amounts[-2:]) / 2  # Average of last 2 periods
                older_avg = sum(amounts[-3:-1]) / 2  # Average of previous 2 periods
                
                if older_avg > 0:
                    trend_change = (recent_avg - older_avg) / older_avg * 100
                    
                    if trend_change > self.alert_thresholds["trend_warning"]:
                        alerts.append(BudgetAlert(
                            alert_type=AlertType.TREND_WARNING,
                            category=category,
                            message=f"{category} spending has increased by {trend_change:.1f}% over recent periods",
                            severity="medium",
                            actual_amount=recent_avg,
                            budget_amount=older_avg,
                            variance_percentage=Decimal(str(trend_change))
                        ))
        
        return alerts


class FinancialMetricsDashboard:
    """Financial metrics visualization dashboard - would be in modules/accounting/analytics/"""
    
    def generate_key_metrics_dashboard(self, income_statement: Dict[str, Any], 
                                     asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate key financial metrics for dashboard visualization"""
        # Extract key values
        total_revenue = income_statement.get("revenue", {}).get("total_revenue", Decimal("0"))
        total_expenses = income_statement.get("expenses", {}).get("total_expenses", Decimal("0"))
        net_income = income_statement.get("net_income", Decimal("0"))
        
        total_assets = asset_data.get("total_assets", Decimal("0"))
        
        # Calculate key ratios
        expense_ratio = (total_expenses / total_revenue * 100).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        ) if total_revenue > 0 else Decimal("0")
        
        savings_rate = (net_income / total_revenue * 100).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        ) if total_revenue > 0 else Decimal("0")
        
        # Monthly expense burn rate (assuming monthly data)
        monthly_burn = total_expenses
        months_of_expenses = (total_assets / monthly_burn).quantize(
            Decimal("0.1"), ROUND_HALF_UP
        ) if monthly_burn > 0 else Decimal("999")
        
        return {
            "key_metrics": {
                "total_income": {
                    "value": float(total_revenue),
                    "display": f"¥{total_revenue:,.2f}",
                    "trend": "stable",  # Would be calculated from historical data
                    "color": "#4CAF50"
                },
                "total_expenses": {
                    "value": float(total_expenses),
                    "display": f"¥{total_expenses:,.2f}",
                    "trend": "stable",
                    "color": "#F44336"
                },
                "net_income": {
                    "value": float(net_income),
                    "display": f"¥{net_income:,.2f}",
                    "trend": "increasing" if net_income > 0 else "decreasing",
                    "color": "#4CAF50" if net_income > 0 else "#F44336"
                },
                "total_assets": {
                    "value": float(total_assets),
                    "display": f"¥{total_assets:,.2f}",
                    "trend": "increasing",
                    "color": "#2196F3"
                }
            },
            "ratios": {
                "expense_ratio": {
                    "value": float(expense_ratio),
                    "display": f"{expense_ratio}%",
                    "benchmark": 70.0,  # 70% is typical benchmark
                    "status": "good" if expense_ratio < 70 else "warning" if expense_ratio < 90 else "poor",
                    "description": "Percentage of income spent on expenses"
                },
                "savings_rate": {
                    "value": float(savings_rate),
                    "display": f"{savings_rate}%",
                    "benchmark": 20.0,  # 20% savings rate benchmark
                    "status": "excellent" if savings_rate >= 20 else "good" if savings_rate >= 10 else "needs_improvement",
                    "description": "Percentage of income saved"
                },
                "emergency_fund": {
                    "value": float(months_of_expenses),
                    "display": f"{months_of_expenses} months",
                    "benchmark": 6.0,  # 6 months of expenses
                    "status": "excellent" if months_of_expenses >= 6 else "good" if months_of_expenses >= 3 else "insufficient",
                    "description": "Months of expenses covered by assets"
                }
            },
            "alerts": [
                {
                    "type": "info",
                    "message": f"Your savings rate of {savings_rate}% is above the recommended 20%" if savings_rate >= 20 else f"Consider increasing savings rate from {savings_rate}% to 20%",
                    "severity": "low"
                }
            ]
        }


class TestAssetTrendCharts:
    """Test asset trend chart generation"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.generator = VisualizationDataGenerator()
        
        # Create sample asset snapshots over time
        self.sample_snapshots = [
            AssetSnapshot("Savings Account", "savings", Decimal("10000.00"), datetime(2024, 1, 31), "user1"),
            AssetSnapshot("Savings Account", "savings", Decimal("11000.00"), datetime(2024, 2, 29), "user1"),
            AssetSnapshot("Savings Account", "savings", Decimal("12500.00"), datetime(2024, 3, 31), "user1"),
            AssetSnapshot("Investment Account", "investment", Decimal("50000.00"), datetime(2024, 1, 31), "user1"),
            AssetSnapshot("Investment Account", "investment", Decimal("52000.00"), datetime(2024, 2, 29), "user1"),
            AssetSnapshot("Investment Account", "investment", Decimal("51000.00"), datetime(2024, 3, 31), "user1"),
        ]
    
    def test_asset_trend_chart_generation(self):
        """Test generating asset trend chart data"""
        chart_data = self.generator.generate_asset_trend_chart(
            self.sample_snapshots, "Savings Account", "savings"
        )
        
        assert chart_data["chart_type"] == "line"
        assert chart_data["title"] == "Savings Account Balance Trend"
        
        # Check data structure
        assert "data" in chart_data
        assert "labels" in chart_data["data"]
        assert "datasets" in chart_data["data"]
        
        # Verify dates
        expected_dates = ["2024-01-31", "2024-02-29", "2024-03-31"]
        assert chart_data["data"]["labels"] == expected_dates
        
        # Verify balances
        expected_balances = [10000.00, 11000.00, 12500.00]
        assert chart_data["data"]["datasets"][0]["data"] == expected_balances
    
    def test_asset_trend_metadata(self):
        """Test asset trend chart metadata calculation"""
        chart_data = self.generator.generate_asset_trend_chart(
            self.sample_snapshots, "Savings Account", "savings"
        )
        
        metadata = chart_data["metadata"]
        
        assert metadata["account_name"] == "Savings Account"
        assert metadata["account_type"] == "savings"
        assert metadata["data_points"] == 3
        assert metadata["current_balance"] == 12500.00
        
        # Check growth rates
        growth_rates = metadata["growth_rates"]
        assert len(growth_rates) == 2  # n-1 growth rates for n data points
        
        # First growth: (11000 - 10000) / 10000 * 100 = 10%
        assert growth_rates[0] == 10.0
        
        # Second growth: (12500 - 11000) / 11000 * 100 = 13.64%
        expected_second_growth = round((12500 - 11000) / 11000 * 100, 2)
        assert growth_rates[1] == expected_second_growth
    
    def test_asset_trend_color_scheme(self):
        """Test asset trend chart uses correct color scheme"""
        chart_data = self.generator.generate_asset_trend_chart(
            self.sample_snapshots, "Savings Account", "savings"
        )
        
        dataset = chart_data["data"]["datasets"][0]
        
        # Should use savings color
        assert dataset["borderColor"] == "#2196F3"
        assert dataset["backgroundColor"] == "#2196F320"  # With transparency
    
    def test_asset_trend_no_data(self):
        """Test asset trend chart with no matching data"""
        chart_data = self.generator.generate_asset_trend_chart(
            self.sample_snapshots, "Nonexistent Account", "checking"
        )
        
        assert "error" in chart_data
        assert chart_data["error"] == "No data available for specified account"
    
    def test_asset_trend_single_data_point(self):
        """Test asset trend chart with single data point"""
        single_snapshot = [self.sample_snapshots[0]]
        
        chart_data = self.generator.generate_asset_trend_chart(
            single_snapshot, "Savings Account", "savings"
        )
        
        # Should still generate chart
        assert chart_data["data"]["labels"] == ["2024-01-31"]
        assert chart_data["data"]["datasets"][0]["data"] == [10000.00]
        assert chart_data["metadata"]["growth_rates"] == []  # No growth data


class TestAssetBreakdownVisualization:
    """Test account-wise asset breakdown visualizations"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.generator = VisualizationDataGenerator()
        
        # Create snapshots for breakdown analysis
        self.breakdown_snapshots = [
            AssetSnapshot("Bank of China", "checking", Decimal("5000.00"), datetime(2024, 3, 31), "user1"),
            AssetSnapshot("ICBC Savings", "savings", Decimal("25000.00"), datetime(2024, 3, 31), "user1"),
            AssetSnapshot("Investment Portfolio", "investment", Decimal("100000.00"), datetime(2024, 3, 31), "user1"),
            AssetSnapshot("401k", "retirement", Decimal("200000.00"), datetime(2024, 3, 31), "user1"),
            AssetSnapshot("Joint Checking", "checking", Decimal("3000.00"), datetime(2024, 3, 31), "user2"),
        ]
    
    def test_account_breakdown_chart_generation(self):
        """Test generating account breakdown chart"""
        chart_data = self.generator.generate_account_breakdown_chart(
            self.breakdown_snapshots, datetime(2024, 3, 31)
        )
        
        assert chart_data["chart_type"] == "doughnut"
        assert "Asset Breakdown - 2024-03-31" in chart_data["title"]
        
        # Check that all account types are included
        labels = chart_data["data"]["labels"]
        assert "checking" in labels
        assert "savings" in labels
        assert "investment" in labels
        assert "retirement" in labels
    
    def test_account_breakdown_calculations(self):
        """Test account breakdown calculations are correct"""
        chart_data = self.generator.generate_account_breakdown_chart(
            self.breakdown_snapshots, datetime(2024, 3, 31)
        )
        
        metadata = chart_data["metadata"]
        breakdown = metadata["breakdown"]
        
        # Total assets: 5000 + 25000 + 100000 + 200000 + 3000 = 333000
        assert metadata["total_assets"] == 333000.00
        
        # Checking total: 5000 + 3000 = 8000
        assert breakdown["checking"]["total_balance"] == Decimal("8000.00")
        assert breakdown["checking"]["percentage"] == 2.40  # 8000/333000 * 100
        
        # Retirement: 200000
        assert breakdown["retirement"]["total_balance"] == Decimal("200000.00")
        expected_retirement_pct = round(200000 / 333000 * 100, 2)
        assert breakdown["retirement"]["percentage"] == expected_retirement_pct
    
    def test_account_breakdown_account_details(self):
        """Test account breakdown preserves account details"""
        chart_data = self.generator.generate_account_breakdown_chart(
            self.breakdown_snapshots, datetime(2024, 3, 31)
        )
        
        metadata = chart_data["metadata"]
        checking_accounts = metadata["breakdown"]["checking"]["accounts"]
        
        # Should have 2 checking accounts
        assert len(checking_accounts) == 2
        
        account_names = [acc["name"] for acc in checking_accounts]
        assert "Bank of China" in account_names
        assert "Joint Checking" in account_names
        
        # Check account details
        bank_of_china = next(acc for acc in checking_accounts if acc["name"] == "Bank of China")
        assert bank_of_china["balance"] == 5000.00
        assert bank_of_china["user_id"] == "user1"
    
    def test_account_breakdown_color_scheme(self):
        """Test account breakdown uses correct colors"""
        chart_data = self.generator.generate_account_breakdown_chart(
            self.breakdown_snapshots, datetime(2024, 3, 31)
        )
        
        labels = chart_data["data"]["labels"]
        colors = chart_data["data"]["datasets"][0]["backgroundColor"]
        
        # Check that colors match account types
        for i, label in enumerate(labels):
            expected_color = self.generator.color_palette.get(label, "#666666")
            assert colors[i] == expected_color


class TestGrowthCalculations:
    """Test month-over-month growth calculations"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.generator = VisualizationDataGenerator()
        
        # Create snapshots for growth calculation
        self.growth_snapshots = [
            AssetSnapshot("Growth Account", "investment", Decimal("10000.00"), datetime(2024, 1, 31), "user1"),
            AssetSnapshot("Growth Account", "investment", Decimal("11500.00"), datetime(2024, 2, 29), "user1"),
            AssetSnapshot("Growth Account", "investment", Decimal("10800.00"), datetime(2024, 3, 31), "user1"),
        ]
    
    def test_growth_metrics_calculation(self):
        """Test growth metrics calculation"""
        growth_data = self.generator.calculate_growth_metrics(
            self.growth_snapshots, "Growth Account", "investment"
        )
        
        assert growth_data["account_name"] == "Growth Account"
        assert growth_data["current_balance"] == Decimal("10800.00")
        assert growth_data["previous_balance"] == Decimal("11500.00")
        
        # Balance change: 10800 - 11500 = -700
        assert growth_data["balance_change"] == Decimal("-700.00")
        
        # Growth percentage: -700 / 11500 * 100 = -6.09%
        expected_growth = (Decimal("-700.00") / Decimal("11500.00") * 100).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )
        assert growth_data["growth_percentage"] == expected_growth
        
        assert growth_data["trend"] == "decreasing"
    
    def test_positive_growth_calculation(self):
        """Test positive growth calculation"""
        positive_snapshots = [
            AssetSnapshot("Savings", "savings", Decimal("5000.00"), datetime(2024, 1, 31), "user1"),
            AssetSnapshot("Savings", "savings", Decimal("5250.00"), datetime(2024, 2, 29), "user1"),
        ]
        
        growth_data = self.generator.calculate_growth_metrics(
            positive_snapshots, "Savings", "savings"
        )
        
        # Growth: (5250 - 5000) / 5000 * 100 = 5%
        assert growth_data["growth_percentage"] == Decimal("5.00")
        assert growth_data["trend"] == "increasing"
    
    def test_annualized_growth_calculation(self):
        """Test annualized growth rate calculation"""
        growth_data = self.generator.calculate_growth_metrics(
            self.growth_snapshots, "Growth Account", "investment"
        )
        
        # Should calculate annualized growth
        assert "annualized_growth" in growth_data
        assert isinstance(growth_data["annualized_growth"], Decimal)
        
        # Period should be calculated correctly
        assert growth_data["period_days"] > 0
        assert "daily_growth" in growth_data
    
    def test_zero_previous_balance_growth(self):
        """Test growth calculation when previous balance is zero"""
        zero_balance_snapshots = [
            AssetSnapshot("New Account", "savings", Decimal("0.00"), datetime(2024, 1, 31), "user1"),
            AssetSnapshot("New Account", "savings", Decimal("1000.00"), datetime(2024, 2, 29), "user1"),
        ]
        
        growth_data = self.generator.calculate_growth_metrics(
            zero_balance_snapshots, "New Account", "savings"
        )
        
        # Should handle zero base case
        assert growth_data["growth_percentage"] == Decimal("100")
        assert growth_data["trend"] == "increasing"
    
    def test_insufficient_data_growth(self):
        """Test growth calculation with insufficient data"""
        single_snapshot = [self.growth_snapshots[0]]
        
        growth_data = self.generator.calculate_growth_metrics(
            single_snapshot, "Growth Account", "investment"
        )
        
        assert "error" in growth_data
        assert growth_data["error"] == "Insufficient data for growth calculation"


class TestAssetAllocationCharts:
    """Test asset allocation pie chart generation"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.generator = VisualizationDataGenerator()
        
        self.allocation_snapshots = [
            AssetSnapshot("Checking 1", "checking", Decimal("10000.00"), datetime(2024, 3, 31), "user1"),
            AssetSnapshot("Savings 1", "savings", Decimal("30000.00"), datetime(2024, 3, 31), "user1"),
            AssetSnapshot("Investment 1", "investment", Decimal("40000.00"), datetime(2024, 3, 31), "user1"),
            AssetSnapshot("401k", "retirement", Decimal("20000.00"), datetime(2024, 3, 31), "user1"),
        ]
    
    def test_asset_allocation_pie_chart(self):
        """Test asset allocation pie chart generation"""
        chart_data = self.generator.generate_asset_allocation_pie_chart(
            self.allocation_snapshots, datetime(2024, 3, 31)
        )
        
        assert chart_data["chart_type"] == "pie"
        assert "Asset Allocation" in chart_data["title"]
        
        # Total assets: 10000 + 30000 + 40000 + 20000 = 100000
        assert chart_data["metadata"]["total_assets"] == 100000.00
    
    def test_allocation_percentage_calculations(self):
        """Test allocation percentage calculations"""
        chart_data = self.generator.generate_asset_allocation_pie_chart(
            self.allocation_snapshots, datetime(2024, 3, 31)
        )
        
        allocation_data = chart_data["metadata"]["allocation_data"]
        
        # Find investment allocation (should be largest)
        investment_data = next(item for item in allocation_data if item["account_type"] == "investment")
        assert investment_data["amount"] == Decimal("40000.00")
        assert investment_data["percentage"] == Decimal("40.00")  # 40000/100000 * 100
        
        # Check savings allocation
        savings_data = next(item for item in allocation_data if item["account_type"] == "savings")
        assert savings_data["percentage"] == Decimal("30.00")  # 30000/100000 * 100
    
    def test_allocation_sorting(self):
        """Test allocation data is sorted by amount"""
        chart_data = self.generator.generate_asset_allocation_pie_chart(
            self.allocation_snapshots, datetime(2024, 3, 31)
        )
        
        allocation_data = chart_data["metadata"]["allocation_data"]
        
        # Should be sorted by amount descending
        amounts = [item["amount"] for item in allocation_data]
        assert amounts == sorted(amounts, reverse=True)
        
        # Largest should be investment
        assert allocation_data[0]["account_type"] == "investment"
        assert chart_data["metadata"]["largest_allocation"] == "investment"
    
    def test_diversification_score_calculation(self):
        """Test diversification score calculation"""
        chart_data = self.generator.generate_asset_allocation_pie_chart(
            self.allocation_snapshots, datetime(2024, 3, 31)
        )
        
        diversification_score = chart_data["metadata"]["diversification_score"]
        
        # Should be a value between 0-100
        assert 0 <= diversification_score <= 100
        assert isinstance(diversification_score, float)
        
        # With 4 asset types, perfect diversification would be 25% each
        # Current allocation (40%, 30%, 20%, 10%) should have moderate diversification
        assert 50 <= diversification_score <= 85  # Reasonable range


class TestFinancialMetricsVisualization:
    """Test financial metrics dashboard visualization"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.dashboard = FinancialMetricsDashboard()
        
        self.sample_income_statement = {
            "revenue": {"total_revenue": Decimal("10000.00")},
            "expenses": {"total_expenses": Decimal("7000.00")},
            "net_income": Decimal("3000.00")
        }
        
        self.sample_asset_data = {
            "total_assets": Decimal("50000.00")
        }
    
    def test_key_metrics_dashboard_generation(self):
        """Test key metrics dashboard generation"""
        dashboard_data = self.dashboard.generate_key_metrics_dashboard(
            self.sample_income_statement, self.sample_asset_data
        )
        
        assert "key_metrics" in dashboard_data
        assert "ratios" in dashboard_data
        
        key_metrics = dashboard_data["key_metrics"]
        
        # Check key metrics
        assert key_metrics["total_income"]["value"] == 10000.00
        assert key_metrics["total_expenses"]["value"] == 7000.00
        assert key_metrics["net_income"]["value"] == 3000.00
        assert key_metrics["total_assets"]["value"] == 50000.00
    
    def test_financial_ratios_calculation(self):
        """Test financial ratios calculation"""
        dashboard_data = self.dashboard.generate_key_metrics_dashboard(
            self.sample_income_statement, self.sample_asset_data
        )
        
        ratios = dashboard_data["ratios"]
        
        # Expense ratio: 7000/10000 * 100 = 70%
        assert ratios["expense_ratio"]["value"] == 70.0
        assert ratios["expense_ratio"]["status"] == "good"  # 70% is at benchmark
        
        # Savings rate: 3000/10000 * 100 = 30%
        assert ratios["savings_rate"]["value"] == 30.0
        assert ratios["savings_rate"]["status"] == "excellent"  # Above 20% benchmark
        
        # Emergency fund: 50000/7000 = 7.1 months
        expected_months = round(50000.0 / 7000.0, 1)
        assert ratios["emergency_fund"]["value"] == expected_months
        assert ratios["emergency_fund"]["status"] == "excellent"  # Above 6 months
    
    def test_ratio_status_determination(self):
        """Test ratio status determination logic"""
        # Test poor expense ratio
        poor_income_statement = {
            "revenue": {"total_revenue": Decimal("10000.00")},
            "expenses": {"total_expenses": Decimal("9500.00")},  # 95% expense ratio
            "net_income": Decimal("500.00")
        }
        
        dashboard_data = self.dashboard.generate_key_metrics_dashboard(
            poor_income_statement, {"total_assets": Decimal("1000.00")}
        )
        
        ratios = dashboard_data["ratios"]
        
        assert ratios["expense_ratio"]["status"] == "poor"  # 95% > 90%
        assert ratios["savings_rate"]["status"] == "needs_improvement"  # 5% < 10%
        assert ratios["emergency_fund"]["status"] == "insufficient"  # < 3 months
    
    def test_dashboard_display_formatting(self):
        """Test dashboard display formatting"""
        dashboard_data = self.dashboard.generate_key_metrics_dashboard(
            self.sample_income_statement, self.sample_asset_data
        )
        
        key_metrics = dashboard_data["key_metrics"]
        
        # Check display formatting
        assert key_metrics["total_income"]["display"] == "¥10,000.00"
        assert key_metrics["net_income"]["display"] == "¥3,000.00"
        
        # Check color coding
        assert key_metrics["net_income"]["color"] == "#4CAF50"  # Green for positive
        assert key_metrics["total_expenses"]["color"] == "#F44336"  # Red for expenses
    
    def test_dashboard_with_zero_values(self):
        """Test dashboard with zero or negative values"""
        zero_income_statement = {
            "revenue": {"total_revenue": Decimal("0.00")},
            "expenses": {"total_expenses": Decimal("1000.00")},
            "net_income": Decimal("-1000.00")
        }
        
        dashboard_data = self.dashboard.generate_key_metrics_dashboard(
            zero_income_statement, {"total_assets": Decimal("5000.00")}
        )
        
        ratios = dashboard_data["ratios"]
        
        # Should handle zero division gracefully
        assert ratios["expense_ratio"]["value"] == 0.0
        assert ratios["savings_rate"]["value"] == 0.0
        
        # Net income should be negative
        net_income = dashboard_data["key_metrics"]["net_income"]
        assert net_income["value"] == -1000.00
        assert net_income["color"] == "#F44336"  # Red for negative


class TestBudgetAlerts:
    """Test budget tracking and alerts"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.alert_system = BudgetAlertSystem()
        
        self.sample_budget_data = [
            {
                "category": "餐饮",
                "actual": Decimal("1200.00"),
                "budget": Decimal("1000.00"),
                "variance": Decimal("200.00"),
                "variance_percentage": Decimal("20.00")
            },
            {
                "category": "交通",
                "actual": Decimal("280.00"),
                "budget": Decimal("300.00"),
                "variance": Decimal("-20.00"),
                "variance_percentage": Decimal("-6.67")
            },
            {
                "category": "房租",
                "actual": Decimal("2200.00"),
                "budget": Decimal("2000.00"),
                "variance": Decimal("200.00"),
                "variance_percentage": Decimal("10.00")
            }
        ]
    
    def test_over_budget_alerts(self):
        """Test over budget alert generation"""
        alerts = self.alert_system.generate_budget_alerts(self.sample_budget_data)
        
        # Should have alerts for over-budget categories
        over_budget_alerts = [alert for alert in alerts if alert.alert_type == AlertType.OVER_BUDGET]
        
        assert len(over_budget_alerts) >= 2  # 餐饮 and 房租 are over budget
        
        # Check specific alert
        food_alert = next(alert for alert in over_budget_alerts if alert.category == "餐饮")
        assert food_alert.actual_amount == Decimal("1200.00")
        assert food_alert.budget_amount == Decimal("1000.00")
        assert "over budget by ¥200.00" in food_alert.message
        assert food_alert.severity == "medium"  # 20% over is medium severity
    
    def test_approaching_limit_alerts(self):
        """Test approaching budget limit alerts"""
        approaching_data = [
            {
                "category": "娱乐",
                "actual": Decimal("270.00"),
                "budget": Decimal("300.00"),
                "variance": Decimal("-30.00"),
                "variance_percentage": Decimal("-10.00")  # Exactly at threshold
            }
        ]
        
        alerts = self.alert_system.generate_budget_alerts(approaching_data)
        
        # Should not generate approaching limit alert for -10% (at threshold)
        approaching_alerts = [alert for alert in alerts if alert.alert_type == AlertType.APPROACHING_LIMIT]
        assert len(approaching_alerts) == 0  # -10% is at threshold, not above
        
        # Test with -5% (above threshold)
        approaching_data[0]["variance_percentage"] = Decimal("-5.00")
        alerts = self.alert_system.generate_budget_alerts(approaching_data)
        approaching_alerts = [alert for alert in alerts if alert.alert_type == AlertType.APPROACHING_LIMIT]
        assert len(approaching_alerts) == 1
    
    def test_alert_severity_determination(self):
        """Test alert severity determination"""
        high_variance_data = [
            {
                "category": "奢侈品",
                "actual": Decimal("1600.00"),
                "budget": Decimal("1000.00"),
                "variance": Decimal("600.00"),
                "variance_percentage": Decimal("60.00")  # High variance
            }
        ]
        
        alerts = self.alert_system.generate_budget_alerts(high_variance_data)
        high_severity_alert = alerts[0]
        
        assert high_severity_alert.severity == "high"  # 60% > 50%
        
        # Test medium severity
        medium_data = high_variance_data.copy()
        medium_data[0]["variance_percentage"] = Decimal("30.00")
        
        alerts = self.alert_system.generate_budget_alerts(medium_data)
        assert alerts[0].severity == "medium"  # 20% < 30% < 50%
    
    def test_alert_sorting_by_severity(self):
        """Test alerts are sorted by severity priority"""
        mixed_severity_data = [
            {
                "category": "Low Priority",
                "actual": Decimal("110.00"),
                "budget": Decimal("100.00"),
                "variance": Decimal("10.00"),
                "variance_percentage": Decimal("10.00")  # Low severity
            },
            {
                "category": "High Priority",
                "actual": Decimal("1800.00"),
                "budget": Decimal("1000.00"),
                "variance": Decimal("800.00"),
                "variance_percentage": Decimal("80.00")  # High severity
            },
            {
                "category": "Medium Priority",
                "actual": Decimal("1300.00"),
                "budget": Decimal("1000.00"),
                "variance": Decimal("300.00"),
                "variance_percentage": Decimal("30.00")  # Medium severity
            }
        ]
        
        alerts = self.alert_system.generate_budget_alerts(mixed_severity_data)
        
        # Should be sorted: high, medium, low
        assert alerts[0].severity == "high"
        assert alerts[1].severity == "medium"  
        assert alerts[2].severity == "low"
        
        assert alerts[0].category == "High Priority"
        assert alerts[1].category == "Medium Priority"
        assert alerts[2].category == "Low Priority"
    
    def test_no_alerts_scenario(self):
        """Test scenario with no alerts needed"""
        good_budget_data = [
            {
                "category": "餐饮",
                "actual": Decimal("800.00"),
                "budget": Decimal("1000.00"),
                "variance": Decimal("-200.00"),
                "variance_percentage": Decimal("-20.00")  # Well under budget
            }
        ]
        
        alerts = self.alert_system.generate_budget_alerts(good_budget_data)
        
        # Should not generate any alerts for well-managed budgets
        assert len(alerts) == 0