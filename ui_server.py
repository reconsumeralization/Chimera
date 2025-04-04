import os
import sys
import socket
import logging
import webbrowser
import threading
import time
import random
import uvicorn
import asyncio
import html
import argparse
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
from pydantic import BaseModel, Field
import base64
import json
from typing import Optional

try:
    import platform
    import psutil
    HAS_PSUTIL = True
except ImportError:
    logging.warning("psutil module not available. System monitoring will be limited.")
    HAS_PSUTIL = False

# --- Configuration ---
HOST = "127.0.0.1"
DEFAULT_PORT = 3000  # Default UI port
MAX_PORT_ATTEMPTS = 10
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Create required directories if they don't exist
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "js"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "css"), exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DevToolkit")

# --- Port Finding Utility ---
def is_port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.1)
        try:
            s.bind((host, port))
            return True
        except (socket.error, OSError):
            return False

def find_available_port(host: str = HOST, start_port: int = DEFAULT_PORT) -> int:
    port = start_port
    for attempt in range(MAX_PORT_ATTEMPTS):
        logger.debug(f"Attempting port {port} (Attempt {attempt + 1}/{MAX_PORT_ATTEMPTS})")
        if is_port_available(host, port):
            logger.info(f"Found available port: {port}")
            return port
        port += 1
    raise RuntimeError(f"Could not find an available port starting from {start_port} after {MAX_PORT_ATTEMPTS} attempts on host {host}")

# --- FastAPI App Setup ---
app = FastAPI(title="Developer's Toolkit", version="3.0.0")

# Mount static files directory if it exists
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# --- Create default index.html if it doesn't exist ---
def create_default_template():
    index_path = os.path.join(TEMPLATES_DIR, "index.html")
    if not os.path.exists(index_path):
        logger.info("Creating default index.html template...")
        with open(index_path, "w") as f:
            f.write("""<!DOCTYPE html>
<html lang="en" data-theme="{{ theme|default('dark') }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title|default('Developer\\'s Toolkit') }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/bootstrap-icons.min.css">
</head>
<body class="bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
    <div class="container mx-auto px-4 py-8">
        <h1 class="text-3xl font-bold mb-6">{{ title|default('Developer\\'s Toolkit') }}</h1>
        <p class="mb-4">Version: {{ version|default('1.0.0') }}</p>
        <p>Connect to MCP at: {{ connection_info.cursor_url|default('') }}</p>
    </div>
    <script>
        // Safe access to settings
        const notificationsEnabled = JSON.parse('{{ notifications_enabled|default("true")|tojson }}');
        const animationsEnabled = JSON.parse('{{ animations_enabled|default("true")|tojson }}');
        const keyboardEnabled = JSON.parse('{{ keyboard_enabled|default("true")|tojson }}');
        
        // Initialize features based on server settings
        console.log(`Features: notifications=${notificationsEnabled}, animations=${animationsEnabled}, keyboard=${keyboardEnabled}`);
    </script>
</body>
</html>""")

create_default_template()

# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, ui_port: int = DEFAULT_PORT, mcp_port: int = 9999):
    """Serves the main HTML page."""
    # MCP connection info
    mcp_host = "127.0.0.1"
    
    # Construct the SSE endpoint URL
    sse_endpoint = f"http://{mcp_host}:{mcp_port}/messages/"
    
    # Create the MCP connection object
    mcp_connection = {
        "type": "mcp",
        "version": "2024-11-05",  # Using a recent version
        "endpoint": sse_endpoint,
        "id": "f086541b-6b70-4a20-a1ce-96ca927e0a74",  # UUID for this MCP server
        "name": "Enhanced Developer's Toolkit"
    }
    
    # Convert to base64 for cursor URL
    cursor_url_data = base64.b64encode(json.dumps(mcp_connection).encode()).decode()
    
    # Create the connection info object
    connection_info = {
        "cursor_url": f"cursor://connect/{cursor_url_data}",
        "cli_command": f"mcp connect localhost:{mcp_port}"
    }
    
    # Make sure index.html exists
    index_path = os.path.join(TEMPLATES_DIR, "index.html")
    if not os.path.exists(index_path):
        logger.error(f"Template file not found: {index_path}")
        create_default_template()
    
    # Additional static file URLs to include safely
    static_files = {
        "bootstrap_css": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css",
        "bootstrap_js": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js",
        "bootstrap_icons": "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css",
        "particles_js": "https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js"
    }
    
    # Optional local static files (only include if files exist)
    static_js_files = ["app.js", "services.js", "utils.js", "theme.js", "notifications.js", 
                       "animations.js", "keyboard.js", "mcp-check.js"]
    
    static_css_files = ["app.css", "services.css", "theme-transition.css", "notifications.css",
                        "animations.css", "keyboard.css"]
    
    # Add local files if they exist
    for js_file in static_js_files:
        file_path = os.path.join(STATIC_DIR, "js", js_file)
        key = f"{os.path.splitext(js_file)[0].replace('-', '_')}_js"
        static_files[key] = f"/static/js/{js_file}" if os.path.exists(file_path) else ""
        
    for css_file in static_css_files:
        file_path = os.path.join(STATIC_DIR, "css", css_file)
        key = f"{os.path.splitext(css_file)[0].replace('-', '_')}_css"
        static_files[key] = f"/static/css/{css_file}" if os.path.exists(file_path) else ""

    # Feature flags with defaults
    feature_flags = {
        "notifications_enabled": True,
        "animations_enabled": True,
        "keyboard_enabled": True
    }

    # Combine everything into template context
    template_context = {
        "request": request, 
        "connection_info": connection_info, 
        "toolkit_version": app.version,
        "current_year": datetime.now().year,
        "title": "Enhanced Developer's Toolkit",
        "description": "A powerful AI coding assistant",
        "version": "1.0.0",
        "theme": "dark",
        **feature_flags,
        **static_files
    }

    return templates.TemplateResponse("index.html", template_context)

@app.get("/system-info")
async def get_system_info():
    """Returns system information for monitoring."""
    info = {
        "timestamp": datetime.now().isoformat(),
        "hostname": socket.gethostname(),
        "python_version": sys.version,
        "server_uptime": time.time()  # This would be process uptime
    }
    
    # Add psutil info if available
    if HAS_PSUTIL:
        info.update({
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available_mb": psutil.virtual_memory().available / (1024 * 1024),
            "disk_usage_percent": psutil.disk_usage('/').percent
        })
    else:
        info["limited_info"] = "psutil module not available for detailed system monitoring"
    
    return info

async def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Enhanced Developer's Toolkit UI Server")
    parser.add_argument("--ui-port", type=int, default=DEFAULT_PORT, help="Port for UI server")
    args = parser.parse_args()
    
    # Use provided port or find an available one
    port = args.ui_port or find_available_port()
    
    print(f"Starting UI server on port {port}...")
    
    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()
    signals = (signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(shutdown(loop)))
    
    # Configure server
    config = {
        "host": HOST,
        "port": port,
        "log_level": "info"
    }
    
    # Start server
    server = uvicorn.Server(uvicorn.Config(app, **config))
    await server.serve()

async def shutdown(loop):
    """Perform graceful shutdown."""
    logger.info("Shutting down UI server...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    
    for task in tasks:
        task.cancel()
    
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

if __name__ == "__main__":
    import signal
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server terminated by user.")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1) 