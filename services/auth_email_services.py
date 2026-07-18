"""
Authentication email notification service.
Handles dispatching transactional One-Time Verification codes (OTPs) via Brevo HTTP API v3.
Includes responsive HTML layout templates formatted for security verification emails.
"""
import httpx
from config import config
from fastapi import HTTPException, status

async def send_otp_email_via_brevo(email: str, otp_code: int) -> None:
    """
    Asynchronously sends a 6-digit verification OTP code to the requested user via Brevo API v3.
    Constructs a responsive HTML template containing the code and its expiration details.
    
    Args:
        email (str): The recipient's email address.
        otp_code (int): The numeric 6-digit verification code.
        
    Raises:
        HTTPException: If the Brevo HTTP API request fails or returns a non-201 status code.
    """
    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "accept" : "application/json",
        "api-key" : config.BREVO_KEY,
        "content-type" : "application/json"
    }

    html_content = f"""\
    <html>
      <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1a1a1a; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 30px 20px;">
        
        <div style="border-bottom: 1px solid #e5e5e5; padding-bottom: 20px; margin-bottom: 30px;">
            <h1 style="margin: 0; font-size: 24px; font-weight: 600;">BidBazaar</h1>
            <p style="margin: 5px 0 0 0; color: #666; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Security & Verification</p>
        </div>

        <p style="font-size: 16px;">Hi there,</p>
        <p style="font-size: 16px;">We received a request to reset the password for your <strong>BidBazaar</strong> account. Use the verification code below to proceed:</p>
        
        <div style="background-color: #f9f9f9; border: 1px solid #e5e5e5; border-radius: 6px; padding: 25px; margin: 30px 0; text-align: center;">
            <p style="margin: 0 0 10px 0; color: #666; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Your Verification Code</p>
            <p style="margin: 0; font-family: monospace; font-size: 32px; font-weight: 700; letter-spacing: 6px; color: #1a1a1a;">{otp_code}</p>
        </div>

        <p style="color: #666; font-size: 14px;">This code will expire in <strong>10 minutes</strong>. If you did not request a password reset, please ignore this email or contact support if you have concerns.</p>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e5e5; color: #999; font-size: 12px;">
            <p style="margin: 0;">- The BidBazaar Team</p>
        </div>
      </body>
    </html>
    """

    payload = {
        "sender" : {
            "name" : "BidBazaar Auth Engine",
            "email" : config.SMTP_EMAIL
        },
        "to" : [
            {"email" : email}
        ],
        "subject" : "Your 6-Digit Password Reset Code 🔒",
        "htmlContent" : html_content
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url,headers=headers,json=payload)

            if response.status_code != 201:
                print(f"Brevo API error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Brevo API error {response.status_code}")
            
        except Exception as e:
            print(f"Failed to send Brevo OTP email: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")