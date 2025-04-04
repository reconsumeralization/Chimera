"""UI routes for serving HTML pages."""
import logging
import structlog
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Any, Dict

from chimera_core.config import get_settings, Settings

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["UI Pages"], include_in_schema=False)

# Templates are initialized in server.py and passed here
# This is a placeholder that will be set by the server
templates: Jinja2Templates = None


def get_templates() -> Jinja2Templates:
    """Get the templates instance, raising an error if not initialized."""
    if templates is None:
        raise HTTPException(
            status_code=500, 
            detail="Template engine not configured"
        )
    return templates


def set_templates(templates_instance: Jinja2Templates) -> None:
    """Set the templates instance for the routes."""
    global templates
    templates = templates_instance


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request, 
    templates: Jinja2Templates = Depends(get_templates),
    settings: Settings = Depends(get_settings)
):
    """Serve the main dashboard page."""
    logger.info("Serving dashboard index page")
    
    # Gather any data needed for the template
    context = {
        "request": request,
        "title": "Project Chimera Dashboard",
        "version": "0.1.0",
        "data_collection_enabled": settings.enable_data_collection,
    }
    
    try:
        return templates.TemplateResponse("index.html", context)
    except Exception as e:
        logger.exception("Failed to render index template", error=str(e))
        raise HTTPException(
            status_code=500, 
            detail=f"Error rendering dashboard: {str(e)}"
        )


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request, 
    templates: Jinja2Templates = Depends(get_templates),
    settings: Settings = Depends(get_settings)
):
    """Serve the settings page."""
    logger.info("Serving settings page")
    
    # Convert settings to dict for template
    settings_dict = {
        k: v for k, v in settings.model_dump().items() 
        if not k.startswith("_")
    }
    
    context = {
        "request": request,
        "title": "Project Chimera Settings",
        "settings": settings_dict,
    }
    
    try:
        return templates.TemplateResponse("settings.html", context)
    except Exception as e:
        logger.exception("Failed to render settings template", error=str(e))
        raise HTTPException(
            status_code=500, 
            detail=f"Error rendering settings page: {str(e)}"
        )


@router.get("/mcp-monitor", response_class=HTMLResponse)
async def mcp_monitor(
    request: Request, 
    templates: Jinja2Templates = Depends(get_templates)
):
    """Serve the MCP monitoring page."""
    logger.info("Serving MCP monitor page")
    
    context = {
        "request": request,
        "title": "MCP Activity Monitor",
    }
    
    try:
        return templates.TemplateResponse("mcp_monitor.html", context)
    except Exception as e:
        logger.exception("Failed to render MCP monitor template", error=str(e))
        raise HTTPException(
            status_code=500, 
            detail=f"Error rendering MCP monitor page: {str(e)}"
        ) 