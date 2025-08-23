#!/usr/bin/env python3
"""
Command-line interface for Personal Finance Agent.
Allows running strategies and backtests without GUI.
"""
import argparse
import sys
from typing import Dict, Any, Optional

from src.app_logger import LOG
from src.strategies.registry import strategy_registry
from src.backtesting.runner import run_backtest
from src.data_center.download import main as download_data
from src.strategies.classic import get_target_weights_and_metrics_standalone

# Import accounting module
from src.accounting import (
    load_transactions_csv, 
    generate_monthly_income_statement,
    generate_ytd_income_statement,
    print_income_statement,
    save_income_statement_csv
)
import os
from datetime import datetime

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

def run_attribution_analysis(strategy_name: str, 
                            period: str = 'daily',
                            export_path: Optional[str] = None,
                            **strategy_params):
    """Run performance attribution analysis for a strategy"""
    print(f"\n🔍 Running attribution analysis for {strategy_name}")
    print(f"Attribution period: {period}")
    
    # Get strategy class
    strategies = strategy_registry.list_strategies()
    if strategy_name not in strategies:
        print(f"❌ Strategy '{strategy_name}' not found")
        print(f"Available strategies: {', '.join(strategies.keys())}")
        return False
    
    strategy_class = strategies[strategy_name]
    
    try:
        # Run backtest with attribution enabled
        print("🚀 Running backtest with attribution analysis...")
        results = run_backtest(
            strategy_class,
            strategy_name,
            enable_attribution=True,
            **strategy_params
        )
        
        if not results or 'error' in results:
            error_msg = results.get('error', 'Unknown error') if results else 'No results returned'
            print(f"❌ Backtest failed: {error_msg}")
            return False
        
        # Check for attribution data
        if 'attribution_analysis' not in results:
            if 'attribution_error' in results:
                print(f"❌ Attribution analysis failed: {results['attribution_error']}")
            else:
                print("❌ No attribution analysis data generated")
            return False
        
        attribution_data = results['attribution_analysis']
        
        # Display results based on selected period
        period_key = f"{period.lower()}_analysis"
        if period_key not in attribution_data:
            print(f"❌ No {period} attribution data available")
            available_periods = [k.replace('_analysis', '') for k in attribution_data.keys() if k.endswith('_analysis')]
            print(f"Available periods: {', '.join(available_periods)}")
            return False
        
        period_data = attribution_data[period_key]
        
        # Display summary
        print(f"\n📊 {period.title()} Attribution Analysis Summary")
        print("=" * 50)
        
        summary_stats = period_data.get('summary_statistics', {})
        print(f"Total Portfolio Return: {summary_stats.get('total_portfolio_return', 0):.2%}")
        print(f"Total Asset Contribution: {summary_stats.get('total_asset_contribution', 0):.2%}")
        print(f"Total Rebalancing Impact: {summary_stats.get('total_rebalancing_impact', 0):.2%}")
        print(f"Attribution Accuracy: {summary_stats.get('attribution_accuracy', 0):.4%}")
        
        # Display top contributors
        print(f"\n🏆 Top Contributors ({period.title()})")
        print("-" * 30)
        top_contributors = period_data.get('top_contributors', {})
        
        for i, (asset, data) in enumerate(list(top_contributors.items())[:5], 1):
            net_impact = data.get('net_impact', 0)
            asset_contrib = data.get('total_contribution', 0)
            rebal_impact = data.get('total_rebalancing_impact', 0)
            
            print(f"{i}. {asset}:")
            print(f"   Net Impact: {net_impact:.3%}")
            print(f"   Asset Contribution: {asset_contrib:.3%}")
            print(f"   Rebalancing Impact: {rebal_impact:.3%}")
        
        # Export data if path provided
        if export_path:
            try:
                from src.performance.attribution import PerformanceAttributor
                attributor = PerformanceAttributor()
                
                # Save attribution data
                daily_attributions = []  # Would need to reconstruct from data
                saved_files = attributor.save_attribution_data(
                    strategy_name, {period: daily_attributions}
                )
                
                if saved_files:
                    print(f"\n💾 Attribution data exported:")
                    for file_type, file_path in saved_files.items():
                        print(f"   {file_type}: {file_path}")
                else:
                    print("⚠️  Failed to export attribution data")
                    
            except Exception as e:
                print(f"⚠️  Export failed: {e}")
        
        print(f"\n✅ Attribution analysis completed for {strategy_name}")
        return True
        
    except Exception as e:
        print(f"❌ Attribution analysis failed: {e}")
        LOG.error(f"Attribution analysis error: {e}")
        return False


