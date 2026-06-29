from unittest.mock import patch
from main import app
from security import get_current_user
from models import User, Item
from datetime import datetime, timezone
import stripe

def test_html_redirect_routes(client):
    """Test that all 4 HTML redirect routes return 200 OK and HTML."""
    for route in ["/payment/return", "/payment/refresh", "/payment/success", "/payment/cancel"]:
        response = client.get(route)
        assert response.status_code == 200
        assert "<html>" in response.text

@patch("services.payment_services.stripe.Account.create")
@patch("services.payment_services.stripe.AccountLink.create")
def test_onboard_new_account(mock_create_link, mock_create_account, client, session):
    """Test onboarding for a user who doesn't have a Stripe account yet."""
    # Create test user
    user = User(username="test_stripe_user", email="test@test.com", hashed_password="hash")
    session.add(user)
    session.commit()
    
    # Mock token generation
    token = "mock_jwt_token"
    
    mock_create_account.return_value.id = "acct_123"
    mock_create_link.return_value.url = "https://stripe.com/onboard"
    
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        response = client.post("/payment/onboard")
    finally:
        app.dependency_overrides.pop(get_current_user)
        
    assert response.status_code == 201
    assert response.json() == {"onboarding_link": "https://stripe.com/onboard"}
    assert mock_create_account.called

@patch("services.payment_services.stripe.AccountLink.create")
def test_onboard_existing_account(mock_create_link, client, session):
    """Test onboarding for a user who already has a Stripe account ID."""
    user = User(username="existing_stripe_user", email="test2@test.com", hashed_password="hash", stripe_account_id="acct_456")
    session.add(user)
    session.commit()
    
    mock_create_link.return_value.url = "https://stripe.com/onboard"
    
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        response = client.post("/payment/onboard")
    finally:
        app.dependency_overrides.pop(get_current_user)
        
    assert response.status_code == 201
    assert response.json() == {"onboarding_link": "https://stripe.com/onboard"}

@patch("services.payment_services.stripe.checkout.Session.create")
def test_checkout_success(mock_create_session, client, session):
    """Test successful generation of a checkout session url."""
    seller = User(username="seller", email="seller@test.com", hashed_password="hash", stripe_account_id="acct_seller")
    session.add(seller)
    session.commit()
    
    item = Item(title="Test Item", description="Desc", starting_price=10.0, owner_id=seller.id, checkout_token="valid_token", end_time=datetime.now(timezone.utc))
    session.add(item)
    session.commit()
    
    mock_create_session.return_value.url = "https://checkout.stripe.com/pay"
    
    # Use allow_redirects=False to catch the RedirectResponse instead of following it
    response = client.get(f"/payment/checkout/{item.id}?token=valid_token", follow_redirects=False)
    
    assert response.status_code == 307
    assert response.headers["location"] == "https://checkout.stripe.com/pay"
    
    # Verify token was nullified
    session.refresh(item)
    assert item.checkout_token is None

def test_checkout_invalid_item(client):
    """Test checkout for non-existent item."""
    response = client.get("/payment/checkout/999?token=token")
    assert response.status_code == 404

def test_checkout_invalid_token(client, session):
    """Test checkout with invalid or missing token."""
    seller = User(username="seller2", email="seller2@test.com", hashed_password="hash")
    session.add(seller)
    session.commit()
    item = Item(title="Item2", description="Desc", starting_price=10.0, owner_id=seller.id, checkout_token="real_token", end_time=datetime.now(timezone.utc))
    session.add(item)
    session.commit()
    
    response = client.get(f"/payment/checkout/{item.id}?token=fake_token")
    assert response.status_code == 403

@patch("services.payment_services.stripe.Webhook.construct_event")
def test_webhook_success(mock_construct, client, session):
    """Test successful processing of a checkout.session.completed webhook."""
    seller = User(username="seller3", email="seller3@test.com", hashed_password="hash")
    buyer = User(username="buyer3", email="buyer3@test.com", hashed_password="hash")
    session.add(seller)
    session.add(buyer)
    session.commit()
    
    item = Item(title="Item3", description="Desc", starting_price=10.0, current_price=10.0, owner_id=seller.id, higher_bidder_id=buyer.id, end_time=datetime.now(timezone.utc))
    session.add(item)
    session.commit()
    
    # Mock Stripe Event
    mock_event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {"item_id": str(item.id)},
                "payment_intent": "pi_123",
                "amount_total": 1000,
                "customer_details": {
                    "email": buyer.email,
                    "address": {
                        "line1": "123 Main St", "city": "City", "state": "ST", "postal_code": "12345", "country": "US"
                    }
                }
            }
        }
    }
    mock_construct.return_value = mock_event
    
    with patch("services.payment_services.send_payment_receipt_email") as mock_receipt, \
         patch("services.payment_services.send_ship_item_email") as mock_ship:
        response = client.post("/payment/webhook", headers={"stripe-signature": "sig"}, content=b"payload")
        
    assert response.status_code == 200
    assert response.json() == {"status": "success"}
    
    session.refresh(item)
    assert item.payment_status == "paid"
    assert item.stripe_payment_id == "pi_123"
    assert mock_receipt.called
    assert mock_ship.called

