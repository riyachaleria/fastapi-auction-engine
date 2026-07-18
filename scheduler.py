"""
Background job scheduler using APScheduler.
Automatically checks for expired auctions and triggers email notifications.
"""
from services.email_services import send_auction_won_email, send_item_sold_email
from models import Item, User,RefreshToken,OTP_Table
from apscheduler.schedulers.background import BackgroundScheduler
from sqlmodel import select, Session,or_
from database import engine
from datetime import datetime, timezone
import secrets
from config import config

def check_expired_auctions() -> None:
    """
    Scheduled job that runs every 60 seconds.
    Finds active auctions past their end time, marks them as inactive,
    and sends winning/sold emails to the buyer and seller.
    """
    with Session(engine) as session:
        current_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        expired_items = session.exec(select(Item).where(Item.is_active == True, Item.end_time < current_utc)).all()

        for item in expired_items:
            item.is_active = False
            seller = session.get(User,item.owner_id)

            if item.higher_bidder_id:
                token = secrets.token_urlsafe(16)
                item.checkout_token = token
                winner = session.get(User,item.higher_bidder_id)

                send_item_sold_email(seller_email=seller.email, username=seller.username, item_title=item.title, final_price=item.current_price)

                send_auction_won_email(
                    username=winner.username,
                    user_email=winner.email,
                    item_title=item.title,
                    final_price=item.current_price,
                    item_id=item.id,
                    checkout_token=token
                )
            else:
                print(f"Auction {item.title} ended with no bids!")

            session.add(item)

        if expired_items:
            session.commit()

def clean_expired_auth_data() -> None:
    """
    Scheduled background cleanup task that purges stale authentication data.
    Runs periodically according to EXPIRED_AUTH_DATA_CLEANUP_MINUTES configuration.
    
    Removes:
        - Refresh tokens that have passed their expiration timestamp (`expires_at < current_time`).
        - Refresh tokens that have been explicitly revoked (`is_revoked == True`).
        - One-Time Verification codes (OTPs) past their 10-minute validity window (`expires_at < current_time`).
        - One-Time Verification codes that have already been consumed (`is_used == True`).
    """
    with Session(engine) as session:
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)

        expired_refresh_rokens = session.exec(select(RefreshToken).where(or_(RefreshToken.expires_at < current_time, RefreshToken.is_revoked == True))).all()

        expired_otp_codes = session.exec(select(OTP_Table).where(or_(OTP_Table.expires_at < current_time, OTP_Table.is_used == True))).all()

        for row in expired_refresh_rokens:
            session.delete(row)

        for row in expired_otp_codes:
            session.delete(row)
        
        if expired_refresh_rokens or expired_otp_codes:
            session.commit()

scheduler = BackgroundScheduler()
scheduler.add_job(check_expired_auctions,'interval',seconds=config.EXPIRED_AUCTIONS_SCHEDULER_SECONDS)
scheduler.add_job(clean_expired_auth_data,'interval',minutes=config.EXPIRED_AUTH_DATA_CLEANUP_MINUTES)