from twilio.rest import Client

from app.config import settings


def send_sms(to_phone: str, message: str):
    if not settings.TWILIO_ACCOUNT_SID:
        raise RuntimeError("Twilio Account SID is not configured")

    if not settings.TWILIO_AUTH_TOKEN:
        raise RuntimeError("Twilio Auth Token is not configured")

    if not settings.TWILIO_PHONE_NUMBER:
        raise RuntimeError("Twilio phone number is not configured")

    client = Client(
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN,
    )

    return client.messages.create(
        body=message,
        from_=settings.TWILIO_PHONE_NUMBER,
        to=to_phone,
    )