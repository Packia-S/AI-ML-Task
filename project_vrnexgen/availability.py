from pydantic import BaseModel, Field, EmailStr, constr, condate
from datetime import datetime, date, time
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    
    hr_email: str
    sender_email: str
    app_password: str
    
    class Config:
        env_file = ".env"
        extra = "ignore"
        
settings = Settings()


HR_EMAIL = settings.hr_email
SENDER_EMAIL = settings.sender_email
APP_PASSWORD = settings.app_password

datetime.now().date()

start_date = datetime(2025,9, 1).date()
end_date = datetime(2025, 12, 30).date()


class RecordAdd(BaseModel):
    """
    This model represents a record to be added.
    """
    fullname: str = Field(description = "Full name of the user")
    email_id: EmailStr = Field(description = "Email ID of the user")
    phone_number: constr(
        min_length = 10,
        max_length = 10
    ) = Field(description = "Phone number of the user") # type:ignore
    date: condate(
        ge = start_date,
        le = end_date
    ) = Field(description = "Availability date of the user(cannot be in the past)") # type:ignore
    time : str = Field(description = "Availability time of the user")
    
    

class UpdateRecord(BaseModel):
    """
    This model represents a record to be updated.
    """
    email_id: EmailStr = Field(description = "Email ID of the user")
    date: condate(
        ge = start_date,
        le = end_date
    ) = Field(description = "Availability date of the user(cannot be in the past)") # type:ignore
    time: str = Field(description = "Availability time of the user") 
    

class RecordExist(BaseModel):
    email_id: EmailStr = Field(description = "Email ID of the user") 
    
    
class AvailabilityCheck(BaseModel):
    date: condate(
        ge = start_date,
        le = end_date
        ) = Field(description = "Availability date of the user(cannot be in the past)") # type:ignore
    time: str = Field(description = "Availability time of the user (HH:MM in 24- hour format)")     
    
# file path 
csv_file = "sample.csv"

if not os.path.exists(csv_file):    
    df = pd.DataFrame(columns=["fullname", "email_id", "phone_number", "date", "time"])
    df.to_csv(csv_file, index=False)
    
# normalization time format
def normalize_time(time_str: str) -> str:
    """
    Convert different time formats into standard 24-hour 'HH:MM' format.
    Examples:
        "2:00" -> "14:00"
        "2:00 pm" -> "14:00"
        "10:30 am" -> "10:30"
    """
    try:
        # Try with AM/PM
        return datetime.strptime(time_str.strip(), "%I:%M %p").strftime("%H:%M")
    except ValueError:
        try:
            # Try without AM/PM
            return datetime.strptime(time_str.strip(), "%H:%M").strftime("%H:%M")
        except ValueError:
            raise ValueError(f"Invalid time format: {time_str}")


# check availablity time 
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

    return True        # Slot is available


