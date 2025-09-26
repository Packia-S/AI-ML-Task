from __future__ import annotations
import os
import datetime as dt
from typing import List
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dateutil import parser
from datetime import datetime, time


from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from zoneinfo import ZoneInfo  # Python 3.9+

from config import settings
from schema import AvailabilityCheck

SCOPES: List[str] = ["https://www.googleapis.com/auth/calendar"]
TIMEZONE = ZoneInfo("Asia/Kolkata")
csv_file = "record_datas.csv"

HR_EMAIL = settings.hr_email
SENDER_EMAIL = settings.sender_email
APP_PASSWORD = settings.app_password

# Ensure CSV exists
if not os.path.exists(csv_file):
    df = pd.DataFrame(columns=["fullname", "email_id", "phone_number", "date", "time"])
    df.to_csv(csv_file, index=False)



# from datetime import datetime, time

def normalize_time(time_input) -> str:
    """
        Normalize time input to HH:MM 24-hour format.
        Accepts time as str or datetime.time or datetime.datetime.
        Accept "2025-9-29" and return "2025-09-29"
        Returns: str in HH:MM format
        
    """
    
    if isinstance(time_input, datetime):
        return time_input.strftime("%H:%M")

    if isinstance(time_input, str):
        # Try multiple formats
        for fmt in ["%H:%M", "%H:%M:%S", "%I:%M %p", "%I %p"]:
            try:
                return datetime.strptime(time_input, fmt).strftime("%H:%M")
            except ValueError:
                continue
        raise ValueError(f"Invalid time format: {time_input}")

    raise TypeError(f"Unsupported type for time: {type(time_input)}")


# def is_available(check: AvailabilityCheck) -> str | bool:
#     """Check availability for a given date and time.

#     Args:
#         check (AvailabilityCheck): The availability check parameters.

#     Returns:
#         str | bool: Availability status or error message.
#     """
    
#     csv_file = "record_datas.csv"
#     df = pd.read_csv(csv_file) if os.path.exists(csv_file) else pd.DataFrame(columns=["fullname","email_id","phone_number","date","time"])
    
#     date_val = check.date
#     time_val = normalize_time(check.time)

#     conflict = df[
#         (df["date"] == date_val)
#         & (df["time"] == time_val)
#         & ((check.email_id is None) | (df["email_id"] != check.email_id))
#     ]

#     if conflict.empty:
#         return True
#     else:
#         return f"⚠️ Slot {date_val} {time_val} is already booked."

def is_available(record: AvailabilityCheck) -> bool:
    """
        Check if the given date and time slot is available for scheduling.
    """
    df = pd.read_csv(csv_file)
    
    # Normalize the CSV time column
    df["time"] = df["time"].apply(normalize_time)
    
    # Convert record values into strings for comparison
    record_date = record.date.strftime("%Y-%m-%d")
    record_time = normalize_time(record.time) 

    if not df[
        (df["date"].astype(str) == record_date) & 
        (df["time"].astype(str) == record_time)
    ].empty:
        return f"Slot already booked"   # Slot already booked

    return True 

    

def send_to_hr(subject: str, body: str):
    """
    Send appointment details to HR via email.
    Args:
        subject (str): Email subject.
        body (str): Email body.
    Returns: None
    """
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = HR_EMAIL
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, HR_EMAIL, msg.as_string())
        print("✅ Mail successfully sent to HR")



def get_calendar_service():
    """
        Authenticate and return a Google Calendar service using existing credentials.json/token.json.
        
    """
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





def parse_datetime(date_str: str, time_str: str):
    """
    Converts human-readable date & time strings into a datetime object.
    Examples:
      date_str = '25 September 2025'
      time_str = '9 pm'
    Returns: datetime object
    """
    dt_combined = f"{date_str} {time_str}"
    try:
        dt_obj = parser.parse(dt_combined)
        return dt_obj
    except Exception as e:
        raise ValueError(
            "Date format must be like almost any human-readable date & time, e.g., '25 September 2025 at 9 pm'"
        ) from e


def schedule_appointment(name, email, phone, date_str, time_str):
    """
    Schedule an appointment in Google Calendar.
    date_str: '23rd September 2025' or '23 September 2025'
    time_str: '9 am', '14:30', etc.
    """
    service = get_calendar_service()
    start_dt = parse_datetime(date_str, time_str)
    end_dt = start_dt + dt.timedelta(minutes = 30)
    
    event = {
        "summary": f"Appointment with {name}",
        "description": f"{name} | {email} | {phone}",
        "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Kolkata"},
    }
    service.events().insert(calendarId="primary", body = event).execute()