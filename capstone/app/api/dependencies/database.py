"""Database dependency."""
from sqlalchemy.orm import Session

from app.db.session import SessionLocal


def get_db() -> Session:
    """
    Get a database session for dependency injection.
    
    Yields:
        SQLAlchemy Session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
