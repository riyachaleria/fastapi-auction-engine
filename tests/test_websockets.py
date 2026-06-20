"""
Integration tests for real-time WebSocket bidding.
Verifies connection handling, valid/invalid bids, closed auctions, and token validation.
"""
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def setup_auction(client: TestClient):
    # 1. Signup and login
    client.post("/auth/signup", json={"username": "wsuser", "email": "ws@test.com", "password": "Password123!"})
    token_resp = client.post("/auth/login", data={"username": "wsuser", "password": "Password123!"})
    token = token_resp.json()["access_token"]
    
    # 2. Create item
    item_resp = client.post("/items/", headers={"Authorization": f"Bearer {token}"}, json={
        "title": "WebSocket Test Item",
        "description": "Testing real-time bids",
        "starting_price": 100.0,
        "duration_minutes": 5
    })
    item_id = item_resp.json()["data"]["id"]
    return token, item_id

def test_websocket_valid_bid(client: TestClient, setup_auction):
    token, item_id = setup_auction
    
    # Connect to the WebSocket
    with client.websocket_connect(f"/bids/{item_id}?token={token}") as websocket:
        # Send a valid bid higher than starting price (100)
        websocket.send_text("150.0")
        
        # Receive the broadcast message
        data = websocket.receive_json()
        assert "new highest bid" in data
        assert data["new highest bid"] == 150.0
        assert data["bidder"] == "wsuser"

def test_websocket_invalid_bid_too_low(client: TestClient, setup_auction):
    token, item_id = setup_auction
    
    with client.websocket_connect(f"/bids/{item_id}?token={token}") as websocket:
        # Send a bid LOWER than starting price (100)
        websocket.send_text("50.0")
        
        # Receive the rejection error
        data = websocket.receive_json()
        assert "error" in data
        assert "Bid rejected" in data["error"]

def test_websocket_unauthorized_token(client: TestClient):
    # Try connecting with a fake token
    with pytest.raises(Exception):
        with client.websocket_connect("/bids/1?token=fake.jwt.token") as websocket:
            websocket.receive_text()  # pragma: no cover

def test_websocket_closed_auction(client: TestClient, session, setup_auction):
    from models import Item
    token, item_id = setup_auction
    
    # Close the auction manually in DB
    item = session.get(Item, item_id)
    item.is_active = False
    session.add(item)
    session.commit()
    
    with client.websocket_connect(f"/bids/{item_id}?token={token}") as websocket:
        # Try sending bid to closed auction
        websocket.send_text("500.0")
        
        # Receive error
        data = websocket.receive_json()
        assert "error" in data
        assert "This auction has completely ended" in data["error"]

def test_websocket_missing_sub(client: TestClient, setup_auction):
    import security
    from fastapi.websockets import WebSocketDisconnect
    token, item_id = setup_auction
    
    # Fake token missing 'sub'
    fake_token = security.create_access_token(data={"hacker": "yes"})
    
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(f"/bids/{item_id}?token={fake_token}") as websocket:
            websocket.receive_text()  # pragma: no cover
            
    assert exc_info.value.code == 1008 # WS_1008_POLICY_VIOLATION
