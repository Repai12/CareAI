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
        # Every caller (auth verification/reset, weekly report, doctor AI
        # summary) treats this as a normal "delivery failed" outcome and
        # logs/notifies accordingly - raising here instead of returning
        # False previously crashed the weekly report and AI summary jobs
        # outright whenever no key was configured (the default state per
        # .env.example), instead of degrading gracefully like every other
        # third-party call in this app is supposed to (README S11).
        print("[Resend] RESEND_API_KEY is not set - email not sent")
        return False

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
