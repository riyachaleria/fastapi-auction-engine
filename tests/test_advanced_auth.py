"""
Comprehensive unit and integration tests for advanced authentication features:
- Refresh token rotation and sliding window expiration
- OTP generation, Brevo email sending (mocked), and defensive password recovery
- Verification code validation and password resetting
- Single-session logout and multi-device logout-all
- Background cleanup scheduler job for expired tokens/OTPs
"""
import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlmodel import Session, select
from unittest.mock import AsyncMock, MagicMock, patch
from jose import jwt

from models import User, RefreshToken, OTP_Table
from security import (
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
    decode_refresh_token,
)
from scheduler import clean_expired_auth_data
from services.auth_email_services import send_otp_email_via_brevo
from config import config

# Helper functions for test user management
def create_user(client: TestClient, username="authuser", email="auth@test.com", password="Password123!"):
    response = client.post("/auth/signup", json={
        "username": username,
        "email": email,
        "password": password
    })
    assert response.status_code == 201
    return response.json()

def login_user(client: TestClient, username="authuser", password="Password123!"):
    response = client.post("/auth/login", data={
        "username": username,
        "password": password
    })
    assert response.status_code == 200
    return response.json()


# ==========================================
# 1. REFRESH TOKEN FLOW TESTS
# ==========================================

def test_refresh_token_normal_window(client: TestClient, session: Session):
    create_user(client, "refuser1", "ref1@test.com")
    tokens = login_user(client, "refuser1")
    refresh_tok = tokens["refresh_token"]

    response = client.post("/auth/refresh", json={"refresh_token": refresh_tok})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data.get("refresh_token") is None


def test_refresh_token_sliding_window_rotation(client: TestClient, session: Session):
    create_user(client, "refuser2", "ref2@test.com")
    tokens = login_user(client, "refuser2")
    refresh_tok = tokens["refresh_token"]

    payload = decode_refresh_token(refresh_tok)
    jti = payload["jti"]

    db_token = session.exec(select(RefreshToken).where(RefreshToken.jti == jti)).first()
    assert db_token is not None
    db_token.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=2)
    session.add(db_token)
    session.commit()

    response = client.post("/auth/refresh", json={"refresh_token": refresh_tok})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data.get("refresh_token") is not None
    assert data["refresh_token"] != refresh_tok

    updated_old_token = session.exec(select(RefreshToken).where(RefreshToken.jti == jti)).first()
    assert updated_old_token.is_revoked is True


def test_refresh_token_revoked_or_expired(client: TestClient, session: Session):
    create_user(client, "refuser3", "ref3@test.com")
    tokens = login_user(client, "refuser3")
    refresh_tok = tokens["refresh_token"]

    payload = decode_refresh_token(refresh_tok)
    jti = payload["jti"]

    db_token = session.exec(select(RefreshToken).where(RefreshToken.jti == jti)).first()
    db_token.is_revoked = True
    session.add(db_token)
    session.commit()

    response = client.post("/auth/refresh", json={"refresh_token": refresh_tok})
    assert response.status_code == 401
    assert "Refresh token has expired or been revoked." in response.text


def test_refresh_token_invalid_jwt(client: TestClient):
    response = client.post("/auth/refresh", json={"refresh_token": "fake.invalid.token"})
    assert response.status_code == 401
    assert "Refresh token is invalid or malformed." in response.text


def test_refresh_token_user_not_found(client: TestClient, session: Session):
    token, jti, exp = create_refresh_token({"sub": "ghost_username"})
    ref_model = RefreshToken(jti=jti, user_id=99999, expires_at=exp)
    session.add(ref_model)
    session.commit()

    response = client.post("/auth/refresh", json={"refresh_token": token})
    assert response.status_code == 401
    assert "User account associated with this token no longer exists." in response.text


def test_refresh_token_wrong_purpose_claim(client: TestClient):
    wrong_token = create_access_token({"sub": "refuser1"})
    response = client.post("/auth/refresh", json={"refresh_token": wrong_token})
    assert response.status_code == 401
    assert "Refresh token is invalid or malformed." in response.text


