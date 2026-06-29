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

def send_auction_won_email(username: str, user_email: str, item_title: str, final_price: float, item_id: int, checkout_token: str) -> None:
    """
    Sends a congratulatory email to the winning bidder of an auction.
    
    Args:
        username (str): The winner's username.
        user_email (str): The winner's email address.
        item_title (str): The title of the won item.
        final_price (float): The final winning bid amount.
        item_id (int): The ID of the item won.
        checkout_token (str): The secure one-time token for checkout.
    """
    msg = EmailMessage()
    msg["Subject"] = f"You won the auction for {item_title}!"
    msg["To"] = user_email
    msg["From"] = config.SMTP_EMAIL

    checkout_url = f"http://localhost:8000/payment/checkout/{item_id}?token={checkout_token}"

    email_content_plain = f"""\
    Congratulations {username}! 🎉
    
    You are the highest bidder! You have officially won the auction for {item_title}.
    Your winning bid was: ${final_price}
    
    Please secure your item by completing your payment using the secure link below:
    {checkout_url}
    
    - The BidBazaar Team
    """

    email_content_html = f"""\
    <html>
      <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1a1a1a; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 30px 20px;">
        
        <div style="border-bottom: 1px solid #e5e5e5; padding-bottom: 20px; margin-bottom: 30px;">
            <h1 style="margin: 0; font-size: 24px; font-weight: 600;">BidBazaar</h1>
            <p style="margin: 5px 0 0 0; color: #666; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Auction Won</p>
        </div>

        <p style="font-size: 16px;">Hi {username},</p>
        <p style="font-size: 16px;">Congratulations! You were the highest bidder and have officially won the auction for <strong>{item_title}</strong>.</p>
        
        <div style="background-color: #f9f9f9; border: 1px solid #e5e5e5; border-radius: 4px; padding: 20px; margin: 30px 0;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding-bottom: 10px; color: #666; font-size: 14px;">Winning Bid</td>
                    <td style="padding-bottom: 10px; text-align: right; font-weight: 600; font-size: 18px;">${final_price}</td>
                </tr>
            </table>
        </div>

        <p style="color: #666; font-size: 14px;">Please secure your item by completing your payment using the secure checkout link below.</p>
        
        <div style="margin: 35px 0;">
            <a href="{checkout_url}" style="background-color: #1a1a1a; color: white; padding: 14px 28px; text-decoration: none; border-radius: 4px; font-weight: 500; font-size: 14px; display: inline-block;">Complete Payment</a>
        </div>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e5e5; color: #999; font-size: 12px;">
            <p style="margin: 0;">If the button doesn't work, copy and paste this link: <br>{checkout_url}</p>
            <p style="margin: 10px 0 0 0;">- The BidBazaar Team</p>
        </div>
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
    
    Your auction for {item_title} has officially ended and was won with a final bid of ${final_price}!
    
    We have just sent the winner a secure checkout link to process their payment. We will email you again the exact moment their payment clears so you can ship the item!
    
    - The BidBazaar Team
    """

    email_content_html = f"""\
    <html>
      <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1a1a1a; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 30px 20px;">
        <div style="border-bottom: 1px solid #e5e5e5; padding-bottom: 20px; margin-bottom: 30px;">
            <h1 style="margin: 0; font-size: 24px; font-weight: 600;">BidBazaar</h1>
            <p style="margin: 5px 0 0 0; color: #666; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Item Sold</p>
        </div>
        
        <p style="font-size: 16px;">Hi {username},</p>
        <p style="font-size: 16px;">Great news! Your auction for <strong>{item_title}</strong> has officially ended and was won with a final bid of <strong>${final_price}</strong>.</p>
        
        <p style="color: #666; font-size: 14px;">We have sent the winner a secure checkout link to process their payment. <strong>We will email you again the exact moment their payment clears</strong> so you can ship the item!</p>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e5e5; color: #999; font-size: 12px;">
            <p style="margin: 0;">- The BidBazaar Team</p>
        </div>
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

def send_payment_receipt_email(username: str, useremail: str, item_title: str, amount_paid: float) -> None:
    message = EmailMessage()
    message["Subject"] = f"Receipt: Payment for {item_title}"
    message["From"] = config.SMTP_EMAIL
    message["To"] = useremail

    email_plain_content = f"""\
    Payment Receipt
    
    Hi {username},
    
    Your payment of ${amount_paid} for {item_title} has been securely processed.
    
    We have notified the seller to package and ship your item to the address you provided during checkout.
    
    Thank you for shopping at BidBazaar.
    """

    email_html_content = f"""\
    <html>
      <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1a1a1a; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 30px 20px;">
        
        <div style="border-bottom: 1px solid #e5e5e5; padding-bottom: 20px; margin-bottom: 30px;">
            <h1 style="margin: 0; font-size: 24px; font-weight: 600;">BidBazaar</h1>
            <p style="margin: 5px 0 0 0; color: #666; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Payment Receipt</p>
        </div>

        <p style="font-size: 16px;">Hi {username},</p>
        <p style="font-size: 16px;">Your payment has been successfully processed.</p>
        
        <div style="background-color: #f9f9f9; border: 1px solid #e5e5e5; border-radius: 4px; padding: 20px; margin: 30px 0;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding-bottom: 10px; color: #666; font-size: 14px;">Item Purchased</td>
                    <td style="padding-bottom: 10px; text-align: right; font-weight: 500;">{item_title}</td>
                </tr>
                <tr>
                    <td style="padding-top: 10px; border-top: 1px solid #e5e5e5; color: #666; font-size: 14px;">Total Paid</td>
                    <td style="padding-top: 10px; border-top: 1px solid #e5e5e5; text-align: right; font-weight: 600; font-size: 18px;">${amount_paid}</td>
                </tr>
            </table>
        </div>

        <p style="color: #666; font-size: 14px;">We have notified the seller to package and ship your item to the address you provided during checkout. You will receive it soon.</p>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e5e5; color: #999; font-size: 12px;">
            <p style="margin: 0;">Thank you for shopping at BidBazaar.</p>
        </div>
      </body>
    </html>
    """

    message.set_content(textwrap.dedent(email_plain_content))
    message.add_alternative(email_html_content, subtype="html")

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(user=config.SMTP_EMAIL, password=config.SMTP_PASSWORD)
            server.send_message(message)
    except Exception as e:
        print(f"Failed to send email: {e}")

def send_ship_item_email(seller_name: str, seller_email: str, item_title: str, buyer_address: str) -> None:
    message = EmailMessage()
    message["Subject"] = f"Action Required: Ship {item_title}"
    message["From"] = config.SMTP_EMAIL
    message["To"] = seller_email

    email_plain_content = f"""\
    Payment Cleared: Action Required
    
    Hi {seller_name},
    
    The buyer has successfully paid for {item_title}. Your payout is now secured in your Stripe account.
    
    Please securely package and ship the item to the following address:
    
    {buyer_address}
    
    - The BidBazaar Team
    """

    email_html_content = f"""\
    <html>
      <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1a1a1a; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 30px 20px;">
        
        <div style="border-bottom: 1px solid #e5e5e5; padding-bottom: 20px; margin-bottom: 30px;">
            <h1 style="margin: 0; font-size: 24px; font-weight: 600;">BidBazaar</h1>
            <p style="margin: 5px 0 0 0; color: #666; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Action Required</p>
        </div>

        <p style="font-size: 16px;">Hi {seller_name},</p>
        <p style="font-size: 16px;">The buyer has successfully paid for <strong>{item_title}</strong>. Your payout is now secured in your Stripe account.</p>
        
        <div style="background-color: #f9f9f9; border: 1px solid #e5e5e5; border-radius: 4px; padding: 20px; margin: 30px 0;">
            <p style="margin: 0 0 10px 0; color: #666; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Ship To:</p>
            <p style="margin: 0; font-family: monospace; font-size: 14px; white-space: pre-line; line-height: 1.5;">{buyer_address}</p>
        </div>

        <p style="color: #666; font-size: 14px;">Please safely package and ship the item to the buyer at the address above as soon as possible.</p>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e5e5; color: #999; font-size: 12px;">
            <p style="margin: 0;">- The BidBazaar Team</p>
        </div>
      </body>
    </html>
    """

    message.set_content(textwrap.dedent(email_plain_content))
    message.add_alternative(email_html_content, subtype="html")

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(user=config.SMTP_EMAIL, password=config.SMTP_PASSWORD)
            server.send_message(message)
    except Exception as e:
        print(f"Failed to send email: {e}")

def send_seller_refund_email(username: str, useremail: str, item_title: str, reason: str) -> None:
    """
    Sends an email to the seller notifying them that the buyer has requested a refund.
    
    Args:
        username (str): The seller's username.
        useremail (str): The seller's email address.
        item_title (str): The title of the refunded item.
        reason (str): The reason provided by the buyer for the refund.
    """
    msg = EmailMessage()
    msg["Subject"] = f"Refund Requested: {item_title}"
    msg["To"] = useremail
    msg["From"] = config.SMTP_EMAIL

    email_plain_content = f"""\
    Refund Requested
    
    Hi {username},
    
    The buyer has requested a refund for {item_title} and it is currently being processed. 
    They have been instructed to ship the item back to you.
    
    Reason provided by the buyer:
    "{reason}"
    
    - The BidBazaar Team
    """

    email_html_content = f"""\
    <html>
      <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1a1a1a; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 30px 20px;">
        
        <div style="border-bottom: 1px solid #e5e5e5; padding-bottom: 20px; margin-bottom: 30px;">
            <h1 style="margin: 0; font-size: 24px; font-weight: 600;">BidBazaar</h1>
            <p style="margin: 5px 0 0 0; color: #666; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Refund Requested</p>
        </div>

        <p style="font-size: 16px;">Hi {username},</p>
        <p style="font-size: 16px;">The buyer has requested a refund for <strong>{item_title}</strong> and the transaction is being reversed. They have been instructed to package and ship the item back to you.</p>
        
        <div style="background-color: #fff3f3; border: 1px solid #ffcaca; border-radius: 4px; padding: 20px; margin: 30px 0;">
            <p style="margin: 0 0 10px 0; color: #d63031; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Reason for Refund:</p>
            <p style="margin: 0; font-family: sans-serif; font-size: 14px; font-style: italic; line-height: 1.5;">"{reason}"</p>
        </div>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e5e5; color: #999; font-size: 12px;">
            <p style="margin: 0;">- The BidBazaar Team</p>
        </div>
      </body>
    </html>
    """

    msg.set_content(textwrap.dedent(email_plain_content))
    msg.add_alternative(email_html_content, subtype="html")

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(user=config.SMTP_EMAIL, password=config.SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")


def send_buyer_refund_email(username: str, useremail: str, item_title: str) -> None:
    """
    Sends a confirmation email to the buyer acknowledging their refund request.
    
    Args:
        username (str): The buyer's username.
        useremail (str): The buyer's email address.
        item_title (str): The title of the refunded item.
    """
    msg = EmailMessage()
    msg["Subject"] = f"Refund Processing: {item_title}"
    msg["To"] = useremail
    msg["From"] = config.SMTP_EMAIL

    email_plain_content = f"""\
    Refund Processing Initiated
    
    Hi {username},
    
    We have successfully initiated the refund for {item_title}. 
    The funds will be returned to your original payment method within 24 hours.
    
    Please safely package and ship the item back to the seller as soon as possible.
    
    - The BidBazaar Team
    """

    email_html_content = f"""\
    <html>
      <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1a1a1a; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 30px 20px;">
        
        <div style="border-bottom: 1px solid #e5e5e5; padding-bottom: 20px; margin-bottom: 30px;">
            <h1 style="margin: 0; font-size: 24px; font-weight: 600;">BidBazaar</h1>
            <p style="margin: 5px 0 0 0; color: #666; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Refund Processing</p>
        </div>

        <p style="font-size: 16px;">Hi {username},</p>
        <p style="font-size: 16px;">We have successfully initiated the refund for <strong>{item_title}</strong>.</p>
        <p style="font-size: 16px;">The funds will be returned to your original payment method within <strong>24 hours</strong>.</p>
        
        <div style="background-color: #f9f9f9; border: 1px solid #e5e5e5; border-radius: 4px; padding: 20px; margin: 30px 0;">
            <p style="margin: 0 0 10px 0; color: #666; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Action Required:</p>
            <p style="margin: 0; font-family: sans-serif; font-size: 14px; line-height: 1.5;">Please safely package and ship the item back to the seller as soon as possible.</p>
        </div>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e5e5; color: #999; font-size: 12px;">
            <p style="margin: 0;">- The BidBazaar Team</p>
        </div>
      </body>
    </html>
    """

    msg.set_content(textwrap.dedent(email_plain_content))
    msg.add_alternative(email_html_content, subtype="html")

    context = ssl.create_default_context()
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(user=config.SMTP_EMAIL, password=config.SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")