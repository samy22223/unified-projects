"""
Settings configuration for Pinnacle AI Platform.

This module contains all configuration settings loaded from environment variables
with sensible defaults for development and production environments.
"""

import os
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class Settings(BaseModel):
    """Application settings with environment variable support."""

    # API Configuration
    API_TITLE: str = "Pinnacle AI Platform"
    API_DESCRIPTION: str = "Advanced AI Assistant Platform with 200+ AI Agents"
    API_VERSION: str = "1.0.0"
    API_DOCS_URL: str = "/docs"
    API_REDOC_URL: str = "/redoc"
    API_V1_PREFIX: str = "/api/v1"

    # Application Configuration
    APP_NAME: str = "Pinnacle AI Platform"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_SECRET_KEY: str = "your-secret-key-change-in-production"

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # CORS Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Database Configuration
    DATABASE_URL: str = "postgresql://user:password@localhost/pinnacle_ai"
    REDIS_URL: str = "redis://localhost:6379"
    MONGODB_URL: str = "mongodb://localhost:27017"

    # AI Configuration
    AI_MODEL_PATH: str = "models/"
    DEFAULT_AI_MODEL: str = "gpt-3.5-turbo"
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.7
    MAX_AGENTS: int = 200
    AGENT_TIMEOUT: int = 300

    # Task Queue Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    TASK_QUEUE_NAME: str = "pinnacle_tasks"

    # Authentication Configuration
    JWT_SECRET_KEY: str = "your-jwt-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    OAUTH_GOOGLE_CLIENT_ID: Optional[str] = None
    OAUTH_GITHUB_CLIENT_ID: Optional[str] = None

    # External API Keys
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_CLOUD_API_KEY: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None

    # Storage Configuration
    UPLOAD_DIR: str = "uploads/"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_FILE_TYPES: List[str] = [
        ".txt", ".pdf", ".docx", ".xlsx", ".csv",
        ".jpg", ".jpeg", ".png", ".gif", ".webp",
        ".mp4", ".avi", ".mov", ".wav", ".mp3"
    ]

    # Monitoring Configuration
    SENTRY_DSN: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Cache Configuration
    CACHE_TTL: int = 3600
    REDIS_CACHE_TTL: int = 3600

    # Email Configuration
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@pinnacle-ai.com"

    # Security Configuration
    RATE_LIMIT_PER_MINUTE: int = 60
    ENABLE_HTTPS_REDIRECT: bool = False
    SSL_CERT_FILE: Optional[str] = None
    SSL_KEY_FILE: Optional[str] = None

    # Agent Configuration
    AGENT_REGISTRY_PATH: str = "config/agents/"
    AGENT_CONFIG_DIR: str = "config/agent_configs/"
    DEFAULT_AGENT_MEMORY_SIZE: int = 1000
    AGENT_HEARTBEAT_INTERVAL: int = 30

    # Multi-modal Configuration
    ENABLE_VISION: bool = True
    ENABLE_AUDIO: bool = True
    ENABLE_VIDEO: bool = True
    MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_AUDIO_SIZE: int = 50 * 1024 * 1024  # 50MB
    MAX_VIDEO_SIZE: int = 100 * 1024 * 1024  # 100MB

    # Performance Configuration
    BATCH_SIZE: int = 32
    MAX_CONCURRENT_REQUESTS: int = 100
    REQUEST_TIMEOUT: int = 60
    WORKER_TIMEOUT: int = 300

    # Development Configuration
    HOT_RELOAD: bool = True
    DEBUG_TOOLBAR: bool = True
    PROFILING_ENABLED: bool = False

    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v):
        """Parse CORS origins from environment variable."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("ALLOWED_FILE_TYPES", mode="before")
    def parse_file_types(cls, v):
        """Parse allowed file types from environment variable."""
        if isinstance(v, str):
            return [file_type.strip() for file_type in v.split(",")]
        return v

    model_config = {"env_file": ".env", "case_sensitive": False}


# Create global settings instance
settings = Settings()