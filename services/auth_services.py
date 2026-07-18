"""
Authentication business logic.
Handles database interactions for user registration and login.
"""
from fastapi import status, HTTPException
from sqlmodel import Session, select
from models import User,RefreshToken,OTP_Table
from schema import Usercreate
from fastapi.security import OAuth2PasswordRequestForm
from security import hash_password, verify_password, create_access_token,create_refresh_token,decode_refresh_token,create_password_reset_token,verify_password_reset_token
from datetime import datetime,timezone,timedelta
from config import config
import secrets

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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is already taken.")
    
    existing_email = session.exec(select(User).where(User.email == user_data.email)).first()

    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email address is already registered.")
    
    hashed_pass = hash_password(user_data.password)

    user_db = User(username=user_data.username, email=user_data.email, hashed_password=hashed_pass)
    session.add(user_db)
    session.commit()
    session.refresh(user_db)

    token = create_access_token({'sub' : user_data.username})
    refresh_token,jti,expires_at = create_refresh_token({'sub' : user_data.username})

    ref_token = RefreshToken(
        jti=jti,
        user_id=user_db.id,
        expires_at=expires_at,
    )

    session.add(ref_token)
    session.commit()

    return (token,refresh_token)

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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")
    
    is_password_correct = verify_password(foam_data.password, db_user.hashed_password)
    
    if not is_password_correct:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")
    
    raw_token = create_access_token({'sub' : db_user.username})
    refresh_token,jti,expires_at = create_refresh_token({'sub' : db_user.username})

    ref_token = RefreshToken(
        jti=jti,
        user_id=db_user.id,
        expires_at=expires_at,
    )

    session.add(ref_token)
    session.commit()

    return (raw_token,refresh_token)

def do_logout(refresh_token: str, session: Session) -> None:
    """
    Revokes a specific session refresh token upon user logout.
    
    Args:
        refresh_token (str): The raw JWT refresh token to revoke.
        session (Session): The database session.
        
    Raises:
        HTTPException: If the token is invalid, expired, or has already been revoked.
    """
    payload = decode_refresh_token(refresh_token=refresh_token)

    jti= payload.get("jti")

    token = session.exec(select(RefreshToken).where(RefreshToken.jti == jti)).first()

    if not token or token.is_revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has expired, is invalid, or has already been revoked.")
    
    token.is_revoked = True
    session.commit()

def do_logout_all(refresh_token: str, session: Session) -> None:
    """
    Revokes all active refresh tokens associated with a user, logging them out of every device/session simultaneously.
    
    Args:
        refresh_token (str): Any valid, active JWT refresh token belonging to the target user.
        session (Session): The database session.
        
    Raises:
        HTTPException: If the provided token is invalid, expired, or has already been revoked.
    """
    payload = decode_refresh_token(refresh_token=refresh_token)

    jti = payload.get("jti")
    token = session.exec(select(RefreshToken).where(RefreshToken.jti == jti)).first()

    if not token or token.is_revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has expired, is invalid, or has already been revoked.")
    
    users = session.exec(select(RefreshToken).where(RefreshToken.user_id == token.user_id)).all()

    for user in users:
        user.is_revoked = True
    session.commit()

