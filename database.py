"""
Database engine configuration and session management.
Provides the primary connection to the PostgreSQL database.
"""
from typing import Generator
from sqlmodel import Session, create_engine

engine = create_engine("***REMOVED***", echo=False)

def get_session() -> Generator[Session, None, None]:  # pragma: no cover
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