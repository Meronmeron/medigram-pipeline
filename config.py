"""
Configuration management for Ethiopian Medical Business Data Platform.
Uses python-dotenv to load environment variables from .env file.
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    postgres_db: str = Field(default="ethiopian_medical_db", env="POSTGRES_DB")
    postgres_user: str = Field(default="medical_user", env="POSTGRES_USER")
    postgres_password: str = Field(default="secure_password_123", env="POSTGRES_PASSWORD")
    database_url: str = Field(
        default="postgresql://medical_user:secure_password_123@localhost:5432/ethiopian_medical_db",
        env="DATABASE_URL"
    )
    
    class Config:
        env_file = ".env"


class TelegramSettings(BaseSettings):
    """Telegram API configuration settings."""
    
    api_id: str = Field(..., env="TELEGRAM_API_ID")
    api_hash: str = Field(..., env="TELEGRAM_API_HASH")
    bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    channels: List[str] = Field(default=[], env="TELEGRAM_CHANNELS")
    scraping_limit: int = Field(default=1000, env="TELEGRAM_SCRAPING_LIMIT")
    scraping_interval: int = Field(default=3600, env="TELEGRAM_SCRAPING_INTERVAL")
    
    class Config:
        env_file = ".env"
    
    @property
    def channel_list(self) -> List[str]:
        """Convert comma-separated channels string to list."""
        if isinstance(self.channels, str):
            return [channel.strip() for channel in self.channels.split(",") if channel.strip()]
        return self.channels


class YOLOSettings(BaseSettings):
    """YOLOv8 model configuration settings."""
    
    model_path: str = Field(default="/app/models/yolov8n.pt", env="YOLO_MODEL_PATH")
    confidence_threshold: float = Field(default=0.5, env="YOLO_CONFIDENCE_THRESHOLD")
    device: str = Field(default="cpu", env="YOLO_DEVICE")
    
    class Config:
        env_file = ".env"


class APISettings(BaseSettings):
    """FastAPI configuration settings."""
    
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    reload: bool = Field(default=True, env="API_RELOAD")
    workers: int = Field(default=1, env="API_WORKERS")
    secret_key: str = Field(..., env="SECRET_KEY")
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    
    class Config:
        env_file = ".env"


class DagsterSettings(BaseSettings):
    """Dagster orchestration configuration settings."""
    
    home: str = Field(default="/app/dagster_home", env="DAGSTER_HOME")
    host: str = Field(default="0.0.0.0", env="DAGSTER_HOST")
    port: int = Field(default=3000, env="DAGSTER_PORT")
    
    class Config:
        env_file = ".env"


class DBTSettings(BaseSettings):
    """dbt configuration settings."""
    
    project_dir: str = Field(default="/app/dbt", env="DBT_PROJECT_DIR")
    profiles_dir: str = Field(default="/app/dbt/profiles", env="DBT_PROFILES_DIR")
    
    class Config:
        env_file = ".env"


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""
    
    level: str = Field(default="INFO", env="LOG_LEVEL")
    file: str = Field(default="/app/logs/app.log", env="LOG_FILE")
    
    class Config:
        env_file = ".env"


class StorageSettings(BaseSettings):
    """Data storage configuration settings."""
    
    data_dir: str = Field(default="/app/data", env="DATA_DIR")
    models_dir: str = Field(default="/app/models", env="MODELS_DIR")
    logs_dir: str = Field(default="/app/logs", env="LOGS_DIR")
    
    class Config:
        env_file = ".env"


class RedisSettings(BaseSettings):
    """Redis configuration settings."""
    
    url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    class Config:
        env_file = ".env"


class Settings(BaseSettings):
    """Main application settings that combines all configuration sections."""
    
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # Sub-settings
    database: DatabaseSettings = DatabaseSettings()
    telegram: TelegramSettings = TelegramSettings()
    yolo: YOLOSettings = YOLOSettings()
    api: APISettings = APISettings()
    dagster: DagsterSettings = DagsterSettings()
    dbt: DBTSettings = DBTSettings()
    logging: LoggingSettings = LoggingSettings()
    storage: StorageSettings = StorageSettings()
    redis: RedisSettings = RedisSettings()
    
    # External APIs
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    google_cloud_credentials: Optional[str] = Field(default=None, env="GOOGLE_CLOUD_CREDENTIALS")
    
    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    prometheus_enabled: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    
    # CORS
    cors_origins: List[str] = Field(default=["http://localhost:3000"], env="CORS_ORIGINS")
    allowed_hosts: List[str] = Field(default=["localhost", "127.0.0.1"], env="ALLOWED_HOSTS")
    
    class Config:
        env_file = ".env"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins string to list."""
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        return self.cors_origins
    
    @property
    def allowed_hosts_list(self) -> List[str]:
        """Convert comma-separated allowed hosts string to list."""
        if isinstance(self.allowed_hosts, str):
            return [host.strip() for host in self.allowed_hosts.split(",") if host.strip()]
        return self.allowed_hosts
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


# Create global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


# Example usage functions
def get_database_url() -> str:
    """Get database URL from settings."""
    return settings.database.database_url


def get_telegram_config() -> dict:
    """Get Telegram configuration as dictionary."""
    return {
        "api_id": settings.telegram.api_id,
        "api_hash": settings.telegram.api_hash,
        "bot_token": settings.telegram.bot_token,
        "channels": settings.telegram.channel_list,
        "scraping_limit": settings.telegram.scraping_limit,
        "scraping_interval": settings.telegram.scraping_interval
    }


def get_yolo_config() -> dict:
    """Get YOLOv8 configuration as dictionary."""
    return {
        "model_path": settings.yolo.model_path,
        "confidence_threshold": settings.yolo.confidence_threshold,
        "device": settings.yolo.device
    }


def get_api_config() -> dict:
    """Get FastAPI configuration as dictionary."""
    return {
        "host": settings.api.host,
        "port": settings.api.port,
        "reload": settings.api.reload,
        "workers": settings.api.workers,
        "secret_key": settings.api.secret_key,
        "jwt_secret_key": settings.api.jwt_secret_key,
        "jwt_algorithm": settings.api.jwt_algorithm,
        "jwt_expiration_hours": settings.api.jwt_expiration_hours
    }


if __name__ == "__main__":
    # Test configuration loading
    print("Configuration loaded successfully!")
    print(f"Environment: {settings.environment}")
    print(f"Database URL: {settings.database.database_url}")
    print(f"API Host: {settings.api.host}:{settings.api.port}")
    print(f"Telegram Channels: {settings.telegram.channel_list}")
    print(f"YOLO Model Path: {settings.yolo.model_path}") 