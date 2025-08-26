"""
Sample Data Generation for Professional Accounting Module

This module provides realistic dummy data for testing and demonstration
of the accounting functionality, covering multiple months with varied transactions.
"""

from decimal import Decimal
from datetime import datetime, date, timedelta
from typing import List, Dict
import uuid

from .models import Transaction, Asset


def generate_sample_transactions(months: int = 3, start_date: date = None) -> List[Transaction]:
    """
    Generate realistic sample transactions for demonstration
    
    Args:
        months: Number of months of data to generate
        start_date: Starting date (defaults to 3 months ago)
        
    Returns:
        List of Transaction objects with realistic data
    """
    if start_date is None:
        start_date = date.today().replace(day=1) - timedelta(days=90)
    
    transactions = []
    current_date = start_date
    
    for month in range(months):
        # Get the month start date
        month_start = current_date.replace(day=1)
        
        # Income transactions (beginning of month)
        transactions.append(Transaction(
            id=str(uuid.uuid4()),
            user_id="demo_user",
            date=datetime.combine(month_start + timedelta(days=1), datetime.min.time()),
            description="月薪收入",
            amount=Decimal("12000.00"),
            category="工资收入",
            account_name="招商银行储蓄卡",
            account_type="Debit",
            transaction_type="Cash",
            notes="基本工资"
        ))
        
        transactions.append(Transaction(
            id=str(uuid.uuid4()),
            user_id="demo_user",
            date=datetime.combine(month_start + timedelta(days=2), datetime.min.time()),
            description="自由职业收入",
            amount=Decimal("3500.00"),
            category="服务收入",
            account_name="支付宝",
            account_type="Debit",
            transaction_type="Cash",
            notes="咨询服务费"
        ))
        
        # Fixed expenses (early in month)
        transactions.append(Transaction(
            id=str(uuid.uuid4()),
            user_id="demo_user",
            date=datetime.combine(month_start + timedelta(days=3), datetime.min.time()),
            description="房租支出",
            amount=Decimal("-3200.00"),
            category="房租",
            account_name="招商银行储蓄卡",
            account_type="Debit",
            transaction_type="Cash",
            notes="一居室月租"
        ))
        
        transactions.append(Transaction(
            id=str(uuid.uuid4()),
            user_id="demo_user",
            date=datetime.combine(month_start + timedelta(days=5), datetime.min.time()),
            description="水电费",
            amount=Decimal("-185.50"),
            category="水电费",
            account_name="微信支付",
            account_type="Debit",
            transaction_type="Cash",
            notes="电费120+水费65.5"
        ))
        
        # Variable expenses throughout the month
        daily_expenses = [
            ("餐饮", ["早餐", "午餐", "晚餐", "咖啡", "外卖"], 15, 80),
            ("交通", ["地铁", "公交", "打车", "共享单车"], 10, 45),
            ("日用购物", ["超市购物", "日用品", "洗护用品", "文具"], 20, 150),
            ("娱乐", ["电影", "KTV", "游戏", "健身"], 50, 200),
            ("通讯", ["话费充值", "网费", "流量包"], 30, 100),
            ("医疗", ["药店", "体检", "看医生"], 40, 300),
            ("服装", ["衣服", "鞋子", "配饰"], 100, 500),
        ]
        
        # Generate variable expenses
        for day_offset in range(0, 28, 2):  # Every 2 days
            for category, descriptions, min_amt, max_amt in daily_expenses:
                if (month * 30 + day_offset) % 7 == 0:  # Roughly weekly expenses
                    import random
                    amount = Decimal(str(random.uniform(min_amt, max_amt)))
                    desc = random.choice(descriptions)
                    account = random.choice(["招商银行储蓄卡", "支付宝", "微信支付"])
                    
                    transactions.append(Transaction(
                        id=str(uuid.uuid4()),
                        user_id="demo_user",
                        date=datetime.combine(month_start + timedelta(days=day_offset), datetime.min.time()),
                        description=desc,
                        amount=-amount,  # Expenses are negative
                        category=category,
                        account_name=account,
                        account_type="Debit",
                        transaction_type="Cash",
                        notes=f"{category}支出"
                    ))
        
        # Investment activities (mid-month)
        if month % 2 == 0:  # Every other month
            transactions.append(Transaction(
                id=str(uuid.uuid4()),
                user_id="demo_user",
                date=datetime.combine(month_start + timedelta(days=15), datetime.min.time()),
                description="股票投资",
                amount=Decimal("-2000.00"),
                category="投资支出",
                account_name="招商银行储蓄卡",
                account_type="Debit",
                transaction_type="Non-Cash",
                notes="购买ETF基金"
            ))
        
        # Credit card payments (end of month)
        transactions.append(Transaction(
            id=str(uuid.uuid4()),
            user_id="demo_user",
            date=datetime.combine(month_start + timedelta(days=25), datetime.min.time()),
            description="信用卡还款",
            amount=Decimal("-1800.00"),
            category="其他支出",
            account_name="招商银行储蓄卡",
            account_type="Debit",
            transaction_type="Cash",
            notes="信用卡月度还款"
        ))
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    return sorted(transactions, key=lambda t: t.date)


