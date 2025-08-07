#!/usr/bin/env python3
"""
Command-line interface for Personal Finance Agent.
Allows running strategies and backtests without GUI.
"""
import argparse
import sys
from typing import Dict, Any

from src.app_logger import LOG
from src.strategies.registry import strategy_registry
from src.backtest_runner import run_backtest
from src.data_download import main as download_data
from src.strategy import get_target_weights_and_metrics_standalone

def list_strategies():
    """List all available strategies"""
    strategies = strategy_registry.list_strategies()
    print("\nAvailable Strategies:")
    print("=" * 50)
    for name, description in strategies.items():
        print(f"- {name}: {description}")
    print()

def run_strategy(strategy_name: str, **kwargs):
    """Run a specific strategy backtest"""
    strategy_class = strategy_registry.get(strategy_name)
    if not strategy_class:
        LOG.error(f"Strategy '{strategy_name}' not found")
        return None
    
    LOG.info(f"Running strategy: {strategy_name}")
    results = run_backtest(strategy_class, strategy_name)
    
    if results:
        print("\n" + "=" * 50)
        print(f"BACKTEST RESULTS: {strategy_name}")
        print("=" * 50)
        print(f"Final Value: ${results['final_value']:,.2f}")
        print(f"Total Return: {results['total_return']:.2f}%")
        print(f"Annualized Return: {results['annualized_return']:.2f}%")
        print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
        print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        print("=" * 50)
    
    return results

def show_portfolio_weights():
    """Show current target weights for dynamic strategy"""
    try:
        weights, reasoning = get_target_weights_and_metrics_standalone()
        if weights:
            print("\n" + "=" * 50)
            print("CURRENT TARGET WEIGHTS")
            print("=" * 50)
            for asset, weight in weights.items():
                print(f"{asset}: {weight:.2%}")
            print()
            
            print("REASONING:")
            for asset, reason in reasoning.items():
                print(f"{asset}: {reason}")
            print("=" * 50)
        else:
            print("Could not calculate target weights. Ensure data is downloaded.")
    except Exception as e:
        LOG.error(f"Error getting target weights: {e}")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Personal Finance Agent - Command Line Interface")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List strategies
    list_parser = subparsers.add_parser('list', help='List available strategies')
    
    # Run strategy
    run_parser = subparsers.add_parser('run', help='Run a strategy backtest')
    run_parser.add_argument('strategy', help='Name of strategy to run')
    run_parser.add_argument('--rebalance-days', type=int, default=30,
                          help='Days between rebalancing (default: 30)')
    run_parser.add_argument('--threshold', type=float, default=0.05,
                          help='Rebalancing threshold (default: 0.05)')
    
    # Download data
    download_parser = subparsers.add_parser('download', help='Download market data')
    download_parser.add_argument('--refresh', action='store_true',
                               help='Refresh existing data files')
    
    # Show weights
    weights_parser = subparsers.add_parser('weights', help='Show current target weights')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'list':
            list_strategies()
        
        elif args.command == 'run':
            # Set strategy parameters if provided
            strategy_params = {}
            if hasattr(args, 'rebalance_days'):
                strategy_params['rebalance_days'] = args.rebalance_days
            if hasattr(args, 'threshold'):
                strategy_params['threshold'] = args.threshold
            
            run_strategy(args.strategy, **strategy_params)
        
        elif args.command == 'download':
            download_data(refresh=getattr(args, 'refresh', False))
        
        elif args.command == 'weights':
            show_portfolio_weights()
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        LOG.error(f"CLI error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()