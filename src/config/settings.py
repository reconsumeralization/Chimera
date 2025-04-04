"""Settings for Project Chimera.

This module defines settings for Project Chimera using Pydantic BaseSettings.
Settings are loaded from environment variables and .env file.
"""

import os
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ChimeraSettings(BaseSettings):
    """Settings for Project Chimera."""
    
    # Environment settings
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="development", description="Environment (development, production)")
    log_level: str = Field(default="INFO", description="Log level")
    
    # Path settings
    data_directory: str = Field(default="data", description="Data directory")
    sqlite_filename: str = Field(default="chimera.db", description="SQLite database filename")
    
    # Database settings
    db_type: str = Field(default="sqlite", description="Database type (sqlite, postgresql)")
    
    # PostgreSQL settings (if db_type is postgresql)
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_user: str = Field(default="postgres", description="PostgreSQL user")
    postgres_password: str = Field(default="postgres", description="PostgreSQL password")
    postgres_db: str = Field(default="chimera", description="PostgreSQL database name")
    
    # AI settings
    ai_api_key: Optional[str] = Field(default=None, description="AI API key")
    ai_model_name: str = Field(default="gpt-4", description="AI model name")
    ai_api_base: Optional[str] = Field(default=None, description="AI API base URL")
    ai_api_version: Optional[str] = Field(default=None, description="AI API version")
    ai_max_tokens: int = Field(default=4000, description="Maximum tokens for AI responses")
    ai_temperature: float = Field(default=0.2, description="Temperature for AI responses")
    
    # Rules settings
    rules_directory: str = Field(default="data/rules", description="Directory for rule files")
    
    # Web server settings
    host: str = Field(default="127.0.0.1", description="Host for the web server")
    port: int = Field(default=8000, description="Port for the web server")
    cors_origins: List[str] = Field(default=["*"], description="CORS origins")
    show_docs: bool = Field(default=True, description="Show API documentation")
    
    # URL settings
    base_url: Optional[str] = Field(default=None, description="Base URL for the server")
    
    # UI settings
    static_dir: str = Field(default="static", description="Directory for static files")
    templates_dir: str = Field(default="templates", description="Directory for templates")
    
    # Allow arbitrary types to be added during runtime
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="CHIMERA_",
        extra="allow"
    )
    
    @field_validator("rules_directory")
    def create_rules_directory(cls, value: str) -> str:
        """Create the rules directory if it doesn't exist."""
        os.makedirs(value, exist_ok=True)
        return value
    
    @field_validator("data_directory")
    def create_data_directory(cls, value: str) -> str:
        """Create the data directory if it doesn't exist."""
        os.makedirs(value, exist_ok=True)
        return value
    
    @field_validator("static_dir")
    def create_static_dir(cls, value: str) -> str:
        """Create the static directory if it doesn't exist."""
        os.makedirs(value, exist_ok=True)
        return value
    
    @field_validator("templates_dir")
    def create_templates_dir(cls, value: str) -> str:
        """Create the templates directory if it doesn't exist."""
        os.makedirs(value, exist_ok=True)
        return value
    
    @property
    def server_url(self) -> str:
        """Get the server URL."""
        if self.base_url:
            return self.base_url
        
        return f"http://{self.host}:{self.port}"
    
    def get_settings_dict(self) -> Dict[str, Any]:
        """
        Get settings as a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary of settings
        """
        return self.model_dump()


def load_settings() -> ChimeraSettings:
    """
    Load settings from environment variables and .env file.
    
    Returns:
        ChimeraSettings: Application settings
    """
    return ChimeraSettings()


# Global settings instance
_settings: Optional[ChimeraSettings] = None


def get_settings() -> ChimeraSettings:
    """
    Get the global settings instance.
    
    Returns:
        ChimeraSettings: Application settings
    """
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings 