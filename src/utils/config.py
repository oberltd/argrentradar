import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Database Configuration
    database_url: str = Field(default="sqlite:///./argentina_real_estate.db", env="DATABASE_URL")
    mongodb_url: str = Field(default="mongodb://localhost:27017/argentina_real_estate", env="MONGODB_URL")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=12000, env="API_PORT")
    api_debug: bool = Field(default=True, env="API_DEBUG")
    
    # Scraping Configuration
    scraping_delay: float = Field(default=1.0, env="SCRAPING_DELAY")
    max_concurrent_requests: int = Field(default=10, env="MAX_CONCURRENT_REQUESTS")
    user_agent_rotation: bool = Field(default=True, env="USER_AGENT_ROTATION")
    proxy_enabled: bool = Field(default=False, env="PROXY_ENABLED")
    proxy_list: Optional[str] = Field(default=None, env="PROXY_LIST")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/app.log", env="LOG_FILE")
    
    # Celery Configuration
    celery_broker_url: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")
    
    # LLM Configuration
    deepseek_base_url: str = Field(default="http://localhost:11434", env="DEEPSEEK_BASE_URL")
    deepseek_api_key: Optional[str] = Field(default=None, env="DEEPSEEK_API_KEY")
    deepseek_model: str = Field(default="deepseek-r1:latest", env="DEEPSEEK_MODEL")
    deepseek_timeout: int = Field(default=30, env="DEEPSEEK_TIMEOUT")
    llm_enabled: bool = Field(default=True, env="LLM_ENABLED")
    
    # Notification Configuration
    telegram_bot_token: Optional[str] = Field(default=None, env="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: Optional[str] = Field(default=None, env="TELEGRAM_CHAT_ID")
    email_smtp_server: Optional[str] = Field(default=None, env="EMAIL_SMTP_SERVER")
    email_smtp_port: int = Field(default=587, env="EMAIL_SMTP_PORT")
    email_username: Optional[str] = Field(default=None, env="EMAIL_USERNAME")
    email_password: Optional[str] = Field(default=None, env="EMAIL_PASSWORD")
    
    # Scraping targets
    target_websites: List[str] = [
        "zonaprop.com.ar",
        "argenprop.com",
        "remax.com.ar",
        "mercadolibre.com.ar",
        "properati.com.ar",
        "inmuebles24.com",
        "navent.com"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()