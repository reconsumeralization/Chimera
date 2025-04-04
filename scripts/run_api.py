#!/usr/bin/env python3
"""
Script to run the Chimera Core API server.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

import structlog
import uvicorn
from dotenv import load_dotenv

from src.chimera_core.utils.logging_config import setup_logging


def run_api():
    """Run the Chimera Core API server."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Get settings from environment variables
    host = os.getenv("CHIMERA_HOST", "127.0.0.1")
    port = int(os.getenv("CHIMERA_PORT", "8000"))
    reload = os.getenv("CHIMERA_RELOAD", "false").lower() == "true"
    log_level = os.getenv("CHIMERA_LOG_LEVEL", "INFO")
    
    # Setup logging
    setup_logging(log_level)
    logger = structlog.get_logger(__name__)
    
    # Log server start
    logger.info(
        "Starting Chimera Core API server",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
    )
    
    # Run the application with uvicorn
    uvicorn.run(
        "src.chimera_core.api.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level.lower(),
    )


if __name__ == "__main__":
    run_api() 