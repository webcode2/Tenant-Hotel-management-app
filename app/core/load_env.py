# create a class and load envfrom pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = Field(...,
                              description="Database connection URL for async SQLAlchemy")

    # Security
    SECRET_KEY: str = Field(..., description="JWT secret key")
    ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24 * 7, description="Token expiry in minutes (default: 7 days)")
    DEBUG: bool = True

    

    # Optional: app-level configuration
    APP_NAME: str = Field(default="Hotel Management System")

    # Pydantic Settings model config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Instantiate settings
settings = Settings()
