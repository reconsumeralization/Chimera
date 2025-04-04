"""Factory for creating and managing service instances.

This module provides a factory class for creating and managing service instances
for the Chimera Core application.
"""

import os
import asyncio
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar, cast

import structlog

from src.chimera_core.config import get_ai_settings, get_db_settings, get_settings
from src.chimera_core.services.ai_client import AIClient
from src.chimera_core.services.context_cache import ContextCacheService
from src.chimera_core.services.database import DatabaseService
from src.chimera_core.services.prompt_service import PromptService
from src.chimera_core.services.rule_engine import RuleEngineService
from src.chimera_core.db_core import connection as db_connection

logger = structlog.get_logger(__name__)

# Type variable for services
T = TypeVar("T")


class ServiceFactory:
    """Factory for creating and managing service instances."""

    # Dictionary to store service instances
    _services: Dict[str, Any] = {}
    _initialized: bool = False
    _lock = asyncio.Lock()  # Lock for thread safety

    @classmethod
    async def initialize(cls) -> None:
        """Initialize all services."""
        async with cls._lock:
            if cls._initialized:
                logger.warning("Services already initialized")
                return

            logger.info("Initializing services")
            
            # Create directories
            settings = get_settings()
            cls._ensure_directories_exist(settings.data_directory)
            cls._ensure_directories_exist(settings.rules_directory)
            
            # Initialize database connection pool FIRST
            try:
                # Initialize the database connection pool
                await db_connection.init_db()
                
                # Create DB Service instance
                cls._services["database"] = DatabaseService()
                await cls._services["database"].initialize()
                logger.info("Database service initialized")
            except Exception as e:
                logger.error("Failed to initialize database service", error=str(e), exc_info=True)
                raise
            
            # Initialize context cache service
            cls._services["context_cache"] = ContextCacheService()
            
            # Initialize prompt service
            cls._services["prompt_service"] = PromptService(
                context_cache_service=cls._services["context_cache"]
            )
            
            # Initialize AI client
            ai_settings = get_ai_settings()
            cls._services["ai_client"] = AIClient(
                api_key=ai_settings["api_key"],
                model=ai_settings["model_name"],
                api_base=ai_settings["api_base"],
                api_version=ai_settings["api_version"],
                max_tokens=ai_settings["max_tokens"],
                temperature=ai_settings["temperature"],
                prompt_service=cls._services["prompt_service"],
            )
            
            # Initialize rule engine service
            cls._services["rule_engine"] = RuleEngineService(
                rules_dir=settings.rules_directory,
                context_cache_service=cls._services["context_cache"],
                ai_client=cls._services["ai_client"],
            )
            
            # Mark as initialized
            cls._initialized = True
            logger.info("Services initialized successfully")

    @classmethod
    async def shutdown(cls) -> None:
        """Shut down all services."""
        async with cls._lock:
            if not cls._initialized:
                logger.warning("Services not initialized")
                return

            logger.info("Shutting down services")
            
            # Ensure AI client is closed first
            if "ai_client" in cls._services:
                ai_client = cast(AIClient, cls._services["ai_client"])
                if hasattr(ai_client, 'close') and callable(getattr(ai_client, 'close')):
                    await ai_client.close()
            
            # Close database connection LAST
            if "database" in cls._services:
                db_service = cast(DatabaseService, cls._services["database"])
                await db_service.close()
            
            # Clear services
            cls._services.clear()
            cls._initialized = False
            logger.info("Services shut down successfully")

    @classmethod
    def get_service(cls, service_key: str) -> Any:
        """
        Get a service instance by key.
        
        Args:
            service_key: Key of service to get
            
        Returns:
            Instance of the requested service
            
        Raises:
            ValueError: If service is not initialized or not found
        """
        if not cls._initialized:
            raise ValueError("Services not initialized")
        
        service = cls._services.get(service_key)
        if service is None:
            raise ValueError(f"Service '{service_key}' not found or not initialized.")
        return service

    @classmethod
    def get_db_service(cls) -> DatabaseService:
        """Get the database service."""
        return cast(DatabaseService, cls.get_service("database"))

    @classmethod
    def get_context_cache_service(cls) -> ContextCacheService:
        """Get the context cache service."""
        return cast(ContextCacheService, cls.get_service("context_cache"))

    @classmethod
    def get_prompt_service(cls) -> PromptService:
        """Get the prompt service."""
        return cast(PromptService, cls.get_service("prompt_service"))

    @classmethod
    def get_ai_client(cls) -> AIClient:
        """Get the AI client."""
        return cast(AIClient, cls.get_service("ai_client"))

    @classmethod
    def get_rule_engine_service(cls) -> RuleEngineService:
        """Get the rule engine service."""
        return cast(RuleEngineService, cls.get_service("rule_engine"))

    @classmethod
    def is_initialized(cls) -> bool:
        """
        Check if services are initialized.
        
        Returns:
            bool: True if services are initialized, False otherwise
        """
        return cls._initialized

    @staticmethod
    def _ensure_directories_exist(directory: str) -> None:
        """
        Ensure that a directory exists, creating it if necessary.
        
        Args:
            directory: Directory path to check
        """
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}") 