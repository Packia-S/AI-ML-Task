from pydantic import BaseModel, Field, EmailStr, constr, condate
from datetime import datetime, date, time

datetime.now().date()

start_date = datetime(2025, 8, 18).date()
end_date = datetime(2025, 12, 31).date()

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
    ) = Field(description = "Availability date of the user") # type:ignore
    time : str = Field(description = "Availability time of the user")
    
class UpdateRecord(BaseModel):
    """
    This model represents a record to be updated.
    """
    email_id: EmailStr = Field(description = "Email ID of the user")
    date: condate(
        ge = start_date,
        le = end_date
    ) = Field(description = "Availability date of the user") # type:ignore
    time: str = Field(description = "Availability time of the user") 
    
class RecordExist(BaseModel):
    email_id: EmailStr = Field(description = "Email ID of the user")
    
class AvailabilityCheck(BaseModel):
    date: condate(
        ge = start_date,
        le = end_date
    ) = Field(description = "Availability date of the user") # type:ignore
    time: str = Field(description = "Availability time of the user (HH:MM in 24- hour format)") 
    email_id: str | None = None 


class DeleteRecord(BaseModel):
    email_id: EmailStr = Field(description = "Email ID of the user")


