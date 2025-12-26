"""Industry and sector data fetching service."""

import yfinance as yf
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class IndustryService:
    """Service to fetch industry and sector data for symbols."""
    
    @staticmethod
    def fetch_industry_data(symbol: str) -> Dict[str, Optional[str]]:
        """
        Fetch industry and sector data for a symbol using yfinance.
        
        Returns dict with 'industry' and 'sector' keys.
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'industry': info.get('industry'),
                'sector': info.get('sector'),
                'company_name': info.get('longName') or info.get('shortName'),
            }
        except Exception as e:
            logger.error(f"Error fetching industry data for {symbol}: {e}")
            return {
                'industry': None,
                'sector': None,
                'company_name': None
            }
    
    @staticmethod
    def batch_fetch_industry_data(symbols: list[str]) -> Dict[str, Dict[str, Optional[str]]]:
        """
        Fetch industry data for multiple symbols.
        
        Returns dict mapping symbol -> industry data.
        """
        results = {}
        
        for symbol in symbols:
            results[symbol] = IndustryService.fetch_industry_data(symbol)
        
        return results
