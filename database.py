"""
Database engine configuration and session management.
Provides the primary connection to the PostgreSQL database.
"""
from typing import Generator
from sqlmodel import Session, create_engine
from config import config
engine = create_engine(config.DATABASE_URI, echo=False)
def get_session() -> Generator[Session, None, None]:
    """
    Dependency injection function for FastAPI routes.
    Yields a database session and safely rolls back in case of an error.
    
    Returns:
        Generator[Session, None, None]: A SQLModel database session.
    """
    with Session(engine) as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise