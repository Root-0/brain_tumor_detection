# brain_tumor_detection/api/settings.py

import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    API_VERSION: str = "1.0.0"
    API_TITLE: str = "Brain Tumor Detection API"
    API_DESCRIPTION: str = "API for automated detection of brain tumors from MRI scans"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey_change_in_production_a6sd98f7a6sdf89asdf")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./brain_tumor_detection.db")
    INITIALIZE_DB: bool = os.getenv("INITIALIZE_DB", "True").lower() == "true"
    
    # Admin user (created on startup if DB is initialized)
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@example.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "adminpassword")
    
    # Model settings
    MODEL_PATH: str = os.getenv("MODEL_PATH", "./models/brain_tumor_model.pt")
    DEVICE: Optional[str] = os.getenv("DEVICE")  # "cuda" or "cpu" or None (auto detect)
    
    # Storage
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "104857600"))  # 100 MB
    
    # CORS
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"

# Create a settings instance
settings = Settings()

# Make sure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)