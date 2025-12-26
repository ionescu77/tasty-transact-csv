"""Transaction processing service."""

from typing import List, Dict, Any, Optional
from sqlmodel import Session, select
from datetime import datetime

from app.models import Account, Transaction, Spread
from app.csv_parser import read_csv_content
from app.classifier import classify_transaction
from app.spreads import group_spreads


class TransactionService:
    """Service for processing and managing transactions."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def process_csv(
        self,
        content: bytes,
        account_name: str = "TastyTrade Main"
    ) -> Dict[str, Any]:
        """
        Process uploaded CSV file:
        1. Parse CSV
        2. Classify transactions
        3. Group spreads
        4. Save to database
        
        Returns summary dict with counts.
        """
        # Get or create account
        account = self._get_or_create_account(account_name)
        
        # Parse CSV
        parsed_transactions = read_csv_content(content)
        
        # Classify each transaction
        for txn in parsed_transactions:
            txn['classified_type'] = classify_transaction(txn)
        
        # Group spreads
        spread_groups = group_spreads(parsed_transactions)
        
        # Track which transactions are in spreads
        spread_txn_ids = set()
        for legs, _ in spread_groups:
            for leg in legs:
                spread_txn_ids.add(id(leg))
        
        # Save spreads
        spread_map = {}  # Map transaction to spread
        for legs, description in spread_groups:
            spread = Spread(
                created_at=legs[0]['datetime'],
                root_symbol=legs[0]['root_symbol'],
                description=description
            )
            self.session.add(spread)
            self.session.flush()  # Get spread ID
            
            for leg in legs:
                spread_map[id(leg)] = spread.id
        
        # Save transactions
        saved_count = 0
        updated_count = 0
        
        for parsed in parsed_transactions:
            # Check if transaction already exists
            existing = self.session.exec(
                select(Transaction).where(
                    Transaction.txn_id == parsed['txn_id'],
                    Transaction.datetime == parsed['datetime'],
                    Transaction.symbol == parsed['symbol']
                )
            ).first()
            
            if existing:
                # Update existing transaction
                self._update_transaction(existing, parsed, account.id, spread_map.get(id(parsed)))
                updated_count += 1
            else:
                # Create new transaction
                txn = self._create_transaction(parsed, account.id, spread_map.get(id(parsed)))
                self.session.add(txn)
                saved_count += 1
        
        self.session.commit()
        
        return {
            'account': account_name,
            'new_transactions': saved_count,
            'updated_transactions': updated_count,
            'spreads_created': len(spread_groups),
            'total_processed': len(parsed_transactions)
        }
    
    def _get_or_create_account(self, name: str) -> Account:
        """Get existing account or create new one."""
        account = self.session.exec(
            select(Account).where(Account.name == name)
        ).first()
        
        if not account:
            account = Account(name=name)
            self.session.add(account)
            self.session.commit()
            self.session.refresh(account)
        
        return account
    
    def _create_transaction(
        self,
        parsed: Dict[str, Any],
        account_id: int,
        spread_id: Optional[int]
    ) -> Transaction:
        """Create Transaction model from parsed data."""
        return Transaction(
            txn_id=parsed['txn_id'],
            datetime=parsed['datetime'],
            type=parsed['classified_type'],
            subtype=parsed['subtype'],
            action=parsed['action'],
            symbol=parsed['symbol'],
            instrument_type=parsed['instrument_type'],
            description=parsed['description'],
            value=parsed['value'],
            quantity=parsed['quantity'],
            price=parsed['price'],
            commissions=parsed['commissions'],
            fees=parsed['fees'],
            multiplier=parsed['multiplier'],
            root_symbol=parsed['root_symbol'],
            underlying_symbol=parsed['underlying_symbol'],
            expiration_date=parsed['expiration_date'],
            strike_price=parsed['strike_price'],
            call_or_put=parsed['call_or_put'],
            net_amount=parsed['net_amount'],
            currency=parsed['currency'],
            account_id=account_id,
            spread_id=spread_id
        )
    
    def _update_transaction(
        self,
        transaction: Transaction,
        parsed: Dict[str, Any],
        account_id: int,
        spread_id: Optional[int]
    ):
        """Update existing transaction with new data."""
        transaction.type = parsed['classified_type']
        transaction.subtype = parsed['subtype']
        transaction.action = parsed['action']
        transaction.value = parsed['value']
        transaction.quantity = parsed['quantity']
        transaction.price = parsed['price']
        transaction.commissions = parsed['commissions']
        transaction.fees = parsed['fees']
        transaction.net_amount = parsed['net_amount']
        transaction.spread_id = spread_id
        transaction.updated_at = datetime.utcnow()
    
    def get_transactions(
        self,
        account_id: Optional[int] = None,
        symbol: Optional[str] = None,
        transaction_type: Optional[str] = None,
        strategy_tag: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Transaction]:
        """Get transactions with filters."""
        query = select(Transaction)
        
        if account_id:
            query = query.where(Transaction.account_id == account_id)
        if symbol:
            # Case-insensitive partial match for symbol, root_symbol, or underlying_symbol
            query = query.where(
                (Transaction.symbol.ilike(f"%{symbol}%")) |
                (Transaction.root_symbol.ilike(f"%{symbol}%")) |
                (Transaction.underlying_symbol.ilike(f"%{symbol}%"))
            )
        if transaction_type:
            query = query.where(Transaction.type == transaction_type)
        if strategy_tag:
            query = query.where(Transaction.strategy_tag == strategy_tag)
        if start_date:
            query = query.where(Transaction.datetime >= start_date)
        if end_date:
            query = query.where(Transaction.datetime <= end_date)
        
        query = query.order_by(Transaction.datetime.desc())
        query = query.offset(offset).limit(limit)
        
        return list(self.session.exec(query).all())
    
    def update_transaction_tags(
        self,
        transaction_id: int,
        strategy_tag: Optional[str] = None,
        industry_tag: Optional[str] = None,
        comment: Optional[str] = None
    ):
        """Update manual tags on a transaction."""
        transaction = self.session.get(Transaction, transaction_id)
        
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        if strategy_tag is not None:
            transaction.strategy_tag = strategy_tag
        if industry_tag is not None:
            transaction.industry_tag = industry_tag
        if comment is not None:
            transaction.comment = comment
        
        transaction.updated_at = datetime.utcnow()
        self.session.commit()
        
        return transaction