def do_refresh(refresh_token: str, session: Session) -> tuple[str, str | None]:
    """
    Refreshes an access token using a valid refresh token.
    Implements sliding window rotation: issues a new refresh token and revokes the old one if within the rotation window.
    
    Args:
        refresh_token (str): The raw JWT refresh token string.
        session (Session): The database session.
        
    Returns:
        tuple[str, str | None]: A tuple containing:
            - str: A newly minted JWT access token.
            - str | None: A newly rotated JWT refresh token if within the sliding window, or None otherwise.
            
    Raises:
        HTTPException: If the refresh token is expired, revoked, invalid, or the user account no longer exists.
    """
    payload = decode_refresh_token(refresh_token=refresh_token)

    jti = payload.get("jti")
    username = payload.get("sub")

    token = session.exec(select(RefreshToken).where(RefreshToken.jti == jti)).first()

    if not token or token.is_revoked or token.expires_at < datetime.now(timezone.utc).replace(tzinfo=None) :
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has expired or been revoked.")
    
    user_db = session.exec(select(User).where(User.username == username)).first()

    if user_db is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account associated with this token no longer exists.")
    
    remaining_days = (token.expires_at - datetime.now(timezone.utc).replace(tzinfo=None)).days

    access_token = create_access_token({"sub" : user_db.username})

    if remaining_days <= config.REFRESH_TOKEN_EXPIRE_WINDOW:
        token.is_revoked = True
        ref_token,jti,exp_time = create_refresh_token({"sub" : user_db.username})

        raw_refresh_token = RefreshToken(
            jti=jti,
            user_id=user_db.id,
            expires_at=exp_time
        )

        session.add(raw_refresh_token)
        session.commit()

        return (access_token,ref_token)
    
    return (access_token,None)

def do_forget_password(email: str, session: Session) -> int | None:
    """
    Initiates the password recovery workflow for a registered user address by generating a secure 6-digit verification code.
    
    Args:
        email (str): The email address requesting password recovery.
        session (Session): The database session.
        
    Returns:
        int | None: The generated 6-digit numeric OTP code if the email is registered, or None otherwise.
    """
    user_db = session.exec(select(User).where(User.email == email)).first()

    if user_db is None:
        return None
    
    otp_code = secrets.randbelow(900000) + 100000
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=config.OTP_EXPIRE_TIME)

    otp_record = OTP_Table(email=email, otp_code=str(otp_code), expires_at=expires_at)
    session.add(otp_record)
    session.commit()

    return otp_code

def do_verify_otp(email: str, otpcode: str, session: Session) -> str:
    """
    Verifies a one-time verification code (OTP) and issues a short-lived authorization token for password resetting.
    Consumes and removes the verification record upon success.
    
    Args:
        email (str): The email address associated with the recovery request.
        otpcode (str): The 6-digit numeric string submitted by the user.
        session (Session): The database session.
        
    Returns:
        str: A short-lived JWT reset token authorized exclusively for password resetting.
        
    Raises:
        HTTPException: If the account/email is invalid, the code does not match, or the code has expired.
    """
    user_db = session.exec(select(User).where(User.email == email)).first()

    if user_db is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email address or verification code.")
    
    otp_db = session.exec(select(OTP_Table).where(OTP_Table.email == user_db.email, OTP_Table.otp_code == otpcode)).first()

    if otp_db is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Verification code is incorrect.")
    
    if otp_db.expires_at < datetime.now(timezone.utc).replace(tzinfo=None) or otp_db.is_used:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Verification code has expired.")

    session.delete(otp_db)
    session.commit()

    token = create_password_reset_token({"sub" : user_db.username})
    
    return token

def do_reset_password(password: str, reset_short_token: str, session: Session) -> tuple[str, str]:
    """
    Applies a new password to a user account using a verified reset token and immediately issues fresh session credentials.
    
    Args:
        password (str): The chosen replacement plaintext password (pre-validated by schema).
        reset_short_token (str): The authorization reset JWT issued after successful OTP verification.
        session (Session): The database session.
        
    Returns:
        tuple[str, str]: A tuple containing:
            - str: A newly minted JWT access token for immediate login.
            - str: A newly minted JWT refresh token.
            
    Raises:
        HTTPException: If the reset authorization token is invalid, expired, or the user account no longer exists.
    """
    username = verify_password_reset_token(reset_short_token)

    user_db = session.exec(select(User).where(User.username == username)).first()

    if user_db is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Password reset authorization token is invalid or has expired.")
    
    hashed_pass = hash_password(password=password)

    user_db.hashed_password = hashed_pass

    access_token = create_access_token({"sub" : user_db.username})
    refresh_token,jti,expires_at = create_refresh_token({'sub' : user_db.username})

    ref_token = RefreshToken(
        jti=jti,
        user_id=user_db.id,
        expires_at=expires_at,
    )

    session.add_all([user_db, ref_token])
    session.commit()

    return (access_token,refresh_token)