@patch("services.payment_services.stripe.Webhook.construct_event")
def test_webhook_unhandled_event(mock_construct, client):
    """Test webhook processing for events we don't care about."""
    mock_construct.return_value = {"type": "payment_intent.succeeded"}
    response = client.post("/payment/webhook", headers={"stripe-signature": "sig"}, content=b"payload")
    assert response.status_code == 200

@patch("services.payment_services.stripe.Webhook.construct_event")
def test_webhook_value_error(mock_construct, client):
    """Test webhook with invalid JSON payload."""
    mock_construct.side_effect = ValueError("Invalid payload")
    response = client.post("/payment/webhook", headers={"stripe-signature": "sig"}, content=b"payload")
    assert response.status_code == 400

@patch("services.payment_services.stripe.Webhook.construct_event")
def test_webhook_signature_error(mock_construct, client):
    """Test webhook with invalid signature."""
    mock_construct.side_effect = stripe.error.SignatureVerificationError("Invalid sig", "sig")
    response = client.post("/payment/webhook", headers={"stripe-signature": "sig"}, content=b"payload")
    assert response.status_code == 400

def test_refund_item_not_found(client, session):
    """Test refunding a non-existent item."""
    buyer = User(username="buyer", email="b@test.com", hashed_password="hash")
    session.add(buyer)
    session.commit()
    
    app.dependency_overrides[get_current_user] = lambda: buyer
    try:
        response = client.post("/payment/refund/999", json={"reason": "Item arrived damaged"})
    finally:
        app.dependency_overrides.pop(get_current_user)
        
    assert response.status_code == 404

def test_refund_unauthorized_user(client, session):
    """Test refunding an item where the current user is not the winning bidder."""
    seller = User(username="seller", email="s@test.com", hashed_password="hash")
    buyer = User(username="buyer", email="b@test.com", hashed_password="hash")
    hacker = User(username="hacker", email="h@test.com", hashed_password="hash")
    session.add_all([seller, buyer, hacker])
    session.commit()
    
    item = Item(title="Item", description="Desc", starting_price=10.0, owner_id=seller.id, higher_bidder_id=buyer.id, end_time=datetime.now(timezone.utc))
    session.add(item)
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: hacker
    try:
        response = client.post(f"/payment/refund/{item.id}", json={"reason": "Item arrived damaged"})
    finally:
        app.dependency_overrides.pop(get_current_user)
        
    assert response.status_code == 403
    assert "Only the winning bidder" in response.text

def test_refund_item_not_paid(client, session):
    """Test refunding an item that hasn't been paid for."""
    seller = User(username="seller2", email="s2@test.com", hashed_password="hash")
    buyer = User(username="buyer2", email="b2@test.com", hashed_password="hash")
    session.add_all([seller, buyer])
    session.commit()
    
    item = Item(title="Item2", description="Desc", starting_price=10.0, owner_id=seller.id, higher_bidder_id=buyer.id, end_time=datetime.now(timezone.utc), payment_status="unpaid")
    session.add(item)
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: buyer
    try:
        response = client.post(f"/payment/refund/{item.id}", json={"reason": "Changed my mind"})
    finally:
        app.dependency_overrides.pop(get_current_user)
        
    assert response.status_code == 400
    assert "cannot be processed" in response.text

@patch("services.payment_services.stripe.Refund.create")
@patch("services.payment_services.send_seller_refund_email")
@patch("services.payment_services.send_buyer_refund_email")
def test_refund_success(mock_send_buyer, mock_send_seller, mock_refund_create, client, session):
    """Test a successful refund flow, including database updates and email dispatching."""
    seller = User(username="seller3", email="s3@test.com", hashed_password="hash")
    buyer = User(username="buyer3", email="b3@test.com", hashed_password="hash")
    session.add_all([seller, buyer])
    session.commit()
    
    item = Item(title="Item3", description="Desc", starting_price=10.0, owner_id=seller.id, higher_bidder_id=buyer.id, end_time=datetime.now(timezone.utc), payment_status="paid", stripe_payment_id="pi_123")
    session.add(item)
    session.commit()

    mock_refund_create.return_value.id = "re_123"

    app.dependency_overrides[get_current_user] = lambda: buyer
    try:
        response = client.post(f"/payment/refund/{item.id}", json={"reason": "Item not as described"})
    finally:
        app.dependency_overrides.pop(get_current_user)
        
    assert response.status_code == 200
    assert "refund is being initiated" in response.json()["message"]
    
    # Verify DB update
    session.refresh(item)
    assert item.payment_status == "refunded"
    
    # Verify Mocks
    mock_refund_create.assert_called_once_with(payment_intent="pi_123")
    mock_send_seller.assert_called_once_with(useremail=seller.email, username=seller.username, item_title=item.title, reason="Item not as described")
    mock_send_buyer.assert_called_once_with(username=buyer.username, useremail=buyer.email, item_title=item.title)