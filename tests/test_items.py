"""
Unit tests for auction item routes.
Verifies item creation, retrieving listings, searching, and filtering.
"""
import pytest
from fastapi.testclient import TestClient
from models import User
from sqlmodel import select

@pytest.fixture
def auth_token(client: TestClient, session):
    client.post("/auth/signup", json={
        "username": "itemuser",
        "email": "item@example.com",
        "password": "password123!"
    })
    response = client.post("/auth/login", data={
        "username": "itemuser",
        "password": "password123!"
    })
    
    user = session.exec(select(User).where(User.username == "itemuser")).first()
    user.stripe_account_id = "acct_test_123"
    session.add(user)
    session.commit()
        
    return response.json()["access_token"]

def test_create_item(client: TestClient, auth_token: str):
    response = client.post(
        "/items/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "title": "Test Item",
            "description": "A very cool test item",
            "starting_price": 50.0,
            "duration_minutes": 10
        }
    )
    assert response.status_code == 201
    assert response.json()["data"]["title"] == "Test Item"
    assert response.json()["data"]["is_active"] == True

def test_create_item_unauthorized(client: TestClient):
    response = client.post(
        "/items/",
        json={
            "title": "No Auth Item",
            "description": "Will fail",
            "starting_price": 10.0,
            "duration_minutes": 5
        }
    )
    assert response.status_code == 401

def test_create_item_without_stripe_account(client: TestClient, session):
    # Create user without stripe_account_id
    client.post("/auth/signup", json={
        "username": "nostripeuser",
        "email": "nostripe@example.com",
        "password": "password123!"
    })
    response = client.post("/auth/login", data={
        "username": "nostripeuser",
        "password": "password123!"
    })
    token = response.json()["access_token"]
    
    # Try to create an item
    response = client.post(
        "/items/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Should Fail",
            "description": "No Stripe Account",
            "starting_price": 10.0,
            "duration_minutes": 5
        }
    )
    assert response.status_code == 403
    assert response.json()["message"] == "You must complete Payment Setup before you can list an item for sale."

def test_get_all_items(client: TestClient, auth_token: str):
    # Create two items to fetch
    client.post("/items/", headers={"Authorization": f"Bearer {auth_token}"}, json={"title": "Apple", "description": "Fruit", "starting_price": 1, "duration_minutes": 5})
    client.post("/items/", headers={"Authorization": f"Bearer {auth_token}"}, json={"title": "Banana", "description": "Fruit", "starting_price": 2, "duration_minutes": 5})
    
    response = client.get("/items/")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) >= 2
    
def test_search_items(client: TestClient, auth_token: str):
    client.post("/items/", headers={"Authorization": f"Bearer {auth_token}"}, json={"title": "Unique Rolex", "description": "Watch", "starting_price": 100, "duration_minutes": 5})
    
    response = client.get("/items/?search=rolex") # Test case-insensitive search
    assert response.status_code == 200
    data = response.json()["data"]
    assert any("Rolex" in item["title"] for item in data)

def test_get_item_by_username(client: TestClient, auth_token: str):
    response = client.get("/items/seller/itemuser") # Case-insensitive handled by ilike
    assert response.status_code == 200
    assert "data" in response.json()

def test_get_item_by_username_empty(client: TestClient):
    response = client.get("/items/seller/does_not_exist")
    assert response.status_code == 200
    assert response.json()["data"] == []

def test_get_all_items_sorting(client: TestClient, auth_token: str):
    # Ensure items exist
    client.post("/items/", headers={"Authorization": f"Bearer {auth_token}"}, json={"title": "Item A", "description": "...", "starting_price": 10, "duration_minutes": 5})
    client.post("/items/", headers={"Authorization": f"Bearer {auth_token}"}, json={"title": "Item B", "description": "...", "starting_price": 20, "duration_minutes": 5})
    
    # Test ascending
    resp_asc = client.get("/items/?sort_by=price_asc")
    assert resp_asc.status_code == 200
    prices_asc = [item["current_price"] for item in resp_asc.json()["data"]]
    assert prices_asc == sorted(prices_asc)
    
    # Test descending
    resp_desc = client.get("/items/?sort_by=price_desc")
    assert resp_desc.status_code == 200
    prices_desc = [item["current_price"] for item in resp_desc.json()["data"]]
    assert prices_desc == sorted(prices_desc, reverse=True)