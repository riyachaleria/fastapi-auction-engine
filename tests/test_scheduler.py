"""
Unit tests for the APScheduler background tasks.
Verifies that expired auctions are properly closed and correct email notifications are triggered.
"""
from sqlmodel import Session
from datetime import datetime, timedelta, timezone
from models import Item, User
from scheduler import check_expired_auctions

def test_check_expired_auctions(session: Session, mock_emails):
    mock_welcome, mock_won, mock_sold = mock_emails
    
    # Create fake user
    seller = User(username="scheduler_seller", email="seller@test.com", hashed_password="pwd")
    session.add(seller)
    session.commit()
    
    # Create fake expired item (set end_time to the past)
    past_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=10)
    item = Item(
        title="Expired Item",
        starting_price=10.0,
        current_price=50.0,
        end_time=past_time,
        is_active=True,
        owner_id=seller.id,
        higher_bidder_id=seller.id # Let's say the seller bid on their own item
    )
    session.add(item)
    session.commit()
    
    # Call the scheduler manually
    check_expired_auctions()
    
    # Check if item was closed in DB
    session.refresh(item)
    assert item.is_active == False
    
    # Check if emails were triggered!
    mock_sold.assert_called_once()
    mock_won.assert_called_once()

def test_check_expired_auctions_no_bids(session: Session, mock_emails):
    mock_welcome, mock_won, mock_sold = mock_emails
    
    # Reset mocks from previous tests
    mock_won.reset_mock()
    mock_sold.reset_mock()
    
    seller = User(username="nobid_seller", email="nobid@test.com", hashed_password="pwd")
    session.add(seller)
    session.commit()
    
    past_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=10)
    item = Item(
        title="Expired Item No Bids",
        starting_price=10.0,
        current_price=10.0,
        end_time=past_time,
        is_active=True,
        owner_id=seller.id,
        higher_bidder_id=None # No bids!
    )
    session.add(item)
    session.commit()
    
    check_expired_auctions()
    
    session.refresh(item)
    assert item.is_active == False
    
    # Emails should NOT be called
    mock_sold.assert_not_called()
    mock_won.assert_not_called()