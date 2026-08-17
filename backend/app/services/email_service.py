"""
services/email_service.py
---------------------------
OWNED BY MEMBER 4 (Repai). Wraps the Resend API - the only file that
knows how to actually send an email. Originally built against SendGrid
per the project spec, swapped to Resend after SendGrid/Twilio's phone
verification rejected the developer's number during signup. Documented
in PR - flag to instructor if asked.
"""

import resend

from app.config import settings

resend.api_key = settings.RESEND_API_KEY


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    if not settings.RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY is not set in .env")

    try:
        resend.Emails.send({
            "from": settings.RESEND_FROM_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        })
        return True
    except Exception as e:
        print(f"[Resend error] {e}")
        return False
