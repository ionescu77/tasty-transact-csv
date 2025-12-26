"""FastAPI routers for transaction management."""

from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select

from app.database import get_session_dependency
from app.services import TransactionService
from app.models import Transaction, Spread, Position
from app.position_tracker import PositionTracker

router = APIRouter()


@router.post("/api/upload")
async def upload_csv(
    file: UploadFile = File(...),
    account_name: str = Form("TastyTrade Main"),
    session: Session = Depends(get_session_dependency)
):
    """Upload and process CSV file."""
    content = await file.read()
    
    service = TransactionService(session)
    result = service.process_csv(content, account_name)
    
    return result


@router.get("/api/transactions")
def get_transactions(
    symbol: Optional[str] = Query(None),
    transaction_type: Optional[str] = Query(None),
    strategy_tag: Optional[str] = Query(None),
    limit: int = Query(1000, le=10000),  # Increased from 100 to 1000
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session_dependency)
):
    """Get transactions with filters."""
    service = TransactionService(session)
    transactions = service.get_transactions(
        symbol=symbol,
        transaction_type=transaction_type,
        strategy_tag=strategy_tag,
        limit=limit,
        offset=offset
    )
    
    return {
        "transactions": transactions,
        "count": len(transactions),
        "offset": offset,
        "limit": limit
    }


@router.get("/api/transactions/{transaction_id}")
def get_transaction(
    transaction_id: int,
    session: Session = Depends(get_session_dependency)
):
    """Get single transaction by ID."""
    transaction = session.get(Transaction, transaction_id)
    if not transaction:
        return {"error": "Transaction not found"}, 404
    
    return transaction


@router.put("/api/transactions/{transaction_id}/tags")
def update_transaction_tags(
    transaction_id: int,
    strategy_tag: Optional[str] = Form(None),
    industry_tag: Optional[str] = Form(None),
    comment: Optional[str] = Form(None),
    session: Session = Depends(get_session_dependency)
):
    """Update transaction tags."""
    service = TransactionService(session)
    
    try:
        transaction = service.update_transaction_tags(
            transaction_id=transaction_id,
            strategy_tag=strategy_tag,
            industry_tag=industry_tag,
            comment=comment
        )
        return transaction
    except ValueError as e:
        return {"error": str(e)}, 404


@router.get("/api/spreads")
def get_spreads(
    symbol: Optional[str] = Query(None),
    session: Session = Depends(get_session_dependency)
):
    """Get all option spreads with their legs."""
    query = select(Spread)
    
    # Filter by symbol if provided (case-insensitive partial match)
    if symbol:
        query = query.where(Spread.root_symbol.ilike(f"%{symbol}%"))
    
    query = query.order_by(Spread.created_at.desc())
    spreads = session.exec(query).all()
    
    result = []
    for spread in spreads:
        # Load legs
        legs = session.exec(
            select(Transaction).where(Transaction.spread_id == spread.id)
        ).all()
        
        # Calculate spread P&L
        total_pnl = sum(leg.net_amount for leg in legs)
        
        result.append({
            "id": spread.id,
            "created_at": spread.created_at,
            "root_symbol": spread.root_symbol,
            "description": spread.description,
            "legs": legs,
            "leg_count": len(legs),
            "total_pnl": total_pnl
        })
    
    return {"spreads": result, "count": len(result)}


@router.get("/api/positions")
def get_positions(
    account_id: Optional[int] = Query(None),
    session: Session = Depends(get_session_dependency)
):
    """Get current open positions."""
    query = select(Position).where(Position.quantity > 0)
    
    if account_id:
        query = query.where(Position.account_id == account_id)
    
    positions = session.exec(query).all()
    
    return {
        "positions": positions,
        "count": len(positions)
    }


@router.post("/api/positions/rebuild")
def rebuild_positions(
    account_id: int = Query(1),
    session: Session = Depends(get_session_dependency)
):
    """Rebuild positions from transactions."""
    tracker = PositionTracker(session)
    tracker.rebuild_positions(account_id)
    
    return {"status": "success", "message": "Positions rebuilt"}


@router.get("/api/analytics/summary")
def get_analytics_summary(
    account_id: int = Query(1),
    session: Session = Depends(get_session_dependency)
):
    """Get analytics summary with P&L and trade stats."""
    tracker = PositionTracker(session)
    
    # Get positions
    positions = tracker.get_current_positions(account_id)
    
    # Calculate realized P&L
    realized_pnl = tracker.calculate_realized_pnl(account_id)
    
    # Get transaction counts
    total_transactions = session.exec(
        select(Transaction).where(Transaction.account_id == account_id)
    ).all()
    
    # Count by type
    type_counts = {}
    for txn in total_transactions:
        type_counts[txn.type] = type_counts.get(txn.type, 0) + 1
    
    # Count spreads
    spread_count = len(session.exec(select(Spread)).all())
    
    return {
        "realized_pnl": realized_pnl,
        "open_positions_count": len(positions),
        "total_transactions": len(total_transactions),
        "transaction_types": type_counts,
        "spreads_count": spread_count,
        "positions": positions
    }
