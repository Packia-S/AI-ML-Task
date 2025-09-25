from newagents import agent_executor
from markrag import get_answer as rag_get_answer

def unified_answer(user_query: str) -> str:
    """
    Get answer from both RAG and Agent, combine intelligently. 
    If user asked question -> use RAG answer.
    if user asked for appointment scheduling -> use Agent answer.
    """
    appointment_keywords = ["appointment", " schedule", "update", "book", "availability", 'time']
    
    # Convert user input to lowercase
    user_input_lower = user_query.lower()

    # Check if any keyword matches
    is_appointment = False
    for word in appointment_keywords:
        if word in user_input_lower:
            is_appointment = True
            break

    # Call the appropriate system
    if is_appointment:
        result = agent_executor.invoke(
            {
                "input": user_query
            }
        )
        # If agent returns a dict with 'output' field
        if isinstance(result, dict) and "output" in result:
            return result["output"]
        return str(result)
    else:
        return rag_get_answer(user_query)