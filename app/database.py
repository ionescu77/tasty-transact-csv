"""Database initialization and session management."""

from sqlmodel import SQLModel, create_engine, Session
from contextlib import contextmanager
from typing import Generator

# SQLite database URL
DATABASE_URL = "sqlite:///./tastytrade.db"

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    connect_args={"check_same_thread": False}  # Needed for SQLite
)


def create_db_and_tables():
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Get database session context manager."""
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session_dependency():
    """FastAPI dependency to get database session."""
    with get_session() as session:
        yield session
