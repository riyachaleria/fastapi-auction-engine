"""
Payment integration services.
Handles Stripe Connect onboarding, Checkout session generation, and webhook processing.
"""
import stripe
from config import config
from models import Item, User
from sqlmodel import Session
from fastapi import Request, HTTPException, status
from services.email_services import send_payment_receipt_email, send_ship_item_email,send_buyer_refund_email,send_seller_refund_email

stripe.api_key = config.STRIPE_SECRET_KEY
webhook_secret = config.STRIPE_WEBHOOK_SECRET

def create_connected_account(user: User) -> str:
    """
    Creates a new Stripe Express connected account for a seller.
    
    Args:
        user (User): The authenticated user registering as a seller.
        
    Returns:
        str: The newly generated Stripe Account ID.
    """
    stripe_response = stripe.Account.create(type="express", email=user.email)
    return stripe_response.id

def create_onboarding_link(account_id: str) -> str:
    """
    Generates a secure, temporary onboarding link for a Stripe connected account.
    
    Args:
        account_id (str): The Stripe Account ID of the seller.
        
    Returns:
        str: The onboarding URL for the seller to complete their profile.
    """
    stripe_response = stripe.AccountLink.create(
        type="account_onboarding",
        account=account_id,
        refresh_url="http://localhost:8000/payment/refresh",
        return_url="http://localhost:8000/payment/return"                                     
    )

    return stripe_response.url

def create_checkout_session(item: Item) -> str:
    """
    Creates a Stripe Checkout session for the winning bidder to pay for an item.
    Automatically routes 95% of funds to the seller and captures a 5% platform fee.
    
    Args:
        item (Item): The auction item that was won.
        
    Returns:
        str: The Stripe Checkout session URL.
    """
    total_cents = int(item.current_price * 100)
    fee_cents = int(total_cents * 0.05)
    
    session = stripe.checkout.Session.create(
        line_items=[{
            'price_data': {
                'currency': "usd",
                'product_data': {
                    'name': item.title
                },
                'unit_amount': total_cents
            },
            'quantity' : 1 
        }],
        metadata={'item_id': item.id},
        mode="payment",
        billing_address_collection="required",
        success_url="http://localhost:8000/payment/success",
        cancel_url="http://localhost:8000/payment/cancel",
        
        payment_intent_data={
            "application_fee_amount": fee_cents,
            "transfer_data": {"destination": item.owner.stripe_account_id}
        }
    )

    return session.url

def process_refund(user_db: User, item_db: Item, refund_request, session: Session, payment_id: str) -> stripe.Refund:
    """
    Executes the complete refund flow for a returned item.
    Reverses the Stripe payment intent, updates the local database state,
    and dispatches notification emails to both the buyer and seller.
    
    Args:
        user_db (User): The buyer requesting the refund.
        item_db (Item): The auction item being refunded.
        refund_request (RefundRequest): The payload containing the refund reason.
        session (Session): The database session.
        payment_id (str): The Stripe Payment Intent ID.
        
    Returns:
        stripe.Refund: The generated Stripe Refund object.
    """
    
    stripe_response = stripe.Refund.create(payment_intent=payment_id)
    
    item_db.payment_status = "refunded"
    session.add(item_db)
    session.commit()

    seller = session.get(User, item_db.owner_id)

    send_seller_refund_email(
        useremail=seller.email,
        username=seller.username,
        item_title=item_db.title,
        reason=refund_request.reason.value
    )

    send_buyer_refund_email(
        username=user_db.username,
        useremail=user_db.email,
        item_title=item_db.title
    )

    return stripe_response

async def get_webhook(request: Request, session: Session) -> None:
    """
    Listens for incoming Stripe Webhook events and processes checkout completions.
    Verifies the webhook signature, marks the item as paid, and dispatches notification emails.
    
    Args:
        request (Request): The incoming FastAPI request containing the payload and signature.
        session (Session): The database session.
        
    Raises:
        HTTPException: If the payload is invalid or the signature verification fails.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")
    
    if event["type"] == "checkout.session.completed":
        session_data = event["data"]["object"]
        item_id = int(session_data["metadata"]["item_id"])
        
        item = session.get(Item, item_id)
        item.stripe_payment_id = session_data["payment_intent"]
        item.payment_status = "paid"
        session.add(item)

        address = session_data["customer_details"]["address"]
        formatted_address = f"{address['line1']}\n{address['city']}, {address['state']} {address['postal_code']}\n{address['country']}"

        buyer_email = session_data["customer_details"]["email"]
        amount_paid = session_data["amount_total"] / 100

        seller = session.get(User, item.owner_id)
        buyer = session.get(User, item.higher_bidder_id)

        send_payment_receipt_email(
            useremail=buyer_email,
            username=buyer.username,
            item_title=item.title,
            amount_paid=amount_paid
        )
        
        send_ship_item_email(
            seller_name=seller.username, 
            seller_email=seller.email,
            item_title=item.title,
            buyer_address=formatted_address
        )

        session.commit()