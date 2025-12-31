"""Service for determining spread and position status (open/closed/orphaned/expired)."""

from typing import List, Dict, Set, Tuple
from datetime import datetime
from sqlmodel import Session, select
import logging

from app.models import Spread, Transaction, PositionStatus

logger = logging.getLogger(__name__)


class SpreadStatusService:
    """Service for analyzing and updating spread status."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def analyze_spread_status(self, spread: Spread) -> str:
        """
        Analyze a spread's status based on its legs AND related transactions.
        
        For spreads that only have closing legs, check if opening legs exist
        in other spreads for the same symbols/strikes/expirations.
        
        Returns: PositionStatus (OPEN, CLOSED, ORPHANED, EXPIRED)
        """
        # Get all legs for this spread
        legs = self.session.exec(
            select(Transaction).where(Transaction.spread_id == spread.id)
        ).all()
        
        if not legs:
            return PositionStatus.ORPHANED.value
        
        # Group legs by action type
        opening_legs = []
        closing_legs = []
        expired_legs = []
        
        for leg in legs:
            action = leg.action.upper() if leg.action else ""
            subtype = leg.subtype.upper() if leg.subtype else ""
            
            # Check for expiration FIRST (before checking action types)
            if "EXPIRATION" in subtype or "RECEIVE DELIVER" in subtype:
                expired_legs.append(leg)
            # Opening positions
            elif "BUY_TO_OPEN" in action or "SELL_TO_OPEN" in action:
                opening_legs.append(leg)
            # Closing positions (only if not already marked as expired)
            elif "BUY_TO_CLOSE" in action or "SELL_TO_CLOSE" in action:
                closing_legs.append(leg)
        
        # If we ONLY have closing legs, check if opening legs exist elsewhere
        if not opening_legs and closing_legs and not expired_legs:
            # Try to find matching opening transactions across ALL spreads
            for closing_leg in closing_legs:
                # Look for opening transaction with same symbol
                matching_open = self.session.exec(
                    select(Transaction).where(
                        Transaction.symbol == closing_leg.symbol,
                        Transaction.action.in_(['BUY_TO_OPEN', 'SELL_TO_OPEN']),
                        Transaction.datetime < closing_leg.datetime
                    ).order_by(Transaction.datetime.desc()).limit(1)
                ).first()
                
                if matching_open:
                    # Found matching opening - add to opening_legs for analysis
                    opening_legs.append(matching_open)
        
        # Determine status based on leg analysis
        has_opening = len(opening_legs) > 0
        has_closing = len(closing_legs) > 0
        has_expired = len(expired_legs) > 0
        
        # If all legs expired
        if has_expired and len(expired_legs) == len(legs):
            return PositionStatus.EXPIRED.value
        
        # If we have closing but no opening = orphaned
        if has_closing and not has_opening and not has_expired:
            return PositionStatus.ORPHANED.value
        
        # If we have opening and closing/expired for all legs = closed
        if has_opening:
            # Count unique symbols in opening legs
            opening_symbols = {leg.symbol for leg in opening_legs}
            
            # Check if all opening positions have corresponding closing/expiration
            all_closed = True
            for symbol in opening_symbols:
                # Find opening quantity for this symbol (absolute value)
                opening_qty = sum(
                    abs(leg.quantity) for leg in opening_legs 
                    if leg.symbol == symbol
                )
                
                # Find closing quantity (closing + expired) (absolute value)
                closing_qty = sum(
                    abs(leg.quantity) for leg in closing_legs + expired_legs
                    if leg.symbol == symbol
                )
                
                # If quantities don't match, position is still open
                # Allow small rounding errors
                if abs(opening_qty - closing_qty) > 0.01:
                    all_closed = False
                    break
            
            if all_closed and (has_closing or has_expired):
                return PositionStatus.CLOSED.value
        
        # Default to open if we have opening legs without full closing
        return PositionStatus.OPEN.value
    
    def update_spread_status(self, spread_id: int) -> Spread:
        """Update the status of a single spread."""
        spread = self.session.get(Spread, spread_id)
        if not spread:
            logger.warning(f"Spread {spread_id} not found")
            return None
        
        old_status = spread.status
        new_status = self.analyze_spread_status(spread)
        
        if old_status != new_status:
            spread.status = new_status
            spread.updated_at = datetime.utcnow()
            
            # Set closed_at timestamp if closing
            if new_status in [PositionStatus.CLOSED.value, PositionStatus.EXPIRED.value]:
                if not spread.closed_at:
                    # Find the latest transaction date as closed date
                    legs = self.session.exec(
                        select(Transaction).where(Transaction.spread_id == spread.id)
                    ).all()
                    if legs:
                        spread.closed_at = max(leg.datetime for leg in legs)
            
            self.session.add(spread)
            self.session.commit()
            self.session.refresh(spread)
            
            logger.info(f"Updated spread {spread_id}: {old_status} -> {new_status}")
        
        return spread
    
    def update_all_spread_statuses(self) -> Dict[str, int]:
        """
        Update status for all spreads in database.
        
        Returns: Dict with counts by status
        """
        spreads = self.session.exec(select(Spread)).all()
        
        status_counts = {
            PositionStatus.OPEN.value: 0,
            PositionStatus.CLOSED.value: 0,
            PositionStatus.ORPHANED.value: 0,
            PositionStatus.EXPIRED.value: 0,
        }
        
        for spread in spreads:
            self.update_spread_status(spread.id)
            status_counts[spread.status] = status_counts.get(spread.status, 0) + 1
        
        logger.info(f"Updated {len(spreads)} spreads: {status_counts}")
        return status_counts
    
    def calculate_realized_pnl(self, exclude_orphaned: bool = True) -> float:
        """
        Calculate realized P&L from closed spreads.
        
        Args:
            exclude_orphaned: If True, exclude orphaned positions from P&L
        """
        query = select(Spread).where(
            Spread.status.in_([PositionStatus.CLOSED.value, PositionStatus.EXPIRED.value])
        )
        
        if exclude_orphaned:
            # Also exclude orphaned from the calculation
            query = query.where(Spread.status != PositionStatus.ORPHANED.value)
        
        closed_spreads = self.session.exec(query).all()
        
        total_pnl = 0.0
        
        for spread in closed_spreads:
            # Get all legs and sum net amounts
            legs = self.session.exec(
                select(Transaction).where(Transaction.spread_id == spread.id)
            ).all()
            
            spread_pnl = sum(leg.net_amount for leg in legs)
            total_pnl += spread_pnl
        
        return total_pnl
    
    def get_spreads_by_status(self, status: str) -> List[Spread]:
        """Get all spreads with a specific status."""
        return list(self.session.exec(
            select(Spread).where(Spread.status == status)
        ).all())
