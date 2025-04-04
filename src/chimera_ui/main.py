"""Main entry point for the Chimera UI server."""
import asyncio
import argparse
import logging
import structlog
import sys
import webbrowser
from pathlib import Path
import uvicorn
from typing import Optional

# Add parent directory to path if running directly
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from chimera_core.utils.network import find_available_port
from chimera_core.utils.logging_config import setup_logging
from chimera_core.config import get_settings

# Import the FastAPI app
from chimera_ui.server import app

logger = structlog.get_logger(__name__)


async def open_browser(url: str, delay: float = 1.5) -> None:
    """Open the browser after a delay."""
    await asyncio.sleep(delay)
    try:
        logger.info(f"Opening browser at {url}")
        webbrowser.open(url)
    except Exception as e:
        logger.error(f"Failed to open browser: {e}")
        logger.info(f"Please manually open {url}")


async def run_server(host: str, port: int, open_browser_flag: bool = True) -> None:
    """Run the UI server using uvicorn."""
    url = f"http://{host}:{port}"
    
    # Create task to open browser if requested
    if open_browser_flag:
        browser_task = asyncio.create_task(open_browser(url))
    
    # Configure Uvicorn
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="info",
        reload=False,  # Set to True for development
    )
    
    server = uvicorn.Server(config)
    
    try:
        logger.info(f"Starting UI server at {url}")
        await server.serve()
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        # Ensure browser task is cancelled if server stops
        if open_browser_flag and 'browser_task' in locals():
            if not browser_task.done():
                browser_task.cancel()


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Chimera UI Server")
    parser.add_argument(
        "--port", 
        type=int, 
        help="Port to run the server on (default: auto-detect)"
    )
    parser.add_argument(
        "--host", 
        type=str, 
        help=f"Host to run the server on (default: {get_settings().ui_server_host})"
    )
    parser.add_argument(
        "--no-browser", 
        action="store_true", 
        help="Don't open a browser window"
    )
    return parser.parse_args()


def main():
    """Main entry point for the UI server."""
    # Parse command line arguments
    args = parse_args()
    
    # Get settings
    settings = get_settings()
    
    # Set up logging
    setup_logging()
    
    # Determine host and port
    host = args.host or settings.ui_server_host
    
    try:
        # If port is specified, use it; otherwise find an available port
        if args.port:
            port = args.port
            logger.info(f"Using specified port: {port}")
        else:
            # Start from the UI server port in settings
            port = find_available_port(host=host, start_port=settings.ui_server_port)
            logger.info(f"Found available port: {port}")
        
        # Run the server
        asyncio.run(run_server(host, port, not args.no_browser))
    
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 