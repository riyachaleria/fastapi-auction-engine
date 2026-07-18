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
from uuid import uuid4

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
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
        
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
    
    user_db = session.exec(select(User).where(User.username == username)).first()
    if user_db is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account associated with this token no longer exists.")
    return user_db

def create_refresh_token(data: dict) -> tuple[str, str, datetime]:
    """
    Generates a long-lived JWT refresh token with a unique UUID (`jti`) and `type="refresh"` claim.
    
    Args:
        data (dict): The payload dictionary containing user identification (e.g., `{"sub": username}`).
        
    Returns:
        tuple[str, str, datetime]: A tuple containing:
            - str: The encoded JWT refresh token string.
            - str: The unique JWT ID (`jti`) assigned to this token.
            - datetime: The UTC expiration datetime of the token.
    """
    jti = str(uuid4())
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS)

    payload = data.copy()
    payload.update({"jti" : jti,"exp" : expires_at,"type" : "refresh"})

    refresh_token = jwt.encode(payload,config.SECRET_KEY,algorithm=config.ALGORITHM)

    return (refresh_token,jti,expires_at)

def decode_refresh_token(refresh_token: str) -> dict:
    """
    Decodes and validates a JWT refresh token, verifying cryptographic signature and required claims.
    
    Args:
        refresh_token (str): The raw JWT refresh token string.
        
    Returns:
        dict: The decoded token payload dictionary containing claims (`sub`, `jti`, `type`, `exp`).
        
    Raises:
        HTTPException: If the token signature is invalid, expired, or missing essential `jti`/`sub`/`type="refresh"` claims.
    """
    try:
        payload = jwt.decode(refresh_token, config.SECRET_KEY, algorithms=[config.ALGORITHM])

        if "jti" not in payload or "sub" not in payload or payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid or malformed.")
        
        return payload
    
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid or malformed.")
    
def create_password_reset_token(data: dict) -> str:
    """
    Generates a short-lived authorization JWT for executing a password reset after OTP verification.
    
    Args:
        data (dict): The payload dictionary containing user subject (e.g., `{"sub": username}`).
        
    Returns:
        str: The encoded short-lived JWT string containing `purpose="password_reset"` claim.
    """
    payload = data.copy()
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=config.PASSWORD_RESET_TOKEN_MINUTES)

    payload.update({"exp" : expires_at, "purpose" : "password_reset"})

    raw_token = jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)

    return raw_token

def verify_password_reset_token(token: str) -> str:
    """
    Verifies the validity and purpose claim of a short-lived password reset authorization token.
    
    Args:
        token (str): The short-lived JWT authorization string.
        
    Returns:
        str: The username extracted from the `sub` claim.
        
    Raises:
        HTTPException: If the token is invalid, expired, or lacks the required `purpose="password_reset"` claim.
    """
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])

        if "sub" not in payload or "purpose" not in payload or payload.get("purpose") != "password_reset":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Password reset token is invalid or has expired.")

        username = payload.get("sub")

        return username
    
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Password reset token is invalid or has expired.")