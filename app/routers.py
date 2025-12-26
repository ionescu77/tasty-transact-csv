"""FastAPI routers for transaction management."""

from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session

from app.database import get_session_dependency
from app.services import TransactionService
from app.models import Transaction

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
    limit: int = Query(100, le=1000),
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
