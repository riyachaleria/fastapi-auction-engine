"""
Auction items business logic.
Handles creation, searching, and filtering of auction items.
"""
from models import Item, User
from sqlmodel import Session, select
from schema import ItemData
from datetime import datetime, timezone, timedelta

def create_item(item_data: ItemData, session: Session, user: User) -> Item:
    """
    Creates a new auction item and calculates its expiration time based on duration.
    
    Args:
        item_data (ItemData): The sanitized item payload.
        session (Session): The database session.
        user (User): The authenticated user creating the auction.
        
    Returns:
        Item: The newly created database object.
    """
    calculated_end_time = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=item_data.duration_minutes)

    new_item = Item(
        title=item_data.title,
        description=item_data.description,
        starting_price=item_data.starting_price,
        current_price=item_data.starting_price,
        end_time=calculated_end_time,
        owner_id=user.id
    )

    session.add(new_item)
    session.commit()
    session.refresh(new_item)

    return new_item

def get_all_items(session: Session, search: str | None, sort_by: str | None) -> list[Item]:
    """
    Retrieves all auction items, optionally filtering by search term and sorting by price.
    Defaults to returning the newest items first.
    
    Args:
        session (Session): The database session.
        search (str | None): Optional search string to filter item titles.
        sort_by (str | None): Optional sorting string ('price_asc' or 'price_desc').
        
    Returns:
        list[Item]: A list of matching auction items.
    """
    query = select(Item)

    if search:
        query = query.where(Item.title.icontains(search))
    
    if sort_by == "price_asc":
        query = query.order_by(Item.current_price.asc())
    elif sort_by == "price_desc":
        query = query.order_by(Item.current_price.desc())
    else:
        query = query.order_by(Item.id.desc())

    all_items = session.exec(query).all()
    return all_items

def all_item_by_username(username: str, session: Session) -> list[Item]:
    """
    Retrieves all items created by a specific user, sorted newest first.
    
    Args:
        username (str): The username of the seller.
        session (Session): The database session.
        
    Returns:
        list[Item]: A list of items owned by the user. Returns empty list if user not found.
    """
    user_db = session.exec(select(User).where(User.username.ilike(username))).first()

    if user_db is None:
        return []
    
    user_db.items.sort(key=lambda x : x.id, reverse=True)

    return user_db.items