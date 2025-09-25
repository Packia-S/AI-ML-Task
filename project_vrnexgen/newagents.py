from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.memory import ConversationBufferMemory
from langchain_core.tools import Tool, BaseTool, tool, StructuredTool
import pandas as pd
import os
from datetime import datetime, date as dt
from availability import add_record, view_records, update_record, is_available,RecordAdd, UpdateRecord, AvailabilityCheck, normalize_time



from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    
    cohere_api_key: str
    google_api_key: str
    langsmith_tracing: bool
    langsmith_endpoint: str
    langsmith_api_key: str
    langsmith_project: str
    
    class Config:
        env_file = ".env"
        extra = "ignore"
        
settings = Settings()
print("Api_keys loaded successfully")


# 1. Load Gemini LLM
llm = ChatGoogleGenerativeAI(
    google_api_key = settings.google_api_key,
    model = "gemini-2.5-flash-lite",
    max_tokens = 5_000
)



@tool("add_record", description="Add a record to csv file", return_direct = True)
def add_record_tool(fullname: str, email_id: str, phone_number: str, date: str, time: str) -> str:
    """
    Add a record if new.
    If email already exists, update the appointment with the new date/time instead.
    Each slot = 30 minutes.
    """
    date_obj = datetime.fromisoformat(date).date()
    
    # Normalize time
    time_obj = normalize_time(time)
    # Ensure date is a datetime.date object
    if isinstance(date, str):
        try:
            # parsing as YYYY-MM-DD 
            date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return f"Invalid date: {date}."
        
    if date < dt.today():
        return f"Invalid date: {date}. Please change the date"
    
    record = RecordAdd(
        fullname = fullname,
        email_id = email_id,
        phone_number = phone_number,
        date = date_obj,
        time = time_obj
    )
    
    if os.path.exists("sample.csv"):
        df = pd.read_csv("sample.csv")

        # Check if email_id already exists
        if email_id in df["email_id"].values:
            return f"email_id '{record.email_id}' already exists."
        if int(record.phone_number) in df["phone_number"].values:
            return f"Phone number '{record.phone_number}' already exists." 
    
    
    check = AvailabilityCheck(date=date_obj, time=time_obj)
    slot_status = is_available(check)
    
    if slot_status is not True:   # means it's already booked
        return slot_status
           
    add_record(record)
    return f"Record added successfully for {fullname} on {date} at {time}."



@tool("view_records", description="View a record from csv file")
def view_records_tool(fullname: str = "") -> str:
    return view_records(fullname)


@tool("update_record", description="Update a record in csv file")
def update_record_tool(email_id: str, date: str, time: str) -> str:
    """
    Update the record as email id, date and time.
    """
    # Convert date string to date object
    date_obj = datetime.fromisoformat(date).date()
    
    # Normalize time
    time_obj = normalize_time(time)
    
    update_data = UpdateRecord(
        email_id = email_id,
        date = date_obj,
        time = time_obj
    )
    
    #  Check if slot already booked by someone else
    check = AvailabilityCheck(date=date_obj, time=time_obj)
    slot_status = is_available(check)
    
    if slot_status is not True: 
        return slot_status
    
    update_record(update_data)
    
    return f"Record updated successfully for email_id: '{email_id}'."

@tool("is_available", description="Check if a given date and time slot is available")
def is_available_tool(date: str, time: str) -> str:
    """
    Check if a slot is free or already booked.
    Each appointment is assumed to last 30 minutes.
    """
    # Convert date string to date object
    date_obj = datetime.fromisoformat(date).date()
    
    # Normalize time
    time_obj = normalize_time(time)
    
    check = AvailabilityCheck(date=date_obj, time=time_obj)
    available = is_available(check)
    
    if available is True:
        return f"Slot available on {date} at {time}"
    return available   # will return: "Slot already booked on YYYY-MM-DD at HH:MM"





available_tools: list[StructuredTool] = [
    add_record_tool, # add record tool
    view_records_tool, # view record tool
    update_record_tool,  # update tool
    is_available_tool # available tool 
]
available_tools



# prompt with memory
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are the VRNeXGen Virtual Assistant Chatbot.

- Appointments can only be scheduled for today or future dates. 
- Past dates are not allowed. If a user requests a past date, politely inform them that only current and future dates are available.

- Your primary role is to assist with appointment scheduling (adding, updating, and validating records).
- Always collect the following details for booking an appointment:
  - fullname
  - email_id
  - phone_number
  - date (YYYY-MM-DD format, e.g., 2025-09-27 for 27th September 2025)
  - time (HH:MM format, 24-hour)

- If the user provides a natural date (e.g., “27th September 25”), convert it into `datetime(2025, 9, 27).date()`.
- If the user does not specify a time, schedule the appointment **30 minutes from the current time** using `datetime.now()`.

### Rules for Scheduling
1. Every appointment must have at least a **30-minute gap** from the previous booking.
   - Example: If an appointment is at 15:00, the next available slot is 15:30 or later.
   - If the user requests 15:05, 15:10, 15:15, or 15:20, politely decline and suggest the nearest available slot (e.g., 15:30).

2. Prevent duplicate users:
   - If the user provides an email ID or phone number that already exists, respond with:
     - “Email [email] has already scheduled an appointment.” or
     - “Phone [number] has already scheduled an appointment.”

3. Prevent overlapping appointments:
   - Do not allow overlapping appointments. 
   - If the requested date and time overlaps or is within 30 minutes of an existing appointment, respond with: 
     - “Slot already booked or too close to existing appointment at [time].”

4. Always confirm the appointment details clearly:
   - Full name
   - Email ID
   - Phone number
   - Date
   - Time

5. To update an appointment, always require:
   - email_id
   - date
   - time

### Responses for Tool Actions
- After adding a record to the CSV file: **“Record added successfully.”**
- After updating a record in the CSV file: **“Record updated successfully.”**

### Important
- When you call a tool, always return the tool’s result message back to the user in your final response.
- Do not leave the response empty.
- Do not provide any extra content outside of company information or appointment details.

- If any required detail is missing or invalid, politely ask the user to provide it.
  - Missing phone number → "Please provide a valid phone number (10 digits)."
  - Invalid date → "Please provide a valid date in YYYY-MM-DD format."
  - Missing email → "Please provide your email address."

"""),
    MessagesPlaceholder(variable_name="chat_history"),   # memory injection
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# Memory
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)



# Create agent
agent = create_openai_functions_agent(
    llm = llm,
    tools = available_tools,
    prompt = prompt
)


agent_executor = AgentExecutor(
    name = "NeXGen",
    agent = agent,
    tools = available_tools,
    memory = memory,
    verbose = True
)

# Run
# agent_executor.invoke({"input": "Hello, who are you?"})
# agent_executor.invoke({"input": "sorry, I want to schedule change on appointment on 25th aug packia30@gmail.com 25th august 2025 is conform date"})

# while True:
#     user_input = input("Enter yor question: ")
    
#     if user_input.lower() in ["exit", "quit"]:
#         print("Exit...")
#         break
#     answer = agent_executor.invoke(
#         {
#             "input": user_input
#         }
#     )
    
#     print(f" Answer : {answer}")    
        
        