"""
Cash flow statement generation business logic

Handles the generation of cash flow statements from transaction data.
"""

from typing import Dict, List, Any

from ..domain.transaction import Transaction
from ..domain.category import CategoryMapper, REVENUE_CATEGORIES

# Cash flow activity type constants
OPERATING_ACTIVITIES = 'Operating Activities'
INVESTING_ACTIVITIES = 'Investing Activities'
FINANCING_ACTIVITIES = 'Financing Activities'

# Transaction type constants
TRANSACTION_TYPE_REVENUE = "revenue"
TRANSACTION_TYPE_EXPENSE = "expense"
TRANSACTION_TYPE_PREPAID_ASSET = "prepaid_asset"

# Statement keys
KEY_DETAILS = 'Details'
KEY_NET_OPERATING = 'Net Cash from Operating'
KEY_NET_INVESTING = 'Net Cash from Investing'
KEY_NET_FINANCING = 'Net Cash from Financing'
KEY_NET_CHANGE = 'Net Change in Cash'
KEY_ENTITY = 'Entity'


class CashFlowStatementGenerator:
    """Generates cash flow statements from transaction data.

    This class processes transaction records and categorizes them into the three
    main cash flow activities: Operating, Investing, and Financing. It calculates
    the net cash flow for each activity type and the overall net change in cash.

    Attributes:
        category_mapper (CategoryMapper): Maps transaction categories to cash flow activities.
    """

    def __init__(self, category_mapper: CategoryMapper) -> None:
        """Initialize the cash flow statement generator.

        Args:
            category_mapper: CategoryMapper instance for categorizing transactions.
        """
        self.category_mapper = category_mapper

    def generate_statement(self, transactions: List[Transaction], entity_name: str) -> Dict[str, Any]:
        """Generate cash flow statement for given transactions.

        Categorizes transactions into Operating, Investing, and Financing activities
        and calculates net cash flows for each category.

        Args:
            transactions: List of Transaction objects to process.
            entity_name: Name of the entity (user or "Combined").

        Returns:
            Dictionary containing:
                - Entity: Name of the entity
                - Operating Activities: Dict with Details and Net Cash from Operating
                - Investing Activities: Dict with Details and Net Cash from Investing
                - Financing Activities: Dict with Details and Net Cash from Financing
                - Net Change in Cash: Sum of all activity cash flows

        Note:
            Transactions with zero amounts are automatically skipped.
            Prepaid asset transactions that don't affect cash flow are also skipped.
        """
        
        operating_activities = 0
        investing_activities = 0
        financing_activities = 0
        
        activity_details = {
            OPERATING_ACTIVITIES: {},
            INVESTING_ACTIVITIES: {},
            FINANCING_ACTIVITIES: {}
        }
        
        for transaction in transactions:
            # Skip transactions with zero amounts
            if transaction.amount == 0:
                continue
            
            # Determine transaction type and cash flow impact - prioritize analysis over stored defaults
            if (hasattr(transaction, 'affects_cash_flow') and
                hasattr(transaction, 'transaction_type') and
                transaction.transaction_type == TRANSACTION_TYPE_PREPAID_ASSET):
                # Trust specific transaction types from CSV processing
                transaction_type = transaction.transaction_type
                affects_cash_flow = transaction.affects_cash_flow
            else:
                # Backward compatibility and analysis-based determination
                affects_cash_flow = True  # Assume all transactions affect cash flow in old format
                if transaction.debit_category in REVENUE_CATEGORIES and transaction.amount > 0:
                    transaction_type = TRANSACTION_TYPE_REVENUE
                elif transaction.amount < 0:
                    transaction_type = TRANSACTION_TYPE_EXPENSE
                else:
                    transaction_type = TRANSACTION_TYPE_EXPENSE
            
            # Skip transactions that don't affect cash flow
            if not affects_cash_flow:
                continue
            
            # Get the cash flow activity type
            # Check both debit and credit categories to properly classify investing/financing activities
            debit_activity = self.category_mapper.get_cashflow_category(transaction.debit_category)
            credit_activity = self.category_mapper.get_cashflow_category(transaction.credit_account)

            # Determine activity type and cash flow direction
            # Prioritize non-operating activities (investing and financing take precedence)
            if debit_activity in [INVESTING_ACTIVITIES, FINANCING_ACTIVITIES]:
                # Debit is investing/financing - this means cash went out for that activity
                activity_type = debit_activity
                category_name = transaction.debit_category
                cash_flow_amount = -abs(transaction.amount)  # Outflow
            elif credit_activity in [INVESTING_ACTIVITIES, FINANCING_ACTIVITIES]:
                # Credit is investing/financing - this means cash came in from that activity
                activity_type = credit_activity
                category_name = transaction.credit_account
                cash_flow_amount = abs(transaction.amount)  # Inflow
            elif transaction_type == TRANSACTION_TYPE_REVENUE:
                # Operating revenue: positive cash flow (cash coming in)
                activity_type = debit_activity
                cash_flow_amount = abs(transaction.amount)
                category_name = transaction.debit_category
            elif transaction_type == TRANSACTION_TYPE_PREPAID_ASSET:
                # Prepaid asset purchase: negative cash flow (cash going out for future benefit)
                activity_type = debit_activity
                cash_flow_amount = -abs(transaction.amount)
                category_name = f"Prepaid: {transaction.debit_category}"
            else:
                # Operating expense: negative cash flow (cash going out)
                activity_type = debit_activity
                cash_flow_amount = -abs(transaction.amount)
                category_name = self.category_mapper.get_expense_category(transaction.debit_category)
            
            # Categorize the cash flow
            if activity_type == OPERATING_ACTIVITIES:
                operating_activities += cash_flow_amount
                activity_details[OPERATING_ACTIVITIES][category_name] = \
                    activity_details[OPERATING_ACTIVITIES].get(category_name, 0) + cash_flow_amount

            elif activity_type == INVESTING_ACTIVITIES:
                investing_activities += cash_flow_amount
                activity_details[INVESTING_ACTIVITIES][category_name] = \
                    activity_details[INVESTING_ACTIVITIES].get(category_name, 0) + cash_flow_amount

            elif activity_type == FINANCING_ACTIVITIES:
                financing_activities += cash_flow_amount
                activity_details[FINANCING_ACTIVITIES][category_name] = \
                    activity_details[FINANCING_ACTIVITIES].get(category_name, 0) + cash_flow_amount
        
        cash_flow_statement = {
            KEY_ENTITY: entity_name,
            OPERATING_ACTIVITIES: {
                KEY_DETAILS: activity_details[OPERATING_ACTIVITIES],
                KEY_NET_OPERATING: operating_activities
            },
            INVESTING_ACTIVITIES: {
                KEY_DETAILS: activity_details[INVESTING_ACTIVITIES],
                KEY_NET_INVESTING: investing_activities
            },
            FINANCING_ACTIVITIES: {
                KEY_DETAILS: activity_details[FINANCING_ACTIVITIES],
                KEY_NET_FINANCING: financing_activities
            },
            KEY_NET_CHANGE: operating_activities + investing_activities + financing_activities
        }
        
        return cash_flow_statement


