"""Main server module for the Chimera UI."""
import logging
import structlog
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import sys
from typing import Optional

from chimera_core.config import get_settings
from .routes import ui_routes
from .api import status_api

logger = structlog.get_logger(__name__)

# Define base directory calculation
def get_project_root() -> Path:
    """Get the project root directory."""
    # If running from src/chimera_ui/server.py
    file_path = Path(__file__).resolve()
    # Go up 3 levels: file -> chimera_ui -> src -> project_root
    return file_path.parent.parent.parent

def get_templates_dir() -> Path:
    """Get the templates directory path."""
    settings = get_settings()
    
    # Check if templates_dir is absolute
    if Path(settings.templates_dir).is_absolute():
        templates_dir = Path(settings.templates_dir)
    else:
        # Relative to project root
        templates_dir = get_project_root() / settings.templates_dir
    
    return templates_dir

def get_static_dir() -> Path:
    """Get the static files directory path."""
    settings = get_settings()
    
    # Check if static_dir is absolute
    if Path(settings.static_dir).is_absolute():
        static_dir = Path(settings.static_dir)
    else:
        # Relative to project root
        static_dir = get_project_root() / settings.static_dir
    
    return static_dir

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    # Create FastAPI app
    app = FastAPI(
        title="Project Chimera Dashboard",
        description="Web UI for the Project Chimera Developer's Toolkit",
        version="0.1.0",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # For development - restrict in production
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Find the templates directory
    templates_dir = get_templates_dir()
    if not templates_dir.exists():
        logger.warning(f"Templates directory not found: {templates_dir}")
        # Create a basic templates directory with a minimal index.html
        templates_dir.mkdir(parents=True, exist_ok=True)
        with open(templates_dir / "index.html", "w") as f:
            f.write("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{{ title }}</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
            </head>
            <body>
                <h1>{{ title }}</h1>
                <p>The templates directory was not found. This is a placeholder page.</p>
            </body>
            </html>
            """)
        logger.info(f"Created minimal templates directory at {templates_dir}")
    
    # Configure Jinja2 templates
    templates = Jinja2Templates(directory=str(templates_dir))
    
    # Set templates in the routes module
    ui_routes.set_templates(templates)
    
    # Find the static files directory
    static_dir = get_static_dir()
    if not static_dir.exists():
        logger.warning(f"Static directory not found: {static_dir}")
        # Create a basic static directory with a minimal style.css
        static_dir.mkdir(parents=True, exist_ok=True)
        with open(static_dir / "style.css", "w") as f:
            f.write("""
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                color: #333;
            }
            h1 {
                color: #0066cc;
            }
            """)
        logger.info(f"Created minimal static directory at {static_dir}")
    
    # Mount static files
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    # Include routers
    app.include_router(ui_routes.router)
    app.include_router(status_api.router)
    
    # Add startup and shutdown event handlers
    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting Chimera UI server")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down Chimera UI server")
    
    # Add request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.debug(f"Request: {request.method} {request.url.path}")
        response = await call_next(request)
        logger.debug(f"Response: {response.status_code}")
        return response
    
    return app

# Create app instance
app = create_app() 