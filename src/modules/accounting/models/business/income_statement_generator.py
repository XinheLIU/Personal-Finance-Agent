"""
Income statement generation business logic

Handles the generation of income statements from transaction data.
"""

from typing import Dict, List, Any

from ..domain.transaction import Transaction
from ..domain.category import CategoryMapper, REVENUE_CATEGORIES


class IncomeStatementGenerator:
    """Generates income statements"""
    
    def __init__(self, category_mapper: CategoryMapper):
        self.category_mapper = category_mapper
    
    def generate_statement(self, transactions: List[Transaction], entity_name: str) -> Dict:
        """Generate income statement for given transactions"""
        
        expense_summary = {}
        revenue_summary = {}
        total_expenses = 0
        total_revenue = 0
        
        for transaction in transactions:
            # Skip transactions with zero amounts
            if transaction.amount == 0:
                continue
            
            # Determine transaction type - prioritize actual analysis over stored attributes
            # since stored attributes may be defaults for old test data
            if transaction.debit_category in REVENUE_CATEGORIES and transaction.amount > 0:
                transaction_type = "revenue"
            elif hasattr(transaction, 'transaction_type') and transaction.transaction_type == "prepaid_asset":
                transaction_type = "prepaid_asset"  # Only trust this specific value
            elif transaction.amount < 0:
                transaction_type = "expense"
            else:
                transaction_type = "expense"
            
            # Skip prepaid asset transactions (they don't affect current period income)
            if transaction_type == "prepaid_asset":
                continue
                
            # Process revenue and expense transactions
            if transaction_type == "revenue":
                # Revenue transaction
                category = transaction.debit_category
                amount = abs(transaction.amount)  # Ensure positive for income statement
                revenue_summary[category] = revenue_summary.get(category, 0) + amount
                total_revenue += amount
            elif transaction_type == "expense":
                # Expense transaction (including expenses from prepaid and reimbursements)
                category = self.category_mapper.get_expense_category(transaction.debit_category)
                # Keep sign! Negative amounts = expense reductions (reimbursements)
                # Positive amounts = regular expenses
                amount = transaction.amount  # DO NOT use abs() - preserve sign!
                expense_summary[category] = expense_summary.get(category, 0) + amount
                total_expenses += amount
        
        # Create income statement structure
        income_statement = {
            'Entity': entity_name,
            'Revenue': revenue_summary,
            'Total Revenue': total_revenue,
            'Expenses': expense_summary,
            'Total Expenses': total_expenses,
            'Net Income': total_revenue - total_expenses
        }
        
        return income_statement


def format_currency(amount: float) -> str:
    """Format currency amount for display in CNY"""
    return f"¥{amount:,.2f}"


def print_income_statement(statement: Dict[str, Any]):
    """Print formatted income statement"""
    print(f"\n{'='*50}")
    print(f"INCOME STATEMENT - {statement['Entity']}")
    print(f"{'='*50}")
    
    print("\nREVENUE:")
    if statement['Revenue']:
        for category, amount in statement['Revenue'].items():
            print(f"  {category}: {format_currency(amount)}")
    else:
        print("  No revenue data")
    print(f"  Total Revenue: {format_currency(statement['Total Revenue'])}")
    
    print("\nEXPENSES:")
    for category, amount in statement['Expenses'].items():
        print(f"  {category}: {format_currency(amount)}")
    print(f"  Total Expenses: {format_currency(statement['Total Expenses'])}")
    
    print(f"\nNET INCOME: {format_currency(statement['Net Income'])}")
    print(f"{'='*50}")