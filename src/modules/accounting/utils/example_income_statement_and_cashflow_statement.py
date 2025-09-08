import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import re
import os

@dataclass
class Transaction:
    """Represents a single transaction"""
    description: str
    amount: float
    debit_category: str
    credit_account: str
    user: str
    
class CategoryMapper:
    """Maps transaction categories to financial statement categories"""
    
    def __init__(self):
        # Define category mappings for income statement
        self.expense_categories = {
            '餐饮': 'Food & Dining',
            '通勤': 'Transportation', 
            '人情/旅行支出': 'Travel & Entertainment',
            '日用购物': 'General Shopping',
            '个人消费': 'Personal Expenses',
            '运动和健康': 'Health & Wellness',
            '水电': 'Utilities',
            '宠物': 'Pet Expenses'
        }
        
        # Define category mappings for cash flow statement
        self.cashflow_categories = {
            '餐饮': 'Operating Activities',
            '通勤': 'Operating Activities',
            '人情/旅行支出': 'Operating Activities', 
            '日用购物': 'Operating Activities',
            '个人消费': 'Operating Activities',
            '运动和健康': 'Operating Activities',
            '水电': 'Operating Activities',
            '宠物': 'Operating Activities'
        }
    
    def get_expense_category(self, category: str) -> str:
        return self.expense_categories.get(category, 'Other Expenses')
    
    def get_cashflow_category(self, category: str) -> str:
        return self.cashflow_categories.get(category, 'Operating Activities')

class TransactionProcessor:
    """Processes raw transaction data"""
    
    def __init__(self, csv_file_path: str):
        self.csv_file_path = csv_file_path
        self.transactions: List[Transaction] = []
        self.category_mapper = CategoryMapper()
    
    def _clean_amount(self, amount_str: str) -> float:
        """Clean and convert amount string to float"""
        if pd.isna(amount_str) or amount_str == '':
            return 0.0
        
        # Remove currency symbols and commas
        cleaned = re.sub(r'[¥,￥$]', '', str(amount_str))
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    
    def load_transactions(self) -> None:
        """Load transactions from CSV file"""
        try:
            df = pd.read_csv(self.csv_file_path)
            
            # Clean column names (remove any extra spaces)
            df.columns = df.columns.str.strip()
            
            for _, row in df.iterrows():
                transaction = Transaction(
                    description=str(row.get('Description', '')).strip(),
                    amount=self._clean_amount(row.get('Amount', 0)),
                    debit_category=str(row.get('Debit', '')).strip(),
                    credit_account=str(row.get('Credit', '')).strip(),
                    user=str(row.get('User', '')).strip()
                )
                self.transactions.append(transaction)
                
        except Exception as e:
            raise Exception(f"Error loading transactions: {e}")
    
    def get_transactions_by_user(self, user: str) -> List[Transaction]:
        """Get all transactions for a specific user"""
        return [t for t in self.transactions if t.user == user]
    
    def get_all_users(self) -> List[str]:
        """Get list of all unique users"""
        return list(set(t.user for t in self.transactions if t.user))

class IncomeStatementGenerator:
    """Generates income statements"""
    
    def __init__(self, category_mapper: CategoryMapper):
        self.category_mapper = category_mapper
    
    def generate_statement(self, transactions: List[Transaction], entity_name: str) -> Dict:
        """Generate income statement for given transactions"""
        
        # For this example, we assume all transactions are expenses (no revenue data)
        # In a real scenario, you'd have revenue transactions too
        
        expense_summary = {}
        total_expenses = 0
        
        for transaction in transactions:
            if transaction.amount > 0:  # Only count positive amounts as expenses
                category = self.category_mapper.get_expense_category(transaction.debit_category)
                expense_summary[category] = expense_summary.get(category, 0) + transaction.amount
                total_expenses += transaction.amount
        
        # Create income statement structure
        income_statement = {
            'Entity': entity_name,
            'Revenue': 0,  # No revenue data in the example
            'Total Revenue': 0,
            'Expenses': expense_summary,
            'Total Expenses': total_expenses,
            'Net Income': 0 - total_expenses  # Negative because only expenses
        }
        
        return income_statement

class CashFlowStatementGenerator:
    """Generates cash flow statements"""
    
    def __init__(self, category_mapper: CategoryMapper):
        self.category_mapper = category_mapper
    
    def generate_statement(self, transactions: List[Transaction], entity_name: str) -> Dict:
        """Generate cash flow statement for given transactions"""
        
        operating_activities = 0
        investing_activities = 0
        financing_activities = 0
        
        activity_details = {
            'Operating Activities': {},
            'Investing Activities': {},
            'Financing Activities': {}
        }
        
        for transaction in transactions:
            if transaction.amount > 0:
                # Categorize cash flows (for this example, most are operating)
                category = self.category_mapper.get_cashflow_category(transaction.debit_category)
                
                if category == 'Operating Activities':
                    operating_activities += transaction.amount
                    expense_type = self.category_mapper.get_expense_category(transaction.debit_category)
                    activity_details['Operating Activities'][expense_type] = \
                        activity_details['Operating Activities'].get(expense_type, 0) + transaction.amount
                elif category == 'Investing Activities':
                    investing_activities += transaction.amount
                elif category == 'Financing Activities':
                    financing_activities += transaction.amount
        
        # Cash flows are negative for expenses
        net_operating = -operating_activities
        net_investing = -investing_activities  
        net_financing = -financing_activities
        
        cash_flow_statement = {
            'Entity': entity_name,
            'Operating Activities': {
                'Details': activity_details['Operating Activities'],
                'Net Cash from Operating': net_operating
            },
            'Investing Activities': {
                'Details': activity_details['Investing Activities'], 
                'Net Cash from Investing': net_investing
            },
            'Financing Activities': {
                'Details': activity_details['Financing Activities'],
                'Net Cash from Financing': net_financing
            },
            'Net Change in Cash': net_operating + net_investing + net_financing
        }
        
        return cash_flow_statement

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
    
    def _save_income_statements(self, statements: List[Dict], filename: str) -> None:
        """Save income statements to CSV"""
        df = pd.DataFrame(statements)
        df.fillna(0, inplace=True)
        df.to_csv(filename, index=False)
    
    def _save_cashflow_statements(self, statements: List[Dict], filename: str) -> None:
        """Save cash flow statements to CSV"""
        df = pd.DataFrame(statements)
        df.fillna(0, inplace=True)
        df.to_csv(filename, index=False)
    
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

# Example usage
if __name__ == "__main__":
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try to find transactions.csv in common locations
    possible_paths = [
        os.path.join(script_dir, "transactions.csv"),  # Same directory as script
        os.path.join(script_dir, "..", "data", "accounting", "transactions.csv"),  # data/accounting folder
        "transactions.csv"  # Current working directory
    ]
    
    transaction_file = None
    for path in possible_paths:
        if os.path.exists(path):
            transaction_file = path
            print(f"Found transactions file at: {transaction_file}")
            break
    
    if transaction_file is None:
        print("Error: Could not find transactions.csv file!")
        print("Looked in the following locations:")
        for path in possible_paths:
            print(f"  - {path}")
        print("\nPlease ensure transactions.csv exists in one of these locations.")
        exit(1)
    
    # Initialize the report generator
    generator = FinancialReportGenerator(transaction_file)
    
    try:
        # Generate reports
        generator.generate_reports()
        
    except Exception as e:
        print(f"Error generating reports: {e}")