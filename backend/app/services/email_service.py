"""
services/email_service.py
---------------------------
OWNED BY MEMBER 4 (Repai). Wraps email delivery - the only file that
knows how to actually send an email. History: SendGrid -> Resend, both
rejected the developer's number/domain at signup, then Resend's own
unverified-domain sandbox mode turned out to only deliver to the
account's own signup address regardless - confirmed live via Resend's
own API error naming that exact address. Swapped to Gmail SMTP: a real
personal Gmail account has neither restriction, sends to anyone
immediately, no domain or account verification needed beyond a normal
Google App Password.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    if not settings.GMAIL_ADDRESS or not settings.GMAIL_APP_PASSWORD:
        # Every caller (password reset, weekly report, doctor AI summary)
        # treats this as a normal "delivery failed" outcome and
        # logs/notifies accordingly - raising here instead of returning
        # False would crash those jobs outright whenever no credentials
        # are configured (the default state per .env.example), instead of
        # degrading gracefully like every other third-party call in this
        # app is supposed to (README S11).
        print("[Gmail SMTP] GMAIL_ADDRESS/GMAIL_APP_PASSWORD not set - email not sent")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.GMAIL_ADDRESS
    msg["To"] = to_email
    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(settings.GMAIL_ADDRESS, settings.GMAIL_APP_PASSWORD)
            server.sendmail(settings.GMAIL_ADDRESS, [to_email], msg.as_string())
        return True
    except Exception as e:
        print(f"[Gmail SMTP error] {e}")
        return False
