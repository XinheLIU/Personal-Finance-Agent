"""
Cash flow statement generation business logic

Handles the generation of cash flow statements from transaction data.
"""

from typing import Dict, List, Any

from ..domain.transaction import Transaction
from ..domain.category import CategoryMapper, REVENUE_CATEGORIES


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
            # Skip transactions with zero amounts
            if transaction.amount == 0:
                continue
            
            # Determine transaction type and cash flow impact - prioritize analysis over stored defaults
            if hasattr(transaction, 'affects_cash_flow') and hasattr(transaction, 'transaction_type') and transaction.transaction_type in ["prepaid_asset"]:
                # Trust specific transaction types from CSV processing
                transaction_type = transaction.transaction_type
                affects_cash_flow = transaction.affects_cash_flow
            else:
                # Backward compatibility and analysis-based determination
                affects_cash_flow = True  # Assume all transactions affect cash flow in old format
                if transaction.debit_category in REVENUE_CATEGORIES and transaction.amount > 0:
                    transaction_type = "revenue"
                elif transaction.amount < 0:
                    transaction_type = "expense"
                else:
                    transaction_type = "expense"
            
            # Skip transactions that don't affect cash flow
            if not affects_cash_flow:
                continue
            
            # Determine cash flow direction based on transaction type
            if transaction_type == "revenue":
                # Revenue: positive cash flow (cash coming in)
                cash_flow_amount = abs(transaction.amount)
                category_name = transaction.debit_category
            elif transaction_type == "prepaid_asset":
                # Prepaid asset purchase: negative cash flow (cash going out for future benefit)
                cash_flow_amount = -abs(transaction.amount)
                category_name = f"Prepaid: {transaction.debit_category}"
            else:
                # Expense: negative cash flow (cash going out)  
                cash_flow_amount = -abs(transaction.amount)
                category_name = self.category_mapper.get_expense_category(transaction.debit_category)
            
            # Get the cash flow activity type
            activity_type = self.category_mapper.get_cashflow_category(transaction.debit_category)
            
            # Categorize the cash flow
            if activity_type == 'Operating Activities':
                operating_activities += cash_flow_amount
                activity_details['Operating Activities'][category_name] = \
                    activity_details['Operating Activities'].get(category_name, 0) + cash_flow_amount
                    
            elif activity_type == 'Investing Activities':
                investing_activities += cash_flow_amount
                activity_details['Investing Activities'][category_name] = \
                    activity_details['Investing Activities'].get(category_name, 0) + cash_flow_amount
                    
            elif activity_type == 'Financing Activities':
                financing_activities += cash_flow_amount
                activity_details['Financing Activities'][category_name] = \
                    activity_details['Financing Activities'].get(category_name, 0) + cash_flow_amount
        
        cash_flow_statement = {
            'Entity': entity_name,
            'Operating Activities': {
                'Details': activity_details['Operating Activities'],
                'Net Cash from Operating': operating_activities
            },
            'Investing Activities': {
                'Details': activity_details['Investing Activities'], 
                'Net Cash from Investing': investing_activities
            },
            'Financing Activities': {
                'Details': activity_details['Financing Activities'],
                'Net Cash from Financing': financing_activities
            },
            'Net Change in Cash': operating_activities + investing_activities + financing_activities
        }
        
        return cash_flow_statement


def format_currency(amount: float) -> str:
    """Format currency amount for display in CNY"""
    return f"¥{amount:,.2f}"


def print_cash_flow_statement(statement: Dict[str, Any]):
    """Print formatted cash flow statement"""
    print(f"\n{'='*50}")
    print(f"CASH FLOW STATEMENT - {statement['Entity']}")
    print(f"{'='*50}")
    
    print("\nOPERATING ACTIVITIES:")
    for category, amount in statement['Operating Activities']['Details'].items():
        print(f"  {category}: {format_currency(-amount)}")
    print(f"  Net Cash from Operating: {format_currency(statement['Operating Activities']['Net Cash from Operating'])}")
    
    print("\nINVESTING ACTIVITIES:")
    if statement['Investing Activities']['Details']:
        for category, amount in statement['Investing Activities']['Details'].items():
            print(f"  {category}: {format_currency(-amount)}")
    else:
        print("  No investing activities")
    print(f"  Net Cash from Investing: {format_currency(statement['Investing Activities']['Net Cash from Investing'])}")
    
    print("\nFINANCING ACTIVITIES:")
    if statement['Financing Activities']['Details']:
        for category, amount in statement['Financing Activities']['Details'].items():
            print(f"  {category}: {format_currency(-amount)}")
    else:
        print("  No financing activities")
    print(f"  Net Cash from Financing: {format_currency(statement['Financing Activities']['Net Cash from Financing'])}")
    
    print(f"\nNET CHANGE IN CASH: {format_currency(statement['Net Change in Cash'])}")
    print(f"{'='*50}")