"""
Background job scheduler using APScheduler.
Automatically checks for expired auctions and triggers email notifications.
"""
from services.email_services import send_auction_won_email, send_item_sold_email
from models import Item, User
from apscheduler.schedulers.background import BackgroundScheduler
from sqlmodel import select, Session
from database import engine
from datetime import datetime, timezone

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

            session.add(item)

            seller = session.get(User,item.owner_id)
            if item.higher_bidder_id:
                winner = session.get(User,item.higher_bidder_id)

                send_item_sold_email(seller_email=seller.email,username=seller.username,item_title=item.title,final_price=item.current_price)

                send_auction_won_email(username=winner.username,user_email=winner.email,item_title=item.title,final_price=item.current_price)
            else:
                print(f"Auction {item.title} ended with no bids!")

        if expired_items:
            session.commit()

scheduler = BackgroundScheduler()
scheduler.add_job(check_expired_auctions,'interval',seconds=60)