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
    ENCODING = "utf-8"
    SMTP_EMAIL = os.getenv('SMTP_EMAIL')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')