# Mail sent to hr email
def send_to_hr(subject: str, body: str):
    """
    Send appointment details to HR via email.
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
        

def add_record(record: RecordAdd) -> str:
    """
    Create a new record for appointment.
    """
    # To see whether the email_id already exist.
    df = pd.read_csv(csv_file)
    
    
    # Prevent duplicate email or phone
    if not df[df["email_id"] == record.email_id].empty:
        return f"Email {record.email_id} has already scheduled an appointment."
    if not df[df["phone_number"] == record.phone_number].empty:
        return f"Phone {record.phone_number} has already scheduled an appointment."


    # Check availability
    availability = is_available(AvailabilityCheck(date=record.date, time=record.time))
    if availability != True:   # if it returns "Slot already booked"
        return availability


    # Append new record
    new_data = {
        "fullname": record.fullname,
        "email_id": record.email_id,
        "phone_number": record.phone_number,
        "date": record.date,
        "time": record.time,
    }
    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
    df.to_csv(csv_file, index=False)
    
    # Send email to HR
    subject = f"New Appointment Request - {record.fullname}"
    body = (
        f"A new appointment has been scheduled:\n\n"
        f"Full Name: {record.fullname}\n"
        f"Email: {record.email_id}\n"
        f"Phone: {record.phone_number}\n"
        f"Date: {record.date}\n"
        f"Time: {record.time}\n\n"
        f"Kindly reply with 'Approved' or 'Reschedule'."
    )
    send_to_hr(subject, body)

    return f"{record.fullname} your appointment scheduled successfully"

# update the record    
def update_record(record: UpdateRecord) -> str:
    """
    Update an existing appointment's date and time based on email_id.
    """
    df = pd.read_csv(csv_file)

    # Check if email exists
    if record.email_id not in df["email_id"].values:
        return f"There is no appointment with this email id {record.email_id}"

    # Normalize new date & time
    new_date = record.date.strftime("%Y-%m-%d")
    new_time = normalize_time(record.time)

    # # Check if the new slot is already booked by someone else
    # if not df[
    #     (df["date"].astype(str) == new_date) &
    #     (df["time"].astype(str) == new_time) &
    #     (df["email_id"] != record.email_id)  # don’t block updating own slot
    # ].empty:
    #     return f"Slot already booked on {new_date} at {new_time}"
    
    # Check if the new slot is already booked (by someone else)
    availability = is_available(AvailabilityCheck(date=record.date, time=new_time))
    if availability != True:
        # If the only conflict is the same email, allow update
        conflict = df[
            (df["date"].astype(str) == new_date.strftime("%Y-%m-%d")) &
            (df["time"].astype(str) == new_time)
        ]
        if not conflict.empty and (conflict["email_id"].iloc[0] != record.email_id):
            return availability

    # Update the appointment
    df.loc[df["email_id"] == record.email_id, "date"] = new_date
    df.loc[df["email_id"] == record.email_id, "time"] = new_time

    # Save
    df.to_csv(csv_file, index=False)
    
    # Send email to HR
    subject = f"Updated Appointment Request - {record.email_id}"
    body = (
        f"An appointment has been updated:\n\n"
        f"Email: {record.email_id}\n"
        f"New Date: {new_date}\n"
        f"New Time: {new_time}\n\n"
        f"Updated Schedule are 'Approved' or 'Reschedule'."
    )
    send_to_hr(subject, body)

    return f"Appointment updated successfully to {new_date} at {new_time}"

    
# view the record
def view_records(_: None = None):
    df = pd.read_csv(csv_file)
    if df.empty:
        print("There has no records")
    else:
        print("view Records")
        print(df.to_string(index = False))  
    
    
    
            
        
if __name__ == "__main__":
    while True:
        print("\n--- Menu ---")
        print("1. Add Record")
        print("2. View Records")
        print("3. Update Record")
        print("4. Exit")
        choice = input("Enter choice: ")

        if choice == "1":
            fullname = input("Enter Fullname: ")
            email_id = input("Enter Email ID: ")
            phone_number = input("Enter Phone Number (10 digits): ")
            date_str = input("Enter Date (YYYY-MM-DD): ")
            time_ = input("enter time:")

            record = RecordAdd(
                fullname=fullname,
                email_id=email_id,
                phone_number=phone_number,
                date=date.fromisoformat(date_str),
                time = time_
            )
            add_record(record)
        elif choice == "2":
            view_records()
        elif choice == "3":
            print("Update Record")
            email = input("Enter Email ID: ")
            date_str = input("Enter your Availability Date (YYYY-MM-DD): ")
            time_str = input("Enter time: ")

            try:
                record = UpdateRecord(
                    email_id=email,
                    date=date.fromisoformat(date_str),  # validate date
                    time=normalize_time(time_str)       # normalize time
                )
                print(update_record(record))
            except ValueError as e:
                print(f"Invalid input: {e}")
        elif choice == "4":
            print("Exit")
            break
        else:
            print("Invalid choice!")

