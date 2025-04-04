"""Factory module for creating and connecting Chimera Core services.

This module provides functions for creating and initializing the core services
of Project Chimera, including the context cache, rule engine, and database.
"""
import os
from typing import Dict, Optional

import structlog

from .config import get_settings
from .services import ContextCacheService, DatabaseService, RuleEngineService, AIClient
from .services.context_cache import ContextCacheOptions

logger = structlog.get_logger(__name__)


class ServiceFactory:
    """Factory for creating and managing Chimera Core services."""
    
    def __init__(self):
        """Initialize the service factory."""
        self.settings = get_settings()
        self.services: Dict[str, object] = {}
        logger.info("Service factory initialized")
    
    async def create_services(self) -> None:
        """Create and initialize all core services."""
        try:
            # Ensure required directories exist
            self._ensure_directories()
            
            # Create database service
            db_service = await self.create_database_service()
            self.services["database"] = db_service
            
            # Create context cache service
            context_cache = await self.create_context_cache_service()
            self.services["context_cache"] = context_cache
            
            # Create rule engine service
            rule_engine = self.create_rule_engine_service()
            self.services["rule_engine"] = rule_engine
            
            # Create AI client service
            ai_client = self.create_ai_client()
            self.services["ai_client"] = ai_client
            
            logger.info("All core services initialized")
        
        except Exception as e:
            logger.error("Failed to create core services", error=str(e))
            raise
    
    def _ensure_directories(self) -> None:
        """Ensure that required directories exist."""
        dirs = [
            self.settings.data_directory,
            self.settings.templates_dir,
            self.settings.static_dir,
            self.settings.rules_dir,
            os.path.join(self.settings.data_directory, "context_cache"),
            os.path.join(self.settings.data_directory, "context_cache", "snapshots"),
        ]
        
        for directory in dirs:
            os.makedirs(directory, exist_ok=True)
            logger.debug("Ensured directory exists", path=directory)
    
    async def create_database_service(self) -> DatabaseService:
        """
        Create and initialize the database service.
        
        Returns:
            DatabaseService: The initialized database service
        """
        try:
            db_service = DatabaseService(echo=self.settings.debug)
            await db_service.initialize()
            
            # Test connection
            if await db_service.check_connection():
                logger.info("Database connection successful")
            else:
                logger.warning("Database connection check failed")
            
            return db_service
        
        except Exception as e:
            logger.error("Failed to create database service", error=str(e))
            raise
    
    async def create_context_cache_service(self) -> ContextCacheService:
        """
        Create and initialize the context cache service.
        
        Returns:
            ContextCacheService: The initialized context cache service
        """
        try:
            cache_dir = os.path.join(self.settings.data_directory, "context_cache")
            
            options = ContextCacheOptions(
                cache_dir=cache_dir,
                max_snapshots=self.settings.context_cache_max_snapshots,
                ttl_days=self.settings.context_cache_ttl_days,
                max_cache_size_mb=self.settings.context_cache_max_size_mb,
                enable_db_storage=True,
                enable_persistent_storage=True
            )
            
            context_cache = ContextCacheService(options)
            
            # Get initial statistics
            stats = await context_cache.get_stats()
            logger.info(
                "Context cache service created",
                total_snapshots=stats["total_snapshots"],
                total_files=stats["total_files"],
                cache_size_bytes=stats["cache_size_bytes"]
            )
            
            return context_cache
        
        except Exception as e:
            logger.error("Failed to create context cache service", error=str(e))
            raise
    
    def create_rule_engine_service(self) -> RuleEngineService:
        """
        Create and initialize the rule engine service.
        
        Returns:
            RuleEngineService: The initialized rule engine service
        """
        try:
            rule_engine = RuleEngineService(self.settings.rules_dir)
            
            # Log rule sets loaded
            rule_sets = rule_engine.get_all_rule_sets()
            rule_count = sum(len(rs.rules) for rs in rule_sets)
            
            logger.info(
                "Rule engine service created",
                rule_set_count=len(rule_sets),
                total_rules=rule_count
            )
            
            return rule_engine
        
        except Exception as e:
            logger.error("Failed to create rule engine service", error=str(e))
            raise
    
    def create_ai_client(self) -> AIClient:
        """
        Create and initialize the AI client service.
        
        Returns:
            AIClient: The initialized AI client service
        """
        try:
            # Use API key from settings
            api_key = self.settings.api_key
            
            # Create the client
            ai_client = AIClient(api_key=api_key)
            
            logger.info("AI client service created", model=ai_client.model)
            
            return ai_client
        
        except Exception as e:
            logger.error("Failed to create AI client service", error=str(e))
            raise
    
    def get_service(self, service_name: str) -> Optional[object]:
        """
        Get a service by name.
        
        Args:
            service_name: Name of the service to get
            
        Returns:
            Optional[object]: The service, or None if not found
        """
        return self.services.get(service_name)
    
    async def close_services(self) -> None:
        """Close all services and release resources."""
        try:
            # Close database connection
            db_service = self.services.get("database")
            if db_service:
                await db_service.close()
            
            # Close AI client
            ai_client = self.services.get("ai_client")
            if ai_client:
                await ai_client.close()
            
            logger.info("All services closed")
        
        except Exception as e:
            logger.error("Failed to close services", error=str(e))
            raise


# Global service factory instance
_service_factory: Optional[ServiceFactory] = None


async def init_services() -> ServiceFactory:
    """
    Initialize the global service factory and create all services.
    
    Returns:
        ServiceFactory: The initialized service factory
    """
    global _service_factory
    
    if _service_factory is None:
        _service_factory = ServiceFactory()
        await _service_factory.create_services()
    
    return _service_factory


def get_service_factory() -> Optional[ServiceFactory]:
    """
    Get the global service factory instance.
    
    Returns:
        Optional[ServiceFactory]: The service factory, or None if not initialized
    """
    return _service_factory


async def close_services() -> None:
    """Close all services and release resources."""
    global _service_factory
    
    if _service_factory:
        await _service_factory.close_services()
        _service_factory = None 