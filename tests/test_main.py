"""
Integration tests for FastAPI core functionality.
Verifies lifespan events (startup/shutdown) and global exception handlers.
"""
from fastapi.testclient import TestClient
from main import app

def test_lifespan():
    """
    Using TestClient in a 'with' block explicitly triggers the FastAPI lifespan events.
    This will start and shutdown the scheduler, testing main.py lines 7-14.
    """
    with TestClient(app) as client:
        # The app is now running with lifespan events triggered
        pass

def test_global_exception_handler():
    """
    To test the global 500 exception handler without breaking our real code,
    we can inject a temporary route into the app that purposely crashes.
    """
    @app.get("/test-500-crash")
    def trigger_error():
        raise Exception("This is a deliberate crash for testing")
        
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/test-500-crash")
        
        # It should trigger the global_exception_handler in exceptions.py
        assert response.status_code == 500
        data = response.json()
        assert data["error"] is True
        assert data["message"] == "An unexpected server error occurred. Please try again later."
        assert data["path"] == "/test-500-crash"
