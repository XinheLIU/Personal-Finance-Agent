#!/usr/bin/env python3
"""
Main entry point for Personal Finance Agent.
Supports both GUI and CLI modes.
"""
import argparse
import sys
from src.app_logger import LOG
from src.strategies.registry import strategy_registry

def main():
    """
    Main entry point that supports both GUI and CLI modes.
    """
    parser = argparse.ArgumentParser(description='Personal Finance Agent')
    parser.add_argument('--mode', type=str, default='gui', 
                       choices=['gui', 'cli'], help='Execution mode')
    parser.add_argument('--strategy', type=str, help='Strategy to run (CLI mode)')
    parser.add_argument('--list-strategies', action='store_true', 
                       help='List available strategies')
    parser.add_argument('--download-data', action='store_true',
                       help='Download market data')
    parser.add_argument('--refresh-data', action='store_true',
                       help='Refresh existing data files')
    
    args = parser.parse_args()
    
    if args.list_strategies:
        strategies = strategy_registry.list_strategies()
        print("\nAvailable Strategies:")
        print("=" * 50)
        for name, description in strategies.items():
            print(f"- {name}: {description}")
        print()
        return
    
    if args.download_data:
        from src.data_download import main as download_main
        download_main(refresh=args.refresh_data)
        return
    
    if args.mode == 'cli':
        if args.strategy:
            # Run specific strategy
            strategy_class = strategy_registry.get(args.strategy)
            if not strategy_class:
                LOG.error(f"Strategy '{args.strategy}' not found")
                print("Use --list-strategies to see available strategies")
                return
            
            from src.backtest_runner import run_backtest
            results = run_backtest(strategy_class, args.strategy)
            
            if results:
                print(f"\nStrategy: {args.strategy}")
                print(f"Final Value: ${results['final_value']:,.2f}")
                print(f"Total Return: {results['total_return']:.2f}%")
                print(f"Annualized Return: {results['annualized_return']:.2f}%")
                print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
                print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        else:
            # Run CLI interface
            from src.cli import main as cli_main
            cli_main()
    
    else:  # GUI mode
        LOG.info("Launching Personal Finance Agent GUI...")
        try:
            from src.gui import demo
            demo.launch()
        except ImportError as e:
            LOG.error(f"Could not import Gradio interface: {e}")
            LOG.error("Please ensure Gradio is installed: pip install gradio")
            sys.exit(1)
        except Exception as e:
            LOG.error(f"Error launching GUI: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()