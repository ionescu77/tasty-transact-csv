#!/usr/bin/env python3
"""Test account info extraction."""

from app.csv_parser import extract_account_info_from_filename

filename = "tastytrade_transactions_history_x5WY77777_250101_to_251125.csv"
account_code, description = extract_account_info_from_filename(filename)

print(f"✓ Account code: {account_code}")
print(f"✓ Description: {description}")
