from __future__ import annotations

import os
import datetime as dt
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from langchain.tools import tool
from zoneinfo import ZoneInfo 

SCOPES: List[str] = ["https://www.googleapis.com/auth/calendar"]
TIMEZONE = ZoneInfo("Asia/Kolkata")


def get_service():
    """Authenticate and return a Google Calendar service."""
    creds: Credentials | None = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def is_slot_free(service, start_dt: dt.datetime, end_dt: dt.datetime) -> bool:
    """
    Check if the primary calendar has any event between start_dt and end_dt.
    Datetimes must be timezone-aware.
    """
    events = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=start_dt.isoformat(),
            timeMax=end_dt.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
        .get("items", [])
    )
    return len(events) == 0


def create_event(service, name: str, email: str, number: str,
                 start_dt: dt.datetime, end_dt: dt.datetime) -> None:
    """Create a new 1-hour appointment event."""
    event = {
        "summary": f"Appointment with {name}",
        "description": f"Email: {email}\nPhone: {number}",
        "start": {"dateTime": start_dt.isoformat(), "timeZone": str(TIMEZONE)},
        "end":   {"dateTime": end_dt.isoformat(), "timeZone": str(TIMEZONE)},
        "attendees": [{"email": email}],
    }
    service.events().insert(calendarId="primary", body=event).execute()
    print("✅ Event created successfully.")
