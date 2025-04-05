#!/bin/bash

echo "Starting Project Chimera..."

# Get absolute path to project root, handling both Git Bash and WSL paths
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Project directory: $PROJECT_DIR"

# Detect environment (Git Bash/MINGW vs WSL)
if [[ "$(uname -a)" == *"MINGW"* ]]; then
    echo "Detected Git Bash environment"
    ENV_TYPE="mingw"
    VENV_PATH="$PROJECT_DIR/venv/Scripts/activate"
    # Convert Windows path to Unix-style for Python imports
    export PYTHONPATH="$PROJECT_DIR"
else
    echo "Detected WSL/Linux environment"
    ENV_TYPE="wsl"
    VENV_PATH="$PROJECT_DIR/venv/bin/activate"
    export PYTHONPATH="$PROJECT_DIR"
fi

# Check if virtual environment exists
if [ ! -f "$VENV_PATH" ]; then
    echo "Error: Virtual environment not found at $VENV_PATH"
    echo "Please run setup.sh or setup.bat to create the virtual environment"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment from $VENV_PATH"
source "$VENV_PATH"

# Create missing schema file if needed
SCHEMA_DIR="$PROJECT_DIR/src/schemas"
CONTEXT_SCHEMA="$SCHEMA_DIR/context_schemas.py"

if [ ! -f "$CONTEXT_SCHEMA" ]; then
    echo "Creating missing context_schemas.py file..."
    mkdir -p "$SCHEMA_DIR"
    cat > "$CONTEXT_SCHEMA" << 'EOF'
"""Context schemas for Chimera API."""

from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field


class ContextItem(BaseModel):
    """Base class for context items."""
    type: str = Field(..., description="Type of context item")
    content: Any = Field(..., description="Content of the context item")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class CodeContext(BaseModel):
    """Context information from code files."""
    items: List[ContextItem] = Field(default_factory=list, description="List of context items")
    workspace_root: Optional[str] = Field(None, description="Root directory of the workspace")
    timestamp: Optional[str] = Field(None, description="Timestamp when context was collected")


class ContextRequest(BaseModel):
    """Request to store context."""
    context: CodeContext = Field(..., description="Context to store")
    session_id: str = Field(..., description="Session identifier")
    overwrite: bool = Field(False, description="Whether to overwrite existing context")


class ContextResponse(BaseModel):
    """Response with stored context."""
    success: bool = Field(..., description="Whether the operation was successful")
    context_id: Optional[str] = Field(None, description="ID of the stored context")
    message: Optional[str] = Field(None, description="Additional information")
EOF
    echo "Created context_schemas.py file"
fi

# Start FastAPI web server
echo "Starting Web Server..."
uvicorn src.chimera_core.api.app:app --reload --host 0.0.0.0 --port 8000 &
WEB_PID=$!

# Wait a moment for the server to start
sleep 3

# Start MCP servers
echo "Starting Code Analysis Server..."
python -m src.chimera_stdio_mcp.server --service code_analysis &
CODE_PID=$!

echo "Starting Tools Server..."
python -m src.chimera_stdio_mcp.server --service tools &
TOOLS_PID=$!

echo
echo "Project Chimera Services Started:"
echo
echo "Web server: http://localhost:8000"
echo "MCP servers running in background"
echo
echo "To stop all services, press Ctrl+C"

# Function to handle script termination
cleanup() {
    echo "Stopping all services..."
    kill $WEB_PID $CODE_PID $TOOLS_PID 2>/dev/null
    deactivate 2>/dev/null || true
    exit 0
}

# Register the cleanup function for script termination
trap cleanup SIGINT SIGTERM

# Wait for user to press Ctrl+C
wait 