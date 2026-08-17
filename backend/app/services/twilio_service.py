from twilio.rest import Client
from app.config import settings


class TwilioService:
    def send_sos_alert(self, phone_numbers: list[str], message: str):
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN or not settings.TWILIO_PHONE_NUMBER:
            raise RuntimeError("Twilio is not configured")

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        results = []
        for phone in phone_numbers:
            results.append(
                client.messages.create(
                    body=message,
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=phone,
                )
            )
        return results


twilio_service = TwilioService()