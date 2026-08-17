import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


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
# CHECK CREDENTIALS
# ============================================================

def check_credentials_file():

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
        scopes=SCOPES,
        autogenerate_code_verifier=False
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
        scopes=SCOPES,
        autogenerate_code_verifier=False
    )

    flow.redirect_uri = REDIRECT_URI

    try:

        flow.fetch_token(
            code=code
        )

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Google authentication failed: {str(e)}"
            )
        )

    credentials = flow.credentials

    try:

        with open(
            TOKEN_FILE,
            "w"
        ) as token:

            token.write(
                credentials.to_json()
            )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Could not save Google token: {str(e)}"
            )
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

        # Refresh expired access token
        if credentials.expired and credentials.refresh_token:

            credentials.refresh(
                Request()
            )

            # Save refreshed credentials
            with open(
                TOKEN_FILE,
                "w"
            ) as token:

                token.write(
                    credentials.to_json()
                )

        return credentials

    except Exception as e:

        raise HTTPException(
            status_code=401,
            detail=(
                "Could not load or refresh Google credentials: "
                f"{str(e)}"
            )
        )


# ============================================================
# BUILD CALENDAR SERVICE
# ============================================================

def get_calendar_service():

    credentials = get_calendar_credentials()

    try:

        service = build(
            "calendar",
            "v3",
            credentials=credentials
        )

        return service

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not connect to Google Calendar API: "
                f"{str(e)}"
            )
        )


# ============================================================
# CALENDAR STATUS
# ============================================================

@router.get("/status")
def calendar_status():

    if not os.path.exists(TOKEN_FILE):

        return {
            "connected": False,
            "message": "Google Calendar is not connected."
        }

    try:

        service = get_calendar_service()

        calendar = service.calendars().get(
            calendarId="primary"
        ).execute()

        return {
            "connected": True,
            "calendar": calendar.get("summary"),
            "message": (
                "Google Calendar is connected successfully."
            )
        }

    except HTTPException:
        raise

    except HttpError as e:

        return {
            "connected": False,
            "message": (
                f"Google Calendar API error: {str(e)}"
            )
        }

    except Exception as e:

        return {
            "connected": False,
            "message": (
                f"Calendar connection error: {str(e)}"
            )
        }


# ============================================================
# GET UPCOMING EVENTS
# ============================================================

@router.get("/events")
def get_calendar_events():

    try:

        service = get_calendar_service()

        now = datetime.now(
            timezone.utc
        ).isoformat()

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

    except HTTPException:
        raise

    except HttpError as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Could not retrieve Google Calendar events: "
                f"{str(e)}"
            )
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Could not retrieve calendar events: "
                f"{str(e)}"
            )
        )


# ============================================================
# CREATE GOOGLE CALENDAR EVENT
# ============================================================

def create_google_calendar_event(
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = ""
):

    service = get_calendar_service()

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

    try:

        created_event = service.events().insert(
            calendarId="primary",
            body=event
        ).execute()

        return created_event

    except HttpError as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Google Calendar event creation failed: "
                f"{str(e)}"
            )
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Google Calendar event creation failed: "
                f"{str(e)}"
            )
        )


# ============================================================
# CREATE EVENT API
# ============================================================

@router.post("/events")
def create_calendar_event(
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = ""
):

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

        "event_id": created_event.get(
            "id"
        ),

        "event_link": created_event.get(
            "htmlLink"
        )
    }


# ============================================================
# UPDATE GOOGLE CALENDAR EVENT
# ============================================================

def update_google_calendar_event(
    event_id: str,
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = ""
):

    service = get_calendar_service()

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

    try:

        updated_event = service.events().update(
            calendarId="primary",
            eventId=event_id,
            body=event
        ).execute()

        return updated_event

    except HttpError as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Google Calendar event update failed: "
                f"{str(e)}"
            )
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Google Calendar event update failed: "
                f"{str(e)}"
            )
        )


# ============================================================
# DELETE GOOGLE CALENDAR EVENT
# ============================================================

def delete_google_calendar_event(
    event_id: str
):

    service = get_calendar_service()

    try:

        service.events().delete(
            calendarId="primary",
            eventId=event_id
        ).execute()

        return True

    except HttpError as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Google Calendar event deletion failed: "
                f"{str(e)}"
            )
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Google Calendar event deletion failed: "
                f"{str(e)}"
            )
        )


# ============================================================
# DELETE EVENT API
# ============================================================

@router.delete("/events/{event_id}")
def delete_calendar_event(
    event_id: str
):

    try:

        delete_google_calendar_event(
            event_id
        )

        return {
            "message": (
                "Calendar event deleted successfully."
            )
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Could not delete calendar event: "
                f"{str(e)}"
            )
        )