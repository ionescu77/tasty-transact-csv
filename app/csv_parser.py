"""CSV parser for TastyTrade transaction history."""

import csv
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from dateutil import parser as date_parser
import pytz


BUCHAREST_TZ = pytz.timezone('Europe/Bucharest')


def extract_account_info_from_filename(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract account code and description from filename.
    
    Example: tastytrade_transactions_history_x5WY77777_250101_to_251125.csv
    Returns: ('x5WY77777', 'tastytrade transactions history 250101 to 251125')
    """
    # Pattern: extract account code (starts with x followed by alphanumeric)
    # and date range from filename
    pattern = r'tastytrade_transactions_history_(x\w+)_(\d{6})_to_(\d{6})\.csv'
    match = re.search(pattern, filename, re.IGNORECASE)
    
    if match:
        account_code = match.group(1)  # e.g., x5WY77777
        start_date = match.group(2)    # e.g., 250101
        end_date = match.group(3)      # e.g., 251125
        
        description = f"tastytrade transactions history {start_date} to {end_date}"
        return account_code, description
    
    # Fallback: try to extract any pattern like x5WY77777
    account_match = re.search(r'(x\w+)', filename, re.IGNORECASE)
    if account_match:
        return account_match.group(1), f"transactions from {filename}"
    
    return None, None


def parse_datetime(date_str: str) -> datetime:
    """
    Parse datetime string from CSV (Europe/Bucharest timezone).
    Convert to UTC for storage.
    """
    if not date_str:
        return None
    
    # Parse the datetime string
    dt = date_parser.parse(date_str)
    
    # If timezone-aware, convert to UTC
    if dt.tzinfo:
        return dt.astimezone(pytz.UTC).replace(tzinfo=None)
    
    # If naive, assume Europe/Bucharest and convert to UTC
    dt_bucharest = BUCHAREST_TZ.localize(dt)
    return dt_bucharest.astimezone(pytz.UTC).replace(tzinfo=None)


def parse_number(value: str) -> float:
    """Parse numeric value, handling commas and dashes."""
    if not value or value == '--':
        return 0.0
    
    # Remove commas and parse
    cleaned = value.replace(',', '')
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def parse_csv_row(row: Dict[str, str]) -> Dict[str, Any]:
    """
    Parse a single CSV row into a structured dictionary.
    
    CSV columns:
    - Date, Type, Sub Type, Action, Symbol, Instrument Type, Description,
    - Value, Quantity, Average Price, Commissions, Fees, Multiplier,
    - Root Symbol, Underlying Symbol, Expiration Date, Strike Price,
    - Call or Put, Order #, Total, Currency
    """
    parsed = {
        'datetime': parse_datetime(row.get('Date', '')),
        'type': row.get('Type', '').strip(),
        'subtype': row.get('Sub Type', '').strip(),
        'action': row.get('Action', '').strip(),
        'symbol': row.get('Symbol', '').strip(),
        'instrument_type': row.get('Instrument Type', '').strip(),
        'description': row.get('Description', '').strip(),
        'value': parse_number(row.get('Value', '0')),
        'quantity': parse_number(row.get('Quantity', '0')),
        'price': parse_number(row.get('Average Price', '0')),
        'commissions': parse_number(row.get('Commissions', '0')),
        'fees': parse_number(row.get('Fees', '0')),
        'multiplier': int(parse_number(row.get('Multiplier', '0'))) if row.get('Multiplier') else None,
        'root_symbol': row.get('Root Symbol', '').strip() or None,
        'underlying_symbol': row.get('Underlying Symbol', '').strip() or None,
        'expiration_date': row.get('Expiration Date', '').strip() or None,
        'strike_price': parse_number(row.get('Strike Price', '0')) if row.get('Strike Price') else None,
        'call_or_put': row.get('Call or Put', '').strip() or None,
        'txn_id': row.get('Order #', '').strip(),
        'net_amount': parse_number(row.get('Total', '0')),
        'currency': row.get('Currency', 'USD').strip(),
    }
    
    return parsed


def read_csv_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Read and parse entire CSV file.
    
    Returns list of parsed transaction dictionaries.
    """
    transactions = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            parsed = parse_csv_row(row)
            transactions.append(parsed)
    
    return transactions


def read_csv_content(content: bytes) -> List[Dict[str, Any]]:
    """
    Read and parse CSV from uploaded file content.
    
    Returns list of parsed transaction dictionaries.
    """
    transactions = []
    
    # Decode bytes to string
    content_str = content.decode('utf-8')
    
    # Split into lines and create CSV reader
    lines = content_str.splitlines()
    reader = csv.DictReader(lines)
    
    for row in reader:
        parsed = parse_csv_row(row)
        transactions.append(parsed)
    
    return transactions
