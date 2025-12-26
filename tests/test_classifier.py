"""Tests for transaction classification."""

import pytest
from app.classifier import classify_transaction, is_option_trade, is_stock_trade


def test_classify_stock_buy():
    """Test stock buy classification."""
    parsed = {
        'type': 'Trade',
        'subtype': 'Buy to Open',
        'action': 'BUY_TO_OPEN',
        'instrument_type': 'Equity',
        'quantity': 1,
        'description': 'Bought 1 IBIT'
    }
    
    assert classify_transaction(parsed) == 'stock_buy'


def test_classify_stock_sell():
    """Test stock sell classification."""
    parsed = {
        'type': 'Trade',
        'subtype': 'Sell to Close',
        'action': 'SELL_TO_CLOSE',
        'instrument_type': 'Equity',
        'quantity': -3,
        'description': 'Sold 3 XOVR'
    }
    
    assert classify_transaction(parsed) == 'stock_sell'


def test_classify_option_buy_to_open():
    """Test option buy to open classification."""
    parsed = {
        'type': 'Trade',
        'subtype': 'Buy to Open',
        'action': 'BUY_TO_OPEN',
        'instrument_type': 'Equity Option',
        'quantity': 1,
        'description': 'Bought 1 SPY Call'
    }
    
    assert classify_transaction(parsed) == 'option_buy'


def test_classify_option_sell_to_open():
    """Test option sell to open classification."""
    parsed = {
        'type': 'Trade',
        'subtype': 'Sell to Open',
        'action': 'SELL_TO_OPEN',
        'instrument_type': 'Equity Option',
        'quantity': 1,
        'description': 'Sold 1 SPY Put'
    }
    
    assert classify_transaction(parsed) == 'option_sell'


def test_classify_deposit():
    """Test deposit classification."""
    parsed = {
        'type': 'Money Movement',
        'subtype': 'Deposit',
        'action': '',
        'instrument_type': '',
        'quantity': 0,
        'description': 'Deposit'
    }
    
    assert classify_transaction(parsed) == 'deposit'


def test_classify_adjustment():
    """Test adjustment classification."""
    parsed = {
        'type': 'Money Movement',
        'subtype': 'Balance Adjustment',
        'action': '',
        'instrument_type': '',
        'quantity': 0,
        'description': 'Regulatory fee adjustment'
    }
    
    assert classify_transaction(parsed) == 'adjustment'


def test_is_option_trade():
    """Test option trade detection."""
    assert is_option_trade('option_buy') == True
    assert is_option_trade('option_sell') == True
    assert is_option_trade('stock_buy') == False


def test_is_stock_trade():
    """Test stock trade detection."""
    assert is_stock_trade('stock_buy') == True
    assert is_stock_trade('stock_sell') == True
    assert is_stock_trade('option_buy') == False
