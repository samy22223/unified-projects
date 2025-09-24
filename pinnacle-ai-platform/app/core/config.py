"""
Configuration settings for OmniCore AI Platform
"""

from pydantic_settings import BaseSettings
from typing import Optional, List
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "OmniCore AI Platform"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database URLs
    database_url: str = "postgresql://omnicore:omnicore_password@postgresql:5432/omnicore"
    mongodb_url: str = "mongodb://mongodb:27017"
    redis_url: str = "redis://redis:6379"
    neo4j_uri: str = "bolt://neo4j:7687"
    chroma_url: str = "http://chroma:8000"
    
    # External Services
    rabbitmq_url: str = "amqp://omnicore:omnicore_password@rabbitmq:5672"
    ollama_base_url: str = "http://ollama:11434"
    
    # Security
    jwt_secret: str = "your_super_secret_jwt_key_change_this_in_production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # AI Models
    default_llm_model: str = "llama3"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Agent Configuration
    max_agents: int = 200
    agent_timeout: int = 300  # seconds
    agent_retry_attempts: int = 3
    
    # Monitoring
    enable_prometheus: bool = True
    metrics_port: int = 8001
    
    # CORS
    cors_origins: List[str] = ["*"]  # Configure for production
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
