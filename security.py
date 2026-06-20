"""
Security and authentication utilities.
Handles password hashing, JWT generation, and token validation for protected routes.
"""
from jose import jwt, JWTError
import bcrypt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status, Depends
from config import config
from fastapi.security import OAuth2PasswordBearer
from database import get_session
from models import User
from sqlmodel import select, Session

def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using bcrypt.
    
    Args:
        password (str): The plaintext password.
        
    Returns:
        str: The bcrypt hashed password string.
    """
    data_bytes = password.encode(config.ENCODING)
    hashed_bytes = bcrypt.hashpw(data_bytes, bcrypt.gensalt())
    return hashed_bytes.decode(config.ENCODING)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext password against a stored bcrypt hash.
    
    Args:
        plain_password (str): The plaintext password.
        hashed_password (str): The stored hash.
        
    Returns:
        bool: True if passwords match, False otherwise.
    """
    plain_bytes = plain_password.encode(config.ENCODING)
    hashed_bytes = hashed_password.encode(config.ENCODING)

    return bcrypt.checkpw(plain_bytes, hashed_bytes)

def create_access_token(data: dict) -> str:
    """
    Generates a new JSON Web Token (JWT) with an expiration time.
    
    Args:
        data (dict): The payload to encode in the token.
        
    Returns:
        str: The encoded JWT string.
    """
    to_encode = data.copy()

    token_expire_time = datetime.now(timezone.utc) + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp" : token_expire_time})

    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)

raw_token = OAuth2PasswordBearer("auth/login")

def get_current_user(user_token: str = Depends(raw_token), session: Session = Depends(get_session)) -> User:
    """
    Dependency injection function to retrieve the currently authenticated user.
    Validates the JWT token and fetches the user from the database.
    
    Args:
        user_token (str): The JWT extracted from the Authorization header.
        session (Session): The database session.
        
    Returns:
        User: The authenticated User object.
        
    Raises:
        HTTPException: If the token is invalid, expired, or the user no longer exists.
    """
    try:
        payload = jwt.decode(user_token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    user_db = session.exec(select(User).where(User.username == username)).first()
    if user_db is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    return user_db