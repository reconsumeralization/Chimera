#!/usr/bin/env python3
"""
Entry point for the Chimera Core server.

This module provides the main function for starting the FastAPI application
using uvicorn server.
"""

import importlib
import logging
import os
from typing import Any, Dict, Optional

import structlog
import uvicorn
from dotenv import load_dotenv

from src.chimera_core.api.app import app
from src.config.settings import get_settings


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure structured logging with structlog.
    
    Args:
        log_level: The log level to use (default: INFO)
    """
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level),
    )
    
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, log_level)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def main() -> None:
    """Start the FastAPI application with uvicorn."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Load settings
    settings = get_settings()
    
    # Configure logging
    configure_logging(settings.log_level)
    
    # Get logger
    logger = structlog.get_logger(__name__)
    
    # Log server start
    logger.info(
        "Starting Chimera Core server",
        host=settings.host,
        port=settings.port,
        environment=settings.environment,
        debug=settings.debug,
    )
    
    # Run the application with uvicorn
    uvicorn.run(
        "src.chimera_core.api.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main() 