"""Routes package for the Chimera Core API.

This package contains all route modules for the Chimera Core API,
including routes for AI, context, and rules.
"""

from .ai_routes import router as ai_router

# List of all routers to be included in the API
routers = [
    ai_router,
] 