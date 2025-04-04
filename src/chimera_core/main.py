"""Entry point for running the Chimera Core FastAPI server."""

import uvicorn

from .config import get_settings

def run():
    """Run the FastAPI server using Uvicorn."""
    settings = get_settings()
    uvicorn.run(
        "src.chimera_core.server:app", # Path to the FastAPI app instance
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.DEBUG, # Enable reload only in debug mode
        workers=1 # Typically 1 worker for async apps, adjust if needed
    )

if __name__ == "__main__":
    run()