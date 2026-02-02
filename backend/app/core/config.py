from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Project
    PROJECT_NAME: str = "BOQ System API"
    VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "boq_user"
    DB_PASSWORD: str = "boq_password_456"
    DB_NAME: str = "boq_system"
    
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    
    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production-please-use-strong-random-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://localhost:8000"
    ]
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".xlsx", ".xls"]
    UPLOAD_DIR: str = "./uploads"
    
    # ML Model
    MODEL_NAME: str = "keepitreal/vietnamese-sbert"
    MODEL_PATH: str = "./models"
    CLASSIFICATION_THRESHOLD: float = 0.8

    # AI/LLM Settings
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = "AIzaSyD4IabzNbbBe6akFwOkYboWn2nzmX934Zg"
    AI_MODEL: str = "gemini-2.0-flash"  # or "gpt-4o-mini", "claude-3-haiku-20240307"
    AI_PROVIDER: str = "gemini"  # "openai", "anthropic", or "gemini"
    AI_NORMALIZATION_ENABLED: bool = True
    AI_NORMALIZATION_BATCH_SIZE: int = 10

    # Multi-Pass AI Analysis Settings
    AI_CONTEXT_ANALYSIS_ENABLED: bool = True  # Pass 1: File context analysis
    AI_CONTEXT_SAMPLE_SIZE: int = 50  # Number of rows to sample for context analysis
    AI_DOMAIN_VALIDATION_ENABLED: bool = True  # Pass 4: Domain validation with AI correction

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


# Create required directories
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.MODEL_PATH, exist_ok=True)
os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)
