import resend

from app.config import settings

resend.api_key = settings.RESEND_API_KEY


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Returns True if Resend accepted the email, False otherwise."""
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