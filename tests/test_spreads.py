"""Tests for spread grouping."""

import pytest
from datetime import datetime
from app.spreads import group_spreads, is_vertical_spread, classify_spread_type


def test_group_spreads_simple():
    """Test grouping of a simple 2-leg spread."""
    transactions = [
        {
            'datetime': datetime(2025, 11, 21, 17, 39, 10),
            'txn_id': '422297191',
            'instrument_type': 'Equity Option',
            'root_symbol': 'GRAB',
            'symbol': 'GRAB  260417C00010000',
            'strike_price': 10.0,
            'call_or_put': 'CALL',
            'expiration_date': '4/17/26',
            'subtype': 'Sell to Open',
            'net_amount': 5.88
        },
        {
            'datetime': datetime(2025, 11, 21, 17, 39, 10),
            'txn_id': '422297191',
            'instrument_type': 'Equity Option',
            'root_symbol': 'GRAB',
            'symbol': 'GRAB  260417C00006000',
            'strike_price': 6.0,
            'call_or_put': 'CALL',
            'expiration_date': '4/17/26',
            'subtype': 'Buy to Open',
            'net_amount': -35.12
        }
    ]
    
    spreads = group_spreads(transactions)
    
    assert len(spreads) == 1
    legs, description = spreads[0]
    assert len(legs) == 2
    assert 'GRAB' in description
    assert 'Call' in description or 'CALL' in description


def test_is_vertical_spread():
    """Test vertical spread detection."""
    legs = [
        {
            'expiration_date': '4/17/26',
            'call_or_put': 'CALL',
            'strike_price': 10.0
        },
        {
            'expiration_date': '4/17/26',
            'call_or_put': 'CALL',
            'strike_price': 6.0
        }
    ]
    
    assert is_vertical_spread(legs) == True


def test_classify_spread_type():
    """Test spread type classification."""
    # Single leg - not a spread
    single_leg = [{'expiration_date': '4/17/26', 'call_or_put': 'CALL'}]
    assert classify_spread_type(single_leg) == "Single Option"
    
    # Vertical spread
    vertical = [
        {'expiration_date': '4/17/26', 'call_or_put': 'CALL', 'strike_price': 10.0},
        {'expiration_date': '4/17/26', 'call_or_put': 'CALL', 'strike_price': 6.0}
    ]
    assert classify_spread_type(vertical) == "Vertical Spread"
