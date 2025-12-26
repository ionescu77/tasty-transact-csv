"""Database models for the TastyTrade transaction analyzer."""

from datetime import datetime as DateTime
from typing import Optional, List
from sqlmodel import SQLModel, Field
from pydantic import ConfigDict


class Account(SQLModel, table=True):
    """Brokerage account."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    __tablename__: str = "accounts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    created_at: DateTime = Field(default_factory=lambda: DateTime.utcnow())


class Spread(SQLModel, table=True):
    """Option spread composed of multiple legs."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    __tablename__: str = "spreads"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: DateTime = Field(index=True)
    root_symbol: str = Field(index=True)
    description: Optional[str] = None


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
    
    # Manual tags
    strategy_tag: Optional[str] = Field(default=None, index=True)
    industry_tag: Optional[str] = Field(default=None, index=True)
    sector_tag: Optional[str] = None
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
    
    # Metadata
    account_id: int = Field(foreign_key="accounts.id", index=True)
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
