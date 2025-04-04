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
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
from pydantic import BaseModel, Field
import base64
import json
from typing import Optional
import platform
import psutil
import argparse

# --- Configuration ---
HOST = "127.0.0.1"
DEFAULT_PORT = 9998
MAX_PORT_ATTEMPTS = 10
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

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

# Mount static files directory
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# --- Models (for Request Body Validation) ---
class CodeAnalysisRequest(BaseModel):
    code: str = Field(..., min_length=1, description="The code snippet to analyze")

class FilePathRequest(BaseModel):
    path: str = Field(..., min_length=1, description="Path to the file or directory")

class CommandRequest(BaseModel):
    command: str = Field(..., min_length=1, description="Command to execute")
    cwd: Optional[str] = Field(None, description="Current working directory")

class GitOperationRequest(BaseModel):
    operation: str = Field(..., min_length=1, description="Git operation to perform")
    path: Optional[str] = Field(".", description="Repository path")

class WriteFileRequest(BaseModel):
    path: str = Field(..., min_length=1, description="Path to the file")
    content: str = Field(..., min_length=1, description="Content to write")

# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, port: int = DEFAULT_PORT):
    """Serves the main HTML page."""
    # MCP connection info
    mcp_port = 9999  # The port where MCP proxy runs
    mcp_host = "127.0.0.1"
    
    # Construct the SSE endpoint URL
    sse_endpoint = f"http://{mcp_host}:{mcp_port}/messages/"
    
    # Create the MCP connection object
    mcp_connection = {
        "type": "mcp",
        "version": "2024-11-05",  # Using a recent version
        "endpoint": sse_endpoint,
        "id": "f086541b-6b70-4a20-a1ce-96ca927e0a74",  # UUID for this MCP server
        "name": "Developer's Toolkit"
    }
    
    # Convert to base64 for cursor URL
    cursor_url_data = base64.b64encode(json.dumps(mcp_connection).encode()).decode()
    
    # Create the connection info object
    connection_info = {
        "cursor_url": f"cursor://connect/{cursor_url_data}",
        "cli_command": f"mcp-proxy --sse-port {mcp_port} -- python mcp_server.py"
    }
    
    # Make sure index.html exists
    index_path = os.path.join(TEMPLATES_DIR, "index.html")
    if not os.path.exists(index_path):
         logger.error(f"Template file not found: {index_path}")
         raise HTTPException(status_code=500, detail="Server configuration error: Template not found.")

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request, 
            "connection_info": connection_info, 
            "toolkit_version": app.version,
            "current_year": datetime.now().year,
            "title": "Project Chimera",
            "description": "A powerful AI coding assistant",
            "version": "1.0.0",
            "theme": "dark",
            "notifications_enabled": True,
            "animations_enabled": True,
            "keyboard_enabled": True,
            "bootstrap_css": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css",
            "bootstrap_js": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js",
            "bootstrap_icons": "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css",
            "particles_js": "https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js",
            "app_js": "/static/js/app.js",
            "services_js": "/static/js/services.js",
            "utils_js": "/static/js/utils.js",
            "theme_js": "/static/js/theme.js",
            "theme_transition_css": "/static/css/theme-transition.css",
            "notifications_js": "/static/js/notifications.js",
            "animations_js": "/static/js/animations.js",
            "app_css": "/static/css/app.css",
            "services_css": "/static/css/services.css",
            "notifications_css": "/static/css/notifications.css",
            "animations_css": "/static/css/animations.css",
            "keyboard_css": "/static/css/keyboard.css",
            "keyboard_js": "/static/js/keyboard.js",
            "mcp_checker_js": "/static/js/mcp-check.js"
        }
    )