def generate_income_statement_cli(period: str, export_csv: bool = False) -> bool:
    """Generate income statement for specified period"""
    try:
        # Load transactions from data/accounting/transactions.csv
        transactions_file = "data/accounting/transactions.csv"
        
        if not os.path.exists(transactions_file):
            print(f"❌ Transaction file not found: {transactions_file}")
            print("Please create the file with transaction data first.")
            return False
        
        # Load transactions
        transactions, errors = load_transactions_csv(transactions_file)
        
        if errors:
            print(f"❌ Errors loading transactions:")
            for error in errors:
                print(f"   {error}")
            return False
        
        if not transactions:
            print("❌ No transactions found in file")
            return False
        
        print(f"✅ Loaded {len(transactions)} transactions")
        
        # Parse period (YYYY-MM format)
        try:
            if period.upper() == "YTD":
                year = datetime.now().year
                statement = generate_ytd_income_statement(transactions, year)
                period_desc = f"YTD {year}"
            else:
                parts = period.split("-")
                if len(parts) != 2:
                    raise ValueError("Period must be in YYYY-MM format or 'YTD'")
                year = int(parts[0])
                month = int(parts[1])
                statement = generate_monthly_income_statement(transactions, month, year)
                period_desc = f"{year}-{month:02d}"
        except ValueError as e:
            print(f"❌ Invalid period format: {e}")
            print("Use YYYY-MM format (e.g., 2025-01) or 'YTD'")
            return False
        
        # Display income statement
        print_income_statement(statement)
        
        # Export to CSV if requested
        if export_csv:
            output_dir = "data/accounting/statements"
            os.makedirs(output_dir, exist_ok=True)
            
            if period.upper() == "YTD":
                output_file = f"{output_dir}/income_statement_YTD_{year}.csv"
            else:
                output_file = f"{output_dir}/income_statement_{period}.csv"
            
            errors = save_income_statement_csv(statement, output_file)
            if errors:
                print(f"❌ Errors saving CSV:")
                for error in errors:
                    print(f"   {error}")
            else:
                print(f"✅ Income statement saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating income statement: {e}")
        LOG.error(f"Income statement generation failed: {e}")
        return False


def accounting_status() -> bool:
    """Show accounting data status"""
    try:
        transactions_file = "data/accounting/transactions.csv"
        assets_file = "data/accounting/assets.csv"
        statements_dir = "data/accounting/statements"
        
        print("\n📊 Accounting Module Status")
        print("=" * 40)
        
        # Check transactions file
        if os.path.exists(transactions_file):
            transactions, errors = load_transactions_csv(transactions_file)
            if errors:
                print(f"❌ Transactions file has errors: {len(errors)}")
                for error in errors[:3]:  # Show first 3 errors
                    print(f"   {error}")
                if len(errors) > 3:
                    print(f"   ... and {len(errors) - 3} more errors")
            else:
                print(f"✅ Transactions: {len(transactions)} records")
                
                # Show date range
                if transactions:
                    dates = [t.date for t in transactions]
                    min_date = min(dates).strftime("%Y-%m-%d")
                    max_date = max(dates).strftime("%Y-%m-%d")
                    print(f"   Date range: {min_date} to {max_date}")
                    
                    # Show categories
                    categories = set(t.category for t in transactions)
                    print(f"   Categories: {len(categories)} unique")
        else:
            print(f"❌ Transactions file not found: {transactions_file}")
            print("   Create this file to start using accounting features")
        
        # Check assets file (optional)
        if os.path.exists(assets_file):
            print(f"✅ Assets file found: {assets_file}")
        else:
            print(f"ℹ️  Assets file not found: {assets_file} (optional)")
        
        # Check statements directory
        if os.path.exists(statements_dir):
            statements = [f for f in os.listdir(statements_dir) if f.endswith('.csv')]
            if statements:
                print(f"✅ Generated statements: {len(statements)}")
                for stmt in sorted(statements)[-3:]:  # Show last 3 statements
                    print(f"   {stmt}")
                if len(statements) > 3:
                    print(f"   ... and {len(statements) - 3} more")
            else:
                print(f"ℹ️  No statements generated yet in: {statements_dir}")
        else:
            print(f"ℹ️  Statements directory will be created when needed: {statements_dir}")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Error checking accounting status: {e}")
        LOG.error(f"Accounting status check failed: {e}")
        return False


