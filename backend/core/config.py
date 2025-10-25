from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path  # <-- Import this

# Build an absolute path to the .env file
# 1. Path(_file_) is the path to this config.py file
# 2. .parent is the 'core' folder
# 3. .parent.parent is the 'backend' folder
# 4. .parent.parent.parent is the root 'nlp-query-engine' folder
# 5. / ".env" points to your .env file
ENV_FILE_PATH = Path(__file__).parent.parent.parent / ".env"


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./employee.db"
    DB_POOL_SIZE: int = 10
    
    # Redis (optional)
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_REDIS: bool = False # Defaults to in-memory cache
    CACHE_TTL: int = 300
    
    # LLM
    GOOGLE_API_KEY: str
    
    # Application
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024
    UPLOAD_DIR: str = "data/uploads"
    INDEX_DIR: str = "data/index"

    class Config:
        env_file = ENV_FILE_PATH  # <-- Use the reliable path
        env_file_encoding = 'utf-8' # Be explicit about encoding

settings = Settings()