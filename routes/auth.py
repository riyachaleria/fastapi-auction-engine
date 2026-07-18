"""
Authentication endpoints.
Provides routes for user registration and JWT login.
"""
from fastapi import APIRouter, status, Depends, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from database import get_session
from sqlmodel import Session
from services.auth_services import do_login, do_signup,do_logout,do_logout_all,do_refresh,do_forget_password,do_reset_password,do_verify_otp
from services.email_services import send_welcome_email
from schema import Usercreate,RefreshTokenRequest,ForgetPasswordRequest,VerifyOTPRequest,ResetPasswordRequest
from services.auth_email_services import send_otp_email_via_brevo

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(user_data: Usercreate, bg_tasks: BackgroundTasks, session: Session = Depends(get_session)) -> dict:
    """
    Register a new user and return an access token.
    Triggers a background task to send a welcome email.

    Request body (JSON):
        username : str — Unique identifier
        email    : str — Valid email address
        password : str — Must contain 8+ chars, 1 number, 1 special char

    Returns:
        201 — User created, returns JWT access token
        400 — Username or email already taken
        422 — Validation error (e.g., weak password)
    """
    token, refresh_token = do_signup(user_data, session)

    bg_tasks.add_task(send_welcome_email, username=user_data.username, user_email=user_data.email)

    return {'access_token' : token, 'refresh_token' : refresh_token, 'token_type' : 'bearer', 'message' : 'You have successfully logged in.'}

@router.post("/login", status_code=status.HTTP_200_OK)
def login(foam_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)) -> dict:
    """
    Authenticate a user and return an access token.

    Form Data:
        username : str
        password : str

    Returns:
        200 — Login successful, returns JWT access token
        401 — Invalid username or password
    """
    token, refresh_token = do_login(foam_data, session)

    return {'access_token' : token, 'refresh_token' : refresh_token, 'token_type' : 'bearer'}

@router.post("/logout", status_code=status.HTTP_200_OK)
def log_out(refresh_token: RefreshTokenRequest, session: Session = Depends(get_session)) -> dict:
    """
    Revokes the specific refresh token associated with the current session.
    
    Request Body (JSON):
        refresh_token : str — The JWT refresh token string
        
    Returns:
        200 — Token successfully revoked
        401 — Unauthorized (invalid, expired, or already revoked token)
    """
    do_logout(refresh_token.refresh_token, session)

    return {'message' : 'You have successfully logged out.'}

@router.post("/logout-all", status_code=status.HTTP_200_OK)
def log_out_all(refresh_token: RefreshTokenRequest, session: Session = Depends(get_session)) -> dict:
    """
    Revokes all active refresh tokens belonging to the user across every logged-in device or session.
    
    Request Body (JSON):
        refresh_token : str — Any valid JWT refresh token belonging to the user
        
    Returns:
        200 — All user sessions successfully revoked across all devices
        401 — Unauthorized (invalid, expired, or already revoked token)
    """
    do_logout_all(refresh_token.refresh_token, session)

    return {'message' : 'You have successfully logged out from all devices.'}

@router.post("/refresh", status_code=status.HTTP_200_OK)
def refresh(refresh_token: RefreshTokenRequest, session: Session = Depends(get_session)) -> dict:
    """
    Issue a new JWT access token using a valid refresh token.
    Rotates the refresh token if it is within the configured sliding expiration window.
    
    Request Body (JSON):
        refresh_token : str — The current JWT refresh token string
        
    Returns:
        200 — Fresh access token (and optionally a rotated refresh token)
        401 — Unauthorized (expired or revoked refresh token)
    """
    access_token, ref_token = do_refresh(refresh_token.refresh_token, session)

    if ref_token is None:
        return {'access_token' : access_token, 'token_type' : 'bearer'}
    
    return {'access_token' : access_token, 'refresh_token' : ref_token, 'token_type' : 'bearer'}

@router.post("/forget-password", status_code=status.HTTP_200_OK)
def forget_password(forget_request: ForgetPasswordRequest, bg_tasks: BackgroundTasks, session: Session = Depends(get_session)) -> dict:
    """
    Initiates password recovery by dispatching a 6-digit OTP verification email via Brevo.
    Enforces a defensive response to prevent user enumeration attacks.
    
    Request Body (JSON):
        email : str — The user's account email
        
    Returns:
        200 — Generic confirmation message regardless of whether the email is registered
    """
    otp_code = do_forget_password(email=forget_request.email, session=session)
    
    if otp_code is not None:
        bg_tasks.add_task(send_otp_email_via_brevo, otp_code=otp_code, email=forget_request.email)

    return {"message" : "If that email is registered, a 6-digit verification code has been sent."}

@router.post("/verify-password", status_code=status.HTTP_200_OK)
def verify_otp(verify_otp_request: VerifyOTPRequest, session: Session = Depends(get_session)) -> dict:
    """
    Validates a 6-digit OTP verification code received via email.
    Issues a short-lived authorization reset token upon successful verification.
    
    Request Body (JSON):
        email : str — The user's email address
        otp   : int — The numeric 6-digit code received
        
    Returns:
        200 — Verification confirmed, returns `reset_token`
        401 — Unauthorized (invalid, expired, or previously consumed OTP code)
    """
    short_token = do_verify_otp(email=verify_otp_request.email, otpcode=str(verify_otp_request.otp), session=session)

    return {"message" : "Verification code verified successfully.", "reset_token" : short_token}

@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(reset_request: ResetPasswordRequest, session: Session = Depends(get_session)) -> dict:
    """
    Resets the user's account password using an authorized verification reset token.
    Immediately issues a new access and refresh token pair upon completion.
    
    Request Body (JSON):
        new_password : str — The replacement password adhering to security constraints
        reset_token  : str — The short-lived JWT authorization token
        
    Returns:
        200 — Password successfully updated, returns fresh access and refresh tokens
        401 — Unauthorized (invalid or expired reset authorization token)
        422 — Validation error (e.g., weak password)
    """
    access_token, refresh_token = do_reset_password(password=reset_request.new_password, reset_short_token=reset_request.reset_token, session=session)

    return {'access_token' : access_token, 'refresh_token' : refresh_token, 'token_type' : 'bearer'}