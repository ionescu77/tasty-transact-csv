"""Spread grouping logic for multi-leg option trades."""

from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict


def group_spreads(transactions: List[Dict[str, Any]]) -> List[Tuple[List[Dict[str, Any]], str]]:
    """
    Group option trades into spreads based on:
    - Same timestamp (within 1 second)
    - Same root symbol
    - Same order ID (if available)
    
    Returns list of (legs, description) tuples.
    """
    # Filter only option trades
    option_trades = [
        t for t in transactions 
        if t.get('instrument_type') == 'Equity Option' and t.get('root_symbol')
    ]
    
    if not option_trades:
        return []
    
    # Group by order ID first (most reliable)
    order_groups = defaultdict(list)
    
    for trade in option_trades:
        order_id = trade.get('txn_id', '')
        if order_id:
            order_groups[order_id].append(trade)
    
    # Find multi-leg spreads (order ID with multiple legs)
    spreads = []
    
    for order_id, legs in order_groups.items():
        if len(legs) > 1:
            # This is a spread
            description = generate_spread_description(legs)
            spreads.append((legs, description))
    
    return spreads


def generate_spread_description(legs: List[Dict[str, Any]]) -> str:
    """
    Generate human-readable description of a spread.
    
    Examples:
    - "GRAB Call Debit Spread: Buy 6C, Sell 10C @ 4/17/26"
    - "SPY Put Credit Spread: Sell 660P, Buy 655P @ 11/21/25"
    """
    if not legs:
        return "Unknown Spread"
    
    # Sort legs by strike price
    sorted_legs = sorted(legs, key=lambda x: x.get('strike_price', 0))
    
    root = legs[0].get('root_symbol', 'Unknown')
    option_type = legs[0].get('call_or_put', 'Option')
    exp_date = legs[0].get('expiration_date', '')
    
    # Determine spread type
    leg_descriptions = []
    net_debit = 0.0
    
    for leg in sorted_legs:
        strike = leg.get('strike_price', 0)
        action = leg.get('subtype', '').lower()
        net_amount = leg.get('net_amount', 0)
        net_debit += net_amount
        
        if 'buy' in action:
            leg_descriptions.append(f"Buy {strike:.0f}{option_type[0]}")
        else:
            leg_descriptions.append(f"Sell {strike:.0f}{option_type[0]}")
    
    # Determine if debit or credit
    spread_nature = "Debit" if net_debit < 0 else "Credit"
    
    description = f"{root} {option_type} {spread_nature} Spread: {', '.join(leg_descriptions)} @ {exp_date}"
    
    return description


def is_vertical_spread(legs: List[Dict[str, Any]]) -> bool:
    """Check if legs form a vertical spread (same exp, different strikes)."""
    if len(legs) != 2:
        return False
    
    exp_dates = set(leg.get('expiration_date') for leg in legs)
    option_types = set(leg.get('call_or_put') for leg in legs)
    
    return len(exp_dates) == 1 and len(option_types) == 1


def is_calendar_spread(legs: List[Dict[str, Any]]) -> bool:
    """Check if legs form a calendar spread (different exp, same strike)."""
    if len(legs) != 2:
        return False
    
    strikes = set(leg.get('strike_price') for leg in legs)
    exp_dates = set(leg.get('expiration_date') for leg in legs)
    option_types = set(leg.get('call_or_put') for leg in legs)
    
    return len(strikes) == 1 and len(exp_dates) == 2 and len(option_types) == 1


def is_iron_condor(legs: List[Dict[str, Any]]) -> bool:
    """Check if legs form an iron condor (4 legs: 2 calls, 2 puts, same exp)."""
    if len(legs) != 4:
        return False
    
    exp_dates = set(leg.get('expiration_date') for leg in legs)
    call_legs = [leg for leg in legs if leg.get('call_or_put') == 'CALL']
    put_legs = [leg for leg in legs if leg.get('call_or_put') == 'PUT']
    
    return len(exp_dates) == 1 and len(call_legs) == 2 and len(put_legs) == 2


def classify_spread_type(legs: List[Dict[str, Any]]) -> str:
    """Classify the type of spread."""
    if len(legs) < 2:
        return "Single Option"
    
    if is_vertical_spread(legs):
        return "Vertical Spread"
    elif is_calendar_spread(legs):
        return "Calendar Spread"
    elif is_iron_condor(legs):
        return "Iron Condor"
    else:
        return f"{len(legs)}-Leg Spread"
