from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    
    hr_email: str
    sender_email: str
    app_password: str
    
    cohere_api_key: str
    google_api_key: str
    pinecone_api_key: str
    
    langsmith_tracing: bool
    langsmith_endpoint: str
    langsmith_api_key: str
    langsmith_project: str
    
    
    class Config:
        env_file = ".env"
        extra = "ignore"
        
settings = Settings()