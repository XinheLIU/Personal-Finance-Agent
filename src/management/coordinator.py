"""
System Coordinator
Central orchestration of the entire quant investment system.
Manages strategy lifecycle, system health, and module communication.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import asyncio
from enum import Enum

from src.app_logger import LOG
from config.system import INITIAL_CAPITAL, COMMISSION
from src.data_center.data_loader import DataLoader
from src.backtesting.engine import EnhancedBacktestEngine
from src.performance.analytics import PerformanceAnalyzer

class SystemState(Enum):
    """System operational states"""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    SHUTDOWN = "shutdown"

class SystemCoordinator:
    """
    Central system coordinator for quant investment platform
    """
    
    def __init__(self, config_dir: str = "config", data_dir: str = "data"):
        self.config_dir = Path(config_dir)
        self.data_dir = Path(data_dir)
        self.state = SystemState.INITIALIZING
        
        # Initialize core modules
        self.data_loader = DataLoader(data_dir)
        self.backtest_engine = EnhancedBacktestEngine(data_root=data_dir)
        self.performance_analyzer = PerformanceAnalyzer()
        
        # System tracking
        self.active_strategies: Dict[str, Dict] = {}
        self.system_metrics: Dict[str, Any] = {}
        self.last_health_check = None
        
        # Logs and analytics
        self.system_log: List[Dict] = []
        self.performance_history: List[Dict] = []
        
        LOG.info("System Coordinator initialized")
    
    def startup_system(self) -> bool:
        """
        Complete system startup sequence
        
        Returns:
            True if startup successful, False otherwise
        """
        try:
            LOG.info("Starting up quant investment system...")
            self.state = SystemState.INITIALIZING
            
            # 1. Check data availability
            if not self._check_data_availability():
                LOG.error("Data availability check failed")
                self.state = SystemState.ERROR
                return False
            
            # 2. Validate system configuration
            if not self._validate_configuration():
                LOG.error("Configuration validation failed")
                self.state = SystemState.ERROR
                return False
            
            # 3. Initialize modules
            if not self._initialize_modules():
                LOG.error("Module initialization failed")
                self.state = SystemState.ERROR
                return False
            
            # 4. Perform health check
            health_status = self.system_health_check()
            if not health_status['overall_healthy']:
                LOG.warning("System health check revealed issues")
            
            self.state = SystemState.READY
            self._log_system_event("system_startup", {"status": "success"})
            LOG.info("System startup completed successfully")
            
            return True
            
        except Exception as e:
            LOG.error(f"System startup failed: {e}")
            self.state = SystemState.ERROR
            self._log_system_event("system_startup", {"status": "error", "error": str(e)})
            return False
    
    def shutdown_system(self) -> bool:
        """
        Graceful system shutdown
        
        Returns:
            True if shutdown successful
        """
        try:
            LOG.info("Initiating system shutdown...")
            self.state = SystemState.SHUTDOWN
            
            # Stop all active strategies
            for strategy_name in list(self.active_strategies.keys()):
                self.stop_strategy(strategy_name)
            
            # Save system state
            self._save_system_state()
            
            self._log_system_event("system_shutdown", {"status": "success"})
            LOG.info("System shutdown completed")
            
            return True
            
        except Exception as e:
            LOG.error(f"System shutdown error: {e}")
            return False
    
    def register_strategy(self, 
                         strategy_class: Any,
                         strategy_name: str,
                         parameters: Dict[str, Any],
                         auto_start: bool = False) -> bool:
        """
        Register a new strategy with the system
        
        Args:
            strategy_class: Strategy class
            strategy_name: Unique strategy name
            parameters: Strategy parameters
            auto_start: Whether to auto-start the strategy
            
        Returns:
            True if registration successful
        """
        try:
            if strategy_name in self.active_strategies:
                LOG.warning(f"Strategy {strategy_name} already registered")
                return False
            
            strategy_info = {
                'class': strategy_class,
                'parameters': parameters,
                'status': 'registered',
                'registration_time': datetime.now(),
                'last_run': None,
                'performance_metrics': {},
                'error_count': 0
            }
            
            self.active_strategies[strategy_name] = strategy_info
            
            if auto_start:
                self.start_strategy(strategy_name)
            
            self._log_system_event("strategy_registered", {
                "strategy_name": strategy_name,
                "auto_start": auto_start
            })
            
            LOG.info(f"Strategy registered: {strategy_name}")
            return True
            
        except Exception as e:
            LOG.error(f"Strategy registration failed for {strategy_name}: {e}")
            return False
    
    def start_strategy(self, strategy_name: str) -> bool:
        """
        Start a registered strategy
        
        Args:
            strategy_name: Name of strategy to start
            
        Returns:
            True if start successful
        """
        try:
            if strategy_name not in self.active_strategies:
                LOG.error(f"Strategy {strategy_name} not registered")
                return False
            
            strategy_info = self.active_strategies[strategy_name]
            
            if strategy_info['status'] == 'running':
                LOG.warning(f"Strategy {strategy_name} already running")
                return True
            
            # Run backtest for the strategy
            results = self.backtest_engine.run_backtest(
                strategy_info['class'],
                strategy_name,
                **strategy_info['parameters']
            )
            
            if 'error' not in results:
                strategy_info['status'] = 'completed'
                strategy_info['last_run'] = datetime.now()
                strategy_info['performance_metrics'] = results
                
                self._log_system_event("strategy_started", {
                    "strategy_name": strategy_name,
                    "performance": {
                        "total_return": results.get('total_return', 0),
                        "sharpe_ratio": results.get('sharpe_ratio', 0)
                    }
                })
                
                LOG.info(f"Strategy {strategy_name} completed successfully")
                return True
            else:
                strategy_info['status'] = 'error'
                strategy_info['error_count'] += 1
                
                LOG.error(f"Strategy {strategy_name} failed: {results['error']}")
                return False
                
        except Exception as e:
            LOG.error(f"Failed to start strategy {strategy_name}: {e}")
            if strategy_name in self.active_strategies:
                self.active_strategies[strategy_name]['status'] = 'error'
                self.active_strategies[strategy_name]['error_count'] += 1
            return False
    
    def stop_strategy(self, strategy_name: str) -> bool:
        """
        Stop a running strategy
        
        Args:
            strategy_name: Name of strategy to stop
            
        Returns:
            True if stop successful
        """
        try:
            if strategy_name not in self.active_strategies:
                LOG.error(f"Strategy {strategy_name} not found")
                return False
            
            strategy_info = self.active_strategies[strategy_name]
            strategy_info['status'] = 'stopped'
            
            self._log_system_event("strategy_stopped", {"strategy_name": strategy_name})
            LOG.info(f"Strategy {strategy_name} stopped")
            
            return True
            
        except Exception as e:
            LOG.error(f"Failed to stop strategy {strategy_name}: {e}")
            return False
    
    def get_strategy_status(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific strategy"""
        return self.active_strategies.get(strategy_name)
    
    def list_strategies(self) -> Dict[str, Dict[str, Any]]:
        """List all registered strategies"""
        return {
            name: {
                'status': info['status'],
                'last_run': info['last_run'],
                'error_count': info['error_count'],
                'performance': info.get('performance_metrics', {})
            }
            for name, info in self.active_strategies.items()
        }
    
    def system_health_check(self) -> Dict[str, Any]:
        """
        Comprehensive system health check
        
        Returns:
            Health status dictionary
        """
        health_status = {
            'timestamp': datetime.now(),
            'overall_healthy': True,
            'issues': [],
            'modules': {}
        }
        
        try:
            # Check data availability
            market_data = self.data_loader.load_market_data()
            data_health = {
                'assets_loaded': len([k for k, v in market_data.items() if not v.empty]),
                'total_assets': len(market_data),
                'latest_data': max([v.index.max() if not v.empty else pd.Timestamp.min 
                                  for v in market_data.values()]),
                'healthy': len([k for k, v in market_data.items() if not v.empty]) > 0
            }
            health_status['modules']['data_center'] = data_health
            
            if not data_health['healthy']:
                health_status['overall_healthy'] = False
                health_status['issues'].append("No market data available")
            
            # Check system resources
            resource_health = {
                'active_strategies': len(self.active_strategies),
                'error_strategies': len([s for s in self.active_strategies.values() 
                                       if s['status'] == 'error']),
                'healthy': True
            }
            
            if resource_health['error_strategies'] > 0:
                health_status['issues'].append(f"{resource_health['error_strategies']} strategies in error state")
            
            health_status['modules']['system_resources'] = resource_health
            
            # Check disk space (simplified)
            try:
                analytics_dir = Path("analytics")
                if analytics_dir.exists():
                    file_count = len(list(analytics_dir.glob("**/*")))
                    disk_health = {'analytics_files': file_count, 'healthy': file_count < 10000}
                    health_status['modules']['disk_space'] = disk_health
            except:
                health_status['issues'].append("Could not check disk space")
            
            self.last_health_check = health_status['timestamp']
            
        except Exception as e:
            health_status['overall_healthy'] = False
            health_status['issues'].append(f"Health check error: {e}")
            LOG.error(f"System health check failed: {e}")
        
        return health_status
    
    def generate_system_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive system status report
        
        Returns:
            System report dictionary
        """
        report = {
            'report_timestamp': datetime.now(),
            'system_state': self.state.value,
            'uptime': (datetime.now() - self.system_metrics.get('startup_time', datetime.now())),
            'health_status': self.system_health_check(),
            'strategies': self.list_strategies(),
            'recent_events': self.system_log[-10:],  # Last 10 events
            'performance_summary': self._generate_performance_summary()
        }
        
        return report
    
    def _check_data_availability(self) -> bool:
        """Check if required data is available"""
        try:
            market_data = self.data_loader.load_market_data()
            pe_data = self.data_loader.load_pe_data()
            
            assets_with_data = [k for k, v in market_data.items() if not v.empty]
            pe_assets_with_data = [k for k, v in pe_data.items() if not v.empty]
            
            LOG.info(f"Data check: {len(assets_with_data)} assets, {len(pe_assets_with_data)} PE datasets")
            
            return len(assets_with_data) > 0
            
        except Exception as e:
            LOG.error(f"Data availability check failed: {e}")
            return False
    
    def _validate_configuration(self) -> bool:
        """Validate system configuration"""
        try:
            # Check if config files exist
            if not (self.config_dir / "assets.py").exists():
                LOG.error("Assets configuration file not found")
                return False
            
            # Validate key parameters
            if INITIAL_CAPITAL <= 0:
                LOG.error("Invalid initial capital configuration")
                return False
            
            if COMMISSION < 0:
                LOG.error("Invalid commission configuration")
                return False
            
            return True
            
        except Exception as e:
            LOG.error(f"Configuration validation failed: {e}")
            return False
    
    def _initialize_modules(self) -> bool:
        """Initialize all system modules"""
        try:
            # Data center already initialized
            # Backtest engine already initialized  
            # Performance analyzer already initialized
            
            self.system_metrics['startup_time'] = datetime.now()
            return True
            
        except Exception as e:
            LOG.error(f"Module initialization failed: {e}")
            return False
    
    def _log_system_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log system events"""
        event = {
            'timestamp': datetime.now(),
            'event_type': event_type,
            'details': details
        }
        self.system_log.append(event)
        
        # Keep only recent events
        if len(self.system_log) > 1000:
            self.system_log = self.system_log[-500:]
    
    def _save_system_state(self) -> None:
        """Save current system state"""
        try:
            state_file = self.data_dir / "system_state.json"
            
            state_data = {
                'timestamp': datetime.now().isoformat(),
                'strategies': {
                    name: {
                        'status': info['status'],
                        'last_run': info['last_run'].isoformat() if info['last_run'] else None,
                        'error_count': info['error_count']
                    }
                    for name, info in self.active_strategies.items()
                },
                'system_metrics': self.system_metrics
            }
            
            import json
            with open(state_file, 'w') as f:
                json.dump(state_data, f, indent=2, default=str)
                
        except Exception as e:
            LOG.error(f"Failed to save system state: {e}")
    
    def _generate_performance_summary(self) -> Dict[str, Any]:
        """Generate performance summary across all strategies"""
        if not self.active_strategies:
            return {'total_strategies': 0}
        
        completed_strategies = [
            s for s in self.active_strategies.values() 
            if s['status'] == 'completed' and s['performance_metrics']
        ]
        
        if not completed_strategies:
            return {'total_strategies': len(self.active_strategies), 'completed': 0}
        
        # Calculate aggregate metrics
        returns = [s['performance_metrics'].get('total_return', 0) for s in completed_strategies]
        sharpe_ratios = [s['performance_metrics'].get('sharpe_ratio', 0) for s in completed_strategies]
        
        return {
            'total_strategies': len(self.active_strategies),
            'completed': len(completed_strategies),
            'avg_return': sum(returns) / len(returns) if returns else 0,
            'best_return': max(returns) if returns else 0,
            'worst_return': min(returns) if returns else 0,
            'avg_sharpe': sum(sharpe_ratios) / len(sharpe_ratios) if sharpe_ratios else 0,
            'strategies_profitable': len([r for r in returns if r > 0])
        }

# Global system coordinator instance
system_coordinator = SystemCoordinator()