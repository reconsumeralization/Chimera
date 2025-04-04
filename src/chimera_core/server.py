"""Chimera Core Server.

This module defines the FastAPI application for the Chimera backend server,
including route registration, middleware, and startup/shutdown events.
"""

import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any, Dict

import structlog
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from prometheus_fastapi_instrumentator import Instrumentator

from src.chimera_core.api.dependencies import initialize_services, shutdown_services
from src.chimera_core.api.routes.ai_routes import router as ai_router
from src.chimera_core.api.routes.context_routes import router as context_router
from src.chimera_core.api.routes.rule_routes import router as rule_router
from src.config.settings import load_settings
from ..config import get_settings
from ..services.service_factory import ServiceFactory
from ..utils.logging_config import setup_logging

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

# --- Lifespan Management ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events (startup/shutdown)."""
    # Startup
    setup_logging(log_level=settings.LOG_LEVEL)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} in {settings.ENVIRONMENT} mode...")
    
    # Initialize Service Factory and store on app state
    app.state.service_factory = ServiceFactory()
    await app.state.service_factory.initialize_services()
    logger.info("Services initialized.")
    
    yield # Application runs here
    
    # Shutdown
    logger.info("Shutting down services...")
    if hasattr(app.state, 'service_factory') and app.state.service_factory:
        await app.state.service_factory.shutdown_services()
    logger.info(f"{settings.APP_NAME} shutdown complete.")

# --- FastAPI App Creation ---

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# --- Middleware ---

# CORS
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    logger.info(f"CORS enabled for origins: {settings.CORS_ORIGINS}")

# Request Logging / Timing
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(
        f"{request.method} {request.url.path} - Completed in {process_time:.4f}s - Status {response.status_code}"
    )
    return response

# --- API Routers ---

# Include routers from the api module
app.include_router(context_router, prefix="/api/v1/context", tags=["Context"])
app.include_router(rule_router, prefix="/api/v1/rules", tags=["Rules"])
app.include_router(ai_router)

# --- Monitoring / Health Checks ---

@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    # Add checks for critical services (DB, AI client) if needed
    return {"status": "ok"}

# Add Prometheus instrumentation if desired
# Instrumentator().instrument(app).expose(app)

# --- Root Endpoint ---

@app.get("/", include_in_schema=False)
async def root():
    return {"message": f"Welcome to {settings.APP_NAME} v{settings.APP_VERSION}"}

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