def test_decode_refresh_token_missing_claims():
    bad_token = jwt.encode({"random": "claim"}, config.SECRET_KEY, algorithm=config.ALGORITHM)
    with pytest.raises(Exception) as exc_info:
        decode_refresh_token(bad_token)
    assert exc_info.value.status_code == 401


# ==========================================
# 2. OTP & FORGET PASSWORD FLOW TESTS
# ==========================================

def test_forget_password_registered_user(client: TestClient, session: Session):
    create_user(client, "otpuser1", "otp1@test.com")
    
    response = client.post("/auth/forget-password", json={"email": "otp1@test.com"})
    assert response.status_code == 200
    assert "If that email is registered" in response.json()["message"]

    otp_record = session.exec(select(OTP_Table).where(OTP_Table.email == "otp1@test.com")).first()
    assert otp_record is not None
    assert len(otp_record.otp_code) == 6
    assert otp_record.is_used is False


def test_forget_password_unregistered_email(client: TestClient, session: Session):
    response = client.post("/auth/forget-password", json={"email": "unregistered@test.com"})
    assert response.status_code == 200
    assert "If that email is registered" in response.json()["message"]

    otp_record = session.exec(select(OTP_Table).where(OTP_Table.email == "unregistered@test.com")).first()
    assert otp_record is None


# ==========================================
# 3. VERIFY OTP FLOW TESTS
# ==========================================

def test_verify_otp_success(client: TestClient, session: Session):
    create_user(client, "otpuser2", "otp2@test.com")
    client.post("/auth/forget-password", json={"email": "otp2@test.com"})
    
    otp_record = session.exec(select(OTP_Table).where(OTP_Table.email == "otp2@test.com")).first()
    assert otp_record is not None

    response = client.post("/auth/verify-password", json={
        "email": "otp2@test.com",
        "otp": int(otp_record.otp_code)
    })
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Verification code verified successfully."
    assert "reset_token" in data

    # Record is deleted from DB upon successful verification (line 192 of auth_services.py)
    updated_otp = session.exec(select(OTP_Table).where(OTP_Table.email == "otp2@test.com")).first()
    assert updated_otp is None


def test_verify_otp_wrong_code(client: TestClient, session: Session):
    create_user(client, "otpuser3", "otp3@test.com")
    client.post("/auth/forget-password", json={"email": "otp3@test.com"})

    response = client.post("/auth/verify-password", json={
        "email": "otp3@test.com",
        "otp": 111111
    })
    assert response.status_code == 401
    assert "Verification code is incorrect." in response.text


def test_verify_otp_expired_code(client: TestClient, session: Session):
    create_user(client, "otpuser4", "otp4@test.com")
    client.post("/auth/forget-password", json={"email": "otp4@test.com"})
    
    otp_record = session.exec(select(OTP_Table).where(OTP_Table.email == "otp4@test.com")).first()
    otp_record.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
    session.add(otp_record)
    session.commit()

    response = client.post("/auth/verify-password", json={
        "email": "otp4@test.com",
        "otp": int(otp_record.otp_code)
    })
    assert response.status_code == 401
    assert "Verification code has expired." in response.text


def test_verify_otp_already_used(client: TestClient, session: Session):
    create_user(client, "otpuser5", "otp5@test.com")
    client.post("/auth/forget-password", json={"email": "otp5@test.com"})
    
    otp_record = session.exec(select(OTP_Table).where(OTP_Table.email == "otp5@test.com")).first()
    otp_record.is_used = True
    session.add(otp_record)
    session.commit()

    response = client.post("/auth/verify-password", json={
        "email": "otp5@test.com",
        "otp": int(otp_record.otp_code)
    })
    assert response.status_code == 401
    assert "Verification code has expired." in response.text


def test_verify_otp_nonexistent_user(client: TestClient):
    # Triggers line 182 inside do_verify_otp where user_db is None
    response = client.post("/auth/verify-password", json={
        "email": "ghost_otp_user@test.com",
        "otp": 123456
    })
    assert response.status_code == 401
    assert "Invalid email address or verification code." in response.text


