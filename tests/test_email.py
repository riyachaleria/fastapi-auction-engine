"""
Unit tests for email notification services.
Verifies SMTP integration and exception handling without sending actual emails.
"""
from unittest.mock import patch, ANY
from services.email_services import (
    send_welcome_email, 
    send_auction_won_email, 
    send_item_sold_email, 
    send_payment_receipt_email, 
    send_ship_item_email,
    send_seller_refund_email,
    send_buyer_refund_email
)

@patch("services.email_services.smtplib.SMTP_SSL")
def test_send_welcome_email_success(mock_smtp):
    # Call the function directly
    send_welcome_email("test_user", "test@example.com")
    
    # Assert SMTP_SSL was called with correct host/port
    mock_smtp.assert_called_once_with("smtp.gmail.com", 465, context=ANY)
    
    # Retrieve the mock object that represents the 'server' inside the 'with' block
    mock_server = mock_smtp.return_value.__enter__.return_value
    
    # Ensure it logged in and sent the message
    mock_server.login.assert_called_once()
    mock_server.send_message.assert_called_once()

@patch("services.email_services.smtplib.SMTP_SSL")
def test_send_welcome_email_failure(mock_smtp):
    # Force the SMTP connection to crash to test the 'except Exception' block
    mock_smtp.side_effect = Exception("SMTP Connection Failed")
    
    # Call the function. It shouldn't crash our app because of the try/except block.
    send_welcome_email("test_user", "test@example.com")

@patch("services.email_services.smtplib.SMTP_SSL")
def test_send_auction_won_email_success(mock_smtp):
    send_auction_won_email("winner", "winner@example.com", "Rolex", 500.0, 1, "test_token")
    mock_smtp.assert_called_once()
    
    mock_server = mock_smtp.return_value.__enter__.return_value
    mock_server.send_message.assert_called_once()

@patch("services.email_services.smtplib.SMTP_SSL")
def test_send_auction_won_email_failure(mock_smtp):
    mock_smtp.side_effect = Exception("SMTP Connection Failed")
    send_auction_won_email("winner", "winner@example.com", "Rolex", 500.0, 1, "test_token")

@patch("services.email_services.smtplib.SMTP_SSL")
def test_send_item_sold_email_success(mock_smtp):
    send_item_sold_email("seller@example.com", "seller", "Rolex", 500.0)
    mock_smtp.assert_called_once()
    
    mock_server = mock_smtp.return_value.__enter__.return_value
    mock_server.send_message.assert_called_once()

@patch("services.email_services.smtplib.SMTP_SSL")
def test_send_item_sold_email_failure(mock_smtp):
    mock_smtp.side_effect = Exception("SMTP Connection Failed")
    send_item_sold_email("seller@example.com", "seller", "Rolex", 500.0)

@patch("services.email_services.smtplib.SMTP_SSL")
def test_send_payment_receipt_email_success(mock_smtp):
    send_payment_receipt_email("buyer@test.com", "JohnBuyer", "Vintage Rolex", 500.0)
    mock_smtp.assert_called_once()
    mock_server = mock_smtp.return_value.__enter__.return_value
    mock_server.send_message.assert_called_once()

@patch("services.email_services.smtplib.SMTP_SSL")
def test_send_payment_receipt_email_failure(mock_smtp):
    mock_smtp.side_effect = Exception("SMTP Connection Failed")
    send_payment_receipt_email("buyer@test.com", "JohnBuyer", "Vintage Rolex", 500.0)

@patch("services.email_services.smtplib.SMTP_SSL")
def test_send_ship_item_email_success(mock_smtp):
    send_ship_item_email("SellerBob", "seller@test.com", "Vintage Rolex", "123 Main St")
    mock_smtp.assert_called_once()
    mock_server = mock_smtp.return_value.__enter__.return_value
    mock_server.send_message.assert_called_once()

@patch("services.email_services.smtplib.SMTP_SSL")
def test_send_ship_item_email_failure(mock_smtp):
    mock_smtp.side_effect = Exception("SMTP Connection Failed")
    send_ship_item_email("SellerBob", "seller@test.com", "Vintage Rolex", "123 Main St")


@patch("services.email_services.smtplib.SMTP_SSL")
def test_send_seller_refund_email_success(mock_smtp):
    send_seller_refund_email("seller", "seller@example.com", "Rolex", "Damaged")
    mock_smtp.assert_called_once()
    mock_server = mock_smtp.return_value.__enter__.return_value
    mock_server.send_message.assert_called_once()

@patch("services.email_services.smtplib.SMTP_SSL")
def test_send_seller_refund_email_failure(mock_smtp):
    mock_smtp.side_effect = Exception("SMTP Connection Failed")
    send_seller_refund_email("seller", "seller@example.com", "Rolex", "Damaged")

@patch("services.email_services.smtplib.SMTP_SSL")
def test_send_buyer_refund_email_success(mock_smtp):
    send_buyer_refund_email("buyer", "buyer@example.com", "Rolex")
    mock_smtp.assert_called_once()
    mock_server = mock_smtp.return_value.__enter__.return_value
    mock_server.send_message.assert_called_once()

@patch("services.email_services.smtplib.SMTP_SSL")
def test_send_buyer_refund_email_failure(mock_smtp):
    mock_smtp.side_effect = Exception("SMTP Connection Failed")
    send_buyer_refund_email("buyer", "buyer@example.com", "Rolex")