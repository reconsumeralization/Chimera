"""Chimera Core Server.

This module defines the FastAPI application for the Chimera backend server,
including route registration, middleware, and startup/shutdown events.
"""

import logging
import os
from typing import Any, Dict

import structlog
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.chimera_core.api.dependencies import initialize_services, shutdown_services
from src.chimera_core.api.routes.ai_routes import router as ai_router
from src.chimera_core.api.routes.context_routes import router as context_router
from src.chimera_core.api.routes.rule_routes import router as rule_router
from src.config.settings import load_settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    cache_logger_on_first_use=True,
)

# Get logger
logger = structlog.get_logger(__name__)

# Load settings
settings = load_settings()

# Create the FastAPI application
app = FastAPI(
    title="Project Chimera",
    description="Context-aware AI assistant for developers",
    version="0.1.0",
    docs_url="/docs" if settings.show_docs else None,
    redoc_url="/redoc" if settings.show_docs else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up static files and templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
static_dir = os.path.join(os.path.dirname(__file__), "static")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates = Jinja2Templates(directory=templates_dir) if os.path.exists(templates_dir) else None


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for all unhandled exceptions."""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# Startup event
@app.on_event("startup")
async def startup_event() -> None:
    """Initialize services and resources on server startup."""
    logger.info("Starting Chimera Core Server...")
    
    try:
        # Initialize services
        await initialize_services()
        logger.info("Services initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize services", error=str(e), exc_info=True)
        raise


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Clean up resources on server shutdown."""
    logger.info("Shutting down Chimera Core Server...")
    
    try:
        # Shutdown services
        await shutdown_services()
        logger.info("Services shut down successfully")
        
    except Exception as e:
        logger.error("Error during shutdown", error=str(e), exc_info=True)


# Register routers
app.include_router(ai_router)
app.include_router(context_router)
app.include_router(rule_router)


# Root endpoint
@app.get("/", include_in_schema=False)
async def root(request: Request) -> Dict[str, Any]:
    """Root endpoint that either returns the UI or API info."""
    # Check if templates are available
    if templates:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "title": "Project Chimera", "version": app.version}
        )
    
    # Return API info
    return {
        "name": "Project Chimera API",
        "version": app.version,
        "docs_url": "/docs" if settings.show_docs else None,
    }


# Health check endpoint
@app.get("/health", include_in_schema=False)
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"} 