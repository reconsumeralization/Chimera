"""Logging configuration for Project Chimera."""
import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any

import structlog
from structlog.stdlib import LoggerFactory

from ..config import get_settings


def setup_logging(log_level: Optional[str] = None) -> None:
    """
    Set up structured logging configuration.
    
    Args:
        log_level: Override log level from settings
    """
    settings = get_settings()
    
    # Use provided log level or fall back to settings
    level = log_level or settings.log_level
    
    # Ensure log directory exists
    log_dir = Path(settings.data_directory) / "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure standard library logging
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "chimera.log"),
        ],
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Set log level for specific loggers
    logging.getLogger("uvicorn").setLevel(level)
    logging.getLogger("fastapi").setLevel(level) 