def format_currency(amount: float) -> str:
    """Format currency amount for display in CNY.

    Args:
        amount: Numeric amount to format.

    Returns:
        Formatted string with CNY symbol and comma separators (e.g., "¥1,000.00").
    """
    return f"¥{amount:,.2f}"


def print_cash_flow_statement(statement: Dict[str, Any]) -> None:
    """Print formatted cash flow statement to console.

    Args:
        statement: Cash flow statement dictionary from CashFlowStatementGenerator.

    Displays:
        - Entity name
        - Operating Activities section with details and net cash flow
        - Investing Activities section with details and net cash flow
        - Financing Activities section with details and net cash flow
        - Net Change in Cash
    """
    print(f"\n{'='*50}")
    print(f"CASH FLOW STATEMENT - {statement[KEY_ENTITY]}")
    print(f"{'='*50}")

    print("\nOPERATING ACTIVITIES:")
    for category, amount in statement[OPERATING_ACTIVITIES][KEY_DETAILS].items():
        print(f"  {category}: {format_currency(-amount)}")
    print(f"  Net Cash from Operating: {format_currency(statement[OPERATING_ACTIVITIES][KEY_NET_OPERATING])}")

    print("\nINVESTING ACTIVITIES:")
    if statement[INVESTING_ACTIVITIES][KEY_DETAILS]:
        for category, amount in statement[INVESTING_ACTIVITIES][KEY_DETAILS].items():
            print(f"  {category}: {format_currency(-amount)}")
    else:
        print("  No investing activities")
    print(f"  Net Cash from Investing: {format_currency(statement[INVESTING_ACTIVITIES][KEY_NET_INVESTING])}")

    print("\nFINANCING ACTIVITIES:")
    if statement[FINANCING_ACTIVITIES][KEY_DETAILS]:
        for category, amount in statement[FINANCING_ACTIVITIES][KEY_DETAILS].items():
            print(f"  {category}: {format_currency(-amount)}")
    else:
        print("  No financing activities")
    print(f"  Net Cash from Financing: {format_currency(statement[FINANCING_ACTIVITIES][KEY_NET_FINANCING])}")

    print(f"\nNET CHANGE IN CASH: {format_currency(statement[KEY_NET_CHANGE])}")
    print(f"{'='*50}")