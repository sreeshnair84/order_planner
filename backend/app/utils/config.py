from pydantic_settings import BaseSettings
from typing import List, Optional, Union
import os

class Settings(BaseSettings):
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
    ALLOWED_FILE_TYPES: Union[str, List[str]] = [".csv", ".xml", ".log", ".txt"]
    
    def __init__(self, **values):
        # Handle comma-separated strings for list fields
        if 'ALLOWED_ORIGINS' in values and isinstance(values['ALLOWED_ORIGINS'], str):
            values['ALLOWED_ORIGINS'] = [origin.strip() for origin in values['ALLOWED_ORIGINS'].split(',')]
        
        if 'ALLOWED_FILE_TYPES' in values and isinstance(values['ALLOWED_FILE_TYPES'], str):
            values['ALLOWED_FILE_TYPES'] = [file_type.strip() for file_type in values['ALLOWED_FILE_TYPES'].split(',')]
        
        super().__init__(**values)
    
    # Email settings
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # Redis settings (for caching and background tasks)
    REDIS_URL: str = "redis://localhost:6379"
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
