from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings
from models import AssistIssue
from langchain_core.messages import HumanMessage



llm = ChatGoogleGenerativeAI(
    google_api_key = settings.google_api_key,
    model = "gemini-2.0-flash"
)

structured_llm = llm.with_structured_output(schema = AssistIssue)


def get_assistance_for_issue(issue: str) -> str:
    
    structured_output: AssistIssue = structured_llm.invoke(
        [
            HumanMessage(content = issue)
        ]
    )
    
    return structured_output.model_dump_json(indent = 4)
    
    

if __name__ == "__main__":
    
    user_issue: str = input("Enter your issue.")
    # print(f"User Issue: {user_issue}")
    
    solution: str = get_assistance_for_issue(user_issue)
    
    print(f"The Structured output is\n{solution}")
    
    
