"""
Pytest configuration and shared fixtures.
Sets up an isolated, in-memory SQLite database for safe, repeatable testing.
Overrides FastAPI dependencies and mocks outbound email services.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool
from main import app
from database import get_session
from unittest.mock import patch

# Create an in-memory SQLite database for testing
sqlite_url = "sqlite://"
engine = create_engine(
    sqlite_url, 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool
)

@pytest.fixture(name="session")
def session_fixture():
    """
    Creates fresh database tables before each test and drops them afterward.
    Yields a SQLModel Session connected to the in-memory SQLite DB.
    """
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        yield session
        
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(session: Session):
    """
    Provides a FastAPI TestClient with the database dependency mocked 
    to use the test session.
    """
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def mock_emails():
    """
    Automatically mocks all email sending functions across all tests
    to prevent spamming real email addresses during CI runs.
    """
    with patch("routes.auth.send_welcome_email") as mock_welcome, \
         patch("scheduler.send_auction_won_email") as mock_won, \
         patch("scheduler.send_item_sold_email") as mock_sold:
        yield mock_welcome, mock_won, mock_sold

@pytest.fixture(autouse=True)
def mock_db_engines():
    """
    Ensures the APScheduler module imports the test SQLite engine
    instead of the production Postgres engine.
    """
    with patch("scheduler.engine", new=engine):
        yield