"""Database models for the TastyTrade transaction analyzer."""

from datetime import datetime as DateTime
from typing import Optional, List
from enum import Enum
from sqlmodel import SQLModel, Field, JSON, Column
from pydantic import ConfigDict


class PositionStatus(str, Enum):
    """Status of a position or spread."""
    OPEN = "open"
    CLOSED = "closed"
    ORPHANED = "orphaned"
    EXPIRED = "expired"


class Symbol(SQLModel, table=True):
    """Symbol master data with industry classification."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    __tablename__: str = "symbols"
    
    symbol: str = Field(primary_key=True, index=True)
    name: Optional[str] = None  # Company/ETF name
    sector: Optional[str] = Field(default=None, index=True)
    industry: Optional[str] = Field(default=None, index=True)
    last_price: Optional[float] = None
    last_updated: Optional[DateTime] = None
    created_at: DateTime = Field(default_factory=lambda: DateTime.utcnow())


class Account(SQLModel, table=True):
    """Brokerage account."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    __tablename__: str = "accounts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # Account code (e.g., x5WY77777)
    description: Optional[str] = None  # Filename metadata (e.g., "tastytrade transactions history 250101 to 251125")
    created_at: DateTime = Field(default_factory=lambda: DateTime.utcnow())
    updated_at: DateTime = Field(default_factory=lambda: DateTime.utcnow())


class Spread(SQLModel, table=True):
    """Option spread composed of multiple legs."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    __tablename__: str = "spreads"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: DateTime = Field(index=True)
    root_symbol: str = Field(index=True)
    description: Optional[str] = None  # Auto-generated description
    
    # Status tracking
    status: str = Field(default=PositionStatus.OPEN.value, index=True)  # open, closed, orphaned, expired
    closed_at: Optional[DateTime] = None
    
    # Manual annotations
    comment: Optional[str] = None  # User comment with timestamp
    comment_updated_at: Optional[DateTime] = None
    tags: Optional[str] = Field(default=None, sa_column=Column(JSON))  # JSON array: ["core", "value", "speculative"]
    
    # Metadata
    updated_at: DateTime = Field(default_factory=lambda: DateTime.utcnow())


class Transaction(SQLModel, table=True):
    """Individual transaction from CSV."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    __tablename__: str = "transactions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # CSV fields
    txn_id: str = Field(index=True)  # Order #
    datetime: DateTime = Field(index=True)  # Stored in UTC
    type: str = Field(index=True)  # Classified type (e.g., "option_buy")
    subtype: str  # Raw CSV Sub Type
    action: str  # Raw CSV Action
    symbol: str = Field(index=True)
    instrument_type: str  # Equity, Equity Option, etc.
    description: str
    value: float  # Raw Value from CSV
    quantity: float
    price: float  # Average Price
    commissions: float
    fees: float
    multiplier: Optional[int] = None
    root_symbol: Optional[str] = Field(default=None, index=True)
    underlying_symbol: Optional[str] = None
    expiration_date: Optional[str] = None  # For options
    strike_price: Optional[float] = None
    call_or_put: Optional[str] = None
    net_amount: float  # Total
    currency: str
    
    # Manual tags (strategy_tag kept for backward compatibility)
    strategy_tag: Optional[str] = Field(default=None, index=True)
    comment: Optional[str] = None
    
    # Foreign keys
    account_id: int = Field(foreign_key="accounts.id", index=True)
    spread_id: Optional[int] = Field(default=None, foreign_key="spreads.id", index=True)
    
    # Metadata
    created_at: DateTime = Field(default_factory=lambda: DateTime.utcnow())
    updated_at: DateTime = Field(default_factory=lambda: DateTime.utcnow())


class Position(SQLModel, table=True):
    """Current open positions."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    __tablename__: str = "positions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    instrument_type: str  # Equity, Equity Option
    quantity: float
    average_price: float
    current_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    
    # For options
    root_symbol: Optional[str] = Field(default=None, index=True)
    expiration_date: Optional[str] = None
    strike_price: Optional[float] = None
    call_or_put: Optional[str] = None
    multiplier: Optional[int] = None
    
    # Status tracking
    status: str = Field(default=PositionStatus.OPEN.value, index=True)
    
    # Manual annotations
    tags: Optional[str] = Field(default=None, sa_column=Column(JSON))  # JSON array: ["core", "value", "growth", "speculative"]
    
    # Metadata
    account_id: int = Field(foreign_key="accounts.id", index=True)
    opened_at: Optional[DateTime] = None
    closed_at: Optional[DateTime] = None
    updated_at: DateTime = Field(default_factory=lambda: DateTime.utcnow())


class TradeMetrics(SQLModel, table=True):
    """Aggregated metrics for trade analysis."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    __tablename__: str = "trade_metrics"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    root_symbol: Optional[str] = Field(default=None, index=True)
    strategy_tag: Optional[str] = Field(default=None, index=True)
    
    # P&L metrics
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    total_pnl: float = 0.0
    
    # Trade stats
    num_trades: int = 0
    win_rate: Optional[float] = None
    avg_trade_duration_days: Optional[float] = None
    
    # Period
    period_start: DateTime
    period_end: DateTime
    
    # Metadata
    account_id: int = Field(foreign_key="accounts.id", index=True)
    updated_at: DateTime = Field(default_factory=lambda: DateTime.utcnow())
