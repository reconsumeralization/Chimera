"""Configuration settings for Chimera Core."""

import os
from pathlib import Path
from typing import Dict, Optional, Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ChimeraSettings(BaseSettings):
    """Settings for Chimera Core."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Application settings
    APP_NAME: str = Field(default="Chimera Core")
    APP_VERSION: str = Field(default="0.1.0")
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")
    LOG_LEVEL: str = Field(default="INFO")
    
    # Path settings
    BASE_DIR: str = str(Path(__file__).parent.parent.parent.absolute())
    DATA_DIRECTORY: str = Field(default="./data")
    WORKSPACE_PATH: str = Field(default=str(Path.cwd()))
    
    # Server settings
    HOST: str = Field(default="127.0.0.1")
    PORT: int = Field(default=8000)
    
    # Security settings
    SECRET_KEY: str = Field(default="CHANGE_ME_IN_PRODUCTION")
    ALLOWED_HOSTS: list[str] = Field(default=["*"])
    CORS_ORIGINS: list[str] = Field(default=["*"])
    
    # AI settings
    AI_PROVIDER: str = Field(default="openai")
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: Optional[str] = None
    OPENAI_MODEL: str = Field(default="gpt-4o")
    
    # Database settings
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./data/chimera.db")
    DATABASE_ECHO: bool = Field(default=False)
    
    # MCP settings
    MCP_SERVER_HOST: str = Field(default="127.0.0.1", alias="mcp_server_host")
    ENABLE_DATA_COLLECTION: bool = Field(default=False, alias="enable_data_collection")
    
    @property
    def workspace_path(self) -> str:
        """Get the workspace path with camelCase naming for compatibility."""
        return self.WORKSPACE_PATH
    
    @field_validator("DATA_DIRECTORY")
    def validate_data_directory(cls, v: str) -> str:
        """Validate and create the data directory if it doesn't exist."""
        path = Path(v)
        if not path.is_absolute():
            # If relative path, make it relative to BASE_DIR
            base_dir = Path(os.environ.get("BASE_DIR", "."))
            path = base_dir / path
        
        # Create directory if it doesn't exist
        path.mkdir(parents=True, exist_ok=True)
        return str(path)


def get_settings() -> ChimeraSettings:
    """Get application settings."""
    return ChimeraSettings()


def get_server_settings() -> Dict[str, Any]:
    """
    Get server-related settings.
    
    Returns:
        Dict[str, Any]: Dictionary with server settings
    """
    settings = get_settings()
    return {
        "host": settings.HOST,
        "port": settings.PORT,
        "debug": settings.DEBUG,
        "environment": settings.ENVIRONMENT,
        "cors_origins": settings.CORS_ORIGINS,
        "show_docs": True,
        "base_url": f"http://{settings.HOST}:{settings.PORT}",
    }


def get_ai_settings() -> Dict[str, Any]:
    """
    Get AI-related settings.
    
    Returns:
        Dict[str, Any]: Dictionary with AI settings
    """
    settings = get_settings()
    return {
        "api_key": settings.OPENAI_API_KEY,
        "model_name": settings.OPENAI_MODEL,
        "api_base": settings.OPENAI_API_BASE,
        "api_version": None,
        "max_tokens": 2048,
        "temperature": 0.7,
    }


def get_rule_settings() -> Dict[str, str]:
    """
    Get rule-related settings.
    
    Returns:
        Dict[str, str]: Dictionary with rule settings
    """
    settings = get_settings()
    rules_dir = Path(settings.DATA_DIRECTORY) / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    return {
        "rules_directory": str(rules_dir),
    }


def get_db_settings() -> Dict[str, Any]:
    """
    Get database-related settings.
    
    Returns:
        Dict[str, Any]: Dictionary with database settings
    """
    settings = get_settings()
    return {
        "db_type": "sqlite" if "sqlite" in settings.DATABASE_URL else "postgresql",
        "db_url": settings.DATABASE_URL,
        "echo": settings.DATABASE_ECHO,
    } 