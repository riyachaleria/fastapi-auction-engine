from database import get_session
from sqlmodel import Session
import pytest

def test_get_session_success():
    gen = get_session()
    session = next(gen)
    assert isinstance(session, Session)
    
    # Complete the generator
    with pytest.raises(StopIteration):
        next(gen)

def test_get_session_rollback():
    gen = get_session()
    session = next(gen)
    
    # Inject an error
    with pytest.raises(Exception, match="Database crashed"):
        gen.throw(Exception("Database crashed"))