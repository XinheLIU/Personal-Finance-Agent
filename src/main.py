#!/usr/bin/env python3
"""
Quant Investment System - Main Entry Point
Professional quantitative investment management platform with modular architecture.

This system follows industry-standard architecture patterns with separate modules for:
- Data Center: Market data management and processing
- Strategy Module: Investment strategy repository
- Backtesting Platform: Historical testing and optimization
- Performance Analysis: Metrics and reporting
- Management Module: System coordination and orchestration
- Trading Module: Order execution (simulation/paper/live)
"""

import argparse
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.app_logger import LOG
from src.management.coordinator import system_coordinator
from src.strategies.registry import StrategyRegistry

def main():
    """
    Main entry point for the Quant Investment System
    
    Supports multiple operation modes:
    - GUI: Interactive web interface (default)
    - CLI: Command-line interface
    - System: System management and health checks
    """
    parser = argparse.ArgumentParser(
        description='Quant Investment System - Professional Portfolio Management Platform',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Launch GUI interface
  %(prog)s --mode cli                # Launch CLI interface  
  %(prog)s --mode system --status    # System health check
  %(prog)s --strategy MyStrategy     # Run specific strategy
  %(prog)s --list-strategies         # List all strategies
  %(prog)s --download-data           # Download market data
        """
    )
    
    # Mode selection
    parser.add_argument('--mode', type=str, default='gui', 
                       choices=['gui', 'cli', 'system'], 
                       help='Operation mode (default: gui)')
    
    # Strategy operations
    parser.add_argument('--strategy', type=str, 
                       help='Strategy to run (CLI mode)')
    parser.add_argument('--list-strategies', action='store_true', 
                       help='List available strategies')
    parser.add_argument('--strategy-details', type=str,
                       help='Show detailed strategy information')
    
    # Data operations  
    parser.add_argument('--download-data', action='store_true',
                       help='Download/update market data')
    parser.add_argument('--refresh-data', action='store_true',
                       help='Force refresh of all data files')
    
    # System operations
    parser.add_argument('--status', action='store_true',
                       help='Show system status and health check')
    parser.add_argument('--startup', action='store_true',
                       help='Initialize system startup sequence')
    parser.add_argument('--shutdown', action='store_true',
                       help='Perform graceful system shutdown')
    
    # Development and debugging
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    parser.add_argument('--validate', action='store_true',
                       help='Validate system configuration')
    
    args = parser.parse_args()
    
    # Configure debug logging if requested
    if args.debug:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
        LOG.info("Debug logging enabled")
    
    # Handle system operations first
    if args.mode == 'system':
        handle_system_operations(args)
        return
    
    # Handle data operations
    if args.download_data or args.refresh_data:
        handle_data_operations(args)
        return
    
    # Handle strategy operations
    if args.list_strategies or args.strategy_details:
        handle_strategy_operations(args)
        return
    
    # Handle validation
    if args.validate:
        validate_system_configuration()
        return
    
    # System startup if requested
    if args.startup or args.mode in ['gui', 'cli']:
        LOG.info("Initializing Quant Investment System...")
        if not system_coordinator.startup_system():
            LOG.error("System startup failed")
            sys.exit(1)
    
    # Launch requested interface
    if args.mode == 'cli':
        launch_cli_interface(args)
    elif args.mode == 'gui':
        launch_gui_interface()
    
    # Graceful shutdown
    if args.shutdown:
        system_coordinator.shutdown_system()

def handle_system_operations(args):
    """Handle system management operations"""
    if args.status:
        print_system_status()
    elif args.startup:
        if system_coordinator.startup_system():
            print("✓ System startup successful")
        else:
            print("✗ System startup failed")
            sys.exit(1)
    elif args.shutdown:
        if system_coordinator.shutdown_system():
            print("✓ System shutdown successful")
        else:
            print("✗ System shutdown failed")
    else:
        print("System mode requires --status, --startup, or --shutdown")

def handle_data_operations(args):
    """Handle data download and refresh operations"""
    try:
        from src.data_center.download import main as download_main
        download_main(refresh=args.refresh_data)
        print("✓ Data operations completed")
    except Exception as e:
        LOG.error(f"Data operations failed: {e}")
        print(f"✗ Data operations failed: {e}")

def handle_strategy_operations(args):
    """Handle strategy listing and details"""
    try:
        strategy_registry = StrategyRegistry()
        
        if args.list_strategies:
            strategies = strategy_registry.list_strategies()
            print("\n📊 Available Investment Strategies:")
            print("=" * 60)
            for name, info in strategies.items():
                print(f"• {name}")
                if 'description' in info:
                    print(f"  Description: {info['description']}")
                if 'category' in info:
                    print(f"  Category: {info['category']}")
                print()
        
        if args.strategy_details:
            strategy_info = strategy_registry.get_strategy_details(args.strategy_details)
            if strategy_info:
                print(f"\n📈 Strategy Details: {args.strategy_details}")
                print("=" * 50)
                for key, value in strategy_info.items():
                    print(f"{key.title()}: {value}")
            else:
                print(f"Strategy '{args.strategy_details}' not found")
                
    except Exception as e:
        LOG.error(f"Strategy operations failed: {e}")
        print(f"✗ Strategy operations failed: {e}")

def validate_system_configuration():
    """Validate system configuration"""
    print("🔍 Validating System Configuration...")
    
    # Check data directories
    required_dirs = ['data/raw', 'data/processed', 'config', 'modules']
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✓ {dir_path} directory exists")
        else:
            print(f"✗ {dir_path} directory missing")
    
    # Check configuration files
    config_files = ['config/assets.py', 'config/system.py']
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✓ {config_file} configuration file exists")
        else:
            print(f"✗ {config_file} configuration file missing")
    
    # Test core imports
    try:
        from config.assets import TRADABLE_ASSETS
        from src.data_center.data_loader import DataLoader
        print(f"✓ Core modules import successfully")
        print(f"✓ Found {len(TRADABLE_ASSETS)} tradable assets configured")
    except Exception as e:
        print(f"✗ Core module import failed: {e}")

def print_system_status():
    """Print comprehensive system status"""
    print("\n🖥️  Quant Investment System Status")
    print("=" * 50)
    
    # System coordinator status
    health = system_coordinator.system_health_check()
    
    print(f"System State: {system_coordinator.state.value}")
    print(f"Overall Health: {'✓ Healthy' if health['overall_healthy'] else '✗ Issues Detected'}")
    print(f"Last Health Check: {health['timestamp']}")
    
    if health['issues']:
        print("\n⚠️  Issues Detected:")
        for issue in health['issues']:
            print(f"  • {issue}")
    
    # Module status
    print("\n📊 Module Status:")
    for module_name, module_health in health.get('modules', {}).items():
        status = "✓" if module_health.get('healthy', True) else "✗"
        print(f"  {status} {module_name.replace('_', ' ').title()}")
    
    # Strategy status
    strategies = system_coordinator.list_strategies()
    print(f"\n🎯 Strategies: {len(strategies)} registered")
    
    for name, info in strategies.items():
        status_icon = {"completed": "✓", "error": "✗", "stopped": "⏸", "running": "▶"}.get(info['status'], "?")
        print(f"  {status_icon} {name} ({info['status']})")

def launch_cli_interface(args):
    """Launch CLI interface"""
    if args.strategy:
        # Run specific strategy
        run_single_strategy(args.strategy)
    else:
        # Launch interactive CLI
        LOG.info("Launching CLI interface...")
        try:
            from src.cli import main as cli_main
            cli_main()
        except Exception as e:
            LOG.error(f"CLI launch failed: {e}")
            print(f"✗ CLI launch failed: {e}")

def launch_gui_interface():
    """Launch GUI interface"""
    LOG.info("Launching Quant Investment System GUI...")
    try:
        from src.gui import demo
        print("🌐 Starting web interface...")
        demo.launch()
    except ImportError as e:
        LOG.error(f"GUI dependencies not available: {e}")
        print("✗ GUI launch failed: Missing dependencies")
        print("Install with: pip install gradio")
        sys.exit(1)
    except Exception as e:
        LOG.error(f"GUI launch failed: {e}")
        print(f"✗ GUI launch failed: {e}")
        sys.exit(1)

def run_single_strategy(strategy_name):
    """Run a single strategy backtest"""
    try:
        from src.backtesting.engine import backtest_engine
        
        # This would need to be adapted to work with the strategy registry
        # For now, placeholder implementation
        LOG.info(f"Running strategy: {strategy_name}")
        print(f"🚀 Running strategy: {strategy_name}")
        print("Strategy execution with new architecture - implementation pending")
        
    except Exception as e:
        LOG.error(f"Strategy execution failed: {e}")
        print(f"✗ Strategy execution failed: {e}")

if __name__ == '__main__':
    main()