def export_attribution_data(strategy_name: str, output_dir: str = "analytics/attribution"):
    """Export attribution data for a strategy to CSV/Excel files"""
    print(f"\n📤 Exporting attribution data for {strategy_name}")
    
    try:
        from pathlib import Path
        
        # Check if attribution data exists
        attribution_dir = Path(output_dir)
        if not attribution_dir.exists():
            print(f"❌ Attribution directory not found: {attribution_dir}")
            return False
        
        # Find attribution files for the strategy
        strategy_safe = strategy_name.replace('/', '_').replace(' ', '_').lower()
        attribution_files = list(attribution_dir.glob(f"{strategy_safe}*attribution*.csv"))
        excel_files = list(attribution_dir.glob(f"{strategy_safe}*attribution*.xlsx"))
        
        if not attribution_files and not excel_files:
            print(f"❌ No attribution files found for {strategy_name}")
            print(f"Run attribution analysis first: cli.py attribution {strategy_name}")
            return False
        
        print(f"📄 Found attribution files:")
        for file_path in sorted(attribution_files + excel_files):
            print(f"   {file_path}")
        
        print(f"\n✅ Attribution data available at: {attribution_dir}")
        return True
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return False

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
    
    # Attribution analysis
    attribution_parser = subparsers.add_parser('attribution', help='Run performance attribution analysis')
    attribution_parser.add_argument('strategy', help='Name of strategy to analyze')
    attribution_parser.add_argument('--period', choices=['daily', 'weekly', 'monthly'], 
                                   default='daily', help='Attribution period (default: daily)')
    attribution_parser.add_argument('--export', help='Export attribution data to specified path')
    attribution_parser.add_argument('--rebalance-days', type=int, default=30,
                                   help='Days between rebalancing (default: 30)')
    attribution_parser.add_argument('--threshold', type=float, default=0.05,
                                   help='Rebalancing threshold (default: 0.05)')
    
    # Export attribution data
    export_parser = subparsers.add_parser('export-attribution', help='Export existing attribution data')
    export_parser.add_argument('strategy', help='Name of strategy to export')
    export_parser.add_argument('--output-dir', default='analytics/attribution',
                              help='Output directory for exported files')
    
    # Download data
    download_parser = subparsers.add_parser('download', help='Download market data')
    download_parser.add_argument('--refresh', action='store_true',
                               help='Refresh existing data files')
    
    # Show weights
    weights_parser = subparsers.add_parser('weights', help='Show current target weights')
    
    # Accounting commands
    accounting_status_parser = subparsers.add_parser('accounting-status', help='Show accounting data status')
    
    generate_statement_parser = subparsers.add_parser('generate-income-statement', help='Generate income statement')
    generate_statement_parser.add_argument('period', help='Period in YYYY-MM format or "YTD"')
    generate_statement_parser.add_argument('--export-csv', action='store_true',
                                          help='Export statement to CSV file')
    
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
        
        elif args.command == 'attribution':
            # Set strategy parameters if provided
            strategy_params = {}
            if hasattr(args, 'rebalance_days'):
                strategy_params['rebalance_days'] = args.rebalance_days
            if hasattr(args, 'threshold'):
                strategy_params['threshold'] = args.threshold
            
            run_attribution_analysis(
                args.strategy, 
                period=args.period,
                export_path=getattr(args, 'export', None),
                **strategy_params
            )
        
        elif args.command == 'export-attribution':
            export_attribution_data(
                args.strategy,
                output_dir=args.output_dir
            )
        
        elif args.command == 'download':
            download_data(refresh=getattr(args, 'refresh', False))
        
        elif args.command == 'weights':
            show_portfolio_weights()
        
        elif args.command == 'accounting-status':
            accounting_status()
        
        elif args.command == 'generate-income-statement':
            generate_income_statement_cli(args.period, export_csv=args.export_csv)
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        LOG.error(f"CLI error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()