def generate_sample_assets(as_of_date: date = None) -> List[Asset]:
    """
    Generate realistic sample assets for demonstration
    
    Args:
        as_of_date: Date for asset snapshot (defaults to today)
        
    Returns:
        List of Asset objects with realistic balances
    """
    if as_of_date is None:
        as_of_date = date.today()
    
    assets = [
        Asset(
            id=str(uuid.uuid4()),
            user_id="demo_user",
            account_name="招商银行储蓄卡",
            balance=Decimal("15300.50"),
            account_type="checking",
            as_of_date=datetime.combine(as_of_date, datetime.min.time()),
            currency="CNY"
        ),
        Asset(
            id=str(uuid.uuid4()),
            user_id="demo_user",
            account_name="支付宝余额",
            balance=Decimal("2800.30"),
            account_type="checking",
            as_of_date=datetime.combine(as_of_date, datetime.min.time()),
            currency="CNY"
        ),
        Asset(
            id=str(uuid.uuid4()),
            user_id="demo_user",
            account_name="微信钱包",
            balance=Decimal("450.80"),
            account_type="checking",
            as_of_date=datetime.combine(as_of_date, datetime.min.time()),
            currency="CNY"
        ),
        Asset(
            id=str(uuid.uuid4()),
            user_id="demo_user",
            account_name="投资账户",
            balance=Decimal("8500.00"),
            account_type="investment",
            as_of_date=datetime.combine(as_of_date, datetime.min.time()),
            currency="CNY"
        )
    ]
    
    return assets


def get_sample_data_summary() -> Dict:
    """Get summary information about the sample data"""
    transactions = generate_sample_transactions()
    assets = generate_sample_assets()
    
    total_income = sum(t.amount for t in transactions if t.amount > 0)
    total_expenses = sum(abs(t.amount) for t in transactions if t.amount < 0)
    total_assets = sum(a.balance for a in assets)
    
    return {
        "transaction_count": len(transactions),
        "asset_count": len(assets),
        "date_range": f"{transactions[0].date.strftime('%Y-%m-%d')} to {transactions[-1].date.strftime('%Y-%m-%d')}",
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_income": total_income - total_expenses,
        "total_assets": total_assets,
        "months_covered": 3
    }


def create_sample_csv_data() -> str:
    """
    Create sample CSV data as string for easy copy/paste
    
    Returns:
        CSV string with sample transaction data
    """
    transactions = generate_sample_transactions()
    
    lines = ["date,description,amount,category,account_name,account_type,notes"]
    
    for t in transactions[:50]:  # Limit to first 50 for readability
        lines.append(
            f"{t.date.strftime('%Y-%m-%d')},{t.description},{float(t.amount)},{t.category},"
            f"{t.account_name},{t.account_type},{t.notes or ''}"
        )
    
    return "\n".join(lines)


def get_csv_format_template() -> str:
    """
    Get CSV format template with explanation
    
    Returns:
        Template string showing required CSV format
    """
    return """Required CSV Format:

Columns (in order):
- date: YYYY-MM-DD format (e.g., 2025-01-15)
- description: Transaction description (Chinese/English supported)
- amount: Decimal amount (negative for expenses, positive for income)
- category: Must match predefined categories
- account_name: Account identifier
- account_type: Cash, Credit, or Debit
- notes: Optional additional information

Example CSV:
date,description,amount,category,account_name,account_type,notes
2025-01-15,餐饮,-68.50,餐饮,招商银行卡,Debit,晚饭
2025-01-10,工资收入,8000.00,工资收入,招商银行卡,Debit,月薪
2025-01-05,房租,-2500.00,房租,招商银行卡,Debit,1月房租

Expense Categories: 餐饮, 房租, 水电费, 交通, 日用购物, 保险, 医疗, 教育, 娱乐, 通讯, 服装, 维修, 其他支出
Revenue Categories: 工资收入, 服务收入, 投资收益, 其他收入"""