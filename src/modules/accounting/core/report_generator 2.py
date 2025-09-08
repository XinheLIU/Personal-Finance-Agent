"""
Main financial report generator class

Orchestrates the generation of income statements and cash flow statements
similar to the example implementation.
"""

import pandas as pd
import os
from typing import Dict, List
from .models import Transaction, CategoryMapper
from .income_statement import IncomeStatementGenerator
from .cash_flow import CashFlowStatementGenerator
from .io import TransactionProcessor


class FinancialReportGenerator:
    """Main class that orchestrates the financial report generation"""
    
    def __init__(self, csv_file_path: str):
        self.processor = TransactionProcessor(csv_file_path)
        self.category_mapper = CategoryMapper()
        self.income_generator = IncomeStatementGenerator(self.category_mapper)
        self.cashflow_generator = CashFlowStatementGenerator(self.category_mapper)
    
    def generate_reports(self, output_dir: str = None) -> None:
        """Generate both income and cash flow statements"""
        
        # Default to same directory as script
        if output_dir is None:
            output_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Load transactions
        self.processor.load_transactions()
        
        # Get all users
        users = self.processor.get_all_users()
        
        # Generate reports for each user and combined
        user_income_data = {}
        user_cashflow_data = {}
        
        # Individual user reports
        for user in users:
            user_transactions = self.processor.get_transactions_by_user(user)
            
            # Income statement
            income_stmt = self.income_generator.generate_statement(user_transactions, f"User: {user}")
            user_income_data[user] = self._flatten_income_statement(income_stmt)
            
            # Cash flow statement  
            cashflow_stmt = self.cashflow_generator.generate_statement(user_transactions, f"User: {user}")
            user_cashflow_data[user] = self._flatten_cashflow_statement(cashflow_stmt)
        
        # Combined report
        all_transactions = self.processor.transactions
        combined_income = self.income_generator.generate_statement(all_transactions, "Combined")
        combined_cashflow = self.cashflow_generator.generate_statement(all_transactions, "Combined")
        
        user_income_data["Combined"] = self._flatten_income_statement(combined_income)
        user_cashflow_data["Combined"] = self._flatten_cashflow_statement(combined_cashflow)
        
        # Transpose the data (users as columns)
        transposed_income = self._transpose_user_data(user_income_data)
        transposed_cashflow = self._transpose_user_data(user_cashflow_data)
        
        # Save to CSV files
        income_file = os.path.join(output_dir, "income_statements.csv")
        cashflow_file = os.path.join(output_dir, "cashflow_statements.csv")
        
        self._save_transposed_data(transposed_income, income_file)
        self._save_transposed_data(transposed_cashflow, cashflow_file)
        
        print(f"Reports generated successfully!")
        print(f"- Income statements saved to: {income_file}")
        print(f"- Cash flow statements saved to: {cashflow_file}")
    
    def _flatten_income_statement(self, stmt: Dict) -> Dict:
        """Flatten income statement for CSV export"""
        flattened = {
            'Entity': stmt['Entity'],
            'Total_Revenue': stmt['Total Revenue'],
            'Total_Expenses': stmt['Total Expenses'],
            'Net_Income': stmt['Net Income']
        }
        
        # Add revenue categories
        for category, amount in stmt['Revenue'].items():
            flattened[f'Revenue_{category.replace(" ", "_")}'] = amount
        
        # Add expense categories
        for category, amount in stmt['Expenses'].items():
            flattened[f'Expense_{category.replace(" ", "_")}'] = amount
            
        return flattened
    
    def _flatten_cashflow_statement(self, stmt: Dict) -> Dict:
        """Flatten cash flow statement for CSV export"""
        flattened = {
            'Entity': stmt['Entity'],
            'Net_Cash_Operating': stmt['Operating Activities']['Net Cash from Operating'],
            'Net_Cash_Investing': stmt['Investing Activities']['Net Cash from Investing'], 
            'Net_Cash_Financing': stmt['Financing Activities']['Net Cash from Financing'],
            'Net_Change_Cash': stmt['Net Change in Cash']
        }
        
        # Add operating activity details
        for category, amount in stmt['Operating Activities']['Details'].items():
            flattened[f'Operating_{category.replace(" ", "_").replace("&", "and")}'] = -amount
            
        return flattened
    
    def _transpose_user_data(self, user_data: Dict[str, Dict]) -> pd.DataFrame:
        """Transpose user data so users become columns"""
        if not user_data:
            return pd.DataFrame()
        
        # Get all unique metrics (rows)
        all_metrics = set()
        for user_dict in user_data.values():
            all_metrics.update(user_dict.keys())
        
        # Remove 'Entity' as it's redundant in transposed format
        all_metrics.discard('Entity')
        all_metrics = sorted(all_metrics)
        
        # Create transposed DataFrame
        transposed_data = {}
        for user, user_dict in user_data.items():
            user_column = []
            for metric in all_metrics:
                user_column.append(user_dict.get(metric, 0))
            transposed_data[user] = user_column
        
        df = pd.DataFrame(transposed_data, index=all_metrics)
        return df
    
    def _save_transposed_data(self, df: pd.DataFrame, filename: str) -> None:
        """Save transposed data to CSV"""
        df.fillna(0).to_csv(filename)