"""Symbol service for managing symbol master data."""

from datetime import datetime
from typing import Optional, List
from sqlmodel import Session, select
import logging

from app.models import Symbol
from app.industry_service import IndustryService

logger = logging.getLogger(__name__)


class SymbolService:
    """Service for managing symbol data."""
    
    def __init__(self, session: Session):
        self.session = session
        self.industry_service = IndustryService()
    
    def get_or_create_symbol(self, symbol: str, fetch_data: bool = True) -> Symbol:
        """
        Get existing symbol or create new one with industry data.
        
        Args:
            symbol: The symbol ticker
            fetch_data: Whether to fetch industry data from yfinance
        """
        # Check if symbol exists
        existing = self.session.exec(
            select(Symbol).where(Symbol.symbol == symbol)
        ).first()
        
        if existing:
            return existing
        
        # Create new symbol
        symbol_data = Symbol(
            symbol=symbol,
            created_at=datetime.utcnow()
        )
        
        # Fetch industry data if requested
        if fetch_data:
            try:
                industry_data = self.industry_service.fetch_industry_data(symbol)
                symbol_data.name = industry_data.get('company_name')
                symbol_data.sector = industry_data.get('sector')
                symbol_data.industry = industry_data.get('industry')
                symbol_data.last_updated = datetime.utcnow()
            except Exception as e:
                logger.warning(f"Could not fetch industry data for {symbol}: {e}")
        
        self.session.add(symbol_data)
        self.session.commit()
        self.session.refresh(symbol_data)
        
        return symbol_data
    
    def update_symbol_data(self, symbol: str, force: bool = False) -> Symbol:
        """
        Update symbol data from yfinance.
        
        Args:
            symbol: The symbol ticker
            force: Update even if recently updated
        """
        symbol_obj = self.get_or_create_symbol(symbol, fetch_data=False)
        
        # Check if update is needed
        if not force and symbol_obj.last_updated:
            # Don't update if updated within last 24 hours
            hours_since_update = (datetime.utcnow() - symbol_obj.last_updated).total_seconds() / 3600
            if hours_since_update < 24:
                return symbol_obj
        
        # Fetch fresh data
        try:
            industry_data = self.industry_service.fetch_industry_data(symbol)
            symbol_obj.name = industry_data.get('company_name')
            symbol_obj.sector = industry_data.get('sector')
            symbol_obj.industry = industry_data.get('industry')
            symbol_obj.last_updated = datetime.utcnow()
            
            self.session.add(symbol_obj)
            self.session.commit()
            self.session.refresh(symbol_obj)
        except Exception as e:
            logger.error(f"Failed to update symbol data for {symbol}: {e}")
        
        return symbol_obj
    
    def batch_update_symbols(self, symbols: List[str]) -> None:
        """Update multiple symbols in batch."""
        for symbol in symbols:
            try:
                self.update_symbol_data(symbol)
            except Exception as e:
                logger.error(f"Failed to update {symbol}: {e}")
    
    def get_symbols_needing_update(self, hours: int = 168) -> List[Symbol]:
        """
        Get symbols that haven't been updated recently.
        
        Args:
            hours: Number of hours threshold (default 1 week)
        """
        cutoff = datetime.utcnow()
        cutoff = cutoff.replace(hour=cutoff.hour - hours)
        
        query = select(Symbol).where(
            (Symbol.last_updated == None) | 
            (Symbol.last_updated < cutoff)
        )
        
        return list(self.session.exec(query).all())
