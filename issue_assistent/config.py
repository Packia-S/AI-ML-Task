from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    
    cohere_api_key: str
    langsmith_tracing: bool
    langsmith_endpoint: str
    langsmith_api_key: str
    langsmith_project: str
    google_api_key: str
    
    class Config:
        env_file = ".env"
        extra = "ignore"
        
settings = Settings()
print("Api_keys loaded successfully")