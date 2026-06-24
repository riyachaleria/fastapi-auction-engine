"""
Auction items endpoints.
Provides routes for creating, viewing, and searching auction items.
"""
from fastapi import APIRouter, status, Depends,HTTPException
from security import get_current_user
from sqlmodel import Session
from database import get_session
from models import User
from services.items_services import create_item, all_item_by_username, get_all_items
from schema import ItemData

router = APIRouter(prefix="/items", tags=["Items"])

@router.post('/', status_code=status.HTTP_201_CREATED)
def list_an_item(itemdata: ItemData, session: Session = Depends(get_session), user: User = Depends(get_current_user)) -> dict:
    """
    Create a new auction item listing.
    Requires a valid JWT Bearer token.

    Request body (JSON):
        title            : str — Item name
        description      : str — Details about the item
        starting_price   : float — Initial bid price
        duration_minutes : int — How long the auction lasts

    Returns:
        201 — Item created successfully
        401 — Unauthorized (invalid/missing token)
        422 — Validation error
    """

    if user.stripe_account_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You must complete Payment Setup before you can list an item for sale.")

    new_item = create_item(itemdata, session, user)

    return {'data' : new_item, 'message' : 'item is succesfully added'}

@router.get('/', status_code=status.HTTP_200_OK)
def get_items(session: Session = Depends(get_session), search: str | None = None, sort_by: str | None = None) -> dict:
    """
    Retrieve all auction items. Supports searching and sorting.

    Query Parameters:
        search  : str (optional) — Filter items by title keyword
        sort_by : str (optional) — 'price_asc' or 'price_desc'

    Returns:
        200 — List of items (newest first by default)
    """
    all_items = get_all_items(session, search, sort_by)

    return {'data' : all_items}

@router.get('/seller/{username}', status_code=status.HTTP_200_OK)
def get_user_items(username: str, session: Session = Depends(get_session)) -> dict:
    """
    Retrieve all auction items created by a specific seller.

    Path Parameters:
        username : str — The seller's username

    Returns:
        200 — List of items owned by the user (or empty list if user not found)
    """
    get_items = all_item_by_username(username, session)

    return {'data' : get_items}