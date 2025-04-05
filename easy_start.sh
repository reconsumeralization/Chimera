#!/bin/bash
# Project Chimera simplified startup script for Linux/Mac/WSL/Git Bash
# Created for accessibility - fewer components, clearer feedback

echo "=============================================="
echo "    Project Chimera - Simplified Startup"
echo "=============================================="
echo

# Get absolute path to project root
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "[INFO] Project directory: $PROJECT_DIR"

# Detect environment (Git Bash/MINGW vs WSL/Linux)
if [[ "$(uname -a)" == *"MINGW"* ]]; then
    echo "[INFO] Detected Git Bash environment"
    VENV_PATH="$PROJECT_DIR/venv/Scripts/activate"
else
    echo "[INFO] Detected WSL/Linux environment"
    VENV_PATH="$PROJECT_DIR/venv/bin/activate"
fi

# Check if virtual environment exists
if [ ! -f "$VENV_PATH" ]; then
    echo "[ERROR] Virtual environment not found at $VENV_PATH"
    echo "[HELP] Please run setup.sh first to create the environment"
    echo "       Or run: python -m venv venv"
    echo "       Then:   source $VENV_PATH && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "[INFO] Activating virtual environment..."
source "$VENV_PATH"

# Set Python path
export PYTHONPATH="$PROJECT_DIR"

# Create/update required schema files
echo "[INFO] Checking for required schema files..."
SCHEMA_DIR="$PROJECT_DIR/src/schemas"
mkdir -p "$SCHEMA_DIR"

# Start just the FastAPI server (most important component)
echo
echo "[INFO] Starting Web API Server only (simplified mode)..."
echo "[INFO] For full functionality, use ./start_chimera.sh instead"
echo
echo "[INFO] Server starting at http://localhost:8000"
echo "[INFO] Press Ctrl+C to stop the server when finished"
echo

# Start the server in the foreground for easier monitoring
uvicorn src.chimera_core.api.app:app --reload --host 0.0.0.0 --port 8000

# Cleanup - this will run when the user presses Ctrl+C
echo
echo "[INFO] Stopping server..."
deactivate 2>/dev/null || true
echo "[INFO] Server stopped." 