"""
Authentication endpoints.
Provides routes for user registration and JWT login.
"""
from fastapi import APIRouter, status, Depends, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from database import get_session
from sqlmodel import Session
from services.auth_services import do_login, do_signup
from services.email_services import send_welcome_email
from schema import Usercreate

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
    token = do_signup(user_data, session)

    bg_tasks.add_task(send_welcome_email, username=user_data.username, user_email=user_data.email)

    return {'access_token' : token, 'token_type' : 'bearer', 'message' : 'you are succesfully loged in'}

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
    token = do_login(foam_data, session)

    return {'access_token' : token, 'token_type' : 'bearer'}
    