"""
services/sms_service.py
--------------------------
SMS delivery for emergency alerts (SOS, fall incidents, missed check-ins -
Member 3 Faisal's routers). Originally built against Twilio, but every
account Faisal tried to open kept failing Twilio's phone-verification-at-
signup step - the same failure mode that already forced email off SendGrid
onto Resend (see email_service.py's docstring). Swapped to Textbelt
instead: no account or phone verification needed at all, just an API key
you get immediately after a card payment (or the free shared key below).

Defaults to Textbelt's free key (`key=textbelt`) - 1 message/day, pooled
globally across every free Textbelt user worldwide, and outright blocked
for some destination countries "due to abuse" (confirmed live against a
+1 number). Treat a quota/country failure as expected, not a bug, while
running on the free key. Set TEXTBELT_API_KEY in .env to a paid key (still
zero verification required to buy one) for reliable delivery.

Same interface as the old twilio_service.py on purpose - callers
(routers/emergency.py, fall_incidents.py, safety_checkin.py) only ever
call send_sos_alert(phone_numbers, message) and catch its exceptions, so
this swap needed zero changes to Faisal's actual logic, just the import
line and call site in each of his three files.
"""

import requests

from app.config import settings

TEXTBELT_URL = "https://textbelt.com/text"


class SmsService:
    def send_sos_alert(self, phone_numbers: list[str], message: str):
        results = []
        for phone in phone_numbers:
            response = requests.post(
                TEXTBELT_URL,
                data={
                    "phone": phone,
                    "message": message,
                    "key": settings.TEXTBELT_API_KEY,
                },
                timeout=10,
            )
            result = response.json()
            if not result.get("success"):
                raise RuntimeError(result.get("error", "Textbelt send failed"))
            results.append(result)
        return results


sms_service = SmsService()
