"""Status API endpoints for the Chimera UI."""
import asyncio
import logging
import structlog
from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List

import httpx
try:
    import psutil
except ImportError:
    psutil = None

from chimera_core.config import get_settings, Settings

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/status", tags=["Status API"])


class SystemStatus(BaseModel):
    """System status model."""
    
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    memory_available_gb: Optional[float] = None
    memory_total_gb: Optional[float] = None
    psutil_available: bool = False
    limited_info: Optional[str] = None


class ServiceStatus(BaseModel):
    """Service status model."""
    
    name: str
    connected: bool
    url: str
    details: Optional[str] = None


class SettingsUpdate(BaseModel):
    """Model for settings updates from the UI."""
    
    enable_data_collection: Optional[bool] = None
    log_level: Optional[str] = Field(None, pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    ui_server_port: Optional[int] = Field(None, gt=0, lt=65536)
    mcp_server_port: Optional[int] = Field(None, gt=0, lt=65536)
    data_anonymization: Optional[bool] = None
    
    # Add more fields as needed, matching the Settings class


async def check_service_health(url: str, timeout: float = 1.0) -> bool:
    """Check if a service is healthy by making a request to its health endpoint."""
    logger.debug("Checking service health", url=url)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            logger.debug("Service health check response", url=url, status_code=response.status_code)
            return response.status_code == 200
    except httpx.RequestError as e:
        logger.warning("Service health check failed", url=url, error=str(e))
        return False
    except Exception as e:
        logger.error("Unexpected error during service health check", url=url, error=str(e))
        return False


@router.get("/system")
async def get_system_info() -> SystemStatus:
    """Get system information."""
    logger.debug("Getting system information")
    
    status = SystemStatus(psutil_available=psutil is not None)
    
    if not psutil:
        status.limited_info = "psutil module not found. Cannot provide CPU/Memory usage."
        return status
    
    try:
        status.cpu_percent = psutil.cpu_percent(interval=0.1)
        
        memory = psutil.virtual_memory()
        status.memory_percent = memory.percent
        status.memory_total_gb = round(memory.total / (1024**3), 2)
        status.memory_available_gb = round(memory.available / (1024**3), 2)
        
        return status
    except Exception as e:
        logger.exception("Error getting system information", error=str(e))
        status.limited_info = f"Error getting system information: {str(e)}"
        return status


@router.get("/services")
async def get_services_status(settings: Settings = Depends(get_settings)) -> List[ServiceStatus]:
    """Get status of all connected services."""
    logger.debug("Getting services status")
    
    services = []
    
    # Check MCP server status
    mcp_url = f"http://{settings.mcp_server_host}:{settings.mcp_server_port}/health"
    mcp_connected = await check_service_health(mcp_url)
    services.append(
        ServiceStatus(
            name="MCP Server",
            connected=mcp_connected,
            url=mcp_url,
            details="Main MCP server for tool execution"
        )
    )
    
    # Add more services as needed
    
    return services


@router.post("/settings")
async def update_settings(
    settings_update: SettingsUpdate = Body(...),
    current_settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """Update settings from the UI."""
    logger.info("Updating settings", updates=settings_update.model_dump(exclude_unset=True))
    
    # Here we'd actually update the settings in a database or config file
    # For now, we'll just return the hypothetical new settings
    
    # Convert current settings to dict
    settings_dict = current_settings.model_dump()
    
    # Apply updates (only non-None values)
    updates = {k: v for k, v in settings_update.model_dump().items() if v is not None}
    settings_dict.update(updates)
    
    # In a real implementation, we'd persist these changes
    # But for now, just return what would be updated
    return {
        "success": True,
        "message": "Settings would be updated (not actually persisted yet)",
        "updated_settings": updates,
        "new_settings": settings_dict
    } 