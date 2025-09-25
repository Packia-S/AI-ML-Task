from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.memory import ConversationBufferMemory
from langchain_core.tools import Tool, BaseTool, tool, StructuredTool
import pandas as pd
import os
from datetime import datetime, date
from availability import add_record, view_records, update_record, RecordAdd, UpdateRecord


from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    
    cohere_api_key: str
    google_api_key: str
    
    class Config:
        env_file = "../chains_test/.env"
        extra = "ignore"
        
settings = Settings()
print("Api_keys loaded successfully")


# 1. Load Gemini LLM
llm = ChatGoogleGenerativeAI(
    google_api_key = settings.google_api_key,
    model = "gemini-2.5-flash-lite",
    max_tokens = 5_000
)
llm


@tool("add_record", description="Add a record to csv file")
def add_record_tool(fullname: str, email_id: str, phone_number: str, date: str) -> str:
    record = RecordAdd(
        fullname=fullname,
        email_id=email_id,
        phone_number=phone_number,
        date=date
    )
    
    if os.path.exists("pandas.csv"):
        df = pd.read_csv("pandas.csv")

        # Check if email_id already exists
        if email_id in df["email_id"].values:
            return f"email_id '{record.email_id}' already exists."
        if int(record.phone_number) in df["phone_number"].values:
            return f"Phone number '{record.phone_number}' already exists." 
                
    return add_record(record)



@tool("view_records", description="View a record from csv file")
def view_records_tool(fullname: str = "") -> str:
    return view_records(fullname)


@tool("update_record", description="Update a record in csv file")
def update_record_tool(email_id: str, date: str) -> str:
    update_data = UpdateRecord(
        email_id=email_id,
        date=date
    )
    return update_record(update_data)



available_tools: list[StructuredTool] = [
    add_record_tool,
    view_records_tool,
    update_record_tool
]
available_tools

# 2. Define prompt with memory
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful AI assistant that can use tools.
    - You are the VRNeXGen Virtual Assistant Chatbot.
    - Only answer company-related questions.
    - If user asks for appointment scheduling, handle add/update in the data file. Use datetime().now().date() format for adding/updating.  eg. 27th september 25 -> datetime(2025, 9, 27).date()
    - Do not provide any extra content beyond the company-related information or appointment details.
"""),
    MessagesPlaceholder(variable_name="chat_history"),   # memory injection
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# 3. Memory
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)



# 4. Create agent
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

# 5. Run
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
        
        