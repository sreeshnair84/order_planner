from pydantic_settings import BaseSettings
from typing import List, Optional, Union
import os

class Settings(BaseSettings):
    # Azure Storage configuration
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = None
    AZURE_STORAGE_CONTAINER: Optional[str] = None
    # Database settings
    DATABASE_URL: str = "postgresql://user:password@localhost/order_management"
    
    # JWT settings
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS settings
    ALLOWED_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ]
    
    # File upload settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "uploads"
    ALLOWED_FILE_TYPES: Union[str, List[str]] = [".csv", ".xml", ".log", ".txt", ".xlsx", ".xls"]
    
    # Email settings
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # Redis settings (for caching and background tasks)
    REDIS_URL: str = "redis://localhost:6379"
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    
    # Azure AI Foundry Configuration
    AZURE_AI_PROJECT_CONNECTION_STRING: Optional[str] = None
    AZURE_AI_PROJECT_ID: Optional[str] = None
    AZURE_AI_RESOURCE_GROUP: Optional[str] = None
    AZURE_AI_SUBSCRIPTION_ID: Optional[str] = None
    AZURE_AI_REGION: str = "eastus"
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_API_VERSION: str = "2024-02-01"
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-4"
    AZURE_OPENAI_MODEL_NAME: str = "gpt-4"
    
    # Azure AI Assistant Configuration
    AZURE_AI_ASSISTANT_ID: Optional[str] = None
    AZURE_AI_THREAD_TIMEOUT: int = 300
    
    # Azure Authentication
    AZURE_CLIENT_ID: Optional[str] = None
    AZURE_CLIENT_SECRET: Optional[str] = None
    AZURE_TENANT_ID: Optional[str] = None
    
    # Application Configuration
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_VERSION: str = "v1"
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Order Processing Configuration
    ORDER_PROCESSING_TIMEOUT: int = 600
    MAX_RETRY_ATTEMPTS: int = 3
    BATCH_PROCESSING_SIZE: int = 50
    
    # AI Agent Configuration
    AI_AGENT_ENABLED: bool = True
    AI_AGENT_MAX_ITERATIONS: int = 10
    AI_AGENT_TEMPERATURE: float = 0.1
    AI_AGENT_MAX_TOKENS: int = 4000
    
    # Monitoring and Telemetry
    AZURE_MONITOR_CONNECTION_STRING: Optional[str] = None
    ENABLE_TELEMETRY: bool = True
    TRACE_SAMPLING_RATE: float = 0.1
    
    # Azure Storage Configuration
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = None
    AZURE_STORAGE_CONTAINER: str = "uploads"
    
    
    def __init__(self, **values):
        # Handle comma-separated strings for list fields
        if 'ALLOWED_ORIGINS' in values and isinstance(values['ALLOWED_ORIGINS'], str):
            values['ALLOWED_ORIGINS'] = [origin.strip() for origin in values['ALLOWED_ORIGINS'].split(',')]
        
        if 'ALLOWED_FILE_TYPES' in values and isinstance(values['ALLOWED_FILE_TYPES'], str):
            values['ALLOWED_FILE_TYPES'] = [file_type.strip() for file_type in values['ALLOWED_FILE_TYPES'].split(',')]
        
        super().__init__(**values)
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