@app.post("/analyze", response_class=HTMLResponse)
async def analyze_code(code_request: CodeAnalysisRequest):
    """
    Analyzes the provided code snippet (simulated).
    Returns HTML fragment with analysis results.
    """
    code = code_request.code
    logger.info(f"Received code for analysis (length: {len(code)})")

    # --- Simulate AI Analysis ---
    await asyncio.sleep(random.uniform(0.5, 1.5)) # Simulate network/processing delay

    # Basic checks (replace with actual AI/logic)
    suggestions = []
    if "let " in code and "var " not in code:
         suggestions.append({
              "type": "info", "title": "Modern JS Syntax",
              "text": "Good use of `let`/`const`. Consider `const` for variables that don't get reassigned."
         })
    if "for (" in code and ".map(" not in code and ".reduce(" not in code and ".forEach(" not in code:
         suggestions.append({
              "type": "improvement", "title": "Functional Approach?",
              "text": "Consider using array methods like `map`, `reduce`, or `forEach` for potentially cleaner iteration.",
              "code": """// Example using reduce:
items.reduce((total, item) => total + item.price, 0);"""
         })
    if "==" in code and "===" not in code:
         suggestions.append({
              "type": "warning", "title": "Type Coercion",
              "text": "Found `==`. Prefer using strict equality `===` to avoid unexpected type coercion."
         })
    if not code.strip():
         suggestions.append({
              "type": "error", "title": "Empty Input",
              "text": "Received empty code. Please provide some code to analyze."
         })
    if not suggestions and code.strip():
         suggestions.append({
              "type": "success", "title": "Looking Good!",
              "text": "No immediate suggestions found by this basic simulation. Keep up the great work!"
         })

    # --- Generate HTML response fragment ---
    # Using f-strings here for simplicity, but Jinja2 could render fragments too
    html_output = "<div class='space-y-3'>"
    type_map = {
        "improvement": ("green", "wrench-adjustable-circle"),
        "warning": ("yellow", "exclamation-triangle"),
        "error": ("red", "x-octagon"),
        "info": ("blue", "info-circle"),
        "success": ("teal", "check-circle"),
    }
    for sug in suggestions:
        color, icon = type_map.get(sug['type'], ("gray", "question-circle"))
        bg_class = f"bg-{color}-500/10 dark:bg-{color}-500/20"
        border_class = f"border-{color}-500/30"
        text_class = f"text-{color}-600 dark:text-{color}-400"
        title_class = f"text-{color}-700 dark:text-{color}-300"

        html_output += f"""
        <div class="p-3 rounded {bg_class} border {border_class}">
            <h4 class="font-semibold {title_class} mb-1 flex items-center gap-2">
                <i class="bi bi-{icon}"></i>
                <span>{sug['title']}</span>
            </h4>
            <p class="text-sm {text_class} mb-1">{sug['text']}</p>
        """
        if sug.get('code'):
             # Use language-markup for plain text, or detect language if possible
             # Use html.escape on user-provided code if displaying it raw
             escaped_code = html.escape(sug['code'])
             html_output += f"""
             <pre class="bg-gray-100 dark:bg-gray-950 p-2 rounded text-xs mt-2 overflow-x-auto language-javascript">
<code class="language-javascript">{escaped_code}</code>
             </pre>
             """
        html_output += "</div>"
    html_output += "</div>"

    # Simulate potential errors
    if "error_test" in code.lower():
        raise HTTPException(status_code=503, detail="Simulated AI service unavailable.")

    return HTMLResponse(content=html_output)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serves the dashboard page."""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "toolkit_version": app.version,
            "current_year": datetime.now().year
        }
    )

@app.get("/code-analysis", response_class=HTMLResponse)
async def code_analysis(request: Request):
    """Serves the code analysis page."""
    return templates.TemplateResponse(
        "code_analysis.html",
        {
            "request": request,
            "toolkit_version": app.version,
            "current_year": datetime.now().year
        }
    )

@app.get("/terminal", response_class=HTMLResponse)
async def terminal(request: Request):
    """Serves the terminal page."""
    return templates.TemplateResponse(
        "terminal.html",
        {
            "request": request,
            "toolkit_version": app.version,
            "current_year": datetime.now().year
        }
    )

@app.get("/git", response_class=HTMLResponse)
async def git(request: Request):
    """Serves the git page."""
    return templates.TemplateResponse(
        "git.html",
        {
            "request": request,
            "toolkit_version": app.version,
            "current_year": datetime.now().year
        }
    )

@app.get("/settings", response_class=HTMLResponse)
async def settings(request: Request):
    """Serves the settings page."""
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "toolkit_version": app.version,
            "current_year": datetime.now().year
        }
    )

# --- API Routes for MCP Services ---

@app.post("/api/analyze-code")
async def api_analyze_code(request: FilePathRequest):
    """API endpoint for code analysis."""
    try:
        # This would normally call the MCP service
        # For now, we'll return a placeholder response
        return {
            "file_path": request.path,
            "size_bytes": 1024,
            "line_count": 50,
            "language": "python",
            "issues": [
                {"type": "warning", "message": "Unused import: os", "line": 5},
                {"type": "info", "message": "Missing return type hint", "line": 10}
            ],
            "metrics": {
                "characters": 1500,
                "words": 300,
                "blank_lines": 10,
                "indentation_levels": 3,
                "functions": 5,
                "classes": 2,
                "imports": 3
            }
        }
    except Exception as e:
        logger.error(f"Error in api_analyze_code: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/execute-command")
async def api_execute_command(request: CommandRequest):
    """API endpoint for executing commands."""
    try:
        # This would normally call the MCP service
        # For now, we'll return a placeholder response
        return {
            "command": request.command,
            "exit_code": 0,
            "stdout": "Command executed successfully",
            "stderr": "",
            "cwd": request.cwd or os.getcwd()
        }
    except Exception as e:
        logger.error(f"Error in api_execute_command: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/list-directory")
async def api_list_directory(request: FilePathRequest):
    """API endpoint for listing directory contents."""
    try:
        # This would normally call the MCP service
        # For now, we'll return a placeholder response
        return {
            "path": request.path,
            "items": [
                {"name": "main.py", "path": "main.py", "type": "file", "size": 1024, "modified": datetime.now().isoformat()},
                {"name": "templates", "path": "templates", "type": "directory", "size": None, "modified": datetime.now().isoformat()},
                {"name": "static", "path": "static", "type": "directory", "size": None, "modified": datetime.now().isoformat()}
            ]
        }
    except Exception as e:
        logger.error(f"Error in api_list_directory: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/read-file")
async def api_read_file(request: FilePathRequest):
    """API endpoint for reading file contents."""
    try:
        # This would normally call the MCP service
        # For now, we'll return a placeholder response
        return {
            "path": request.path,
            "content": "# This is a placeholder file content",
            "size": 1024,
            "modified": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in api_read_file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/write-file")
async def api_write_file(request: WriteFileRequest):
    """API endpoint for writing file contents."""
    try:
        # This would normally call the MCP service
        # For now, we'll return a placeholder response
        return {
            "path": request.path,
            "success": True,
            "size": len(request.content)
        }
    except Exception as e:
        logger.error(f"Error in api_write_file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/git-operations")
async def api_git_operations(request: GitOperationRequest):
    """API endpoint for git operations."""
    try:
        # This would normally call the MCP service
        # For now, we'll return a placeholder response
        if request.operation == "status":
            return {
                "branch": "main",
                "changes": [
                    {"file": "main.py", "status": "M"},
                    {"file": "new_file.txt", "status": "??"}
                ]
            }
        elif request.operation == "branch":
            return {
                "branches": ["main", "feature/new-feature", "bugfix/fix-bug"],
                "current": 0
            }
        elif request.operation == "log":
            return {
                "entries": [
                    {"hash": "abc123", "author": "User", "message": "Initial commit", "date": datetime.now().isoformat()},
                    {"hash": "def456", "author": "User", "message": "Add new feature", "date": datetime.now().isoformat()}
                ]
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported git operation: {request.operation}")
    except Exception as e:
        logger.error(f"Error in api_git_operations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/project-metrics")
async def api_project_metrics(path: str = "."):
    """API endpoint for project metrics."""
    try:
        # This would normally call the MCP service
        # For now, we'll return a placeholder response
        return {
            "path": path,
            "files": 10,
            "directories": 3,
            "total_lines": 500,
            "languages": {
                ".py": {"files": 5, "lines": 300},
                ".html": {"files": 3, "lines": 150},
                ".js": {"files": 2, "lines": 50}
            },
            "largest_files": [
                {"path": "main.py", "size": 1024, "lines": 100},
                {"path": "mcp_server.py", "size": 512, "lines": 50}
            ],
            "recent_files": [
                {"path": "main.py", "modified": datetime.now().isoformat()},
                {"path": "templates/index.html", "modified": datetime.now().isoformat()}
            ]
        }
    except Exception as e:
        logger.error(f"Error in api_project_metrics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system-info")
async def api_system_info():
    """API endpoint for system information."""
    try:
        # This would normally call the MCP service
        # For now, we'll return a placeholder response
        return {
            "platform": platform.platform(),
            "python_version": sys.version,
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "disk_usage": {"/": {"total": 1000000000, "used": 500000000, "free": 500000000, "percent": 50.0}},
            "process_id": os.getpid(),
            "working_directory": os.getcwd()
        }
    except Exception as e:
        logger.error(f"Error in api_system_info: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# --- Main Execution ---
# Define server and browser functions first, before they are used

def run_server(port=DEFAULT_PORT):
    """Run the server on the specified port."""
    try:
        uvicorn.run(app, host=HOST, port=port, log_level="info")
    except OSError as e:
        if "address already in use" in str(e).lower():
            logger.error(f"Port {port} is already in use. Please try a different port.")
            sys.exit(1)
        raise

def open_browser(port=DEFAULT_PORT):
    """Open browser after a short delay."""
    # Wait a moment for server to bind
    time.sleep(1.5)
    webbrowser.open(f"http://{HOST}:{port}/")
    logger.info(f"Browser opened at http://{HOST}:{port}/")

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Enhanced Developer's Toolkit Web Server")
    parser.add_argument("--port", type=int, default=9998, help="Port for web server")
    args = parser.parse_args()
    
    try:
        # Find an available port if one is not specified
        if 'port' in args and args.port:
            port = args.port
        else:
            port = find_available_port()
            
        # Start the server in a separate thread
        server_thread = threading.Thread(target=run_server, args=(port,), daemon=True)
        server_thread.start()
        
        # Open a browser window after a short delay
        browser_thread = threading.Thread(target=open_browser, args=(port,), daemon=True)
        browser_thread.start()
        
        # Keep the main thread alive
        server_thread.join()
    except KeyboardInterrupt:
        logger.info("Server terminated by user.")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1) 