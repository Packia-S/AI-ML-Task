from langchain_cohere import ChatCohere
from langchain_cohere.embeddings import CohereEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from agents import agent_executor


from dotenv import load_dotenv

load_dotenv()

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    
    cohere_api_key: str
    langsmith_tracing: bool
    langsmith_endpoint: str
    langsmith_api_key: str
    langsmith_project: str
    google_api_key: str
    pinecone_api_key: str
    
    class Config:
        env_file = ".env"
        extra = "ignore"
        
settings = Settings()
print("Api_keys loaded successfully")

llm = ChatCohere(
    cohere_api_key = settings.cohere_api_key
)

embeddings = CohereEmbeddings(
    model="embed-english-light-v3.0"
)

vectorstore = PineconeVectorStore(
    pinecone_api_key = settings.pinecone_api_key,
    index_name = "cohere-vrnexgen-db",
    embedding = embeddings
    
)

retriever = vectorstore.as_retriever(
    search_type = "similarity_score_threshold",
    search_kwargs={'k' : 15, 'score_threshold': 0.3}
)

print(retriever.invoke("vrnexgen links"))

prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system","""You are an intelligent, reliable, and concise AI assistant developed by VRNexGen Technologies.
Your goal is to help users by accurately answering their questions using only the context provided in the retrieved documents.

Avoid using the word based on this content.

Do not make up answers or use external knowledge. If the answer cannot be found in the provided context, respond with:
"I'm sorry, I couldn't find relevant information on that topic based on the available documents."

Keep your responses clear, technically accurate, and directly relevant to the user's question.

Provide a related link in the answer given below.
"""),
        ("system","""Here are the related context based on the this answer the question\n{related_documents}"""),
        ("human","""{question}""")
    ]
)

def get_related_chunks(question : str) -> str:
    related_docs = retriever.invoke(question)
    related_chunks = "\n".join([f"{doc.page_content} - Source Url {doc.metadata["source"]}" for doc in related_docs])
    return related_chunks


related_info  = RunnableLambda(get_related_chunks)

def get_answer(question: str) -> str:
    related_docs = related_info.invoke(question)
    chain = prompt_template | llm | StrOutputParser()
    
    response = chain.invoke(
        {
            "question": question,
            "related_documents": related_docs
        }
    )
    
    return response



# if __name__ == "__main__":
#     while True:
#         question = input("Enter your question: ")
#         if question.lower() in ["exit", "quit"]:
#             print("Exiting the program.")
#             break
#         answer = get_answer(question)
#         print(f" Answer : {answer}")