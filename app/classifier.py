"""Transaction classification logic."""

from typing import Dict, Any


def classify_transaction(parsed: Dict[str, Any]) -> str:
    """
    Classify transaction based on Type, Sub Type, Action, and Instrument Type.
    
    Returns a classification string:
    - deposit, withdrawal
    - stock_buy, stock_sell
    - option_buy, option_sell, option_assignment, option_expiration
    - dividend, fee, adjustment, interest
    """
    txn_type = parsed['type'].lower()
    subtype = parsed['subtype'].lower()
    action = parsed['action'].lower()
    instrument = parsed['instrument_type'].lower()
    
    # Money movements
    if txn_type == 'money movement':
        if 'deposit' in subtype or 'transfer' in subtype:
            return 'deposit'
        elif 'withdrawal' in subtype:
            return 'withdrawal'
        elif 'balance adjustment' in subtype or 'adjustment' in subtype:
            if 'interest' in parsed['description'].lower():
                return 'interest'
            return 'adjustment'
        elif 'credit interest' in subtype:
            return 'interest'
        else:
            return 'adjustment'
    
    # Dividends and distributions
    if txn_type == 'receive deliver':
        if 'dividend' in subtype.lower():
            return 'dividend'
        return 'dividend'  # Assume dividends for receive/deliver
    
    # Trades
    if txn_type == 'trade':
        # Options
        if 'option' in instrument:
            if 'buy to open' in subtype or 'buy_to_open' in action:
                return 'option_buy'
            elif 'sell to open' in subtype or 'sell_to_open' in action:
                return 'option_sell'
            elif 'buy to close' in subtype or 'buy_to_close' in action:
                return 'option_buy_to_close'
            elif 'sell to close' in subtype or 'sell_to_close' in action:
                return 'option_sell_to_close'
            elif 'assignment' in subtype:
                return 'option_assignment'
            elif 'expiration' in subtype or 'expire' in subtype:
                return 'option_expiration'
            else:
                # Generic option trade
                if parsed['quantity'] > 0:
                    return 'option_buy'
                else:
                    return 'option_sell'
        
        # Stocks/ETFs
        elif 'equity' in instrument:
            if 'buy' in subtype or 'buy' in action or parsed['quantity'] > 0:
                return 'stock_buy'
            elif 'sell' in subtype or 'sell' in action or parsed['quantity'] < 0:
                return 'stock_sell'
            else:
                # Fallback based on quantity
                if parsed['quantity'] > 0:
                    return 'stock_buy'
                else:
                    return 'stock_sell'
        
        # Future options or other instruments
        else:
            if 'buy' in subtype or 'buy' in action:
                return 'other_buy'
            elif 'sell' in subtype or 'sell' in action:
                return 'other_sell'
            return 'other_trade'
    
    # Corporate actions
    if 'corporate action' in txn_type:
        return 'corporate_action'
    
    # Fees
    if 'fee' in txn_type or 'fee' in subtype:
        return 'fee'
    
    # Default to adjustment
    return 'adjustment'


def is_option_trade(classification: str) -> bool:
    """Check if transaction is an option trade."""
    return classification.startswith('option_')


def is_stock_trade(classification: str) -> bool:
    """Check if transaction is a stock/ETF trade."""
    return classification.startswith('stock_')


def is_opening_trade(classification: str) -> bool:
    """Check if transaction is opening a position."""
    return classification in ['option_buy', 'option_sell', 'stock_buy']


def is_closing_trade(classification: str) -> bool:
    """Check if transaction is closing a position."""
    return classification in ['option_buy_to_close', 'option_sell_to_close', 'stock_sell']
