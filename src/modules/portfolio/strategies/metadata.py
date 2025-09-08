"""
Strategy Metadata System
Provides comprehensive information about strategies including performance attribution,
parameters, and documentation for professional portfolio management.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import pandas as pd

@dataclass
class StrategyMetadata:
    """Comprehensive metadata for investment strategies"""
    
    # Basic Information
    name: str
    strategy_id: str
    category: str  # 'static', 'dynamic', 'factor', 'momentum', etc.
    description: str
    
    # Strategy Details
    target_weights: Dict[str, float] = field(default_factory=dict)
    rebalancing_frequency: str = "monthly"  # daily, weekly, monthly, quarterly, annual
    risk_level: str = "medium"  # low, medium, high
    
    # Performance Attribution
    primary_factors: List[str] = field(default_factory=list)  # e.g., ['value', 'momentum', 'size']
    asset_classes: List[str] = field(default_factory=list)  # e.g., ['equity', 'bonds', 'commodities']
    geographic_exposure: Dict[str, float] = field(default_factory=dict)  # e.g., {'US': 0.6, 'China': 0.3, 'International': 0.1}
    
    # Strategy Parameters
    parameters: Dict[str, Any] = field(default_factory=dict)
    parameter_ranges: Dict[str, Tuple[Any, Any]] = field(default_factory=dict)  # For optimization
    
    # Benchmark Information
    benchmark: Optional[str] = None
    benchmark_weights: Dict[str, float] = field(default_factory=dict)
    
    # Risk Characteristics
    expected_volatility: Optional[float] = None
    max_drawdown_target: Optional[float] = None
    var_95: Optional[float] = None  # Value at Risk 95%
    
    # Implementation Details
    minimum_capital: float = 10000.0
    trading_costs: float = 0.001  # 0.1% per transaction
    liquidity_requirements: str = "high"  # high, medium, low
    
    # Documentation
    author: str = "System"
    version: str = "1.0"
    created_date: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    documentation: str = ""
    
    # Performance History (populated after backtesting)
    backtest_results: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    def update_performance(self, results: Dict[str, Any]) -> None:
        """Update performance metrics after backtesting"""
        self.backtest_results = results
        self.last_modified = datetime.now()
        
        # Extract key metrics
        if 'annual_return' in results:
            self.performance_metrics['annual_return'] = results['annual_return']
        if 'sharpe_ratio' in results:
            self.performance_metrics['sharpe_ratio'] = results['sharpe_ratio']
        if 'max_drawdown' in results:
            self.performance_metrics['max_drawdown'] = results['max_drawdown']
        if 'volatility' in results:
            self.performance_metrics['volatility'] = results['volatility']
    
    def get_risk_score(self) -> float:
        """Calculate overall risk score (0-10 scale)"""
        risk_scores = {'low': 3, 'medium': 5, 'high': 8}
        base_score = risk_scores.get(self.risk_level, 5)
        
        # Adjust based on volatility
        if self.expected_volatility:
            if self.expected_volatility > 0.20:
                base_score += 1
            elif self.expected_volatility < 0.10:
                base_score -= 1
        
        return min(10, max(1, base_score))
    
    def get_asset_allocation_summary(self) -> Dict[str, Dict[str, float]]:
        """Get structured asset allocation summary"""
        allocation = {
            'by_asset_class': {},
            'by_geography': self.geographic_exposure.copy(),
            'by_asset': self.target_weights.copy()
        }
        
        # Categorize assets by class
        asset_class_mapping = {
            'SP500': 'equity', 'NASDAQ100': 'equity', 'CSI300': 'equity', 'CSI500': 'equity',
            'HSI': 'equity', 'HSTECH': 'equity', 'VEA': 'equity', 'VWO': 'equity',
            'TLT': 'bonds', 'IEF': 'bonds', 'SHY': 'bonds', 'TIP': 'bonds',
            'GLD': 'commodities', 'DBC': 'commodities',
            'VNQ': 'real_estate',
            'CASH': 'cash'
        }
        
        for asset, weight in self.target_weights.items():
            asset_class = asset_class_mapping.get(asset, 'other')
            allocation['by_asset_class'][asset_class] = allocation['by_asset_class'].get(asset_class, 0) + weight
        
        return allocation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'strategy_id': self.strategy_id,
            'category': self.category,
            'description': self.description,
            'target_weights': self.target_weights,
            'rebalancing_frequency': self.rebalancing_frequency,
            'risk_level': self.risk_level,
            'primary_factors': self.primary_factors,
            'asset_classes': self.asset_classes,
            'geographic_exposure': self.geographic_exposure,
            'parameters': self.parameters,
            'benchmark': self.benchmark,
            'expected_volatility': self.expected_volatility,
            'max_drawdown_target': self.max_drawdown_target,
            'minimum_capital': self.minimum_capital,
            'trading_costs': self.trading_costs,
            'author': self.author,
            'version': self.version,
            'created_date': self.created_date.isoformat(),
            'last_modified': self.last_modified.isoformat(),
            'performance_metrics': self.performance_metrics
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyMetadata':
        """Create from dictionary"""
        # Handle datetime conversion
        if isinstance(data.get('created_date'), str):
            data['created_date'] = datetime.fromisoformat(data['created_date'])
        if isinstance(data.get('last_modified'), str):
            data['last_modified'] = datetime.fromisoformat(data['last_modified'])
        
        return cls(**data)

class StrategyLibrary:
    """Central library for strategy metadata and documentation"""
    
    def __init__(self):
        self.strategies: Dict[str, StrategyMetadata] = {}
    
    def register(self, metadata: StrategyMetadata) -> None:
        """Register strategy metadata"""
        self.strategies[metadata.strategy_id] = metadata
    
    def get_strategy(self, strategy_id: str) -> Optional[StrategyMetadata]:
        """Get strategy metadata by ID"""
        return self.strategies.get(strategy_id)
    
    def list_strategies(self, category: Optional[str] = None) -> List[StrategyMetadata]:
        """List all strategies, optionally filtered by category"""
        strategies = list(self.strategies.values())
        if category:
            strategies = [s for s in strategies if s.category == category]
        return sorted(strategies, key=lambda x: x.name)
    
    def search_strategies(self, 
                         risk_level: Optional[str] = None,
                         asset_class: Optional[str] = None,
                         min_return: Optional[float] = None,
                         max_volatility: Optional[float] = None) -> List[StrategyMetadata]:
        """Search strategies by criteria"""
        results = []
        
        for strategy in self.strategies.values():
            # Filter by risk level
            if risk_level and strategy.risk_level != risk_level:
                continue
            
            # Filter by asset class
            if asset_class:
                allocation = strategy.get_asset_allocation_summary()
                if asset_class not in allocation['by_asset_class'] or allocation['by_asset_class'][asset_class] == 0:
                    continue
            
            # Filter by performance criteria
            if min_return and strategy.performance_metrics.get('annual_return', 0) < min_return:
                continue
            
            if max_volatility and strategy.performance_metrics.get('volatility', 1) > max_volatility:
                continue
            
            results.append(strategy)
        
        return sorted(results, key=lambda x: x.performance_metrics.get('sharpe_ratio', 0), reverse=True)
    
    def generate_comparison_table(self, strategy_ids: List[str]) -> pd.DataFrame:
        """Generate comparison table for multiple strategies"""
        data = []
        
        for strategy_id in strategy_ids:
            if strategy_id not in self.strategies:
                continue
            
            strategy = self.strategies[strategy_id]
            data.append({
                'Strategy': strategy.name,
                'Category': strategy.category,
                'Risk Level': strategy.risk_level,
                'Annual Return': strategy.performance_metrics.get('annual_return', 'N/A'),
                'Volatility': strategy.performance_metrics.get('volatility', 'N/A'),
                'Sharpe Ratio': strategy.performance_metrics.get('sharpe_ratio', 'N/A'),
                'Max Drawdown': strategy.performance_metrics.get('max_drawdown', 'N/A'),
                'Risk Score': strategy.get_risk_score()
            })
        
        return pd.DataFrame(data)

# Global strategy library instance
strategy_library = StrategyLibrary()