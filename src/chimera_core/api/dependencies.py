"""FastAPI dependencies for the Chimera API.

This module provides dependencies for FastAPI routes, including service injections
and authentication.
"""

from typing import Annotated, Optional

import structlog
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from src.chimera_core.config import get_settings
from src.chimera_core.services.ai_client import AIClient
from src.chimera_core.services.context_cache import ContextCacheService
from src.chimera_core.services.database import DatabaseService
from src.chimera_core.services.prompt_service import PromptService
from src.chimera_core.services.rule_engine import RuleEngineService
from src.chimera_core.services.service_factory import ServiceFactory

logger = structlog.get_logger(__name__)

# API Key security schema
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> bool:
    """
    Verify the API key if authentication is enabled.
    
    Args:
        api_key: The API key from the request header
        
    Returns:
        bool: True if the API key is valid or authentication is disabled
        
    Raises:
        HTTPException: If the API key is invalid
    """
    settings = get_settings()
    
    # Check if API key validation is disabled
    if not getattr(settings, "enable_api_auth", True):
        return True
    
    # Get the configured API key
    configured_api_key = getattr(settings, "api_key", None)
    
    # If no API key is configured, authentication is effectively disabled
    if not configured_api_key:
        return True
    
    # Validate the API key
    if api_key != configured_api_key:
        logger.warning("Invalid API key provided", provided_key=api_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": API_KEY_NAME},
        )
    
    return True


async def get_db_service() -> DatabaseService:
    """
    Get the database service.
    
    Returns:
        DatabaseService: The database service
        
    Raises:
        HTTPException: If the service is not initialized
    """
    try:
        return ServiceFactory.get_db_service()
    except ValueError as e:
        logger.error("Failed to get database service", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service not available",
        )


async def get_context_cache_service() -> ContextCacheService:
    """
    Get the context cache service.
    
    Returns:
        ContextCacheService: The context cache service
        
    Raises:
        HTTPException: If the service is not initialized
    """
    try:
        return ServiceFactory.get_context_cache_service()
    except ValueError as e:
        logger.error("Failed to get context cache service", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Context cache service not available",
        )


async def get_prompt_service() -> PromptService: # type: ignore
    """
    Get the prompt service.
    
    Returns:
        PromptService: The prompt service
        
    Raises:
        HTTPException: If the service is not initialized
    """
    try:
        return ServiceFactory.get_prompt_service()
    except ValueError as e:
        logger.error("Failed to get prompt service", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prompt service not available",
        )


async def get_ai_client() -> AIClient:
    """
    Get the AI client.
    
    Returns:
        AIClient: The AI client
        
    Raises:
        HTTPException: If the service is not initialized
    """
    try:
        return ServiceFactory.get_ai_client()
    except ValueError as e:
        logger.error("Failed to get AI client", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not available",
        )


async def get_rule_engine_service() -> RuleEngineService:
    """
    Get the rule engine service.
    
    Returns:
        RuleEngineService: The rule engine service
        
    Raises:
        HTTPException: If the service is not initialized
    """
    try:
        return ServiceFactory.get_rule_engine_service()
    except ValueError as e:
        logger.error("Failed to get rule engine service", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rule engine service not available",
        )


# Create annotated dependencies for use in route functions
DBService = Annotated[DatabaseService, Depends(get_db_service)]
ContextService = Annotated[ContextCacheService, Depends(get_context_cache_service)]
PromptService = Annotated[PromptService, Depends(get_prompt_service)]
AIService = Annotated[AIClient, Depends(get_ai_client)]
RuleService = Annotated[RuleEngineService, Depends(get_rule_engine_service)]
APIKey = Annotated[bool, Depends(verify_api_key)] 