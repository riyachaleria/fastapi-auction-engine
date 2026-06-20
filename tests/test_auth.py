"""
Unit tests for authentication routes and services.
Verifies signup, login, password validation, and JWT token edge cases.
"""
from fastapi.testclient import TestClient

def test_signup(client: TestClient):
    response = client.post("/auth/signup", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123!"
    })
    assert response.status_code == 201
    assert "access_token" in response.json()

def test_signup_duplicate_username(client: TestClient):
    # First signup
    client.post("/auth/signup", json={
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "password123!"
    })
    # Duplicate username
    response = client.post("/auth/signup", json={
        "username": "testuser2",
        "email": "test3@example.com",
        "password": "password123!"
    })
    assert response.status_code == 400

def test_login_success(client: TestClient):
    client.post("/auth/signup", json={
        "username": "loginuser",
        "email": "login@example.com",
        "password": "password123!"
    })
    
    response = client.post("/auth/login", data={
        "username": "loginuser",
        "password": "password123!"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_invalid_password(client: TestClient):
    client.post("/auth/signup", json={
        "username": "failuser",
        "email": "fail@example.com",
        "password": "password123!"
    })
    
    response = client.post("/auth/login", data={
        "username": "failuser",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_signup_invalid_password_format(client: TestClient):
    # Missing special character
    response = client.post("/auth/signup", json={
        "username": "weakpwd",
        "email": "weak@example.com",
        "password": "password123"
    })
    assert response.status_code == 422 # Unprocessable Entity

def test_signup_duplicate_email(client: TestClient):
    client.post("/auth/signup", json={
        "username": "emailuser1",
        "email": "same@example.com",
        "password": "Password123!"
    })
    # Same email, different username
    response = client.post("/auth/signup", json={
        "username": "emailuser2",
        "email": "same@example.com",
        "password": "Password123!"
    })
    assert response.status_code == 400

def test_login_invalid_username(client: TestClient):
    response = client.post("/auth/login", data={
        "username": "doesnotexist",
        "password": "Password123!"
    })
    assert response.status_code == 401

def test_invalid_token(client: TestClient):
    # Try fetching items with a fake token
    response = client.post("/items/", headers={"Authorization": "Bearer fake.jwt.token"}, json={
        "title": "Hack", "description": "Me", "starting_price": 10, "duration_minutes": 5
    })
    assert response.status_code == 401

def test_token_user_deleted(client: TestClient):
    # Since we can't easily access the DB session here to delete the user, 
    # we can fake a token with a 'sub' that doesn't exist
    import security
    fake_token = security.create_access_token(data={"sub": "ghost_user"})
    
    response = client.post("/items/", headers={"Authorization": f"Bearer {fake_token}"}, json={
        "title": "Should Fail", "description": "User is gone", "starting_price": 10, "duration_minutes": 5
    })
    assert response.status_code == 401

def test_token_missing_sub(client: TestClient):
    import security
    # Create a token but purposely leave out the 'sub' key (the username)
    fake_token = security.create_access_token(data={"hacker": "yes_i_am_a_hacker"})
    
    # Try using it to access a protected endpoint
    response = client.post("/items/", headers={"Authorization": f"Bearer {fake_token}"}, json={
        "title": "Hack", "description": "Me", "starting_price": 10, "duration_minutes": 5
    })
    
    # Should be rejected at line 38 in security.py where it checks if username is None
    assert response.status_code == 401
    assert "Invalid token" in response.text
