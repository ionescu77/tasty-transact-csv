"""Tests for CSV parser."""

import pytest
from datetime import datetime
from app.csv_parser import parse_datetime, parse_number, parse_csv_row


def test_parse_datetime():
    """Test datetime parsing with timezone."""
    # Test with timezone
    dt = parse_datetime("2025-11-22T23:20:54+0200")
    assert isinstance(dt, datetime)
    assert dt.tzinfo is None  # Should be converted to naive UTC
    
    # Test without timezone (should assume Europe/Bucharest)
    dt2 = parse_datetime("2025-11-22 23:20:54")
    assert isinstance(dt2, datetime)


def test_parse_number():
    """Test number parsing."""
    assert parse_number("123.45") == 123.45
    assert parse_number("1,234.56") == 1234.56
    assert parse_number("--") == 0.0
    assert parse_number("") == 0.0


def test_parse_csv_row():
    """Test parsing a complete CSV row."""
    row = {
        'Date': '2025-11-21T17:39:10+0200',
        'Type': 'Trade',
        'Sub Type': 'Sell to Open',
        'Action': 'SELL_TO_OPEN',
        'Symbol': 'GRAB  260417C00010000',
        'Instrument Type': 'Equity Option',
        'Description': 'Sold 1 GRAB 04/17/26 Call 10.00 @ 0.07',
        'Value': '7.00',
        'Quantity': '1',
        'Average Price': '7.00',
        'Commissions': '-1.00',
        'Fees': '-0.12',
        'Multiplier': '100',
        'Root Symbol': 'GRAB',
        'Underlying Symbol': 'GRAB',
        'Expiration Date': '4/17/26',
        'Strike Price': '10.0',
        'Call or Put': 'CALL',
        'Order #': '422297191',
        'Total': '5.88',
        'Currency': 'USD'
    }
    
    parsed = parse_csv_row(row)
    
    assert parsed['symbol'] == 'GRAB  260417C00010000'
    assert parsed['type'] == 'Trade'
    assert parsed['subtype'] == 'Sell to Open'
    assert parsed['action'] == 'SELL_TO_OPEN'
    assert parsed['quantity'] == 1.0
    assert parsed['price'] == 7.0
    assert parsed['fees'] == -0.12
    assert parsed['multiplier'] == 100
    assert parsed['root_symbol'] == 'GRAB'
    assert parsed['strike_price'] == 10.0
    assert parsed['call_or_put'] == 'CALL'
    assert parsed['net_amount'] == 5.88
    assert isinstance(parsed['datetime'], datetime)
