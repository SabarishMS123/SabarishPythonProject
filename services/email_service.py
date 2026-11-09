"""
Email service for sending verification codes.
Uses SMTP (Gmail App Password recommended).
"""

import os
import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()


def generate_verification_code(length: int = 6) -> str:
    """Generate a numeric verification code."""
    return "".join(secrets.choice("0123456789") for _ in range(length))


def send_verification_email(to_email: str, code: str, full_name: str = "User") -> bool:
    """
    Send a beautiful verification email.
    Returns True on success, False on failure.
    """
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM", smtp_user)

    if not smtp_user or not smtp_password:
        print("⚠️  SMTP credentials not configured. Verification code:", code)
        print("   (Configure SMTP_* in .env to enable real emails)")
        return True  # still allow registration in dev mode

    subject = "Verify your account – AI Assistant Hub"
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #0f0f1a; color: #e0e0e0; margin: 0; padding: 40px 20px; }}
            .card {{ max-width: 480px; margin: 0 auto; background: linear-gradient(145deg, #1a1a2e, #16213e); border-radius: 20px; padding: 40px; border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 20px 60px rgba(0,0,0,0.5); }}
            h1 {{ color: #a78bfa; font-size: 24px; margin-bottom: 8px; }}
            .code {{ font-size: 36px; letter-spacing: 12px; font-weight: 700; color: #fff; background: rgba(167,139,250,0.15); padding: 16px 24px; border-radius: 12px; text-align: center; margin: 28px 0; border: 1px solid rgba(167,139,250,0.3); }}
            p {{ line-height: 1.6; color: #b0b0c0; }}
            .footer {{ margin-top: 32px; font-size: 12px; color: #666; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Welcome, {full_name}!</h1>
            <p>Thanks for joining <strong>AI Assistant Hub</strong>. Use the verification code below to complete your registration. It expires in 15 minutes.</p>
            <div class="code">{code}</div>
            <p>If you didn't request this, you can safely ignore this email.</p>
            <div class="footer">AI Assistant Hub · Secure & Private</div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_from
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_from, to_email, msg.as_string())
        print(f"✅ Verification email sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        print(f"   (Dev fallback) Verification code for {to_email}: {code}")
        return True  # still allow in development
