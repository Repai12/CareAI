import os
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/calendar",
    tags=["Google Calendar"]
)


# ============================================================
# FILE LOCATIONS
# ============================================================

# calendar.py is inside:
#
# backend/app/
#
# dirname(__file__)              -> backend/app
# dirname(dirname(__file__))     -> backend

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

CREDENTIALS_FILE = os.path.join(
    BASE_DIR,
    "credentials.json"
)

TOKEN_FILE = os.path.join(
    BASE_DIR,
    "token.json"
)


# ============================================================
# GOOGLE CALENDAR SETTINGS
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/calendar"
]

REDIRECT_URI = "http://localhost:8000/calendar/callback"


# ============================================================
# CHECK CREDENTIALS FILE
# ============================================================

def check_credentials_file():
    """
    Make sure Google's credentials.json exists
    in the backend folder.
    """

    if not os.path.exists(CREDENTIALS_FILE):
        raise HTTPException(
            status_code=404,
            detail=(
                "credentials.json not found in backend folder. "
                f"Expected location: {CREDENTIALS_FILE}"
            )
        )


# ============================================================
# GOOGLE LOGIN
# ============================================================

@router.get("/login")
def calendar_login():

    check_credentials_file()

    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES
    )

    flow.redirect_uri = REDIRECT_URI

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )

    return RedirectResponse(
        url=authorization_url
    )


# ============================================================
# GOOGLE CALLBACK
# ============================================================

@router.get("/callback")
def calendar_callback(code: str):

    check_credentials_file()

    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES
    )

    flow.redirect_uri = REDIRECT_URI

    try:

        flow.fetch_token(
            code=code
        )

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=f"Google authentication failed: {str(e)}"
        )

    credentials = flow.credentials

    # Save Google's access/refresh token
    with open(TOKEN_FILE, "w") as token:

        token.write(
            credentials.to_json()
        )

    return {
        "message": "Google Calendar connected successfully!",
        "status": "authenticated"
    }


# ============================================================
# LOAD GOOGLE CREDENTIALS
# ============================================================

def get_calendar_credentials():

    if not os.path.exists(TOKEN_FILE):

        raise HTTPException(
            status_code=401,
            detail=(
                "Google Calendar is not connected yet. "
                "Please visit /calendar/login first."
            )
        )

    try:

        credentials = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=f"Could not load Google credentials: {str(e)}"
        )

    return credentials


# ============================================================
# TEST CALENDAR CONNECTION
# ============================================================

@router.get("/status")
def calendar_status():

    if not os.path.exists(TOKEN_FILE):

        return {
            "connected": False,
            "message": "Google Calendar is not connected."
        }

    try:

        credentials = get_calendar_credentials()

        service = build(
            "calendar",
            "v3",
            credentials=credentials
        )

        calendar = service.calendars().get(
            calendarId="primary"
        ).execute()

        return {
            "connected": True,
            "calendar": calendar.get("summary"),
            "message": "Google Calendar is connected successfully."
        }

    except Exception as e:

        return {
            "connected": False,
            "message": f"Calendar connection error: {str(e)}"
        }


# ============================================================
# GET UPCOMING EVENTS
# ============================================================

@router.get("/events")
def get_calendar_events():

    credentials = get_calendar_credentials()

    try:

        service = build(
            "calendar",
            "v3",
            credentials=credentials
        )

        now = datetime.utcnow().isoformat() + "Z"

        events_result = service.events().list(
            calendarId="primary",
            timeMin=now,
            maxResults=20,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get(
            "items",
            []
        )

        formatted_events = []

        for event in events:

            start = event.get(
                "start",
                {}
            )

            formatted_events.append({
                "id": event.get("id"),
                "title": event.get(
                    "summary",
                    "No title"
                ),
                "description": event.get(
                    "description",
                    ""
                ),
                "start": start.get(
                    "dateTime",
                    start.get("date")
                ),
                "location": event.get(
                    "location",
                    ""
                )
            })

        return {
            "events": formatted_events
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Could not retrieve calendar events: {str(e)}"
            )
        )


# ============================================================
# CREATE GOOGLE CALENDAR EVENT HELPER
# ============================================================

def create_google_calendar_event(
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = ""
):

    credentials = get_calendar_credentials()

    service = build(
        "calendar",
        "v3",
        credentials=credentials
    )

    event = {
        "summary": title,
        "description": description,
        "location": location,
        "start": {
            "dateTime": start_time,
            "timeZone": "Asia/Dhaka"
        },
        "end": {
            "dateTime": end_time,
            "timeZone": "Asia/Dhaka"
        }
    }

    created_event = service.events().insert(
        calendarId="primary",
        body=event
    ).execute()

    return created_event


# ============================================================
# CREATE CALENDAR APPOINTMENT API ENDPOINT
# ============================================================

@router.post("/events")
def create_calendar_event(
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = ""
):

    try:

        created_event = create_google_calendar_event(
            title=title,
            start_time=start_time,
            end_time=end_time,
            description=description,
            location=location
        )

        return {
            "message": (
                "Appointment added to Google Calendar successfully!"
            ),
            "event_id": created_event.get("id"),
            "event_link": created_event.get("htmlLink")
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Could not create calendar event: {str(e)}"
            )
        )
# ============================================================
# UPDATE GOOGLE CALENDAR EVENT HELPER
# ============================================================

def update_google_calendar_event(
    event_id: str,
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = ""
):

    credentials = get_calendar_credentials()

    service = build(
        "calendar",
        "v3",
        credentials=credentials
    )

    event = {
        "summary": title,
        "description": description,
        "location": location,
        "start": {
            "dateTime": start_time,
            "timeZone": "Asia/Dhaka"
        },
        "end": {
            "dateTime": end_time,
            "timeZone": "Asia/Dhaka"
        }
    }

    updated_event = service.events().update(
        calendarId="primary",
        eventId=event_id,
        body=event
    ).execute()

    return updated_event
# ============================================================
# DELETE GOOGLE CALENDAR EVENT HELPER
# ============================================================

def delete_google_calendar_event(
    event_id: str
):

    credentials = get_calendar_credentials()

    service = build(
        "calendar",
        "v3",
        credentials=credentials
    )

    service.events().delete(
        calendarId="primary",
        eventId=event_id
    ).execute()

    return True

# ============================================================
# DELETE CALENDAR EVENT
# ============================================================

@router.delete("/events/{event_id}")
def delete_calendar_event(
    event_id: str
):

    credentials = get_calendar_credentials()

    try:

        service = build(
            "calendar",
            "v3",
            credentials=credentials
        )

        service.events().delete(
            calendarId="primary",
            eventId=event_id
        ).execute()

        return {
            "message": "Calendar event deleted successfully."
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Could not delete calendar event: {str(e)}"
            )
        )