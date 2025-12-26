"""Position tracking and P&L calculation."""

from typing import List, Dict, Any, Optional
from sqlmodel import Session, select
from datetime import datetime
from collections import defaultdict

from app.models import Transaction, Position


class PositionTracker:
    """Service to track positions and calculate P&L."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def rebuild_positions(self, account_id: int):
        """
        Rebuild all positions from transactions.
        Clears existing positions and recalculates from scratch.
        """
        # Clear existing positions for this account
        existing_positions = self.session.exec(
            select(Position).where(Position.account_id == account_id)
        ).all()
        
        for pos in existing_positions:
            self.session.delete(pos)
        
        # Get all transactions ordered by date
        transactions = self.session.exec(
            select(Transaction)
            .where(Transaction.account_id == account_id)
            .order_by(Transaction.datetime)
        ).all()
        
        # Track positions by symbol
        positions = defaultdict(lambda: {
            'quantity': 0.0,
            'total_cost': 0.0,
            'last_transaction': None
        })
        
        for txn in transactions:
            key = self._get_position_key(txn)
            
            if txn.type in ['stock_buy', 'option_buy']:
                # Opening or adding to position
                positions[key]['quantity'] += abs(txn.quantity)
                positions[key]['total_cost'] += abs(txn.net_amount)
                positions[key]['last_transaction'] = txn
                
            elif txn.type in ['stock_sell', 'option_sell_to_close']:
                # Closing or reducing position
                positions[key]['quantity'] -= abs(txn.quantity)
                # Proportionally reduce cost basis
                if positions[key]['quantity'] > 0:
                    cost_ratio = positions[key]['quantity'] / (positions[key]['quantity'] + abs(txn.quantity))
                    positions[key]['total_cost'] *= cost_ratio
                else:
                    positions[key]['total_cost'] = 0
                positions[key]['last_transaction'] = txn
        
        # Create Position records for open positions
        for key, data in positions.items():
            if data['quantity'] > 0.01:  # Only open positions
                txn = data['last_transaction']
                avg_price = data['total_cost'] / data['quantity'] if data['quantity'] > 0 else 0
                
                position = Position(
                    symbol=txn.symbol,
                    instrument_type=txn.instrument_type,
                    quantity=data['quantity'],
                    average_price=avg_price,
                    root_symbol=txn.root_symbol,
                    expiration_date=txn.expiration_date,
                    strike_price=txn.strike_price,
                    call_or_put=txn.call_or_put,
                    multiplier=txn.multiplier,
                    account_id=account_id,
                    updated_at=datetime.utcnow()
                )
                
                self.session.add(position)
        
        self.session.commit()
    
    def _get_position_key(self, txn: Transaction) -> str:
        """Generate unique key for position tracking."""
        if txn.instrument_type == 'Equity Option':
            return f"{txn.symbol}_{txn.expiration_date}_{txn.strike_price}_{txn.call_or_put}"
        else:
            return txn.symbol
    
    def calculate_realized_pnl(
        self,
        account_id: int,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> float:
        """
        Calculate realized P&L from closed positions.
        
        Matches buys with sells to calculate realized gains/losses.
        """
        query = select(Transaction).where(
            Transaction.account_id == account_id,
            Transaction.type.in_(['stock_sell', 'option_sell_to_close'])
        )
        
        if symbol:
            query = query.where(Transaction.symbol == symbol)
        if start_date:
            query = query.where(Transaction.datetime >= start_date)
        if end_date:
            query = query.where(Transaction.datetime <= end_date)
        
        closing_transactions = self.session.exec(query).all()
        
        total_pnl = 0.0
        
        for close_txn in closing_transactions:
            # Find corresponding opening transaction(s)
            # Simplified: assume FIFO matching
            proceeds = abs(close_txn.net_amount)
            
            # Get opening transactions for this symbol
            open_query = select(Transaction).where(
                Transaction.account_id == account_id,
                Transaction.symbol == close_txn.symbol,
                Transaction.datetime < close_txn.datetime,
                Transaction.type.in_(['stock_buy', 'option_buy'])
            ).order_by(Transaction.datetime)
            
            opening_txns = list(self.session.exec(open_query).all())
            
            # Match quantity
            remaining_qty = abs(close_txn.quantity)
            cost_basis = 0.0
            
            for open_txn in opening_txns:
                if remaining_qty <= 0:
                    break
                
                available_qty = abs(open_txn.quantity)
                match_qty = min(remaining_qty, available_qty)
                
                cost_basis += (abs(open_txn.net_amount) / available_qty) * match_qty
                remaining_qty -= match_qty
            
            # Calculate P&L
            pnl = proceeds - cost_basis
            total_pnl += pnl
        
        return total_pnl
    
    def get_current_positions(self, account_id: int) -> List[Position]:
        """Get all current open positions."""
        return list(self.session.exec(
            select(Position)
            .where(Position.account_id == account_id)
            .where(Position.quantity > 0)
        ).all())
