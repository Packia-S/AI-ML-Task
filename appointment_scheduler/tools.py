from schema import RecordAdd, UpdateRecord, AvailabilityCheck, DeleteRecord
from utils import (
    is_available,
    send_to_hr,
    normalize_time,
    schedule_appointment,
    parse_datetime,
    get_calendar_service,
)
from datetime import datetime, timedelta
from langchain_core.tools import tool, StructuredTool
import pandas as pd
import os

csv_file = "record_datas.csv"


def load_csv() -> pd.DataFrame:
    """
        Load CSV or return empty DataFrame with correct columns.
        Returns: pd.DataFrame with columns ["fullname", "email_id", "phone_number", "date", "time"]
    """
    if os.path.exists(csv_file):
        return pd.read_csv(csv_file)
    else:
        return pd.DataFrame(columns=["fullname", "email_id", "phone_number", "date", "time"])


@tool
def add_record(record: RecordAdd) -> str:
    """
        Add a new appointment and sync with Google Calendar.
        1. Check availability
        2. Save to CSV
        3. Add to Google Calendar
        4. Notify HR via email
    """
    df = load_csv()

    date_str = record.date.strftime("%Y-%m-%d")
    time_str = normalize_time(record.time)

    # Check availability
    availability = is_available(AvailabilityCheck(date=date_str, time=time_str, email_id = record.email_id))
    if availability != True:
        return availability

    # Save to CSV
    new_entry = {
        "fullname": record.fullname,
        "email_id": record.email_id,
        "phone_number": record.phone_number,
        "date": date_str,
        "time": time_str,
    }
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index = True)
    df.to_csv(csv_file, index = False)

    # Add to Google Calendar
    try:
        service = get_calendar_service()
        start_dt = parse_datetime(date_str, time_str)
        end_dt = start_dt + timedelta(minutes = 30)
        event = {
            "summary": f"Appointment with {record.fullname}",
            "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Kolkata"},
        }
        service.events().insert(calendarId = "primary", body = event).execute()
    except Exception as e:
        return f"CSV saved, but Google Calendar failed: {e}"

    # Notify HR
    subject = f"New Appointment - {record.fullname}"
    body = f"Appointment booked:\nName: {record.fullname}\nEmail: {record.email_id}\nDate: {date_str}\nTime: {time_str}"
    send_to_hr(subject, body)

    return f"✅ Appointment added for {record.fullname} on {date_str} at {time_str}"


@tool
def update_record(record: UpdateRecord) -> str:
    """
        Update an appointment and sync with Google Calendar.
        1. Check if email exists
        2. Check new availability
        3. Update CSV
        4. Update Google Calendar
        5. Notify HR via email"""
    df = load_csv()
    if record.email_id not in df["email_id"].values:
        return f"❌ No appointment found for email {record.email_id}"

    new_date = record.date.strftime("%Y-%m-%d")
    new_time = normalize_time(record.time)

    availability = is_available(AvailabilityCheck(date = new_date, time = new_time, email_id = record.email_id))
    if availability != True:
        return f"⚠️ Slot already booked or too close to another appointment."
        

    # Update CSV
    df.loc[df["email_id"] == record.email_id, ["date", "time"]] = [new_date, new_time]
    df.to_csv(csv_file, index = False)

    # Update Google Calendar
    try:
        service = get_calendar_service()
        fullname = df[df["email_id"] == record.email_id]["fullname"].values[0]
        events = service.events().list(
            calendarId = "primary",
            q = f"Appointment with {fullname}",
            singleEvents=True
        ).execute().get("items", [])
        if events:
            event = events[0]
            start_dt = parse_datetime(new_date, new_time)
            end_dt = start_dt + timedelta(minutes = 30)
            event["start"]["dateTime"] = start_dt.isoformat()
            event["end"]["dateTime"] = end_dt.isoformat()
            service.events().update(calendarId = "primary", eventId = event["id"], body = event).execute()
    except Exception as e:
        return f"CSV updated, but Google Calendar update failed: {e}"

    # Notify HR
    subject = f"Updated Appointment - {record.email_id}"
    body = f"Appointment updated:\nEmail: {record.email_id}\nNew Date: {new_date}\nNew Time: {new_time}"
    send_to_hr(subject, body)

    return f"✅ Appointment updated to {new_date} at {new_time}"


@tool
def delete_record(email_id: str) -> str:
    """
        Delete an appointment and remove from Google Calendar.
        1. Check if email exists
        2. Remove from CSV
        3. Remove from Google Calendar
        4. Notify HR via email
    """
    df = load_csv()
    if email_id not in df["email_id"].values:
        return f"❌ No appointment found for {email_id}"

    fullname = df[df["email_id"] == email_id]["fullname"].values[0]
    df = df[df["email_id"] != email_id]
    df.to_csv(csv_file, index=False)

    # Delete from Google Calendar
    try:
        service = get_calendar_service()
        events = service.events().list(
            calendarId="primary",
            q=f"Appointment with {fullname}",
            singleEvents=True
        ).execute().get("items", [])
        if events:
            service.events().delete(calendarId="primary", eventId=events[0]["id"]).execute()
    except Exception as e:
        return f"CSV updated, but Google Calendar delete failed: {e}"

    # Notify HR
    subject = f"Deleted Appointment - {email_id}"
    body = f"Appointment deleted:\nEmail: {email_id}\nName: {fullname}"
    send_to_hr(subject, body)

    return f"Appointment for {fullname} deleted"


@tool
def book_gcal_appointment(name: str, email: str, phone_number: str,
                          date_str: str, time_str: str) -> str:
    """
        Book an appointment: CSV + HR + Google Calendar.
        1. Check duplicate email
        2. Check availability
        3. Save to CSV
        4. Add to Google Calendar
    """

    # Parse date & time
    dt_obj = parse_datetime(date_str, time_str)
    date_val = dt_obj.strftime("%Y-%m-%d")
    time_val = dt_obj.strftime("%H:%M")

    # Load CSV
    df = load_csv()

    # Check duplicate
    if not df[df["email_id"] == email].empty:
        return f"⚠️ Email {email} has already scheduled an appointment."

    # Check availability
    availability = is_available(AvailabilityCheck(date=date_val, time=time_val))
    if availability != True:
        return availability

    # Save to CSV
    new_data = {
        "fullname": name,
        "email_id": email,
        "phone_number": phone_number,
        "date": date_val,
        "time": time_val,
    }
    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
    df.to_csv(csv_file, index=False)

    # Send to Google Calendar
    try:
        schedule_appointment(name, email, phone_number, date_str, time_str)
    except Exception as e:
        return f"{name} saved in CSV and HR notified, but Google Calendar failed: {e}"

    # Notify HR
    subject = f"New Appointment Request - {name}"
    body = f"Appointment scheduled:\nName: {name}\nEmail: {email}\nPhone_number: {phone_number}\nDate: {date_val}\nTime: {time_val}"
    send_to_hr(subject, body)

    return f"✅ Appointment scheduled successfully: {name} • {date_val} • {time_val}"


available_tools: list[StructuredTool] = [
    add_record,
    update_record,
    delete_record,
    book_gcal_appointment
]
