"""
Authentication business logic.
Handles database interactions for user registration and login.
"""
from fastapi import status, HTTPException
from sqlmodel import Session, select
from models import User
from schema import Usercreate
from fastapi.security import OAuth2PasswordRequestForm
from security import hash_password, verify_password, create_access_token

def do_signup(user_data: Usercreate, session: Session) -> str:
    """
    Registers a new user, hashes their password, and issues an access token.
    
    Args:
        user_data (Usercreate): The sanitized registration payload.
        session (Session): The database session.
        
    Returns:
        str: A newly minted JWT access token.
        
    Raises:
        HTTPException: If the username or email is already taken.
    """
    existing_user = session.exec(select(User).where(User.username == user_data.username)).first()

    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
    
    existing_email = session.exec(select(User).where(User.email == user_data.email)).first()

    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email already taken")
    
    hashed_pass = hash_password(user_data.password)

    user_db = User(username=user_data.username, email=user_data.email, hashed_password=hashed_pass)
    session.add(user_db)
    session.commit()
    session.refresh(user_db)

    token = create_access_token({'sub' : user_data.username})
    return token

def do_login(foam_data: OAuth2PasswordRequestForm, session: Session) -> str:
    """
    Authenticates a user via username and password, returning an access token.
    
    Args:
        foam_data (OAuth2PasswordRequestForm): The login payload.
        session (Session): The database session.
        
    Returns:
        str: A newly minted JWT access token.
        
    Raises:
        HTTPException: If the credentials are invalid.
    """
    db_user = session.exec(select(User).where(User.username == foam_data.username)).first()
    
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    
    is_password_correct = verify_password(foam_data.password, db_user.hashed_password)
    
    if not is_password_correct:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    
    raw_token = create_access_token({'sub' : db_user.username})
    return raw_token