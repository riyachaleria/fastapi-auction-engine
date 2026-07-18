"""
Configuration settings for the BidBazaar application.
Loads environment variables and sets up global constants.
"""
import os
from dotenv import load_dotenv

load_dotenv()

class config():
    """
    Application configuration variables.
    These are accessed statically throughout the application.
    """
    SECRET_KEY = os.getenv('SECRET_KEY')
    DATABASE_URI = os.getenv('DATABASE_URL') or 'sqlite:///fallback.db'

    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 30
    REFRESH_TOKEN_EXPIRE_WINDOW = 5
    PASSWORD_RESET_TOKEN_MINUTES = 5
    OTP_EXPIRE_TIME = 10
    EXPIRED_AUCTIONS_SCHEDULER_SECONDS = 60
    EXPIRED_AUTH_DATA_CLEANUP_MINUTES = 90

    ENCODING = "utf-8"
    SMTP_EMAIL = os.getenv('SMTP_EMAIL')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    BREVO_KEY = os.getenv('BREVO_API')

    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')