# ==========================================
# 4. RESET PASSWORD FLOW TESTS
# ==========================================

def test_reset_password_success(client: TestClient, session: Session):
    create_user(client, "resetuser1", "reset1@test.com", "OldPassword123!")
    client.post("/auth/forget-password", json={"email": "reset1@test.com"})
    otp_record = session.exec(select(OTP_Table).where(OTP_Table.email == "reset1@test.com")).first()

    verify_resp = client.post("/auth/verify-password", json={
        "email": "reset1@test.com",
        "otp": int(otp_record.otp_code)
    })
    reset_token = verify_resp.json()["reset_token"]

    reset_resp = client.post("/auth/reset-password", json={
        "new_password": "NewPassword888!",
        "reset_token": reset_token
    })
    assert reset_resp.status_code == 200
    data = reset_resp.json()
    assert "access_token" in data
    assert "refresh_token" in data

    old_login = client.post("/auth/login", data={"username": "resetuser1", "password": "OldPassword123!"})
    assert old_login.status_code == 401

    new_login = client.post("/auth/login", data={"username": "resetuser1", "password": "NewPassword888!"})
    assert new_login.status_code == 200


def test_reset_password_invalid_or_wrong_purpose_token(client: TestClient):
    resp = client.post("/auth/reset-password", json={"new_password": "ValidPassword123!", "reset_token": "fake.jwt"})
    assert resp.status_code == 401

    acc_token = create_access_token({"sub": "resetuser1"})
    resp2 = client.post("/auth/reset-password", json={"new_password": "ValidPassword123!", "reset_token": acc_token})
    assert resp2.status_code == 401


def test_reset_password_user_not_found(client: TestClient):
    reset_token = create_password_reset_token({"sub": "non_existent_username"})
    resp = client.post("/auth/reset-password", json={"new_password": "ValidPassword123!", "reset_token": reset_token})
    assert resp.status_code == 401
    assert "Password reset authorization token is invalid or has expired." in resp.text


def test_reset_password_weak_password(client: TestClient):
    reset_token = create_password_reset_token({"sub": "resetuser1"})
    resp = client.post("/auth/reset-password", json={"new_password": "pwd", "reset_token": reset_token})
    assert resp.status_code == 422
    assert resp.json()["error"] is True



# ==========================================
# 5. LOGOUT & LOGOUT-ALL FLOW TESTS
# ==========================================

def test_logout_success(client: TestClient, session: Session):
    create_user(client, "logoutuser1", "log1@test.com")
    tokens = login_user(client, "logoutuser1")
    ref_token = tokens["refresh_token"]

    response = client.post("/auth/logout", json={"refresh_token": ref_token})
    assert response.status_code == 200
    assert response.json()["message"] == "You have successfully logged out."

    payload = decode_refresh_token(ref_token)
    db_token = session.exec(select(RefreshToken).where(RefreshToken.jti == payload["jti"])).first()
    assert db_token.is_revoked is True

    refresh_resp = client.post("/auth/refresh", json={"refresh_token": ref_token})
    assert refresh_resp.status_code == 401


def test_logout_nonexistent_token(client: TestClient):
    # Pass a valid JWT string whose JTI does not exist in DB to trigger line 106
    fake_ref_token, _, _ = create_refresh_token({"sub": "logoutuser1"})
    response = client.post("/auth/logout", json={"refresh_token": fake_ref_token})
    assert response.status_code == 401
    assert "Refresh token has expired, is invalid, or has already been revoked." in response.text


def test_logout_all_success(client: TestClient, session: Session):
    create_user(client, "logoutuser2", "log2@test.com")
    tokens1 = login_user(client, "logoutuser2")
    tokens2 = login_user(client, "logoutuser2")

    ref_token = tokens2["refresh_token"]

    response = client.post("/auth/logout-all", json={"refresh_token": ref_token})
    assert response.status_code == 200
    assert response.json()["message"] == "You have successfully logged out from all devices."

    user = session.exec(select(User).where(User.username == "logoutuser2")).first()
    revoked_tokens = session.exec(select(RefreshToken).where(RefreshToken.user_id == user.id)).all()
    assert len(revoked_tokens) >= 2
    for t in revoked_tokens:
        assert t.is_revoked is True


