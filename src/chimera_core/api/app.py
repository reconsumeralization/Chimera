"""Main FastAPI application for Chimera Core.

This module defines the FastAPI application instance with all routes, middleware,
and dependencies configured.
"""

import os
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import structlog
from fastapi import FastAPI, Request, staticfiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from src.chimera_core.api.routes import ai_routes, context_routes, rule_routes
from src.chimera_core.config import get_settings
from src.chimera_core.services.service_factory import ServiceFactory
from src.config.settings import ChimeraSettings

logger = structlog.get_logger(__name__)


def create_app(settings: Optional[ChimeraSettings] = None) -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Args:
        settings: Optional settings object. If None, settings will be loaded 
                 from environment variables.
    
    Returns:
        FastAPI: Configured FastAPI application
    """
    if settings is None:
        settings = get_settings()
    
    # Configure FastAPI app
    app = FastAPI(
        title="Project Chimera API",
        description="API for Project Chimera, providing AI-assisted coding tools and context-aware assistance.",
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
    
    # Setup static files
    current_dir = Path(__file__).parent.parent
    static_dir = current_dir / settings.static_dir
    os.makedirs(static_dir, exist_ok=True)
    app.mount("/static", staticfiles.StaticFiles(directory=str(static_dir)), name="static")
    
    # Setup templates
    templates_dir = current_dir / settings.templates_dir
    os.makedirs(templates_dir, exist_ok=True)
    templates = Jinja2Templates(directory=str(templates_dir))
    
    # Create a default Chimera-themed index.html if it doesn't exist
    index_path = templates_dir / "index.html"
    if not index_path.exists():
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Chimera</title>
    <style>
        :root {
            --chimera-primary: #3a5a7d;
            --chimera-secondary: #ef6c57;
            --chimera-accent: #6ba1d9;
            --chimera-bg: #f5f7fa;
            --chimera-text: #2c3e50;
            --chimera-heading: #1c2b3a;
            --chimera-light-text: #6c7686;
            --chimera-border: #e0e7ee;
            --chimera-hover: rgba(107, 161, 217, 0.1);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
        }
        
        body {
            background-color: var(--chimera-bg);
            color: var(--chimera-text);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        header {
            background-color: var(--chimera-primary);
            color: white;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        main {
            flex: 1;
            padding: 2rem;
            max-width: 1200px;
            margin: 0 auto;
            width: 100%;
        }
        
        .card {
            background-color: white;
            border-radius: 8px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 15px rgba(0,0,0,0.05);
            border: 1px solid var(--chimera-border);
        }
        
        h1, h2, h3 {
            color: var(--chimera-heading);
            margin-bottom: 1rem;
        }
        
        .status {
            display: inline-block;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: 500;
            margin-top: 1rem;
        }
        
        .status.online {
            background-color: rgba(39, 174, 96, 0.1);
            color: #27ae60;
        }
        
        .status.initializing {
            background-color: rgba(243, 156, 18, 0.1);
            color: #f39c12;
        }
        
        .status.error {
            background-color: rgba(231, 76, 60, 0.1);
            color: #e74c3c;
        }
        
        footer {
            text-align: center;
            padding: 1.5rem;
            color: var(--chimera-light-text);
            background-color: white;
            border-top: 1px solid var(--chimera-border);
        }
        
        .api-info {
            font-size: 0.9rem;
            color: var(--chimera-light-text);
            margin-top: 0.5rem;
        }
        
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-top: 2rem;
        }
        
        .feature-item {
            background-color: white;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 2px 15px rgba(0,0,0,0.05);
            border: 1px solid var(--chimera-border);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .feature-item:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.07);
        }
        
        .feature-title {
            color: var(--chimera-primary);
            font-size: 1.2rem;
            margin-bottom: 0.5rem;
        }
        
        .feature-desc {
            color: var(--chimera-text);
            font-size: 0.95rem;
            line-height: 1.5;
        }
        
        .chimera-logo {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            font-weight: 700;
            letter-spacing: -1px;
            background: linear-gradient(135deg, var(--chimera-primary), var(--chimera-accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        @media (max-width: 768px) {
            main {
                padding: 1rem;
            }
            
            .feature-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <header>
        <div class="chimera-logo">CHIMERA</div>
        <h1>Context-Aware AI Assistant</h1>
    </header>
    
    <main>
        <div class="card">
            <h2>Server Status</h2>
            <p>The Chimera Core API is currently running.</p>
            <p class="status {{ 'online' if status == 'Online' else 'initializing' if status == 'Initializing' else 'error' }}">
                {{ status }}
            </p>
            <p class="api-info">API Version: {{ api_version }}</p>
        </div>
        
        <h2>Features</h2>
        <div class="feature-grid">
            <div class="feature-item">
                <h3 class="feature-title">Context-Aware AI</h3>
                <p class="feature-desc">Chimera understands your code in context, providing more relevant assistance by knowing your project structure.</p>
            </div>
            <div class="feature-item">
                <h3 class="feature-title">Code Generation</h3>
                <p class="feature-desc">Generate code snippets, functions, or entire components with context-aware AI assistance.</p>
            </div>
            <div class="feature-item">
                <h3 class="feature-title">Code Explanation</h3>
                <p class="feature-desc">Get detailed or brief explanations of any code snippet or function in your project.</p>
            </div>
            <div class="feature-item">
                <h3 class="feature-title">Code Analysis</h3>
                <p class="feature-desc">Identify potential issues, bugs, and improvement opportunities in your code.</p>
            </div>
            <div class="feature-item">
                <h3 class="feature-title">Test Generation</h3>
                <p class="feature-desc">Automatically generate comprehensive test cases for your functions and components.</p>
            </div>
            <div class="feature-item">
                <h3 class="feature-title">Rule Engine</h3>
                <p class="feature-desc">Define custom rules to automate repetitive tasks and enforce coding standards.</p>
            </div>
        </div>
    </main>
    
    <footer>
        <p>Project Chimera &copy; 2023 - Context-aware AI coding assistant</p>
    </footer>
    
    <script>
        // Simple animation for the feature items
        document.addEventListener('DOMContentLoaded', function() {
            const featureItems = document.querySelectorAll('.feature-item');
            featureItems.forEach((item, index) => {
                item.style.opacity = '0';
                item.style.transform = 'translateY(20px)';
                
                setTimeout(() => {
                    item.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                    item.style.opacity = '1';
                    item.style.transform = 'translateY(0)';
                }, 100 + (index * 100));
            });
        });
    </script>
</body>
</html>
""")
        logger.info("Created default Chimera-themed index.html template")
    
    # Application startup event
    @app.on_event("startup")
    async def startup_event() -> None:
        """Initialize services when the application starts."""
        logger.info("Starting Chimera Core API")
        try:
            await ServiceFactory.initialize()
            logger.info("Services initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize services", error=str(e))
            raise
    
    # Application shutdown event
    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        """Shutdown services when the application shuts down."""
        logger.info("Shutting down Chimera Core API")
        try:
            await ServiceFactory.shutdown()
            logger.info("Services shut down successfully")
        except Exception as e:
            logger.error("Failed to shut down services", error=str(e))
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle all unhandled exceptions globally."""
        logger.error(
            "Unhandled exception",
            endpoint=str(request.url),
            method=request.method,
            error=str(exc),
            exc_info=exc,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error. Please check the logs for more information."},
        )
    
    # Root endpoint serving the HTML template
    @app.get("/", include_in_schema=False)
    async def root(request: Request) -> Any:
        """Serve the index page."""
        status = "Online"
        try:
            # Check if services are initialized
            if not ServiceFactory.is_initialized():
                status = "Initializing"
        except Exception:
            status = "Error"
        
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "api_version": app.version,
                "status": status,
                "base_url": settings.server_url,
            },
        )
    
    # Include routers
    app.include_router(ai_routes.router)
    app.include_router(context_routes.router)
    app.include_router(rule_routes.router)
    
    return app


app = create_app() 