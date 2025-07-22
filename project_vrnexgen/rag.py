#from langchain.document_loaders.text import TextLoader
from langchain_cohere import ChatCohere
from langchain_cohere import CohereEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables
from pydantic_settings import BaseSettings



class Settings(BaseSettings):
    pinecone_api_key: str
    cohere_api_key: str
    
    class Config:
        env_file = ".env"
        
        
settings = Settings()

# Initialize LLM
llm = ChatCohere(cohere_api_key = settings.cohere_api_key)



# Initialize Embeddings
embedding_model = CohereEmbeddings(model = "embed-english-light-v3.0", cohere_api_key = settings.cohere_api_key)

    
# connecting pinecone vector store
vectorstore = PineconeVectorStore(
    pinecone_api_key = settings.pinecone_api_key,
    index_name = "langchain-vrnexgen",
    embedding = embedding_model
)

# Create a retriever from the vector store
retriever = vectorstore.as_retriever(
    search_type = "similarity_score_threshold",
    search_kwargs={'k' : 4, 'score_threshold': 0.3}
)


prompt = ChatPromptTemplate.from_template(
    """
    You are a helpful assistant going to answer questions based on the relavant documents.
    Relavant documents: {relevant_documents}
    Question : {question}
    Answer: your answer
    """
)


def get_answer(question: str) -> str:
    """
    Retrieve an answer to a given question using a retriever and language model.

    This function performs the following steps:
    1. Uses the retriever to find relevant documents based on the input question.
    2. Concatenates the content of the relevant documents.
    3. Formats a prompt using the question and the relevant document content.
    4. Invokes the language model with the formatted prompt to generate an answer.

    Args:
        question (str): The question to be answered.

    Returns:
        str: The generated answer from the language model.
    """
    relevant_documents = retriever.invoke(question)
    info = "\n".join([doc.page_content for doc in relevant_documents])
    formated_prompt = prompt.format_prompt(**{"question": question, "relevant_documents": info} )
    response = llm.invoke(formated_prompt)
    
    return response.content






if __name__ == "__main__":
    while True:
        question = input("Enter your question: ")
        if question.lower() in ["exit", "quit"]:
            print("Exiting the program.")
            break
        answer = get_answer(question)
        print(f" Answer : {answer}")