def test_logout_all_nonexistent_token(client: TestClient):
    # Pass a valid JWT string whose JTI does not exist in DB to trigger line 118
    fake_ref_token, _, _ = create_refresh_token({"sub": "logoutuser2"})
    response = client.post("/auth/logout-all", json={"refresh_token": fake_ref_token})
    assert response.status_code == 401
    assert "Refresh token has expired, is invalid, or has already been revoked." in response.text


# ==========================================
# 6. SCHEDULER CLEANUP TASK TESTS
# ==========================================

def test_clean_expired_auth_data(session: Session):
    current_time = datetime.now(timezone.utc).replace(tzinfo=None)

    t1 = RefreshToken(jti="expired-jti", user_id=1, expires_at=current_time - timedelta(days=1), is_revoked=False)
    t2 = RefreshToken(jti="revoked-jti", user_id=1, expires_at=current_time + timedelta(days=1), is_revoked=True)
    t3 = RefreshToken(jti="active-jti", user_id=1, expires_at=current_time + timedelta(days=10), is_revoked=False)

    o1 = OTP_Table(email="test@test.com", otp_code="111111", expires_at=current_time - timedelta(minutes=10), is_used=False)
    o2 = OTP_Table(email="test2@test.com", otp_code="222222", expires_at=current_time + timedelta(minutes=10), is_used=True)
    o3 = OTP_Table(email="test3@test.com", otp_code="333333", expires_at=current_time + timedelta(minutes=10), is_used=False)

    session.add_all([t1, t2, t3, o1, o2, o3])
    session.commit()

    clean_expired_auth_data()

    remaining_tokens = session.exec(select(RefreshToken)).all()
    remaining_otps = session.exec(select(OTP_Table)).all()

    assert len(remaining_tokens) == 1
    assert remaining_tokens[0].jti == "active-jti"

    assert len(remaining_otps) == 1
    assert remaining_otps[0].email == "test3@test.com"


# ==========================================
# 7. BREVO EMAIL SERVICE UNIT TESTS (MOCKED)
# ==========================================

def test_send_otp_email_via_brevo_success():
    with patch("services.auth_email_services.httpx.AsyncClient") as mock_client_cls:
        mock_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"messageId": "<test-message-id@brevo.com>"}
        mock_instance.post.return_value = mock_response
        mock_client_cls.return_value.__aenter__.return_value = mock_instance

        asyncio.run(send_otp_email_via_brevo("testrecipient@gmail.com", 123456))

        mock_instance.post.assert_called_once()
        args, kwargs = mock_instance.post.call_args
        assert args[0] == "https://api.brevo.com/v3/smtp/email"
        assert kwargs["headers"]["api-key"] == config.BREVO_KEY
        assert kwargs["json"]["to"][0]["email"] == "testrecipient@gmail.com"
        assert "123456" in kwargs["json"]["htmlContent"]


def test_send_otp_email_via_brevo_http_error():
    with patch("services.auth_email_services.httpx.AsyncClient") as mock_client_cls:
        mock_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"message": "Invalid email address"}'
        mock_instance.post.return_value = mock_response
        mock_client_cls.return_value.__aenter__.return_value = mock_instance

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(send_otp_email_via_brevo("bademail@gmail.com", 654321))
        assert exc_info.value.status_code == 500
        mock_instance.post.assert_called_once()


def test_send_otp_email_via_brevo_network_exception():
    with patch("services.auth_email_services.httpx.AsyncClient") as mock_client_cls:
        mock_instance = AsyncMock()
        mock_instance.post.side_effect = Exception("Network timeout")
        mock_client_cls.return_value.__aenter__.return_value = mock_instance

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(send_otp_email_via_brevo("timeout@gmail.com", 999999))
        assert exc_info.value.status_code == 500
        mock_instance.post.assert_called_once()