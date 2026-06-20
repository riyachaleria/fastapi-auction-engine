"""
Email notification service.
Handles sending transactional emails (welcome, auction won, item sold) via SMTP.
Includes both plain text and HTML fallback versions for maximum compatibility.
"""
import smtplib
import ssl
import textwrap
from config import config
from email.message import EmailMessage

def send_welcome_email(username: str, user_email: str) -> None:
    """
    Sends a welcome email to a newly registered user.
    
    Args:
        username (str): The user's chosen username.
        user_email (str): The user's registered email address.
    """
    msg = EmailMessage()
    msg["Subject"] = "Welcome to BidBazaar!"
    msg["To"] = user_email
    msg["From"] = config.SMTP_EMAIL

    email_content_plain = f"""\
    Hi {username},
    Welcome to BidBazaar! Your account has been successfully created.
    Get ready to place some bids and win amazing items!
    
    Happy Bidding!
    - The BidBazaar Team
    """

    email_content_html = f"""\
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <h2 style="color: #2c3e50;">Hi {username},</h2>
        <p>Welcome to <strong>BidBazaar</strong>! Your account has been successfully created.</p>
        <p>Get ready to place some bids and win amazing items!</p>
        <br>
        <p>Happy Bidding!</p>
        <p><strong>- The BidBazaar Team</strong></p>
      </body>
    </html>
    """

    msg.set_content(textwrap.dedent(email_content_plain))
    msg.add_alternative(email_content_html, subtype='html')

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(user=config.SMTP_EMAIL, password=config.SMTP_PASSWORD)
            server.send_message(msg)

    except Exception as e:
        print(f"Failed to send email: {e}")

def send_auction_won_email(username: str, user_email: str, item_title: str, final_price: float) -> None:
    """
    Sends a congratulatory email to the winning bidder of an auction.
    
    Args:
        username (str): The winner's username.
        user_email (str): The winner's email address.
        item_title (str): The title of the won item.
        final_price (float): The final winning bid amount.
    """
    msg = EmailMessage()
    msg["Subject"] = f"You won the auction for {item_title}!"
    msg["To"] = user_email
    msg["From"] = config.SMTP_EMAIL

    email_content_plain = f"""\
    Congratulations {username}! 🎉
    
    You are the highest bidder! You have officially won the auction for {item_title}.
    Your winning bid was: ${final_price}
    
    Please log in to your account to complete your purchase.
    
    - The BidBazaar Team
    """

    email_content_html = f"""\
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <h2 style="color: #27ae60;">Congratulations {username}! 🎉</h2>
        <p>You are the highest bidder! You have officially won the auction for <strong>{item_title}</strong>.</p>
        <p>Your winning bid was: <strong>${final_price}</strong></p>
        <br>
        <p>Please log in to your account to complete your purchase.</p>
        <p><strong>- The BidBazaar Team</strong></p>
      </body>
    </html>
    """

    msg.set_content(textwrap.dedent(email_content_plain))
    msg.add_alternative(email_content_html, subtype='html')

    context= ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(user=config.SMTP_EMAIL, password=config.SMTP_PASSWORD)
            server.send_message(msg)
    
    except Exception as e:
        print(f"Failed to send email: {e}")

def send_item_sold_email(seller_email: str, username: str, item_title: str, final_price: float) -> None:
    """
    Sends a notification email to a seller when their item successfully sells.
    
    Args:
        seller_email (str): The seller's email address.
        username (str): The seller's username.
        item_title (str): The title of the sold item.
        final_price (float): The final closing price of the auction.
    """
    msg = EmailMessage()
    msg["Subject"] = f"Your item {item_title} has sold! 🎉"
    msg["To"] = seller_email
    msg["From"] = config.SMTP_EMAIL

    email_content_plain = f"""\
    Great news, {username}! 💰
    
    Your auction for {item_title} has officially ended!
    It successfully sold for a final price of: ${final_price}
    
    The winner will be contacting you shortly to arrange payment.
    
    - The BidBazaar Team
    """

    email_content_html = f"""\
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <h2 style="color: #2980b9;">Great news, {username}! 💰</h2>
        <p>Your auction for <strong>{item_title}</strong> has officially ended!</p>
        <p>It successfully sold for a final price of: <strong>${final_price}</strong></p>
        <br>
        <p>The winner will be contacting you shortly to arrange payment.</p>
        <p><strong>- The BidBazaar Team</strong></p>
      </body>
    </html>
    """
    msg.set_content(textwrap.dedent(email_content_plain))
    msg.add_alternative(email_content_html, subtype='html')

    context= ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(user=config.SMTP_EMAIL, password=config.SMTP_PASSWORD)
            server.send_message(msg)
    
    except Exception as e:
        print(f"Failed to send email: {e}")