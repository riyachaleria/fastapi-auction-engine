"""
Payment and onboarding endpoints.
Provides routes for Stripe Connect onboarding, checkout sessions, and webhook handling.
"""
from fastapi import APIRouter, status, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from security import get_current_user
from models import User, Item
from services.payment_services import create_onboarding_link, create_connected_account, create_checkout_session, process_refund, get_webhook
from database import get_session
from sqlmodel import Session

router = APIRouter(prefix="/payment", tags=["payment"])

@router.post("/onboard", status_code=status.HTTP_201_CREATED)
def get_user_onboard(user_db: User = Depends(get_current_user), session: Session = Depends(get_session)) -> dict:
    """
    Generate a Stripe Express onboarding link for a seller.
    Requires a valid JWT Bearer token.

    Returns:
        201 — Returns the Stripe onboarding URL.
    """
    if user_db.stripe_account_id is None:
        user_db.stripe_account_id = create_connected_account(user=user_db)
        session.add(user_db)
        session.commit()

    onboarding_url = create_onboarding_link(user_db.stripe_account_id)

    return {"onboarding_link" : onboarding_url}

@router.get("/checkout/{item_id}", status_code=status.HTTP_200_OK)
def get_ready_checkout_window(item_id: int, token: str, session: Session = Depends(get_session)) -> RedirectResponse:
    """
    Validate a one-time checkout token and redirect the user to Stripe Checkout.

    Path Parameters:
        item_id : int — The ID of the auction item won.

    Query Parameters:
        token : str — The secure checkout token generated when the auction ended.

    Returns:
        307 — Temporary redirect to the Stripe Checkout session.
        403 — Forbidden (Invalid or expired link).
        404 — Item not found.
    """
    item = session.get(Item, item_id)

    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")
    
    if item.checkout_token != token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or expired link.")
    
    item.checkout_token = None
    session.add(item)
    session.commit()
    
    payment_url = create_checkout_session(item=item)

    return RedirectResponse(url=payment_url)

@router.post("/webhook", status_code=status.HTTP_200_OK)
async def recieve_webhook(request: Request, session: Session = Depends(get_session)) -> dict:
    """
    Listen for asynchronous Stripe webhook events (e.g., checkout.session.completed).
    Verifies the Stripe signature and processes the event logic.

    Returns:
        200 — Webhook processed successfully.
        400 — Invalid payload or signature.
    """
    await get_webhook(request, session)

    return {"status": "success"}

@router.get("/return", response_class=HTMLResponse)
def onboard_return() -> str:
    """
    Callback URL for successful Stripe Connect onboarding.
    """
    return "<html><body style='font-family: Arial; text-align: center; padding: 50px;'><h1>🎉 Onboarding Complete!</h1><p>You can now close this tab and return to the app.</p></body></html>"

@router.get("/refresh", response_class=HTMLResponse)
def onboard_refresh() -> str:
    """
    Callback URL for expired/failed Stripe Connect onboarding.
    """
    return "<html><body style='font-family: Arial; text-align: center; padding: 50px;'><h1>⚠️ Session Expired</h1><p>Please generate a new onboarding link and try again.</p></body></html>"

@router.get("/success", response_class=HTMLResponse)
def checkout_success() -> str:
    """
    Callback URL for successful Stripe Checkout.
    """
    return "<html><body style='font-family: Arial; text-align: center; padding: 50px;'><h1>✅ Payment Successful!</h1><p>Your payment has cleared. You can close this tab and check your email for the receipt.</p></body></html>"

@router.get("/cancel", response_class=HTMLResponse)
def checkout_cancel() -> str:
    """
    Callback URL for cancelled Stripe Checkout.
    """
    return "<html><body style='font-family: Arial; text-align: center; padding: 50px;'><h1>❌ Payment Cancelled</h1><p>You cancelled the checkout. You can safely close this tab.</p></body></html>"